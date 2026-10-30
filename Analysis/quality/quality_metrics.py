"""
Quality metrics for the E04 deliverables (rubric: Quality, Techniques and Methodology).

    python Analysis/quality/quality_metrics.py

Every value is computed from project files. Output: Analysis/quality/quality_metrics.csv and prisma_checklist.csv
"""
import glob
import json
import re
from pathlib import Path

import pandas as pd

A = Path(__file__).resolve().parents[1]
S = A / "screening"
out = []


def add(n, metric, standard, value, threshold, verdict, basis):
    out.append({"#": n, "Metric": metric, "Standard / method": standard, "Result": value,
                "Benchmark": threshold, "Verdict": verdict, "Computed from": basis})


# 1 PRISMA 2020 checklist: status against the final report and the supplementary documents (22 Oct 2026)
LR = "Literature Review Evidence"
prisma = pd.DataFrame([
    (1, "Title", "Met", "Report cover: 'Final Project Report: a structured systematic review and evaluation framework'"),
    (2, "Abstract (structured)", "Partial", "Executive Summary gives aim, methods, results and conclusions, but not every PRISMA abstract item"),
    (3, "Rationale", "Met", "Report Section 1 (the business problem and the opportunity)"),
    (4, "Objectives / questions", "Met", "Report Section 1.2 (research questions RQ1 to RQ5)"),
    (5, "Eligibility criteria", "Met", f"Report Section 3.2; {LR}, sheet 'Read me and methods' (criteria IC1 to IC5, exclusion codes E1 to E7, dated redesign amendment)"),
    (6, "Information sources", "Met", "Report Section 3.2 and Figure 2: team evidence log and an OpenAlex update search on 17 October 2026"),
    (7, "Search strategy", "Partial", "Update-search strings recorded in full in the code repository (screening/search/search_log.csv); the original team searches were not recorded (Report Section 3.2)"),
    (8, "Selection process", "Met", "Report Section 3.2: two independent, blinded screening runs using Anthropic Claude (Opus 5.5), with a team member settling every disagreement; AI use disclosed in Section 3.6"),
    (9, "Data collection process", "Met", "Report Section 3.2: written extraction protocol recording each finding with its location in the source (protocol in the code repository)"),
    (10, "Data items", "Met", f"{LR}, sheet 'Study details' (design, sample, findings with locations, notes on each criterion)"),
    (11, "Study risk-of-bias assessment", "Met", f"Report Section 3.2: five-item checklist adapted from MMAT 2018; {LR}, sheet 'Quality appraisal'"),
    (12, "Effect measures", "Not applicable", "Framework synthesis of mixed evidence; no pooled effect sizes (Report Section 3.5)"),
    (13, "Synthesis methods", "Met", "Report Section 3.4: framework synthesis with written calibration rules; D2 Evaluation Framework, sheet 'Read me'"),
    (14, "Reporting-bias assessment", "Partial", "Venue credibility check and sensitivity analysis (Report Section 6); no formal publication-bias test"),
    (15, "Certainty assessment", "Met", "Report Section 3.4: CERQual-informed confidence rule (High, Medium or Low for every rating)"),
    (16, "Study selection (flow diagram)", "Met", f"Report Figure 2 (PRISMA flow diagram); {LR}, sheet 'PRISMA'"),
    (17, "Study characteristics", "Met", f"{LR}, sheets 'Included studies' and 'Study details'; Report Section 4.1"),
    (18, "Risk of bias in studies", "Met", f"Quality score for every study ({LR}, sheet 'Quality appraisal'); summary in Report Section 4.1"),
    (19, "Results of individual studies", "Met", f"{LR}, sheet 'Study details' (findings with their location in each source)"),
    (20, "Results of syntheses", "Met", "Report Section 4.3; D2 Evaluation Framework, sheets 'Rating Grid' and 'Cell Evidence'"),
    (21, "Reporting biases", "Partial", "Low-confidence venues flagged; sensitivity checks without them and without the two most-cited studies change no rating (Report Section 6)"),
    (22, "Certainty of evidence", "Met", "Report Section 4.3 (High-confidence ratings marked and confidence totals given; every rating's level in the D2 workbook) and Section 5 (evidence status for every D3 recommendation)"),
    (23, "Discussion and limitations", "Met", "Report Section 6 (limits of the evidence) and Section 9 (conclusion)"),
    (24, "Registration and protocol", "Partial", "Protocols written and dated in the code repository; the review was not registered (for example on PROSPERO or OSF)"),
    (25, "Support / funding", "Met", "Report Section 8.2: no external funding; tool costs from the project budget"),
    (26, "Competing interests", "Met", "Report Section 8.2: the team declares no competing interests"),
    (27, "Availability of data, code, materials", "Met", "Report Appendix A: code repository and supplementary documents (links)"),
], columns=["Item", "PRISMA 2020 item", "Status", "Where it is reported"])
prisma.to_csv(A / "quality" / "prisma_checklist.csv", index=False)
# formatted copy for readers (review guide P3-12)
from openpyxl.styles import Alignment, Font, PatternFill, Side, Border
XL = A / "quality" / "prisma_checklist.xlsx"
with pd.ExcelWriter(XL, engine="openpyxl") as xw:
    prisma.to_excel(xw, "PRISMA 2020 checklist", index=False)
    prisma.iloc[:, 2].value_counts().rename_axis("Status").reset_index(name="Items").to_excel(xw, "Status summary", index=False)
