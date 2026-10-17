"""
Fetch verified bibliographic metadata and abstracts for evidence-log records.

Run from the IRP Working Directory:
    python Analysis/screening/fetch_metadata.py

Input:   Analysis/screening/evidence_log_snapshot.csv (exported from the evidence log, read only)
Output:  Analysis/screening/metadata_fetched.csv

Sources, in order: OpenAlex (abstract, authors, venue, year, type, open-access link),
then Crossref (fills gaps, often has the abstract for ACM / T&F), then Semantic Scholar.
Only records with a DOI are looked up; other links are kept for manual checking.
"""
import json
import re
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
SNAP = ROOT / "Analysis" / "screening" / "evidence_log_snapshot.csv"
OUT = ROOT / "Analysis" / "screening" / "metadata_fetched.csv"
UA = {"User-Agent": "E04-IRP-screening/1.0 (University of Adelaide student project)"}


def get_json(url):
    try:
        req = urllib.request.Request(url, headers=UA)
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa: BLE001 - record and move on
        return {"_error": str(e)}


def doi_of(link):
    m = re.search(r"10\.\d{4,9}/[^\s?#]+", str(link))
    return m.group(0).rstrip(".") if m else None


def openalex_abstract(inv):
    if not inv:
        return ""
    pos = {}
    for word, idx in inv.items():
        for i in idx:
            pos[i] = word
    return " ".join(pos[i] for i in sorted(pos))


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", s or "")).strip()


rows = []
snap = pd.read_csv(SNAP)
for _, rec in snap.iterrows():
    doi = doi_of(rec["DOI / Link"])
    out = {"Record ID": rec["Record ID"], "doi": doi, "link": rec["DOI / Link"],
           "title": "", "authors": "", "year": "", "venue": "", "type": "",
           "abstract": "", "oa_url": "", "source": "", "error": ""}
    if doi:
        oa = get_json("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi))
        if "_error" not in oa:
            out.update(
                title=oa.get("title") or "",
                authors="; ".join(a["author"]["display_name"] for a in oa.get("authorships", [])),
                year=oa.get("publication_year") or "",
                venue=((oa.get("primary_location") or {}).get("source") or {}).get("display_name") or "",
                type=oa.get("type") or "",
                abstract=openalex_abstract(oa.get("abstract_inverted_index")),
                oa_url=(oa.get("open_access") or {}).get("oa_url") or "",
                source="openalex")
        else:
            out["error"] = "openalex: " + oa["_error"]
        if not out["abstract"] or not out["title"]:
            cr = get_json("https://api.crossref.org/works/" + urllib.parse.quote(doi))
            m = cr.get("message", {}) if "_error" not in cr else {}
            if m:
                out["title"] = out["title"] or " ".join(m.get("title", []))
                out["authors"] = out["authors"] or "; ".join(
                    f"{a.get('given', '')} {a.get('family', '')}".strip() for a in m.get("author", []))
                out["venue"] = out["venue"] or " ".join(m.get("container-title", []))
                parts = (m.get("issued") or {}).get("date-parts") or [[None]]
                out["year"] = out["year"] or (parts[0][0] or "")
                out["type"] = out["type"] or m.get("type", "")
                if not out["abstract"] and m.get("abstract"):
                    out["abstract"] = strip_tags(m["abstract"])
                    out["source"] += "+crossref"
        if not out["abstract"]:
            ss = get_json("https://api.semanticscholar.org/graph/v1/paper/DOI:" + urllib.parse.quote(doi)
                          + "?fields=title,abstract,tldr,openAccessPdf")
            if "_error" not in ss:
                out["abstract"] = ss.get("abstract") or ((ss.get("tldr") or {}).get("text") or "")
                out["oa_url"] = out["oa_url"] or ((ss.get("openAccessPdf") or {}).get("url") or "")
                if out["abstract"]:
                    out["source"] += "+semanticscholar"
        time.sleep(0.3)
    rows.append(out)

pd.DataFrame(rows).to_csv(OUT, index=False)
df = pd.DataFrame(rows)
print(f"{len(df)} records; {df.doi.notna().sum()} with DOI; {(df.title != '').sum()} titles; "
      f"{(df.abstract.str.len() > 50).sum()} abstracts; {(df.oa_url != '').sum()} open-access links")
