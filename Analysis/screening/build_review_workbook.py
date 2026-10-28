"""
Build Analysis/Literature_Review_Evidence.xlsx from the screening and extraction outputs.

    python Analysis/screening/build_review_workbook.py

Run merge_extraction.py first. Every number is read from the CSV outputs.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from start_sheet import add_start_sheet

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

import json, re
cited = set()
for f in list((D.parent / "D2_framework" / "cells").glob("*.json")) + list((D.parent / "D3_recommendations" / "out").glob("*.json")):
    cited |= set(re.findall(r"\b([RS]\d{2,3})\b", f.read_text(encoding="utf-8")))
inc["Cited in D2/D3"] = inc["Record ID"].isin(cited).map({True: "Yes", False: "No"})
tier = inc.set_index("Record ID").evidence_tier
d2cells = [c for f in (D.parent / "D2_framework" / "cells").glob("*.json")
           for c in json.loads(f.read_text(encoding="utf-8"))["cells"]]
ncells = len(d2cells)
mixed = sum(1 for c in d2cells if any(tier.get(k) == "Supporting" for k in c["key_studies"]))
emp = inc[inc.evidence_type == "empirical"]
core_q = pd.to_numeric(emp[emp.evidence_tier == "Core"].quality_score).mean()
supp_q = pd.to_numeric(emp[emp.evidence_tier == "Supporting"].quality_score).mean()
prisma = pd.concat([prisma, pd.DataFrame([
    {"stage": "  of which used in the D2/D3 synthesis", "n": int((inc["Cited in D2/D3"] == "Yes").sum())},
    {"stage": "  of which not cited in D2/D3 (background only)", "n": int((inc["Cited in D2/D3"] == "No").sum())}])],
    ignore_index=True)

methods = pd.DataFrame([
    ("Purpose", "Evidence base for the structured systematic literature review (D1) supporting the Evaluation "
                "Framework (D2) and Recommendation Matrix (D3)."),
    ("Reporting standard", "PRISMA 2020 flow (sheet 'PRISMA'). Update search run on 17 October 2026, covering publication years "
                           "2022-2026 up to that date."),
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
    ("Title/abstract screening", "Two independent, blinded screening runs (A and B) using Anthropic Claude (Opus 5.5), with identical instructions; "
                                 "B was blinded to A's decisions. A human team member adjudicated every "
                                 "disagreement. Kappa in sheet 'Screening agreement' therefore measures the "
                                 "consistency of the two runs, not agreement between two people."),
    ("Full-text screening and extraction", "AI-assisted extraction against a written protocol "
                                           "(screening/extraction/EXTRACTION_PROTOCOL.md). Full texts came from "
                                           "legal open-access copies and team-supplied PDFs; no paywall was "
                                           "bypassed. Findings record their location in the source."),
    ("Quality appraisal", "Five-item checklist adapted from MMAT 2018 and CASP: clear aim; appropriate method; "
                          "adequate sample description; findings supported; limitations acknowledged. "
                          "Score 0-5. Conceptual papers score N on the sample item by design."),
    ("Evidence tiers", f"Core = the team evidence log's 'Include' ({(inc.evidence_tier == 'Core').sum()} studies). Supporting = "
                       "other studies meeting IC1-IC5. Core studies were read first and are flagged in D2, but "
                       f"their mean quality is lower (empirical Core {core_q:.1f} vs Supporting {supp_q:.1f}; "
                       f"sheet 'Quality summary'). Ratings therefore also draw on Supporting studies ({mixed} of {ncells} D2 "
                       "ratings cite at least one), and High confidence needs a qualifying empirical study of "
                       "quality 4 or more."),
    ("AI assistance disclosure", "Screening and extraction were AI-assisted (Claude), with human adjudication "
                                 "and verification. This is declared in the report."),
    ("Reproducibility", "Scripts in Analysis/screening: fetch_metadata.py, compute_agreement.py, "
                        "finalise_ta.py, match_papers.py, merge_extraction.py, build_review_workbook.py."),
], columns=["Item", "Detail"])


# ---------------------------------------------------------------- reading versions of the sheets
CODE = {"E1": "Not higher education", "E2": "Not about assessment, or not focused on assessment redesign",
        "E3": "No generative AI", "E4": "Not peer reviewed", "E5": "Outside 2022-2026", "E6": "Not in English",
        "E7": "No full text available"}


def first_author(a, y):
    names = [x.strip() for x in str(a).split(";") if x.strip() and x.strip().lower() != "nan"]
    if not names:
        return f"({y})"
    sur = names[0].split()[-1]
    return f"{sur}{' et al.' if len(names) > 2 else (' and ' + names[1].split()[-1] if len(names) == 2 else '')} ({y})"


def offers(r):
    note = "" if pd.isna(r.redesign_note) else str(r.redesign_note).strip()
    if note:
        return note
    first = str(r.key_findings).split(" | ")[0]
    return re.sub(r"\s*\[[^\]]*\]\s*$", "", first).strip()


yr = lambda y: int(y) if pd.notna(y) and str(y).strip() else "n.d."
inc_read = pd.DataFrame({
    "Record ID": inc["Record ID"],
    "Study": [first_author(a, yr(y)) for a, y in zip(inc.authors, inc.year)],
    "Title": inc.title,
    "Tier": inc.evidence_tier,
    "Computing-specific": inc.computing.map({"Y": "Yes", "Partial": "Partly", "N": "No"}),
    "Assessment types it informs": inc.assessment_types.fillna("").str.replace(";", ",", regex=False),
    "What it offers for redesign": [offers(r) for r in inc.itertuples()],
    "Quality (0-5)": inc.quality_score,
    "Cited in D2/D3": inc["Cited in D2/D3"],
})
DETAIL = {"Record ID": "Record ID", "title": "Title", "authors": "Authors", "year": "Year", "venue": "Venue",
          "doi": "DOI", "fulltext_status": "Full text", "study_design": "Study design", "country": "Country",
          "discipline": "Discipline", "level": "Level", "sample": "Sample", "evidence_type": "Evidence type",
          "key_findings": "Key findings (location in the source in brackets)",
          "author_recommendations": "Author recommendations", "limitations": "Limitations",
          "redesign_relevance": "Redesign relevance", "quality_note": "Quality note",
          "dim_capability_verification": "Notes: capability verification", "dim_integrity_security": "Notes: integrity and security",
          "dim_lo_alignment": "Notes: learning-outcome alignment", "dim_authenticity": "Notes: authenticity",
          "dim_appropriate_ai_use": "Notes: appropriate AI use", "dim_process_visibility": "Notes: process visibility",
          "dim_scalability": "Notes: scalability", "dim_workload": "Notes: staff workload",
          "dim_feasibility": "Notes: feasibility and cost", "dim_accessibility_equity": "Notes: accessibility and equity",
          "team_log_decision": "Team evidence log decision", "stream": "Identification stream",
          "extraction_level": "Extraction level", "venue_flag": "Venue check", "venue_weight": "Venue weight",
          "ft_reason": "Full-text eligibility note"}
inc_detail = inc[list(DETAIL)].rename(columns=DETAIL)
inc_detail["Redesign relevance"] = inc_detail["Redesign relevance"].map(
    {"a_redesign": "Proposes or evaluates a redesign", "b_informs_redesign": "Evidence a redesign must respond to"})

def stream_of(s):
    s = str(s)
    return "Evidence log" if s.startswith("A.") else "Update search" if s.startswith("B.") else "Combined"
prisma_read = pd.DataFrame({"Stream": [stream_of(s) for s in prisma.stage],
                            "Stage": [re.sub(r"^[AB]\.\s*", "", str(s)).strip() for s in prisma.stage],
                            "Records": prisma.n})
prisma_read["Stage"] = prisma_read["Stage"].str.replace("TOTAL studies included in review", "Total studies included in the review")
PLAIN = {"Evidence-log stream: records identified (team lists + team-supplied papers)":
             "Records identified (team source lists and team-supplied papers)",
         "Update search: hits across 9 strings (with overlap)": "Hits across the 9 search strings (with overlap)",
         "Computing-specific (Y)": "Computing-specific", "Core (team log Include)": "Core tier (team evidence log 'Include')",
         "Supporting": "Supporting tier", "Full text": "Assessed with full text", "Abstract only": "Assessed on abstract only",
         "a_redesign": "Propose or evaluate an assessment redesign",
         "b_informs_redesign": "Give evidence a redesign must respond to"}
PLAIN_L = {k.lower(): v for k, v in PLAIN.items()}
prisma_read["Stage"] = prisma_read["Stage"].str.strip().map(lambda s: PLAIN_L.get(s.lower(), s))
prisma_read["Stage"] = prisma_read["Stage"].str.replace(r"^of which (E\d)$", lambda m: "  of which: " + CODE[m.group(1)][0].lower() + CODE[m.group(1)][1:], regex=True)
prisma_read["Stage"] = prisma_read["Stage"].apply(lambda s: re.sub(r"^(\s*)([a-z])", lambda m: m.group(1) + m.group(2).upper(), s))
in_total = prisma_read.Stream.eq("Combined") & ~prisma_read.Stage.str.startswith("Total")
prisma_read.loc[in_total, "Stage"] = "  " + prisma_read.loc[in_total, "Stage"]

agree_read = pd.DataFrame({"Comparison": agree.comparison, "Stage": agree.stage, "Records": agree.n,
                           "Agreement (%)": (agree.pct_agreement * 100).round(1),
                           "Cohen's kappa": agree.cohens_kappa.round(2)})
agree_read["Screeners"] = "Two independent, blinded Claude (Opus 5.5) runs; a team member settled disagreements"

qual_read = qual.rename(columns={"evidence_tier": "Tier", "evidence_type": "Evidence type",
                                 "quality_score": "Quality (0-5)", "quality_note": "Quality note"})
qsum_read = qsum.rename(columns={"evidence_tier": "Tier", "evidence_type": "Evidence type", "count": "Studies",
                                 "mean": "Mean quality", "median": "Median", "min": "Lowest", "max": "Highest"})
qsum_read["Mean quality"] = qsum_read["Mean quality"].round(1)

excl_read = excl.copy()
excl_read.insert(excl_read.columns.get_loc("exclusion_code") + 1, "Reason category",
                 excl_read.exclusion_code.map(CODE).fillna(""))
excl_read = excl_read.rename(columns={"authors": "Authors", "year": "Year", "title": "Title", "stage": "Stage",
                                      "exclusion_code": "Code", "reason": "Screener note", "resolution": "How decided"})

with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    methods.to_excel(xw, "Read me and methods", index=False)
    prisma_read.to_excel(xw, "PRISMA", index=False)
    agree_read.to_excel(xw, "Screening agreement", index=False)
    cov.to_excel(xw, "Coverage by type", index=False)
    inc_read.to_excel(xw, "Included studies", index=False)
    inc_detail.to_excel(xw, "Study details", index=False)
    qual_read.to_excel(xw, "Quality appraisal", index=False)
    qsum_read.to_excel(xw, "Quality summary", index=False)
    excl_read.to_excel(xw, "Excluded with reasons", index=False)

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
    fixed = {"Included studies": [10, 24, 50, 11, 12, 30, 60, 10, 10], "PRISMA": [16, 70, 10],
             "Screening agreement": [42, 34, 9, 12, 12, 40]}.get(ws.title)
    if fixed:
        for i, w in enumerate(fixed):
            ws.column_dimensions[ws.cell(1, i + 1).column_letter].width = w
    if ws.title == "Study details":
        ws.freeze_panes = "C2"
wb.save(XLSX)
print("Wrote", XLSX, "-", len(inc), "included studies")
print(cov[["Assessment type", "Core studies", "Supporting studies", "Of which computing-specific"]].to_string(index=False))

add_start_sheet(XLSX, "Literature Review Evidence",
    "The evidence base for the project: how studies were found and selected, and what each of the 143 included "
    "studies contributes.",
    ["Open 'PRISMA' to see how 586 screened records became 143 included studies.",
     "Open 'Included studies' for one row per study: what it offers for assessment redesign, its quality score "
     "and the assessment types it informs. The full extraction for each study is in 'Study details'.",
     "Use 'Excluded with reasons' to check any study that was left out."],
    [("PRISMA", "Study selection counts at each stage"),
     ("Included studies", "All 143 included studies, one line each: what each offers, quality and types"),
     ("Study details", "The full extraction for each study: findings with their location, sample, limitations"),
     ("Coverage by type", "How many studies support each assessment type"),
     ("Quality appraisal", "The quality score and note for each study"),
     ("Quality summary", "Average quality by tier and study type"),
     ("Screening agreement", "Agreement between the two screening runs (kappa)"),
     ("Excluded with reasons", "Every excluded record and the reason"),
     ("Read me and methods", "Eligibility criteria, screening and extraction method")])