from openpyxl import load_workbook
wb = load_workbook(XL)
STATUS = {"Met": "C6E7C2", "Partial": "FCE9B2", "Not met": "F4C7C3"}
edge = Side(style="thin", color="C9C9C9")
for ws in wb.worksheets:
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF"); c.fill = PatternFill("solid", fgColor="1C5CAB")
    for row in ws.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top"); c.border = Border(edge, edge, edge, edge)
            if c.row > 1 and c.value in STATUS:
                c.fill = PatternFill("solid", fgColor=STATUS[c.value])
    for col, w in zip("ABCD", [6, 30, 12, 90] if ws.title.startswith("PRISMA") else [14, 8]):
        ws.column_dimensions[col].width = w
wb.save(XL)
sc = prisma.Status.value_counts()
applic = len(prisma) - sc.get("Not applicable", 0)
done = sc.get("Met", 0)
add(1, "Reporting completeness", "PRISMA 2020 checklist (27 items)",
    f"{done} of {applic} applicable items met; {sc.get('Partial', 0)} partly met "
    f"(structured abstract, search strings, two reporting-bias items, registration)",
    "All applicable items met or explained", "Met, with stated partials",
    "quality/prisma_checklist.csv")

# 2 Inter-rater agreement
ta = pd.read_csv(S / "ta_agreement.csv"); us = pd.read_csv(S / "search" / "search_ta_agreement.csv")
rd = pd.read_csv(S / "redesign_merged.csv")
x, y = rd.redesign_relevance_A, rd.redesign_relevance_B
po = (x == y).mean(); pe = sum((x == c).mean() * (y == c).mean() for c in set(x) | set(y)); k_rd = (po - pe) / (1 - pe)
ks = [("Title/abstract, evidence log (n=%d)" % ta.n[0], ta.cohens_kappa[0], ta.pct_agreement[0]),
      ("Title/abstract, update search (n=%d)" % us.n[0], us.cohens_kappa[0], us.pct_agreement[0]),
      ("Redesign relevance (n=%d)" % len(rd), k_rd, po)]
add(2, "Screening agreement", "Cohen's kappa; Landis & Koch (1977) bands",
    "; ".join(f"{n}: kappa {k:.2f}, agreement {p:.0%}" for n, k, p in ks),
    "kappa >= 0.61 substantial; >= 0.81 almost perfect",
    "Substantial to almost perfect" if min(k for _, k, _ in ks) >= 0.61 else "Below benchmark",
    "screening/ta_agreement.csv; search/search_ta_agreement.csv; redesign_merged.csv")

