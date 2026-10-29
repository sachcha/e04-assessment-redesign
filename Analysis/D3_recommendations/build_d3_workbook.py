"""
Build Analysis/D3_Recommendation_Matrix.xlsx from the calibrated D3 outputs.

    python Analysis/D3_recommendations/build_d3_workbook.py

Sheets: Read me | Recommendation Matrix (Part A, required format) | Decision Guide (Part B grid) |
        Decision Guide Detail | Monitoring Framework (Part C) | References
Citations are Record IDs; they become IEEE numbers in the final report.
"""
import json
import re
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from start_sheet import add_start_sheet

import pandas as pd
from openpyxl import load_workbook
from openpyxl.comments import Comment
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.worksheet.hyperlink import Hyperlink

D = Path(__file__).resolve().parent
XLSX = D.parent / "D3_Recommendation_Matrix.xlsx"
ORDER = ["Supervised assessment", "Unsupervised formats", "Oral assessments", "Practical demonstrations",
         "Staged submissions", "Process evidence", "Personalised tasks", "AI-use declarations"]
LOS = ["LO1 Foundational knowledge", "LO2 Programming and implementation skill",
       "LO3 Analysis, design and problem solving", "LO4 Professional and collaborative practice",
       "LO5 Critical and responsible use of AI"]
COHORTS = ["Small (<50)", "Medium (50-200)", "Large (>200)"]
bl = lambda xs: "\n".join(f"- {x}" for x in xs)


def stat_word(s):
    """Plain evidence-status label for the reading columns."""
    for k, v in (("Implemented in computing", "Implemented in computing"),
                 ("Implemented in another", "Implemented in another discipline"),
                 ("Partly", "Partly implemented"), ("Proposal", "Proposal (pilot first)")):
        if s.startswith(k):
            return v
    return s

A = {json.load(open(f, encoding="utf-8"))["assessment_type"]: json.load(open(f, encoding="utf-8"))
     for f in D.glob("out/partA_*.json")}
B = json.load(open(D / "out/partB_decision_guide.json", encoding="utf-8"))
C = json.load(open(D / "out/partC_monitoring_framework.json", encoding="utf-8"))
SUM = json.load(open(D / "out/summaries.json", encoding="utf-8"))

part_a = pd.DataFrame([{
    "Assessment Type": t, "In short: problem": SUM["partA"][t]["problem"],
    "In short: recommended redesign": SUM["partA"][t]["redesign"], "Evidence status": stat_word(A[t]["evidence_status"]),
    "Identified Problem (full)": A[t]["identified_problem"],
    "Recommended Redesign (full)": bl(A[t]["recommended_redesign"]), "Justification": A[t]["justification"],
    "Implementation Considerations": bl(A[t]["implementation_considerations"]),
    "Evidence status (full)": A[t]["evidence_status"], "Evidence status basis": A[t]["evidence_status_basis"],
    "Risks and limits": A[t]["risks_and_limits"],
    "Team strategy (Project Context s.11)": A[t].get("related_team_strategy", "")} for t in ORDER])

cells = {(c["learning_outcome"], c["cohort"]): c for c in B["cells"]}
order_cells = [(lo, co) for lo in LOS for co in COHORTS]
detail = pd.DataFrame([{
    "Learning outcome": lo, "Cohort": co, "Main assessment": cells[(lo, co)]["main_assessment"],
    "Verification layer": cells[(lo, co)]["verification_layer"], "AI-use level": cells[(lo, co)]["ai_use_level"],
    "Rationale": cells[(lo, co)]["rationale"], "Trade-offs": cells[(lo, co)]["trade_offs"],
    "Evidence status": cells[(lo, co)]["evidence_status"],
    "Key studies": ", ".join(cells[(lo, co)]["key_studies"])} for lo, co in order_cells])


def short(s, n=170):
    s = re.sub(r"\s*\[[^\]]+\](,\s*\[[^\]]+\])*", "", s).strip()
    return s if len(s) <= n else s[:n].rsplit(" ", 1)[0] + "..."


STAT = {"Implemented in computing": "IMPLEMENTED (computing)", "Implemented in another": "IMPLEMENTED (other field)",
        "Partly": "PARTLY IMPLEMENTED", "Proposal": "PROPOSAL"}


def stat(s):
    return next((v for k, v in STAT.items() if s.startswith(k)), s)


grid = pd.DataFrame([{"Learning outcome": lo, **{co: "" for co in COHORTS}} for lo in LOS])

