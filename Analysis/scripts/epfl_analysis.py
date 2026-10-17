"""
Secondary analysis of the EPFL / NLP4Education dataset (Borges et al., 2024).

Run from the IRP Working Directory:
    python Analysis/scripts/epfl_analysis.py

Inputs (read only):  Datasets/EPFL Dataset/{courses.json, questions.json, grade_per_question.csv}
Outputs:             Analysis/outputs/EPFL/*.csv, Analysis/figures/EPFL_*.png

Unit of analysis
----------------
Each question was answered by 2 models x 8 prompting strategies (16 rows per question).
Those rows are not independent, so all headline figures are computed at QUESTION level
(one value per question per model) and then summarised. Row-level means are not reported.

Grade scale (from the dataset README and observed values)
---------------------------------------------------------
MCQ:          0 or 1 (exact match with the gold option index).
Open answer:  0, 0.33, 0.66 or 1, assigned automatically by GPT-4 acting as grader.
Because the two question types are graded differently, MCQ vs open-answer comparisons
are indicative only.

Definitions used in this analysis (our own, not the original paper's)
---------------------------------------------------------------------
correct          grade == 1
mostly_correct   grade >= 0.66 (for MCQ this equals correct)
mean_grade       mean of the 8 prompt grades for a question/model
best_of_8        max grade over the 8 prompts (a student who tries several prompts and
                 can recognise the best answer; an upper bound, not a realistic default)
majority_8       question counted as correct if >= 5 of 8 prompts are correct
zero_shot        the single Zero-Shot prompt (closest to a student pasting the question)
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Datasets" / "EPFL Dataset"
OUT = ROOT / "Analysis" / "outputs" / "EPFL"
FIG = ROOT / "Analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

RNG = np.random.default_rng(2026)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
MODEL_LABEL = {"GPT-4": "GPT-4", "ChatGPT": "GPT-3.5 (ChatGPT)"}
MODEL_COLOR = {"GPT-4": BLUE, "ChatGPT": ORANGE}

plt.rcParams.update({
    "font.family": "Calibri", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 300, "savefig.bbox": "tight",
})


def boot_ci(x, n=2000):
    """95% percentile bootstrap CI for a mean (question-level values)."""
    x = np.asarray(x, dtype=float)
    if len(x) < 2:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    m = x[idx].mean(axis=1)
    return tuple(np.percentile(m, [2.5, 97.5]))


# ---------------------------------------------------------------- load
courses = pd.DataFrame(json.load(open(DATA / "courses.json", encoding="utf-8")))
questions = pd.DataFrame(json.load(open(DATA / "questions.json", encoding="utf-8")))
questions["question_id"] = questions["question_id"].astype(int)
questions["course_id"] = questions["course_id"].astype(int)
grades = pd.read_csv(DATA / "grade_per_question.csv", low_memory=False)

# courses.json is the authoritative metadata source. The grades CSV labels 14 online
# courses as "Bachelor" and 15 others as "Uncategorized", so its year/program fields are
# replaced with the courses.json values.
courses["level"] = courses["course_year"].str.capitalize()
courses["program"] = courses["course_program"].fillna("Online (Life Sciences/Physics)")
grades = grades.drop(columns=["program", "year", "language"]).merge(
    courses[["course_id", "level", "program", "course_language"]], on="course_id", how="left")
grades = grades.rename(columns={"course_language": "language"})
grades["qtype"] = grades["question_type"].map({"MCQ": "MCQ", "OpenAnswer": "Open answer"})
grades["is_cs"] = grades["program"].eq("Computer Science")

# ---------------------------------------------------------------- coverage
expected_rows = len(questions) * 2 * 8
coverage = pd.DataFrame([
    ("Courses in courses.json", len(courses)),
    ("Courses with graded questions", grades.course_id.nunique()),
    ("Questions in questions.json", len(questions)),
    ("Questions with grades", grades.question_id.nunique()),
    ("  of which MCQ", grades.loc[grades.qtype == "MCQ", "question_id"].nunique()),
    ("  of which open answer", grades.loc[grades.qtype == "Open answer", "question_id"].nunique()),
    ("Computer Science courses", grades.loc[grades.is_cs, "course_id"].nunique()),
    ("Computer Science questions", grades.loc[grades.is_cs, "question_id"].nunique()),
    ("Grade rows expected (questions x 2 models x 8 prompts)", expected_rows),
    ("Grade rows present", len(grades)),
    ("Grade rows missing", expected_rows - len(grades)),
    ("Missing grade values", int(grades.grade.isna().sum())),
    ("Questions with Bloom's / difficulty labels", 0),
], columns=["item", "value"])
coverage.to_csv(OUT / "00_coverage.csv", index=False)

courses_tbl = (grades.groupby(["program", "level"])
               .agg(courses=("course_id", "nunique"), questions=("question_id", "nunique"))
               .reset_index())
courses_tbl.to_csv(OUT / "00_courses_by_program_level.csv", index=False)

# ---------------------------------------------------------------- question-level table
grades["correct"] = (grades.grade == 1).astype(int)
grades["mostly_correct"] = (grades.grade >= 0.66).astype(int)
keys = ["question_id", "course_id", "model", "qtype", "program", "level", "language", "is_cs"]
ql = grades.groupby(keys).agg(
    n_prompts=("grade", "size"),
    mean_grade=("grade", "mean"),
    best_of_8=("grade", "max"),
    n_correct=("correct", "sum"),
    n_mostly=("mostly_correct", "sum"),
).reset_index()
zs = grades[grades.prompt_type == "Zero-Shot"][["question_id", "model", "grade"]]
ql = ql.merge(zs.rename(columns={"grade": "zero_shot"}), on=["question_id", "model"], how="left")
ql["best_correct"] = (ql.best_of_8 == 1).astype(int)
ql["best_mostly"] = (ql.best_of_8 >= 0.66).astype(int)
ql["zs_correct"] = (ql.zero_shot == 1).astype(float)
ql["zs_mostly"] = (ql.zero_shot >= 0.66).astype(float)
ql.loc[ql.zero_shot.isna(), ["zs_correct", "zs_mostly"]] = np.nan
ql["majority_correct"] = (ql.n_correct >= 5).astype(int)
ql["never_correct"] = (ql.n_correct == 0).astype(int)
ql.to_csv(OUT / "question_level_scores.csv", index=False)


def summarise(df, by):
    rows = []
    for k, g in df.groupby(by):
        k = k if isinstance(k, tuple) else (k,)
        lo, hi = boot_ci(g.mean_grade)
        rows.append(dict(zip(by, k), **{
            "n_questions": len(g),
            "mean_grade_avg_prompts": g.mean_grade.mean(),
            "mean_grade_ci_low": lo, "mean_grade_ci_high": hi,
            "pct_correct_zero_shot": 100 * g.zs_correct.mean(),
            "pct_mostly_correct_zero_shot": 100 * g.zs_mostly.mean(),
            "pct_correct_majority_of_8": 100 * g.majority_correct.mean(),
            "pct_correct_best_of_8": 100 * g.best_correct.mean(),
            "pct_mostly_correct_best_of_8": 100 * g.best_mostly.mean(),
            "pct_never_correct_any_prompt": 100 * g.never_correct.mean(),
        }))
    return pd.DataFrame(rows)


# 1. Overall by model and question type
t1 = pd.concat([
    summarise(ql.assign(qtype="All"), ["model", "qtype"]),
    summarise(ql, ["model", "qtype"]),
]).sort_values(["model", "qtype"])
t1.to_csv(OUT / "01_overall_by_model_qtype.csv", index=False)

# 2. Computer Science only
t2 = pd.concat([
    summarise(ql[ql.is_cs].assign(qtype="All"), ["model", "qtype"]),
    summarise(ql[ql.is_cs], ["model", "qtype"]),
]).sort_values(["model", "qtype"])
t2.to_csv(OUT / "02_computer_science_by_model_qtype.csv", index=False)

# 3. By program, level and language (GPT-4 and GPT-3.5)
summarise(ql, ["model", "program"]).to_csv(OUT / "03a_by_program.csv", index=False)
summarise(ql, ["model", "level"]).to_csv(OUT / "03b_by_level.csv", index=False)
summarise(ql, ["model", "language"]).to_csv(OUT / "03c_by_language.csv", index=False)
summarise(ql[ql.is_cs], ["model", "level", "qtype"]).to_csv(OUT / "03d_cs_by_level_qtype.csv", index=False)

# 4. Prompting strategies (question-level grade per prompt, then averaged)
pr_rows = []
for (m, qt), g in grades.groupby(["model", "qtype"]):
    piv = g.pivot_table(index="question_id", columns="prompt_type", values="grade")
    for p in piv.columns:
        lo, hi = boot_ci(piv[p].dropna())
        pr_rows.append({"model": m, "qtype": qt, "prompt_type": p,
                        "n_questions": piv[p].notna().sum(), "mean_grade": piv[p].mean(),
                        "ci_low": lo, "ci_high": hi})
    complete = piv.dropna()
    fr = stats.friedmanchisquare(*[complete[c] for c in complete.columns])
    pr_rows.append({"model": m, "qtype": qt, "prompt_type": "FRIEDMAN TEST",
                    "n_questions": len(complete), "mean_grade": fr.statistic, "ci_low": fr.pvalue,
                    "ci_high": np.nan})
prompts = pd.DataFrame(pr_rows)
prompts.to_csv(OUT / "04_prompt_strategies.csv", index=False)
prompt_range = (prompts[prompts.prompt_type != "FRIEDMAN TEST"]
                .groupby(["model", "qtype"]).mean_grade.agg(["min", "max"])
                .assign(range_pts=lambda d: 100 * (d["max"] - d["min"])).reset_index())
prompt_range.to_csv(OUT / "04b_prompt_strategy_range.csv", index=False)

# 5. Model comparison (paired by question)
mc_rows = []
for qt, g in pd.concat([ql.assign(qtype="All"), ql]).groupby("qtype"):
    w = g.pivot_table(index="question_id", columns="model", values="mean_grade").dropna()
    wt = stats.wilcoxon(w["GPT-4"], w["ChatGPT"])
    mc_rows.append({"qtype": qt, "n_questions": len(w), "gpt4_mean": w["GPT-4"].mean(),
                    "gpt35_mean": w["ChatGPT"].mean(),
                    "difference_pts": 100 * (w["GPT-4"] - w["ChatGPT"]).mean(),
                    "pct_questions_gpt4_better": 100 * (w["GPT-4"] > w["ChatGPT"]).mean(),
                    "pct_questions_gpt35_better": 100 * (w["GPT-4"] < w["ChatGPT"]).mean(),
                    "wilcoxon_W": wt.statistic, "wilcoxon_p": wt.pvalue})
pd.DataFrame(mc_rows).to_csv(OUT / "05_model_comparison_paired.csv", index=False)

# 6. MCQ vs open answer (GPT-4, question-level mean grade, Mann-Whitney U)
qt_rows = []
for scope, g in [("All courses", ql), ("Computer Science", ql[ql.is_cs])]:
    for m in ["GPT-4", "ChatGPT"]:
        a = g[(g.model == m) & (g.qtype == "MCQ")].mean_grade
        b = g[(g.model == m) & (g.qtype == "Open answer")].mean_grade
        u = stats.mannwhitneyu(a, b, alternative="two-sided")
        r_rb = 1 - 2 * u.statistic / (len(a) * len(b))  # rank-biserial correlation
        qt_rows.append({"scope": scope, "model": m, "n_mcq": len(a), "n_open": len(b),
                        "mean_mcq": a.mean(), "mean_open": b.mean(),
                        "mannwhitney_U": u.statistic, "p": u.pvalue, "rank_biserial": -r_rb})
pd.DataFrame(qt_rows).to_csv(OUT / "06_mcq_vs_open.csv", index=False)

# 7. MCQ chance baseline (single-answer MCQs with a parsable option list)
def n_options(s):
    try:
        v = json.loads(s) if isinstance(s, str) else s
        return len(v) if isinstance(v, list) else np.nan
    except Exception:
        try:
            v = eval(s, {"__builtins__": {}})  # option lists are stored as Python-style lists
            return len(v) if isinstance(v, (list, tuple)) else np.nan
        except Exception:
            return np.nan

mcq_q = questions[questions.question_type == "mcq"].copy()
mcq_q["n_options"] = mcq_q.question_options.apply(n_options)
mcq_q["single_answer"] = mcq_q.multiple_correct_answers.astype(str).eq("False")
single = mcq_q[mcq_q.single_answer & mcq_q.n_options.ge(2)]
chance_rows = []
for m in ["GPT-4", "ChatGPT"]:
    g = ql[(ql.model == m) & ql.question_id.isin(single.question_id)].merge(
        single[["question_id", "n_options"]], on="question_id")
    chance_rows.append({"model": m, "n_single_answer_mcq": len(g),
                        "median_options": g.n_options.median(),
                        "expected_pct_correct_by_chance": 100 * (1 / g.n_options).mean(),
                        "pct_correct_zero_shot": 100 * g.zs_correct.mean(),
                        "pct_correct_best_of_8": 100 * g.best_correct.mean()})
pd.DataFrame(chance_rows).to_csv(OUT / "07_mcq_chance_baseline.csv", index=False)

# 8. Course-level picture (how many courses would a "paste the question" user do well in?)
cl = (ql.groupby(["course_id", "program", "level", "model"])
      .agg(n_questions=("question_id", "size"), zero_shot_mean=("zero_shot", "mean"),
           mean_grade=("mean_grade", "mean"), best_of_8_mean=("best_of_8", "mean"),
           pct_correct_best_of_8=("best_correct", "mean"))
      .reset_index())
cl["pct_correct_best_of_8"] *= 100
cl.to_csv(OUT / "08_course_level.csv", index=False)
thr_rows = []
for (m, scope), g in pd.concat([cl.assign(scope="All courses"),
                                cl[cl.program == "Computer Science"].assign(scope="Computer Science")]
                               ).groupby(["model", "scope"]):
    g = g[g.n_questions >= 10]
    thr_rows.append({"model": m, "scope": scope, "courses_with_10plus_questions": len(g),
                     "courses_zero_shot_mean_ge_0.5": int((g.zero_shot_mean >= 0.5).sum()),
                     "courses_best_of_8_mean_ge_0.5": int((g.best_of_8_mean >= 0.5).sum()),
                     "median_course_zero_shot_mean": g.zero_shot_mean.median(),
                     "min_course_zero_shot_mean": g.zero_shot_mean.min(),
                     "max_course_zero_shot_mean": g.zero_shot_mean.max()})
pd.DataFrame(thr_rows).to_csv(OUT / "08b_course_threshold_summary.csv", index=False)

# 9. Exploratory question characteristics (simple text heuristics, GPT-4 only)
qc = questions[["question_id", "question_body"]].copy()
body = qc.question_body.fillna("")
qc["words"] = body.str.split().str.len()
qc["has_code"] = body.str.contains(
    r"```|\bdef |\breturn\b|\bclass |;\s*$|\{|\}|=>|\bint |\bvoid |\bval |\bfor\s*\(|\bwhile\s*\(",
    regex=True)
qc["has_maths"] = body.str.contains(r"\$|\\frac|\\sum|\\int|\^", regex=True)
qc["length_band"] = pd.qcut(qc.words, 4, labels=["Q1 shortest", "Q2", "Q3", "Q4 longest"])
g4 = ql[ql.model == "GPT-4"].merge(qc, on="question_id")
ch_rows = []
for feat in ["has_code", "has_maths", "length_band"]:
    for (qt, val), g in g4.groupby(["qtype", feat], observed=True):
        lo, hi = boot_ci(g.mean_grade)
        ch_rows.append({"feature": feat, "value": str(val), "qtype": qt, "n_questions": len(g),
                        "mean_grade": g.mean_grade.mean(), "ci_low": lo, "ci_high": hi,
                        "pct_correct_best_of_8": 100 * g.best_correct.mean()})
pd.DataFrame(ch_rows).to_csv(OUT / "09_question_characteristics_gpt4.csv", index=False)
cs4 = g4[g4.is_cs]
rho = stats.spearmanr(g4.words, g4.mean_grade)
pd.DataFrame([{"scope": "All GPT-4", "spearman_rho_words_vs_grade": rho.correlation, "p": rho.pvalue,
               "n": len(g4)}]).to_csv(OUT / "09b_length_correlation.csv", index=False)

# ---------------------------------------------------------------- figures
def bar_pair(ax, cats, vals, title, ylabel, fmt="{:.0f}%"):
    x = np.arange(len(cats))
    w = 0.38
    for i, m in enumerate(["GPT-4", "ChatGPT"]):
        v = [vals[(m, c)] for c in cats]
        bars = ax.bar(x + (i - 0.5) * w, v, w - 0.03, color=MODEL_COLOR[m], label=MODEL_LABEL[m])
        for b, val in zip(bars, v):
            ax.text(b.get_x() + b.get_width() / 2, val + 1.2, fmt.format(val), ha="center",
                    va="bottom", fontsize=8, color=INK)
    ax.set_xticks(x)
    ax.set_xticklabels(cats)
    ax.set_title(title, loc="left", fontsize=11, color=INK)
    ax.set_ylabel(ylabel)
    ax.grid(axis="x", visible=False)


# Figure 1: zero-shot vs majority vs best-of-8, CS courses, GPT-4 and GPT-3.5, by question type
fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=True)
for ax, qt in zip(axes, ["MCQ", "Open answer"]):
    sub = t2[t2.qtype == qt].set_index("model")
    cats = ["Zero-shot", "Majority of 8", "Best of 8"]
    cols = {"Zero-shot": "pct_correct_zero_shot", "Majority of 8": "pct_correct_majority_of_8",
            "Best of 8": "pct_correct_best_of_8"}
    vals = {(m, c): sub.loc[m, cols[c]] for m in ["GPT-4", "ChatGPT"] for c in cats}
    bar_pair(ax, cats, vals, f"{qt} (n = {int(sub.n_questions.iloc[0]):,} questions)",
             "% of questions fully correct" if qt == "MCQ" else "")
    ax.set_ylim(0, 105)
axes[0].legend(frameon=False, loc="upper left", fontsize=8)
fig.suptitle("Computer Science courses: share of questions answered fully correctly",
             x=0.01, ha="left", fontsize=12, color=INK)
fig.savefig(FIG / "EPFL_fig1_cs_correct_by_strategy.png")
plt.close(fig)

# Figure 2: GPT-4 mean grade by program (question-level, with 95% CI), MCQ and open answer
p4 = summarise(ql[ql.model == "GPT-4"], ["program", "qtype"])
order = (p4.groupby("program").n_questions.sum().sort_values().index.tolist())
fig, ax = plt.subplots(figsize=(8, 4.8))
y = np.arange(len(order))
for i, (qt, col) in enumerate([("MCQ", BLUE), ("Open answer", AQUA)]):
    s = p4[(p4.qtype == qt) & (p4.n_questions >= 20)].set_index("program").reindex(order)
    yy = y + (i - 0.5) * 0.36
    ax.errorbar(s.mean_grade_avg_prompts, yy,
                xerr=[s.mean_grade_avg_prompts - s.mean_grade_ci_low,
                      s.mean_grade_ci_high - s.mean_grade_avg_prompts],
                fmt="o", ms=6, color=col, ecolor=col, elinewidth=1.5, capsize=0, label=qt,
                markeredgecolor="white", markeredgewidth=1)
def _n(p, qt):
    v = p4[(p4.program == p) & (p4.qtype == qt)].n_questions
    return int(v.iloc[0]) if len(v) else 0
labels = [f"{p}\n(MCQ n = {_n(p, 'MCQ'):,}, open n = {_n(p, 'Open answer'):,})" for p in order]
ax.set_yticks(y)
ax.set_yticklabels(labels)
ax.set_xlim(0, 1)
ax.set_xlabel("GPT-4 mean grade per question, averaged over 8 prompts (0 to 1), with 95% CI")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, loc="lower right", fontsize=8)
ax.set_title("GPT-4 performance by program and question type", loc="left", fontsize=12, color=INK)
ax.text(0, -0.22, "Groups with fewer than 20 questions are not plotted.", transform=ax.transAxes,
        fontsize=8, color=INK2)
fig.savefig(FIG / "EPFL_fig2_gpt4_by_program.png")
plt.close(fig)

# Figure 3: prompt strategies, GPT-4, mean grade by question type
fig, ax = plt.subplots(figsize=(8, 3.6))
p = prompts[(prompts.model == "GPT-4") & (prompts.prompt_type != "FRIEDMAN TEST")]
order_p = p[p.qtype == "MCQ"].sort_values("mean_grade").prompt_type.tolist()
y = np.arange(len(order_p))
for i, (qt, col) in enumerate([("MCQ", BLUE), ("Open answer", AQUA)]):
    s = p[p.qtype == qt].set_index("prompt_type").reindex(order_p)
    ax.errorbar(s.mean_grade, y + (i - 0.5) * 0.36,
                xerr=[s.mean_grade - s.ci_low, s.ci_high - s.mean_grade],
                fmt="o", ms=6, color=col, ecolor=col, elinewidth=1.5, label=qt,
                markeredgecolor="white", markeredgewidth=1)
ax.set_yticks(y)
ax.set_yticklabels(order_p)
ax.set_xlim(0.4, 0.9)
ax.set_xlabel("GPT-4 mean grade (0 to 1), with 95% CI, all courses")
ax.grid(axis="y", visible=False)
ax.legend(frameon=False, loc="lower right", fontsize=8)
ax.set_title("Prompting strategy matters more for MCQ than for open answers", loc="left", fontsize=12, color=INK)
fig.savefig(FIG / "EPFL_fig3_prompt_strategies.png")
plt.close(fig)

# Figure 4: distribution of CS course-level GPT-4 zero-shot mean grade
cs_cl = cl[(cl.program == "Computer Science") & (cl.model == "GPT-4") & (cl.n_questions >= 10)]
cs_cl = cs_cl.sort_values("zero_shot_mean")
fig, ax = plt.subplots(figsize=(8, 3.4))
lvl_col = {"Bachelor": BLUE, "Master": ORANGE}
ax.bar(range(len(cs_cl)), cs_cl.zero_shot_mean, 0.75,
       color=[lvl_col[l] for l in cs_cl.level])
ax.axhline(0.5, color=INK2, lw=1, ls="--")
ax.text(-0.4, 0.93, "Dashed line = 0.5 reference (illustrative, not a pass mark)",
        ha="left", fontsize=8, color=INK2)
ax.set_xticks(range(len(cs_cl)))
ax.set_xticklabels([f"{n}" for n in cs_cl.n_questions], fontsize=7)
ax.set_xlabel("Individual CS courses (label = number of questions)")
ax.set_ylabel("GPT-4 zero-shot mean grade")
ax.set_ylim(0, 1)
ax.grid(axis="x", visible=False)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color=BLUE, label="Bachelor"), Patch(color=ORANGE, label="Master")],
          frameon=False, loc="upper left", fontsize=8, bbox_to_anchor=(0, 0.9))
ax.set_title("GPT-4 zero-shot performance varies widely between CS courses",
             loc="left", fontsize=12, color=INK)
fig.savefig(FIG / "EPFL_fig4_cs_course_spread.png")
plt.close(fig)

print("EPFL analysis complete. Outputs in", OUT)