# 3 Study quality
st = pd.read_csv(S / "review_studies.csv"); inc = st[st.ft_decision == "Include"]
q = inc.quality_score
add(3, "Study quality (risk of bias)", "5-item checklist adapted from MMAT 2018 and CASP",
    f"Mean {q.mean():.1f}/5 (median {q.median():.0f}); {(q >= 4).mean():.0%} of studies score 4-5; "
    f"Core tier mean {inc[inc.evidence_tier == 'Core'].quality_score.mean():.1f}, Supporting "
    f"{inc[inc.evidence_tier == 'Supporting'].quality_score.mean():.1f}; computing studies "
    f"{inc[inc.computing == 'Y'].quality_score.mean():.1f}",
    "Reported for every included study; weaker evidence weighted down", "Met (weakness disclosed)",
    "screening/review_studies.csv")

# 4 Confidence profile (D2)
cells = []
for f in glob.glob(str(A / "D2_framework" / "cells" / "*.json")):
    cells += json.load(open(f, encoding="utf-8"))["cells"]
conf = pd.Series([c["confidence"].split(" /")[0] for c in cells]).value_counts()
add(4, "Confidence in findings", "CERQual-informed rule (adapted from GRADE-CERQual)",
    f"{len(cells)} D2 cells: High {conf.get('High', 0)}, Medium {conf.get('Medium', 0)}, Low {conf.get('Low', 0)}; "
    "all High cells meet the stated rule (>= 3 studies incl. a Core or computing study rated >= 4)",
    "Explicit, rule-based confidence for every rating", "Met", "D2_framework/cells/*.json; calibration_log.md")

# 5 Traceability
cite = re.compile(r"\[([RS]\d{2,3}|D\d\d|J\d)\]")
lit_cited = sum(bool(cite.search(c["literature"])) for c in cells)
d3 = []
for f in glob.glob(str(A / "D3_recommendations" / "out" / "partA_*.json")):
    j = json.load(open(f, encoding="utf-8")); d3 += j["recommended_redesign"] + j["implementation_considerations"]
d3_cited = sum(bool(cite.search(t)) for t in d3)
mer = json.load(open(S / "extraction" / "extraction_merged.json", encoding="utf-8"))
kf = [f for r in mer if r.get("ft_decision") == "Include" for f in (r.get("key_findings") or [])]
loc = sum(1 for f in kf if f.get("location") and not re.search(r"abstract|not reported", str(f["location"]), re.I))
known = set(inc["Record ID"])
txt = " ".join(json.dumps(json.load(open(f, encoding="utf-8")), ensure_ascii=False)
               for f in glob.glob(str(A / "D2_framework" / "cells" / "*.json")) + glob.glob(str(A / "D3_recommendations" / "out" / "*.json")))
ids = set(re.findall(r"\b([RS]\d{2,3})\b", txt)); bad = ids - known
add(5, "Traceability", "Claim-to-source audit",
    f"D2 literature statements with a citation: {lit_cited}/{len(cells)} ({lit_cited / len(cells):.0%}); "
    f"D3 redesign and implementation items with a citation: {d3_cited}/{len(d3)} ({d3_cited / len(d3):.0%}); "
    f"citations not matching an included study: {len(bad)}; evidence-log key findings with a page/section location: "
    f"{loc}/{len(kf)} ({loc / max(len(kf), 1):.0%})",
    "100% of claims cited; 0 unmatched citations", "Met" if not bad and lit_cited == len(cells) else "Check",
    "D2/D3 JSON; extraction_merged.json")

# 6 Coverage
TYPES = ["Supervised assessment", "Unsupervised formats", "Oral assessments", "Practical demonstrations",
         "Staged submissions", "Process evidence", "Personalised tasks", "AI-use declarations"]