comp = pd.DataFrame([{"Component": x["component"], "Description": x["description"],
                      "What it can evidence": x["what_it_can_evidence"], "What it cannot": x["what_it_cannot"],
                      "Evidence": x["evidence"], "Evidence status": x.get("evidence_status", "")}
                     for x in C["components"]])
c_meta = pd.DataFrame([
    ("Purpose", C["purpose"]), ("Status", C["status"]), ("Scope note", C.get("scope_note", "")),
    ("Evidence status", f"{C.get('evidence_status', '')}. {C.get('evidence_status_basis', '')}"),
    ("Core limitation", C.get("core_limitation", "")),
    ("How it combines with verification", C["how_it_combines_with_verification"]),
    ("Privacy, ethics and legal requirements", bl(C["privacy_ethics_legal_requirements"])),
    ("Implementation steps", "\n".join(f"{i + 1}. {s}" for i, s in enumerate(C["implementation_steps"]))),
    ("Open questions and validation needed", bl(C["open_questions_and_validation_needed"]))],
    columns=["Item", "Detail"])

st = pd.read_csv(D.parent / "screening" / "review_studies.csv").set_index("Record ID")
alltxt = json.dumps([A, B, C], ensure_ascii=False)
cited = sorted(set(re.findall(r"\b([RS]\d{2,3})\b", alltxt)) & set(st.index), key=lambda x: (x[0], int(x[1:])))


def ieee(r):
    au = [a.strip() for a in str(r.authors).split(";") if a.strip() and a.strip().lower() != "nan"]
    sh = lambda n: " ".join([x[0] + "." for x in n.split()[:-1]] + n.split()[-1:]) if len(n.split()) > 1 else n
    doi = str(r.doi).replace("https://doi.org/", "")
    doi = f", doi: {doi}" if doi and doi.lower() not in ("nan", "not reported", "") else ""
    yr = int(r.year) if pd.notna(r.year) else "n.d."
    return f'{", ".join(sh(x) for x in au[:6]) + (" et al." if len(au) > 6 else "")}, "{r.title}," {r.venue}, {yr}{doi}.'


refs = pd.DataFrame([{"Record ID": k, "Tier": st.loc[k, "evidence_tier"], "Computing": st.loc[k, "computing"],
                      "Quality (0-5)": st.loc[k, "quality_score"],
                      "Reference (IEEE style, to be numbered)": ieee(st.loc[k])} for k in cited])
LEGAL = [("LEG1", "Surveillance Devices Act 2016 (SA), ss 3 and 8, consolidated version 21 Sept. 2023. [Online]. Available: legislation.sa.gov.au"),
         ("LEG2", "Disability Standards for Education 2005 (Cth), F2005L00767, as amended by the Disability Standards for Education Amendment Standards 2025."),
         ("LEG3", "Adelaide University, \"Privacy Policy,\" Adelaide, SA, Australia, effective 1 Jan. 2026.")]
refs = pd.concat([refs, pd.DataFrame([{"Record ID": k, "Tier": "Legislation or policy", "Computing": "",
                                       "Quality (0-5)": "", "Reference (IEEE style, to be numbered)": v}
                                      for k, v in LEGAL])], ignore_index=True)

