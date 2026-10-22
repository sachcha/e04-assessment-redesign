"""
Build Analysis/D2_Evaluation_Framework.xlsx from the calibrated cell files.

    python Analysis/D2_framework/build_d2_workbook.py

Sheets: Read me | Evaluation Matrix (required summary format) | Rating Grid | Cell Evidence | References
Citations are Record IDs here; they are converted to IEEE numbers (first-citation order) in the final report.
"""
import json
import re
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

D = Path(__file__).resolve().parent
XLSX = D.parent / "D2_Evaluation_Framework.xlsx"
ORDER = ["Supervised assessment", "Unsupervised formats", "Oral assessments", "Practical demonstrations",
         "Staged submissions", "Process evidence", "Personalised tasks", "AI-use declarations"]
DIMS = [("capability_verification", "Capability verification"), ("genai_exposure", "GenAI exposure"),
        ("authorship_assurance", "Authorship assurance"), ("lo_alignment", "Learning-outcome alignment"),
        ("authenticity", "Authenticity"), ("appropriate_ai_use", "Appropriate AI use"),
        ("process_visibility", "Process visibility"), ("scalability", "Scalability"),
        ("workload", "Staff workload"), ("feasibility", "Feasibility and cost"),
        ("accessibility_equity", "Accessibility and equity")]

rows = {}
for f in D.glob("cells/*.json"):
    j = json.load(open(f, encoding="utf-8"))
    rows[j["assessment_type"]] = j
bullets = lambda xs: "\n".join(f"- {x}" for x in xs)

DEF = json.load(open(D / "type_definitions.json", encoding="utf-8"))
TAGS = pd.read_csv(D.parent / "screening" / "review_studies.csv").fillna("")
TAGS = TAGS[TAGS.ft_decision == "Include"]
n_tagged = lambda t: int(TAGS.assessment_types.apply(lambda s: t in [x.strip() for x in s.split(";")]).sum())
summary = pd.DataFrame([{
    "Assessment Type": t, "Scope (what is rated)": DEF[t]["scope"],
    "Evaluation Finding": rows[t]["evaluation_finding"],
    "Strengths": bullets(rows[t]["strengths"]), "Limitations": bullets(rows[t]["limitations"]),
    "Practical Considerations": bullets(rows[t]["practical_considerations"]),
    "Evidence gaps": bullets(rows[t].get("evidence_gaps", [])),
    "Studies tagged with this type": n_tagged(t)} for t in ORDER])

def basis(c, n=4):
    """Key citations shown in the grid cell: up to n key studies plus any dataset codes used."""
    ks = [f"[{k}]" for k in c["key_studies"][:n]]
    ds = re.findall(r"\[(D\d\d|J\d)\]", c.get("dataset", ""))
    ks += [f"[{d}]" for d in dict.fromkeys(ds)][:2]
    return ", ".join(ks)


def note(c):
    parts = [c["literature"], c.get("dataset", ""), c["interpretation"]]
    if c.get("conflicts"):
        parts.append("Caveat: " + c["conflicts"])
    return "\n\n".join(p for p in parts if p)[:1800]


grid, grid_notes = [], {}
for i, t in enumerate(ORDER):
    cells = {c["dimension"]: c for c in rows[t]["cells"]}
    grid.append({"Assessment Type": t, **{lab: f'{cells[k]["rating"]} ({cells[k]["confidence"]})\n{basis(cells[k])}'
                                         for k, lab in DIMS}})
    for jdx, (k, lab) in enumerate(DIMS):
        grid_notes[(i + 2, jdx + 2)] = (note(cells[k]), i * len(DIMS) + jdx + 2)
grid = pd.DataFrame(grid)

