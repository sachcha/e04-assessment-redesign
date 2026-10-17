"""
Merge the five full-text extraction batches, apply review corrections, and compute PRISMA counts.

    python Analysis/screening/merge_extraction.py

Inputs:  extraction/batch_1..5.json (first pass), extraction/reextract_1..3.json (full-text
         re-extraction of records first done from abstracts), extraction/new_records_extraction.json
         (R89-R96, added from the team's Papers/ folder), evidence_log_snapshot.csv, ta_final_decisions.csv,
         ta_new_records_screenerA.csv, and the team's E04_Evidence_Log_final.xlsx (core / background tiers)
Outputs: extraction/extraction_merged.json, extracted_studies.csv, prisma_counts.csv,
         fulltext_requests.csv (papers to download manually to upgrade abstract-only records)
"""
import json
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent
X = D / "extraction"
DIMS = ["authenticity", "capability_verification", "integrity_security", "lo_alignment",
        "appropriate_ai_use", "scalability", "workload", "feasibility", "process_visibility",
        "accessibility_equity"]

recs = []
for k in range(1, 6):
    recs += json.load(open(X / f"batch_{k}.json", encoding="utf-8"))
by_id = {r["record_id"]: r for r in recs}

# Full-text re-extractions replace abstract-only versions (team-supplied PDFs, 17 Oct 2026).
reextracted = set()
for k in range(1, 4):
    for r in json.load(open(X / f"reextract_{k}.json", encoding="utf-8")):
        by_id[r["record_id"]] = r
        reextracted.add(r["record_id"])
new_recs = json.load(open(X / "new_records_extraction.json", encoding="utf-8"))
for r in new_recs:
    by_id[r["record_id"]] = {k: v for k, v in r.items() if not k.startswith("ta_")}

# Correction 1 (superseded if R80 was re-extracted): R80 was excluded E7 because the reviewer found no abstract, but a verbatim
# abstract was already retrieved (Semantic Scholar record; see pending_for_screening_supplement.txt).
r80 = by_id["R80"]
if "R80" not in reextracted: r80.update({
    "fulltext_status": "abstract only",
    "source_used": "Semantic Scholar abstract for DOI 10.1109/TALE66047.2025.11346650",
    "ft_decision": "Include", "ft_exclusion_code": "",
    "ft_reason": "Meets IC1-IC5 on the abstract: GenAI-permitted computing assessment with prompt submission, "
                 "reflective rationale and in-person viva. Full text not legally accessible.",
    "study_design": "Practice report / case study", "country": "not reported (transnational education)",
    "discipline": "Computing (Java programming)", "computing": "Y", "level": "Undergraduate (second year)",
    "sample": "Over 750 students across two transnational programmes", "genai_tools": "GenAI (unspecified)",
    "assessment_types": ["Unsupervised formats", "Oral assessments", "AI-use declarations"],
    "key_findings": [
        {"finding": "Students could use GenAI on Java mini-projects but had to submit their prompts, give a "
                    "reflective rationale and demonstrate understanding; assessment combined a report, code and an "
                    "in-person viva.", "location": "abstract"},
        {"finding": "Prompt justification and viva sessions were reported to improve critical thinking, problem-"
                    "solving and programming understanding; impact varied with individual readiness.",
         "location": "abstract"},
        {"finding": "Clear guidance was associated with consistent engagement and fewer mark-review requests.",
         "location": "abstract"},
    ],
    "evidence_type": "empirical",
    "dimensions": {**{d: "" for d in DIMS},
        "capability_verification": "In-person viva used to check understanding of GenAI-assisted code.",
        "appropriate_ai_use": "GenAI encouraged, with prompts and a reflective rationale submitted.",
        "scalability": "Implemented with over 750 students across two programmes.",
        "process_visibility": "Submitted prompts make the AI-assisted process visible."},
    "author_recommendations": ["Combine permitted GenAI use with prompt submission and an in-person viva "
                               "(evaluated only through reported outcomes; survey results pending)."],
    "limitations": "Abstract only; outcome evidence is descriptive and the end-of-module survey was not yet reported.",
    "quality": {"q1": "Y", "q2": "Unclear", "q3": "Y", "q4": "Unclear", "q5": "N", "quality_score": 2,
                "note": "Appraised from the abstract only."},
})
# Correction 3 (17 Oct 2026, team decision): R75 is pre-GenAI (2022, CNN recommender). For consistency with
# excluding the pre-GenAI CS1QA dataset, it is excluded from the review and kept as background only.
by_id["R75"].update({"ft_decision": "Exclude", "ft_exclusion_code": "E3",
                     "ft_reason": "Pre-GenAI (2022) AI recommender; no generative AI context. Excluded for "
                                  "consistency with the currency rule applied to the CS1QA dataset; cited as "
                                  "background only."})

# Amendment 3 (17 Oct 2026): IC2 sharpened to assessment redesign. Dual classification (redesign_screenerA/B.csv)
# with human adjudication of keep/drop disagreements (R07 drop, R89 keep) and label tie-breaks (R03 -> b).
rd = pd.read_csv(D / "redesign_merged.csv").set_index("Record ID")
RD_ADJ = {"R07": "c_not_redesign", "R89": "a_redesign", "R03": "b_informs_redesign"}
for rid, r in by_id.items():
    if rid in rd.index:
        lab = RD_ADJ.get(rid, rd.loc[rid, "redesign_relevance_A"])
        r["redesign_relevance"] = lab
        if lab == "c_not_redesign" and r["ft_decision"] == "Include":
            r.update({"ft_decision": "Exclude", "ft_exclusion_code": "E2",
                      "ft_reason": "Amendment 3 (redesign focus): " + str(rd.loc[rid, "note"])})