readme = pd.DataFrame([
    ("Deliverable", "D3 Computing Assessment Recommendation Matrix / Decision Guide. It turns the D2 evaluation into "
                    "redesign recommendations (RQ3, RQ5; brief: assessment combinations for different computing "
                    "learning outcomes and class sizes)."),
    ("Part A", "Recommendation Matrix, one row per assessment type, in the agreed format: Assessment Type | Identified "
               "Problem | Recommended Redesign | Justification | Implementation Considerations. Every problem comes "
               "from D2 ratings."),
    ("Part B", "Decision Guide: 5 learning outcomes x 3 cohort sizes. Each cell combines a main assessment, a "
               "proportionate verification layer and an AI-use level."),
    ("Part C", "AI-use monitoring framework for unsupervised assessment: the middle ground agreed in the approved scope change, "
               "a system that identifies AI use from recorded evidence rather than a text detector. A conceptual proposal, "
               "not a deployed system and not an AI detector."),
    ("Learning outcomes", "LO1 Foundational knowledge (concepts, theory, algorithms). LO2 Programming and implementation "
                          "skill. LO3 Analysis, design and problem solving. LO4 Professional and collaborative practice "
                          "(projects, client work, communication). LO5 Critical and responsible use of AI (evaluating, "
                          "verifying and correcting AI output). Based on Bloom's revised taxonomy and the outcome groupings "
                          "used in the included studies."),
    ("Cohort sizes", "Small (<50), Medium (50-200), Large (>200)."),
    ("Evidence status (Level 3)", "Implemented in computing (descriptive evidence): a similar redesign was implemented "
                                  "and reported in a computing course; this does not show it works. Implemented in "
                                  "another discipline (descriptive evidence). Partly implemented: components tried "
                                  "separately. Proposal (not yet tested). No included study evaluated a computing "
                                  "redesign with a randomised or concurrent control group."),
    ("Evidence levels", "Level 1 findings and Level 2 interpretations are in D2. D3 holds Level 3 recommendations, each "
                        "with its evidence status (Project Context s.16)."),
    ("Cross-cutting principles", bl(B["cross_cutting_principles"])),
    ("AI-use level labels", "'AI permitted with declaration' names the permitted-use level only. Declarations are "
                            "not evidence of how AI was used; that evidence is captured by the system (Part C)."),
    ("Staff time", "Staff-time figures are minimums. R84's 1,000 staff minutes per 100 students assumes 10 minutes "
                   "and one examiner. Applying R95's overruns (1.27 to 1.9 times the plan) and two examiners [S156] "
                   "gives about 1,270 to 3,800 minutes per 100 students, before scheduling and moderation."),
    ("Residual risk", "Sampled checks leave most students in large cohorts verified only by the supervised test, "
                      "for example about 80% of an LO2 large cohort when 1 in 5 are sampled."),
    ("Team strategies", "Codes in the last column of the Recommendation Matrix are the team's preliminary strategies "
                        "(Project Context s.11): A supervised assessments; B short oral viva; C multi-stage "
                        "assessment; D University-controlled GenAI environment; E AI-assisted assessment with error "
                        "correction; F AI-supported formative feedback."),
    ("Calibration", "See D3_recommendations/calibration_log.md."),
    ("Citations", "Record IDs listed in References; converted to IEEE numbers in the final report."),
], columns=["Item", "Detail"])

with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    readme.to_excel(xw, "Read me", index=False)
    part_a.to_excel(xw, "Recommendation Matrix", index=False)
    grid.to_excel(xw, "Decision Guide", index=False)
    detail.to_excel(xw, "Decision Guide Detail", index=False)
    c_meta.to_excel(xw, "Monitoring Framework", index=False, startrow=0)
    comp.to_excel(xw, "Monitoring Framework", index=False, startrow=len(c_meta) + 3)
    refs.to_excel(xw, "References", index=False)

wb = load_workbook(XLSX)
head = PatternFill("solid", fgColor="1C5CAB")
thin = Side(style="thin", color="D0D0D0")
FILL = {"[IMPLEMENTED (computing)]": "C6E7C2", "[IMPLEMENTED (other field)]": "DDEFD9",
        "[PARTLY IMPLEMENTED]": "FCE9B2", "[PROPOSAL]": "E8E8E8"}
widths = {"Read me": [22, 120], "Recommendation Matrix": [22, 34, 48, 22, 50, 60, 55, 55, 26, 45, 40, 14],
          "Decision Guide": [24, 44, 44, 44], "Decision Guide Detail": [26, 14, 45, 45, 30, 50, 40, 26, 22],
          "Monitoring Framework": [30, 60, 45, 45, 45, 26], "References": [9, 10, 9, 8, 110]}
for ws in wb.worksheets:
    ws.freeze_panes = "B2"
    for row in ws.iter_rows():
        for c in row:
            if c.value is None:
                continue
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            for k, col in FILL.items():
                if k in str(c.value):
                    c.fill = PatternFill("solid", fgColor=col)
    for c in ws[1]:
        if c.value is not None:
            c.font = Font(bold=True, color="FFFFFF"); c.fill = head
    for i, w in enumerate(widths.get(ws.title, [])):
        ws.column_dimensions[ws.cell(1, i + 1).column_letter].width = w
mf = wb["Monitoring Framework"]
for c in mf[len(c_meta) + 4]:
    if c.value is not None:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = head
dg = wb["Decision Guide"]
from openpyxl.cell.rich_text import CellRichText, TextBlock
from openpyxl.cell.text import InlineFont
B_ = InlineFont(rFont="Calibri", sz=11, b=True, color="001F5F"); N_ = InlineFont(rFont="Calibri", sz=11)
STATUS_FILL = {"Implemented in computing": "C6E7C2", "Implemented in another discipline": "E2F0D9",
               "Partly implemented": "FCE9B2", "Proposal (pilot first)": "FFF2CC"}