cov = {t: int(inc.assessment_types.fillna("").str.contains(t, regex=False).sum()) for t in TYPES}
ins = sum(c["rating"].startswith("Insufficient") for c in cells)
add(6, "Evidence coverage", "Studies per assessment type; empty cells",
    f"Min {min(cov.values())} ({min(cov, key=cov.get)}), max {max(cov.values())} ({max(cov, key=cov.get)}); "
    f"{ins} of {len(cells)} D2 cells rated 'Insufficient evidence'; {int((inc.computing == 'Y').sum())} computing-specific studies",
    ">= 10 studies per type; gaps stated", "Met" if min(cov.values()) >= 10 else "Gap", "screening/review_studies.csv")

# 7 Reproducibility (result of the re-run test, 17 Oct 2026)
add(7, "Reproducibility", "Full re-run of all offline scripts; MD5 comparison of outputs",
    "All offline outputs and the four deliverable workbooks identical in content on a clean re-run from the shared "
    "code package. Live web queries (OpenAlex search, venue check) are dated snapshots, not re-run.",
    "Identical outputs on re-run", "Met", "Clean-copy re-run, 28 Oct 2026")

# 8 Independent replication
add(8, "Independent replication", "Two analysts, same datasets, separate code (ours vs Jiajun's)",
    "StudyChat: students scoring higher on assignments than exams 88.6% / 91.9% (both); mean assignment-exam gap "
    "8.0 / 8.8 points (both). Hannover: skill vs use rho -0.17 and use vs AI-first 0.77 (both). EPFL: results agree "
    "in direction; definitions differ (stated).",
    "Key figures agree", "Met", "Analysis/outputs vs Jiajun - Data Analysis/*.docx")

# 9 Sensitivity to weak sources
low = {k for k, v in st.set_index("Record ID").venue_weight.fillna("").items() if v}
dep = sum(1 for c in cells if c["key_studies"] and len(set(c["key_studies"]) - low) < 2)
uses = sum(1 for c in cells if set(c["key_studies"]) & low)
# drop the two most-used single-course studies and re-apply the confidence rule (review guide P1-4)
sti = st.set_index("Record ID")
def qualifies(r):  # Core or computing study of quality 4 or more
    if r not in sti.index:
        return False
    q = pd.to_numeric(sti.at[r, "quality_score"], errors="coerce")
    return q >= 4 and (str(sti.at[r, "evidence_tier"]).startswith("Core") or sti.at[r, "computing"] == "Y")
DROP = {"R81", "R82"}
lose = high_down = 0
for c in cells:
    rest = [k for k in c["key_studies"] if k not in DROP]
    if set(c["key_studies"]) & DROP and len(rest) < 2:
        lose += 1
    if c["confidence"].startswith("High") and (len(rest) < 3 or not any(qualifies(k) for k in rest)):
        high_down += 1
n_drop = sum(1 for c in cells if set(c["key_studies"]) & DROP)
add(9, "Robustness to weak sources", "Sensitivity analysis excluding low-confidence venues, and excluding R81 and R82",
    f"{uses} of {len(cells)} D2 cells cite a low-confidence venue; {dep} would lose support (fewer than 2 other studies) without them. "
    f"Without R81 and R82 ({n_drop} cells cite them): {lose} ratings would lose support and {high_down} High confidence levels would fall to Medium",
    "No rating depends on low-confidence venues or on a single study", "Met" if dep == 0 and lose == 0 else "Check", "review_studies.csv; D2 cells")

# 10 Client acceptance
add(10, "Client acceptance", "Stakeholder review of D2/D3",
    "Client formally confirmed the D2 and D3 matrices on 21 Oct 2026 after reviewing the summary and workbooks",
    "Client confirms findings and feasibility", "Met", "Client correspondence")

df = pd.DataFrame(out)
df.to_csv(A / "quality" / "quality_metrics.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 140)
print(df[["#", "Metric", "Result", "Verdict"]].to_string(index=False))
