"""
Build Analysis/Literature_Review_Evidence.xlsx from the screening and extraction outputs.

    python Analysis/screening/build_review_workbook.py

Run merge_extraction.py first. Every number is read from the CSV outputs.
"""
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

D = Path(__file__).resolve().parent
XLSX = D.parent / "Literature_Review_Evidence.xlsx"

st = pd.read_csv(D / "review_studies.csv")
prisma = pd.read_csv(D / "prisma_counts_combined.csv")
agree = pd.concat([pd.read_csv(D / "ta_agreement.csv").assign(stage="Title/abstract, evidence-log stream"),
                   pd.read_csv(D / "search" / "search_ta_agreement.csv").assign(stage="Title/abstract, update search")])
rdm = pd.read_csv(D / "redesign_merged.csv")
_x, _y = rdm.redesign_relevance_A, rdm.redesign_relevance_B
_po = (_x == _y).mean(); _pe = sum((_x == c).mean() * (_y == c).mean() for c in set(_x) | set(_y))
agree = pd.concat([agree, pd.DataFrame([{"comparison": "Redesign relevance (a/b/c), Amendment 3", "n": len(rdm),
                   "pct_agreement": _po, "cohens_kappa": (_po - _pe) / (1 - _pe),
                   "stage": "Full text, evidence-log stream"}])])
ta = pd.read_csv(D / "ta_final_decisions.csv")
sta = pd.read_csv(D / "search" / "search_ta_final.csv")
meta = pd.read_csv(D / "metadata_fetched.csv").fillna("")

inc = st[st.ft_decision == "Include"].copy()
inc["tier_order"] = inc.evidence_tier.map({"Core": 0, "Supporting": 1})
inc = inc.sort_values(["tier_order", "Record ID"], key=lambda c: c if c.name == "tier_order"
                      else c.str[1:].astype(int)).drop(columns="tier_order")

TYPES = ["Supervised assessment", "Unsupervised formats", "Oral assessments", "Practical demonstrations",
         "Staged submissions", "Process evidence", "Personalised tasks", "AI-use declarations"]
cov = []
for t in TYPES:
    has = inc.assessment_types.fillna("").str.contains(t, regex=False)
    cov.append({"Assessment type": t, "Core studies": int((has & (inc.evidence_tier == "Core")).sum()),
                "Supporting studies": int((has & (inc.evidence_tier == "Supporting")).sum()),
                "All included": int(has.sum()),
                "Of which computing-specific": int((has & (inc.computing == "Y")).sum()),
                "Of which empirical": int((has & (inc.evidence_type == "empirical")).sum()),
                "Record IDs": ", ".join(inc.loc[has, "Record ID"])})
cov = pd.DataFrame(cov)

excl_ta = ta[ta.ta_final == "Exclude"].merge(meta[["Record ID", "title", "authors", "year"]], on="Record ID")
excl_ta = excl_ta[["Record ID", "authors", "year", "title", "exclusion_code", "reason", "resolution"]]
excl_ta.insert(4, "stage", "Title/abstract")
excl_ft = st[st.ft_decision == "Exclude"][["Record ID", "authors", "year", "title", "ft_exclusion_code", "ft_reason"]]
excl_ft = excl_ft.rename(columns={"ft_exclusion_code": "exclusion_code", "ft_reason": "reason"})
excl_ft.insert(4, "stage", "Full text")
excl_ft["resolution"] = "Full-text reviewer"
sx = sta[sta.ta_final == "Exclude"].rename(columns={"Search ID": "Record ID", "exclusion_code_A": "exclusion_code",
                                                    "reason_A": "reason"})
sx = sx.assign(authors="", stage="Title/abstract (update search)")[["Record ID", "authors", "year", "title", "stage",
                                                                   "exclusion_code", "reason", "resolution"]]
excl = pd.concat([excl_ta, excl_ft, sx])

qual = inc[["Record ID", "evidence_tier", "evidence_type", "quality_score", "quality_note"]]
qsum = (inc.groupby(["evidence_tier", "evidence_type"]).quality_score
        .agg(["count", "mean", "median", "min", "max"]).round(2).reset_index())