dg.cell(1, 1).value = "Learning outcome"
for j, co in enumerate(COHORTS):
    dg.cell(1, j + 2).value = co
for i, lo in enumerate(LOS):
    dg.row_dimensions[i + 2].height = 168
    dg.cell(i + 2, 1).font = Font(bold=True)
    dg.cell(i + 2, 1).alignment = Alignment(wrap_text=True, vertical="center")
    for j, co in enumerate(COHORTS):
        cell = dg.cell(i + 2, j + 2); x = cells[(lo, co)]; s = SUM["partB"][f"{lo[:3]}|{co}"]
        status = stat_word(x["evidence_status"])
        cell.value = CellRichText(TextBlock(B_, "Main task: "), TextBlock(N_, s["main"] + "\n\n"),
                                  TextBlock(B_, "Individual check: "), TextBlock(N_, s["check"] + "\n\n"),
                                  TextBlock(B_, "AI use: "), TextBlock(N_, s["ai"] + "\n\n"),
                                  TextBlock(B_, "Evidence: "), TextBlock(N_, status))
        cell.fill = PatternFill("solid", fgColor=STATUS_FILL.get(status, "FFFFFF"))
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        cm = Comment(f"WHY: {x['rationale']}\n\nTRADE-OFFS: {x['trade_offs']}"[:1800], "D3 evidence")
        cm.width, cm.height = 480, 320
        cell.comment = cm
        cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'Decision Guide Detail'!A{i * 3 + j + 2}")
r0 = len(LOS) + 3
dg.cell(r0, 1, "How to read").font = Font(bold=True, color="001F5F")
dg.cell(r0, 2, "Find the learning outcome (row) and class size (column). Each cell gives the main task, how each "
               "student's own understanding is checked, and what AI use is allowed. Hover over a cell for the "
               "reasoning; click it for the full row with the studies behind it.").alignment = Alignment(wrap_text=True, vertical="top")
dg.merge_cells(start_row=r0, start_column=2, end_row=r0, end_column=4)
dg.row_dimensions[r0].height = 32
dg.cell(r0 + 1, 1, "Cell colour").font = Font(bold=True, color="001F5F")
for j, (lab, col) in enumerate(list(STATUS_FILL.items())[:2] + [list(STATUS_FILL.items())[3]]):
    c = dg.cell(r0 + 1, j + 2, lab); c.fill = PatternFill("solid", fgColor=col)
    c.alignment = Alignment(horizontal="center")
dg.freeze_panes = "B2"

ra = wb["Recommendation Matrix"]
for r in range(2, ra.max_row + 1):
    ra.row_dimensions[r].height = 50
    ra.cell(r, 1).font = Font(bold=True)
    st_ = ra.cell(r, 4).value or ""
    ra.cell(r, 4).fill = PatternFill("solid", fgColor=STATUS_FILL.get(st_, "FFFFFF"))
    for c in (2, 3, 4):
        ra.cell(r, c).alignment = Alignment(wrap_text=True, vertical="top")
for c in range(1, 5):
    ra.cell(1, c).fill = PatternFill("solid", fgColor="001F5F")
ra.freeze_panes = "B2"
wb.save(XLSX)
print("Wrote", XLSX, "|", len(cited), "studies cited")

add_start_sheet(XLSX, "D3 Recommendation Matrix and Decision Guide",
    "Turns the D2 ratings into practical redesigns: one per assessment type, combinations by learning outcome "
    "and class size, and an AI-use monitoring framework.",
    ["Open 'Recommendation Matrix'. The first three columns give each assessment type's problem, the recommended "
     "redesign and its evidence status in one line each; the columns after them give the full detail.",
     "Open 'Decision Guide' and find your learning outcome (row) and class size (column). Hover over a cell, or "
     "see 'Decision Guide Detail', for the reasoning and trade-offs.",
     "Check the evidence status: 'Proposal' means it should be piloted first."],
    [("Recommendation Matrix", "One redesign per assessment type, with justification and implementation notes"),
     ("Decision Guide", "Recommended combination for each learning outcome and class size"),
     ("Decision Guide Detail", "The reasoning, trade-offs and key studies behind each Decision Guide cell"),
     ("Monitoring Framework", "The proposed AI-use evidence system, its layers and legal requirements"),
     ("References", "Every cited study and legal source"),
     ("Read me", "Definitions, evidence status labels, staff-time assumptions and principles")])
