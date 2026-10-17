"""
Merge the OpenAlex update-search records (S001-S494) with the evidence-log stream, check venue credibility,
and produce the combined review table and PRISMA counts.

    python Analysis/screening/merge_extraction.py      # evidence-log stream first
    python Analysis/screening/merge_update_search.py

Inputs:  extracted_studies.csv (log stream), search/search_ta_final.csv, search/ft_full_1..3.json,
         search/ft_light_1..4.json, search/search_log.csv, search/search_results.csv
Outputs: review_studies.csv (all full-text-assessed records, both streams), prisma_counts_combined.csv,
         venue_check.csv, fulltext_requests_combined.csv
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent
S = D / "search"
UA = {"User-Agent": "E04-IRP-search/1.0 (university student project)"}
DIMS = ["authenticity", "capability_verification", "integrity_security", "lo_alignment",
        "appropriate_ai_use", "scalability", "workload", "feasibility", "process_visibility",
        "accessibility_equity"]

# ---------------------------------------------------------------- update-search extraction
recs = []
for name in [f"ft_full_{k}.json" for k in (1, 2, 3)] + [f"ft_light_{k}.json" for k in (1, 2, 3, 4)]:
    level = "full" if "full" in name else "light"
    for r in json.load(open(S / name, encoding="utf-8")):
        r["extraction_level"] = level
        recs.append(r)

# Full-text re-extractions of papers first extracted from abstracts (team-supplied PDFs, 17 Oct 2026).
_rx = S / "ft_reextract_requested.json"
if _rx.exists():
    _by = {r["record_id"]: r for r in json.load(open(_rx, encoding="utf-8"))}
    recs = [dict(_by[r["record_id"]], extraction_level=r["extraction_level"]) if r["record_id"] in _by else r for r in recs]

# Adjudicated corrections (human adjudicator, 17 Oct 2026) are applied in ADJ below after review.
ADJ = json.load(open(S / "adjudication.json", encoding="utf-8")) if (S / "adjudication.json").exists() else {}
for r in recs:
    if r["record_id"] in ADJ:
        r.update(ADJ[r["record_id"]])


def row(r):
    q = r.get("quality") or {}
    out = {
        "Record ID": r["record_id"], "stream": "update search", "title": r.get("title"), "authors": r.get("authors"),
        "year": r.get("year"), "venue": r.get("venue"), "doi": r.get("doi"),
        "fulltext_status": r.get("fulltext_status"), "ft_decision": r.get("ft_decision"),
        "ft_exclusion_code": r.get("ft_exclusion_code") or "", "ft_reason": r.get("ft_reason"),
        "study_design": r.get("study_design"), "country": r.get("country"), "discipline": r.get("discipline"),
        "computing": r.get("computing"), "level": r.get("level"), "sample": r.get("sample"),
        "evidence_type": r.get("evidence_type"),
        "assessment_types": "; ".join(r.get("assessment_types") or []),
        "key_findings": " | ".join(f"{f.get('finding')} [{f.get('location')}]" for f in r.get("key_findings") or []),
        "author_recommendations": " | ".join(r.get("author_recommendations") or []),
        "limitations": r.get("limitations"), "redesign_relevance": r.get("redesign_relevance", ""),
        "redesign_note": r.get("redesign_note", ""), "quality_score": q.get("quality_score"),
        "quality_note": q.get("note", ""), "extraction_level": r.get("extraction_level"),
    }
    for d in DIMS:
        out[f"dim_{d}"] = (r.get("dimensions") or {}).get(d, "")
    return out


us = pd.DataFrame([row(r) for r in recs])
us["evidence_tier"] = us.ft_decision.map(lambda d: "Supporting" if d == "Include" else "")
us["team_log_decision"] = ""

log = pd.read_csv(D / "extracted_studies.csv")
log["stream"] = "evidence log"
log["extraction_level"] = "full"
allst = pd.concat([log, us], ignore_index=True)

# ---------------------------------------------------------------- venue credibility check (included only)
KNOWN = ["elsevier", "springer", "wiley", "taylor", "routledge", "ieee", "acm", "association for computing",
         "sage", "mdpi", "frontiers", "emerald", "iop", "oxford", "cambridge", "bmc", "plos", "aaai",
         "informa", "nature", "american psychological", "teqsa", "jutlp", "university of wollongong",
         "australasian society", "ascilite", "dove", "bmj", "hindawi"]


def call(url):
    for a in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except Exception:  # noqa: BLE001
            time.sleep(2 + 3 * a)
    return {}


inc = allst[allst.ft_decision == "Include"]
vc = []
for _, r in inc.iterrows():
    doi = str(r.doi or "").replace("https://doi.org/", "")
    src, info = {}, {}
    if doi and doi.lower() not in ("nan", "not reported", ""):
        w = call("https://api.openalex.org/works/doi:" + urllib.parse.quote(doi) + "?select=primary_location")
        src = ((w.get("primary_location") or {}).get("source") or {})
        if src.get("id"):
            info = call("https://api.openalex.org/sources/" + src["id"].split("/")[-1]
                        + "?select=display_name,host_organization_name,is_in_doaj,is_core,works_count,type")
        time.sleep(0.3)
    pub = (info.get("host_organization_name") or "")
    known = any(k in (pub + " " + str(r.venue)).lower() for k in KNOWN)
    flag = "" if (info.get("is_core") or known) else "check venue"
    vc.append({"Record ID": r["Record ID"], "venue": r.venue, "openalex_source": info.get("display_name", ""),
               "publisher": pub, "is_core": info.get("is_core"), "in_doaj": info.get("is_in_doaj"),
               "source_type": info.get("type"), "works_count": info.get("works_count"), "flag": flag})
vc = pd.DataFrame(vc)
vc.to_csv(D / "venue_check.csv", index=False)
allst = allst.merge(vc[["Record ID", "flag"]].rename(columns={"flag": "venue_flag"}), on="Record ID", how="left")
# Human adjudication (17 Oct 2026): venues whose peer review could not be verified are kept at low weight.
# They may corroborate but never be the sole support for a D2/D3 rating (sensitivity check in the report).
LOW_VENUE = {"S010", "S023", "S048", "S092", "S113", "S193", "S206", "S214", "S331", "S431", "S451", "S453",
             "S454", "S467"}
allst["venue_weight"] = allst["Record ID"].map(lambda r: "low-confidence venue" if r in LOW_VENUE else "")
allst.to_csv(D / "review_studies.csv", index=False)

# ---------------------------------------------------------------- combined PRISMA 2020
lp = pd.read_csv(D / "prisma_counts.csv").set_index("stage")["n"]
slog = pd.read_csv(S / "search_log.csv")
sres = pd.read_csv(S / "search_results.csv")
sta = pd.read_csv(S / "search_ta_final.csv")
uinc = us[us.ft_decision == "Include"]
uexc = us[us.ft_decision == "Exclude"]
tot_inc = allst[allst.ft_decision == "Include"]
p = [
    ("A. Evidence-log stream: records identified (team lists + team-supplied papers)",
     int(lp["Records identified from team-compiled source lists"]
         + lp["Records identified from other sources (team-supplied papers, 17 Oct)"])),
    ("A. duplicates removed", int(lp["Duplicates removed"])),
    ("A. screened at title/abstract", int(lp["Records screened (title/abstract)"])),
    ("A. excluded at title/abstract", int(lp["Records excluded at title/abstract"])),
    ("A. full texts assessed", int(lp["Reports sought for retrieval"])),
    ("A. excluded at full text (incl. Amendment 3 redesign rule)", int(lp["Reports excluded at full-text stage"])),
    ("A. included", int(lp["Studies included in review"])),
    ("B. Update search: hits across 9 strings (with overlap)", int(slog.hits.sum())),
    ("B. unique records retrieved", len(sres)),
    ("B. already in evidence log (duplicates removed)", int((sres.already_in_log.fillna("") != "").sum())),
    ("B. screened at title/abstract", len(sta)),
    ("B. excluded at title/abstract", int((sta.ta_final == "Exclude").sum())),
    ("B. full texts sought", len(us)),
    ("B.   assessed with full text", int((~us.fulltext_status.str.contains("abstract only", na=False)).sum())),
    ("B.   assessed on abstract only (no legal full text)",
     int(us.fulltext_status.str.contains("abstract only", na=False).sum())),
    ("B. excluded at full text", len(uexc)),
] + [(f"B.   of which {c}", int(n)) for c, n in uexc.ft_exclusion_code.value_counts().items()] + [
    ("B. included", len(uinc)),
    ("TOTAL studies included in review", len(tot_inc)),
    ("  Core (team log Include)", int((tot_inc.evidence_tier == "Core").sum())),
    ("  Supporting", int((tot_inc.evidence_tier == "Supporting").sum())),
    ("  computing-specific (Y)", int((tot_inc.computing == "Y").sum())),
    ("  a_redesign", int((tot_inc.redesign_relevance == "a_redesign").sum())),
    ("  b_informs_redesign", int((tot_inc.redesign_relevance == "b_informs_redesign").sum())),
    ("  full text", int((~tot_inc.fulltext_status.str.contains("abstract only", na=False)).sum())),
    ("  abstract only", int(tot_inc.fulltext_status.str.contains("abstract only", na=False).sum())),
    ("  low-confidence venue (kept at low weight)", int((tot_inc.venue_weight != "").sum())),
]
pd.DataFrame(p, columns=["stage", "n"]).to_csv(D / "prisma_counts_combined.csv", index=False)
for s, n in p:
    print(f"{s:80s} {n}")
need = tot_inc[tot_inc.fulltext_status.str.contains("abstract only", na=False)][
    ["Record ID", "authors", "year", "title", "venue", "doi", "computing", "redesign_relevance"]]
need.to_csv(D / "fulltext_requests_combined.csv", index=False)