methods = pd.DataFrame([
    ("Purpose", "Evidence base for the structured systematic literature review (D1) supporting the Evaluation "
                "Framework (D2) and Recommendation Matrix (D3)."),
    ("Reporting standard", "PRISMA 2020 flow (sheet 'PRISMA'). Search cut-off 16 October 2026."),
    ("Identification", "Stream A: the team's evidence log (team-compiled source lists; original search strings "
                       "were not recorded) plus 8 team-supplied papers. Stream B: a documented supplementary update "
                       "search in OpenAlex on 17 Oct 2026 (9 strings; see screening/search/search_log.csv)."),
    ("Amendment 3 (redesign focus)", "17 Oct 2026: IC2 sharpened. Studies must propose, implement or evaluate an "
                                     "assessment (re)design, or give evidence that directly informs redesign. "
                                     "Labels: a_redesign, b_informs_redesign; c_not_redesign excluded (E2)."),
    ("Proportionate extraction", "Computing studies from the update search had full extraction; non-computing ones "
                                 "had a full-text eligibility check plus light extraction and act only as Supporting "
                                 "corroboration."),
    ("Venue credibility", "Venues not indexed as core, not in DOAJ and without a recognised publisher were checked "
                          "manually. 14 unverifiable venues are kept at low weight: they may corroborate but never "
                          "be the sole support for a rating."),
    ("Eligibility", "IC1 higher education; IC2 assessment design, validity or integrity as a primary or "
                    "substantial focus; IC3 GenAI or AI in assessment; IC4 peer-reviewed or formal framework "
                    "paper; IC5 2022-2026, English. Exclusion codes E1-E7 as in the evidence log Guide."),
    ("Title/abstract screening", "Two independent AI-assisted screeners (A and B). B was blinded to A's "
                                 "decisions. Disagreements were adjudicated by a human team member. Agreement "
                                 "is in sheet 'Screening agreement'."),
    ("Full-text screening and extraction", "AI-assisted extraction against a written protocol "
                                           "(screening/extraction/EXTRACTION_PROTOCOL.md). Full texts came from "
                                           "legal open-access copies and team-supplied PDFs; no paywall was "
                                           "bypassed. Findings record their location in the source."),
    ("Quality appraisal", "Five-item checklist adapted from MMAT 2018 and CASP: clear aim; appropriate method; "
                          "adequate sample description; findings supported; limitations acknowledged. "
                          "Score 0-5. Conceptual papers score N on the sample item by design."),
    ("Evidence tiers", "Core = the team evidence log's 'Include' (21 studies). Supporting = other studies "
                       "meeting IC1-IC5 (team log 'Background'). Core studies drive the D2/D3 ratings; "
                       "supporting studies corroborate."),
    ("AI assistance disclosure", "Screening and extraction were AI-assisted (Claude), with human adjudication "
                                 "and verification. This must be declared in the report."),
    ("Reproducibility", "Scripts in Analysis/screening: fetch_metadata.py, compute_agreement.py, "
                        "finalise_ta.py, match_papers.py, merge_extraction.py, build_review_workbook.py."),
], columns=["Item", "Detail"])

with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    methods.to_excel(xw, "Read me and methods", index=False)
    prisma.rename(columns={"stage": "PRISMA stage", "n": "Records"}).to_excel(xw, "PRISMA", index=False)
    agree.round(3).to_excel(xw, "Screening agreement", index=False)
    cov.to_excel(xw, "Coverage by type", index=False)
    inc.drop(columns=["ft_decision", "ft_exclusion_code"]).to_excel(xw, "Included studies", index=False)
    qual.to_excel(xw, "Quality appraisal", index=False)
    qsum.to_excel(xw, "Quality summary", index=False)
    excl.to_excel(xw, "Excluded with reasons", index=False)

wb = load_workbook(XLSX)
head = PatternFill("solid", fgColor="1C5CAB")
thin = Side(style="thin", color="D0D0D0")
for ws in wb.worksheets:
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = head
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
    for col in ws.columns:
        longest = max(len(str(c.value or "")) for c in col)
        ws.column_dimensions[col[0].column_letter].width = min(max(longest + 2, 10), 60)
wb.save(XLSX)
print("Wrote", XLSX, "-", len(inc), "included studies")
print(cov[["Assessment type", "Core studies", "Supporting studies", "Of which computing-specific"]].to_string(index=False))