ev = []
for t in ORDER:
    for c in rows[t]["cells"]:
        lab = dict(DIMS)[c["dimension"]]
        ev.append({"Assessment Type": t, "Dimension": lab, "Rating": c["rating"], "Confidence": c["confidence"],
                   "[L] Literature finding": c["literature"], "[D] Dataset finding": c["dataset"],
                   "[I] Our interpretation": c["interpretation"], "Conflicts / caveats": c["conflicts"],
                   "Cohort note": c.get("cohort_note", ""), "Key studies": ", ".join(c["key_studies"]),
                   "Supporting studies": c["n_supporting"], "Computing studies": c["computing_studies"],
                   "Core studies": c["core_studies"], "Low-confidence-venue studies": c.get("low_conf_venue_studies", 0)})
ev = pd.DataFrame(ev)

# references for every cited Record ID (IEEE-style; numbers assigned in the final report)
st = pd.read_csv(D.parent / "screening" / "review_studies.csv").set_index("Record ID")
txt = json.dumps(rows, ensure_ascii=False)
cited = sorted(set(re.findall(r"\b([RS]\d{2,3})\b", txt)) & set(st.index), key=lambda x: (x[0], int(x[1:])))


def ieee(r):
    au = [a.strip() for a in str(r.authors).split(";") if a.strip() and a.strip().lower() != "nan"]
    def short(n):
        p = n.split()
        return " ".join([x[0] + "." for x in p[:-1]] + p[-1:]) if len(p) > 1 else n
    a = ", ".join(short(x) for x in au[:6]) + (" et al." if len(au) > 6 else "")
    doi = str(r.doi).replace("https://doi.org/", "")
    doi = f", doi: {doi}" if doi and doi.lower() not in ("nan", "not reported", "") else ""
    yr = int(r.year) if pd.notna(r.year) else "n.d."
    return f'{a}, "{r.title}," {r.venue}, {yr}{doi}.'


refs = pd.DataFrame([{"Record ID": k, "Tier": st.loc[k, "evidence_tier"], "Computing": st.loc[k, "computing"],
                      "Quality (0-5)": st.loc[k, "quality_score"], "Venue weight": st.loc[k].get("venue_weight", ""),
                      "Reference (IEEE style, to be numbered)": ieee(st.loc[k])} for k in cited])
dcodes = open(D / "dataset_evidence.md", encoding="utf-8").read()

readme = pd.DataFrame([
    ("Deliverable", "D2 Assessment Strategy Evaluation Framework: eight assessment types rated on 11 dimensions for "
                    "computing higher education in the GenAI era."),
    ("Evidence base", f"{len(st[st.ft_decision == 'Include'])} included studies (Literature_Review_Evidence.xlsx) plus "
                      "our dataset analysis (D01-D28) and Jiajun's team analysis (J1-J6)."),
    ("Dimensions", "Validity: capability verification, GenAI exposure, authorship assurance, learning-outcome alignment, "
                   "authenticity. Integration: appropriate AI use, process visibility. Practicality: scalability, staff "
                   "workload, feasibility and cost, accessibility and equity. Merged from the proposal's dimensions, "
                   "the Project Context criteria and Jiajun's framework."),
    ("Ratings", "Strong / Moderate / Weak / Insufficient evidence. Strong is always the favourable end (for GenAI "
                "exposure, Strong = hard for GenAI to complete). Moderate = mixed, or depends on how the task is designed. "
                "What Strong and Weak mean for each dimension is in the sheet 'Rating anchors'."),
    ("Confidence", "CERQual-informed (adapted from GRADE-CERQual, using a study-count rule): High needs at least 3 studies including a Core or computing study rated 4 or "
                   "more, with consistent findings; Medium = 2 or more with inconsistency or weaker designs; Low = "
                   "0-1 studies or conceptual or untested evidence. A High rating also needs an empirical qualifying study; "
                   "a conceptual framework alone does not qualify. Abstract-only studies corroborate but never "
                   "qualify a rating on their own."),
    ("Evidence levels", "[L] literature finding, [D] our dataset finding, [I] our interpretation. Recommendations "
                        "(Level 3) are in D3, not here."),
    ("Calibration", "Ratings were calibrated across types (rules C1-C4) and every change is logged in "
                    "D2_framework/calibration_log.md."),
    ("Citations", "Record IDs (Rxx = evidence-log stream, Sxxx = update search) are listed in the References sheet "
                  "and converted to IEEE numbers in the final report."),
    ("Type definitions", "Each assessment type is rated in its defining form below. Weaker variants are named as "
                         "exceptions in the cells. Supervision is treated as a condition within types, not as a "
                         "separate category, so the eight types in the project brief are kept unchanged."),
] + [(f"Definition: {t}", f"{DEF[t]['scope']} Includes: {DEF[t]['includes']} Excludes: {DEF[t]['excludes']}")
     for t in ORDER] + [
    ("Dataset codes", "D01-D28 and J1-J6 are listed in full in the sheet 'Dataset codes'."),
], columns=["Item", "Detail"])