# Correction 2: normalise out-of-protocol values flagged by reviewers.
by_id["R52"]["computing"] = "N"  # discipline not stated; UK business/humanities markers per abstract

recs = list(by_id.values())
json.dump(recs, open(X / "extraction_merged.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

rows = []
for r in recs:
    q = r.get("quality") or {}
    row = {
        "Record ID": r["record_id"], "title": r["title"], "authors": r["authors"], "year": r["year"],
        "venue": r["venue"], "doi": r["doi"], "fulltext_status": r["fulltext_status"],
        "ft_decision": r["ft_decision"], "ft_exclusion_code": r.get("ft_exclusion_code") or "",
        "ft_reason": r["ft_reason"], "study_design": r["study_design"], "country": r["country"],
        "discipline": r["discipline"], "computing": r["computing"], "level": r["level"],
        "sample": r["sample"], "evidence_type": r["evidence_type"],
        "assessment_types": "; ".join(r.get("assessment_types") or []),
        "key_findings": " | ".join(f"{f['finding']} [{f['location']}]" for f in r.get("key_findings") or []),
        "author_recommendations": " | ".join(r.get("author_recommendations") or []),
        "limitations": r["limitations"], "redesign_relevance": r.get("redesign_relevance", ""),
        "redesign_note": r.get("redesign_note", ""), "quality_score": q.get("quality_score"),
        "quality_note": q.get("note", ""),
    }
    for d in DIMS:
        row[f"dim_{d}"] = (r.get("dimensions") or {}).get(d, "")
    rows.append(row)
st = pd.DataFrame(rows)
team = pd.read_excel(D.parents[1] / "E04_Evidence_Log_final.xlsx", "Evidence Log")
team = team[team["Title"].notna()].set_index("Record ID")["Final Decision"]
st["team_log_decision"] = st["Record ID"].map(team)
st["evidence_tier"] = st.apply(lambda r: "" if r.ft_decision != "Include"
                               else ("Core" if r.team_log_decision == "Include" else "Supporting"), axis=1)
st = st.sort_values("Record ID", key=lambda c: c.str[1:].astype(int))
st.to_csv(D / "extracted_studies.csv", index=False)

# ---------------------------------------------------------------- PRISMA 2020 counts
snap = pd.read_csv(D / "evidence_log_snapshot.csv")
snap = snap[snap["Title"].notna()]                      # R89-R99 are empty template rows
ta = pd.read_csv(D / "ta_final_decisions.csv")
n_ident = len(snap)
n_dup = int((snap["Final Decision"] == "Duplicate").sum())
team_ta_excl = int(((snap["Final Decision"] == "Exclude") & (snap["Title/Abstract Screen"] == "Exclude")).sum())
ta_excl = int((ta.ta_final == "Exclude").sum()) + team_ta_excl
inc = st[st.ft_decision == "Include"]
ft_excl = st[st.ft_decision == "Exclude"]
na = pd.read_csv(D / "ta_new_records_screenerA.csv")
n_new = len(na)
prisma = [
    ("Records identified from team-compiled source lists", n_ident),
    ("Records identified from other sources (team-supplied papers, 17 Oct)", n_new),
    ("Duplicates removed", n_dup),
    ("Records screened (title/abstract)", n_ident + n_new - n_dup),
    ("Records excluded at title/abstract", ta_excl),
    ("  of which E2 not about assessment/integrity", int((ta.exclusion_code == "E2").sum())),
    ("  of which E1 not higher education", int((ta.exclusion_code == "E1").sum())),
    ("  of which E3 no AI context", int((ta.exclusion_code == "E3").sum())),
    ("  of which excluded earlier by team", team_ta_excl),
    ("Reports sought for retrieval", len(st)),
    ("Reports assessed with full text", int((st.fulltext_status != "abstract only").sum())),
    ("Reports assessed on abstract only (full text not legally accessible)",
     int((st.fulltext_status == "abstract only").sum())),
    ("Reports excluded at full-text stage", len(ft_excl)),
] + [(f"  of which {c}", int(n)) for c, n in ft_excl.ft_exclusion_code.value_counts().items()] + [
    ("Studies included in review", len(inc)),
    ("  of which core (team log Include)", int((inc.evidence_tier == "Core").sum())),
    ("  of which supporting", int((inc.evidence_tier == "Supporting").sum())),
    ("  of which computing-specific", int((inc.computing == "Y").sum())),
    ("  of which full text", int((inc.fulltext_status != "abstract only").sum())),
    ("  of which abstract only", int((inc.fulltext_status == "abstract only").sum())),
]
pd.DataFrame(prisma, columns=["stage", "n"]).to_csv(D / "prisma_counts.csv", index=False)
for s, n in prisma:
    print(f"{s:75s} {n}")

need = inc[inc.fulltext_status == "abstract only"][["Record ID", "authors", "year", "title", "venue", "doi",
                                                     "computing", "quality_score"]]
need.to_csv(D / "fulltext_requests.csv", index=False)
print("\nAbstract-only included:", len(need))
print(ft_excl[["Record ID", "ft_exclusion_code", "ft_reason"]].to_string(index=False))
