"""
Match the PDFs in Papers/ (read only) to evidence-log records by DOI, falling back to the title.

    python Analysis/screening/match_papers.py

Output: Analysis/screening/papers_matched.csv (one row per PDF), plus full text of each unique PDF
in Analysis/screening/extraction/text/<RecordID or file stem>.txt for extraction.
"""
import difflib
import hashlib
import re
from pathlib import Path

import pandas as pd
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
PAPERS = ROOT / "Papers"
D = ROOT / "Analysis" / "screening"
TXT = D / "extraction" / "text"
TXT.mkdir(parents=True, exist_ok=True)

meta = pd.read_csv(D / "metadata_fetched.csv").fillna("")
snap = pd.read_csv(D / "evidence_log_snapshot.csv")
titles = dict(zip(snap["Record ID"], snap["Title"].fillna("")))
dois = {r["doi"].lower(): r["Record ID"] for _, r in meta.iterrows() if r["doi"]}
norm = lambda s: re.sub(r"[^a-z0-9 ]", " ", str(s).lower()).split()

rows, seen = [], {}
for pdf in sorted(PAPERS.glob("*.pdf")):
    h = hashlib.md5(pdf.read_bytes()).hexdigest()
    try:
        reader = PdfReader(str(pdf))
        text = "\n".join((p.extract_text() or "") for p in reader.pages)
        pages = len(reader.pages)
    except Exception as e:  # noqa: BLE001
        text, pages = "", 0
    head = text[:6000]
    rid, how = "", ""
    for m in re.findall(r"10\.\d{4,9}/[^\s\"<>]+", head):
        m = m.rstrip(".,;)").lower()
        for d, r in dois.items():
            if m.startswith(d) or d.startswith(m):
                rid, how = r, "doi"
                break
        if rid:
            break
    if not rid:
        words = " ".join(norm(head[:1500] + " " + pdf.stem))
        best, score = "", 0.0
        for r, t in titles.items():
            tw = " ".join(norm(t))
            if len(tw) < 15:
                continue
            s = 1.0 if tw in words else difflib.SequenceMatcher(None, tw, " ".join(norm(pdf.stem))).ratio()
            if s > score:
                best, score = r, s
        if score >= 0.75:
            rid, how = best, f"title ({score:.2f})"
    dup_of = seen.get(h, "")
    seen.setdefault(h, pdf.name)
    first_line = re.sub(r"\s+", " ", head[:200])
    rows.append({"file": pdf.name, "record_id": rid, "match": how, "pages": pages, "chars": len(text),
                 "duplicate_file_of": dup_of, "first_text": first_line})
    if not dup_of and text:
        (TXT / f"{rid or pdf.stem[:60]}.txt").write_text(text, encoding="utf-8")

df = pd.DataFrame(rows)
df.to_csv(D / "papers_matched.csv", index=False)
print(len(df), "PDFs;", (df.duplicate_file_of == "").sum(), "unique;", (df.record_id != "").sum(), "matched")
print(df[(df.record_id == "") & (df.duplicate_file_of == "")][["file", "first_text"]].to_string(index=False))