proto = (D / "SYNTHESIS_PROTOCOL.md").read_text(encoding="utf-8")
anchors = []
for line in proto.splitlines():
    m = re.match(r"\| (\d+) \| \w+ \| ([^|]+) \| ([^|]+) \| ([^|]+) \|", line)
    if m:
        anchors.append({"#": int(m.group(1)), "Dimension": m.group(2).strip(), "Strong means": m.group(3).strip(),
                        "Moderate means": "Mixed, or depends on how the task is designed (the cell says on what)",
                        "Weak means": m.group(4).strip()})
anchors = pd.DataFrame(anchors)
codes = pd.DataFrame([{"Code": m.group(1), "Source": m.group(2), "Finding and limitations": m.group(3)}
                      for m in re.finditer(r"^- \[([DJ]\d+)\] \(([^)]*)\) (.*)$", dcodes, re.M)])

with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    readme.to_excel(xw, "Read me", index=False)
    anchors.to_excel(xw, "Rating anchors", index=False)
    codes.to_excel(xw, "Dataset codes", index=False)
    summary.to_excel(xw, "Evaluation Matrix", index=False)
    grid.to_excel(xw, "Rating Grid", index=False)
    ev.to_excel(xw, "Cell Evidence", index=False)
    refs.to_excel(xw, "References", index=False)

wb = load_workbook(XLSX)
head = PatternFill("solid", fgColor="1C5CAB")
thin = Side(style="thin", color="D0D0D0")
FILL = {"Strong": "C6E7C2", "Moderate": "FCE9B2", "Weak": "F4C7C3", "Insufficient evidence": "E3E3E3"}
widths = {"Read me": [18, 120], "Evaluation Matrix": [22, 45, 60, 55, 55, 55, 40, 10],
          "Rating Grid": [22] + [21] * 11, "Cell Evidence": [20, 20, 12, 10, 60, 45, 45, 40, 30, 22, 9, 9, 9, 9],
          "References": [9, 10, 9, 8, 18, 110], "Rating anchors": [5, 26, 50, 40, 45],
          "Dataset codes": [8, 36, 150]}
for ws in wb.worksheets:
    ws.freeze_panes = "B2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = head
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
            v = str(c.value or "")
            if ws.title in ("Rating Grid", "Cell Evidence"):
                for k, col in FILL.items():
                    if v.startswith(k):
                        c.fill = PatternFill("solid", fgColor=col)
    for i, w in enumerate(widths.get(ws.title, [])):
        ws.column_dimensions[ws.cell(1, i + 1).column_letter].width = w
from openpyxl.comments import Comment
from openpyxl.worksheet.hyperlink import Hyperlink
ws = wb["Rating Grid"]
for (r, c), (txt, ev_row) in grid_notes.items():
    cell = ws.cell(r, c)
    cm = Comment(txt, "D2 evidence"); cm.width, cm.height = 480, 320
    cell.comment = cm
    cell.hyperlink = Hyperlink(ref=cell.coordinate, location=f"'Cell Evidence'!A{ev_row}")
for r in range(2, len(ORDER) + 2):
    ws.row_dimensions[r].height = 62
ws.cell(len(ORDER) + 3, 1, "How to read: each cell shows rating (confidence) and the key studies it rests on. "
        "Hover for the evidence summary; click to open the full evidence row in 'Cell Evidence'.")
wb.save(XLSX)
print("Wrote", XLSX)
print(grid.to_string(index=False))
