"""
Secondary analysis of the StudyChat dataset (McNichols et al., 2025; v1.1, Spring 2026).

Run from the IRP Working Directory:
    python Analysis/scripts/studychat_analysis.py

Inputs (read only):  Datasets/StudyChat/dialogues/{f24,s25}_labeled_dialogues.jsonl
                     Datasets/StudyChat/scores/{f24,s25}_grades_released_normalized.csv
Outputs:             Analysis/outputs/StudyChat/*.csv, Analysis/figures/StudyChat_*.png

Context
-------
COMPSCI 383 (Artificial Intelligence), UMass Amherst, Fall 2024 and Spring 2025.
Students could use a course chatbot (gpt-4o-mini) on seven take-home programming
assignments (a1-a7). The three exams (e1-e3) were proctored, with no AI.
Grades are normalised to 0-1. `llm` is the points-weighted assignment average,
`no_llm` is the exam average. Exam 2 had extra credit, so values can exceed 1.

Unit of analysis
----------------
One dialogue row is one student prompt (a turn). Heavy users contribute hundreds of
turns, so every headline figure is computed at STUDENT level (one value per student)
and then summarised. Turn-level counts are reported only as descriptive coverage.

Definitions used in this analysis (our own, not the original paper's)
---------------------------------------------------------------------
Each turn carries a GPT-4.1 dialogue-act label "category>subcategory".
production     writing_request or editing_request (asking the AI to write or change
               code or text: the closest proxy for "asking for the solution")
write_code     writing_request>Write Code only
understanding  conceptual_questions or contextual_questions (concept, code
               explanation, output interpretation, assignment clarification)
verification   verification (asking the AI to check the student's own work)
share_*        that student's turns in the group / all of that student's turns
gap            llm - no_llm (assignment average minus exam average)
Share measures are only computed for students with >= MIN_TURNS turns, so that a
student with two prompts does not get a share of 0% or 100%.
Labels are LLM-generated and contain noise. All associations are observational.
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
DATA = ROOT / "Datasets" / "StudyChat"
OUT = ROOT / "Analysis" / "outputs" / "StudyChat"
FIG = ROOT / "Analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

SEMESTERS = ["f24", "s25"]
SEM_LABEL = {"f24": "Fall 2024", "s25": "Spring 2025"}
ASSIGNMENTS = ["a1", "a2", "a3", "a4", "a5", "a6", "a7"]
EXAMS = ["e1", "e2", "e3"]
MIN_TURNS = 10

RNG = np.random.default_rng(2026)
BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
SEM_COLOR = {"f24": BLUE, "s25": ORANGE}

plt.rcParams.update({
    "font.family": "Calibri", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 300, "savefig.bbox": "tight",
})

GROUPS = {
    "production": ["writing_request", "editing_request"],
    "understanding": ["conceptual_questions", "contextual_questions"],
    "verification": ["verification"],
    "provide_context": ["provide_context"],
    "off_topic_misc": ["off_topic", "misc"],
}
CATEGORY_LABEL = {
    "writing_request": "Writing request", "conceptual_questions": "Conceptual question",
    "provide_context": "Provide context", "contextual_questions": "Contextual question",
    "verification": "Verification", "editing_request": "Editing request",
    "off_topic": "Off topic", "misc": "Misc",
}


def boot_ci(x, fn=np.mean, n=2000):
    """95% percentile bootstrap CI for a statistic of student-level values."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return (np.nan, np.nan)
    idx = RNG.integers(0, len(x), size=(n, len(x)))
    m = np.apply_along_axis(fn, 1, x[idx]) if fn is not np.mean else x[idx].mean(axis=1)
    return tuple(np.percentile(m, [2.5, 97.5]))


def holm(p):
    """Holm-Bonferroni adjusted p-values."""
    p = np.asarray(p, dtype=float)
    order = np.argsort(p)
    adj = np.empty_like(p)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (len(p) - rank) * p[i])
        adj[i] = min(1.0, running)
    return adj


# ---------------------------------------------------------------- load
rows = []
for sem in SEMESTERS:
    with open(DATA / "dialogues" / f"{sem}_labeled_dialogues.jsonl", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            lab = d.get("llm_label")
            label = lab.get("label") if isinstance(lab, dict) else str(lab)
            rows.append({
                "semester": sem, "userId": d["userId"], "chatId": d["chatId"],
                "topic": d["topic"], "label": label,
                "interaction": int(d["interactionCount"]),
                "prompt_chars": len(d.get("prompt") or ""),
            })
turns = pd.DataFrame(rows)
turns["category"] = turns["label"].str.split(">").str[0]
for g, cats in GROUPS.items():
    turns[g] = turns["category"].isin(cats)
turns["write_code"] = turns["label"].eq("writing_request>Write Code")

grades = pd.concat([
    pd.read_csv(DATA / "scores" / f"{sem}_grades_released_normalized.csv").assign(semester=sem)
    for sem in SEMESTERS
], ignore_index=True)
grades["gap"] = grades["llm"] - grades["no_llm"]

# ---------------------------------------------------------------- S0 coverage
cov = []
for sem in SEMESTERS + ["all"]:
    t = turns if sem == "all" else turns[turns.semester == sem]
    g = grades if sem == "all" else grades[grades.semester == sem]
    users = set(t.userId)
    cov.append({
        "semester": sem, "turns": len(t), "chats": t.chatId.nunique(),
        "students_with_chats": len(users), "students_with_grades": len(g),
        "linked_students": int(g.userId.isin(users).sum()),
        "graded_no_chats": int((~g.userId.isin(users)).sum()),
        "chats_no_grades": len(users - set(g.userId)),
    })
pd.DataFrame(cov).to_csv(OUT / "S0_coverage.csv", index=False)

# ---------------------------------------------------------------- student-level features
def shares(df, by):
    agg = df.groupby(by).agg(
        turns=("chatId", "size"), chats=("chatId", "nunique"),
        assignments_used=("topic", "nunique"),
        median_prompt_chars=("prompt_chars", "median"),
        **{f"n_{g}": (g, "sum") for g in list(GROUPS) + ["write_code"]},
    ).reset_index()
    for g in list(GROUPS) + ["write_code"]:
        agg[f"share_{g}"] = agg[f"n_{g}"] / agg["turns"]
    return agg


stu = shares(turns, ["semester", "userId"])
stu = stu.merge(grades, on=["semester", "userId"], how="left")
stu["linked"] = stu["llm"].notna()
stu["log_turns"] = np.log10(stu["turns"])
share_cols = [c for c in stu.columns if c.startswith("share_")]
stu.loc[stu.turns < MIN_TURNS, share_cols] = np.nan
stu.drop(columns=["directory_name"]).to_csv(OUT / "student_level_features.csv", index=False)

# ---------------------------------------------------------------- S1 dialogue acts
cat_turn = turns.groupby("category").size()
stu_cat = (turns.groupby(["userId", "category"]).size()
           .unstack(fill_value=0))
stu_cat = stu_cat.loc[stu_cat.sum(axis=1) >= MIN_TURNS]
stu_cat = stu_cat.div(stu_cat.sum(axis=1), axis=0)
s1 = []
for c in cat_turn.index:
    lo, hi = boot_ci(stu_cat[c].values)
    s1.append({"category": c, "turns": int(cat_turn[c]),
               "turn_share": cat_turn[c] / len(turns),
               "student_mean_share": stu_cat[c].mean(), "ci_low": lo, "ci_high": hi,
               "students_using_at_least_once": int((stu_cat[c] > 0).sum()),
               "n_students": len(stu_cat)})
s1 = pd.DataFrame(s1).sort_values("student_mean_share", ascending=False)
s1.to_csv(OUT / "S1_dialogue_acts_category.csv", index=False)

sub = turns.groupby(["category", "label"]).size().rename("turns").reset_index()
sub["turn_share"] = sub["turns"] / len(turns)
sub.sort_values("turns", ascending=False).to_csv(OUT / "S1b_dialogue_acts_subcategory.csv", index=False)

# headline student-level group shares
s1c = []
for g in list(GROUPS) + ["write_code"]:
    x = stu[f"share_{g}"].dropna()
    lo, hi = boot_ci(x.values)
    s1c.append({"group": g, "n_students": len(x), "mean_share": x.mean(),
                "ci_low": lo, "ci_high": hi, "median_share": x.median(),
                "q1": x.quantile(.25), "q3": x.quantile(.75),
                "pct_students_share_ge_50": (x >= .5).mean()})
pd.DataFrame(s1c).to_csv(OUT / "S1c_student_group_shares.csv", index=False)

# ---------------------------------------------------------------- S2 first move in each chat
first = turns.sort_values("interaction").groupby("chatId").head(1)
s2 = (first.groupby("category").size().rename("chats").reset_index())
s2["share_of_chats"] = s2["chats"] / s2["chats"].sum()
s2["subcategory_write_code"] = s2["category"].map(
    {"writing_request": int(first.write_code.sum())}).fillna(np.nan)
s2.sort_values("chats", ascending=False).to_csv(OUT / "S2_first_turn_of_chat.csv", index=False)

# ---------------------------------------------------------------- S3 by assignment
sa = shares(turns, ["semester", "topic", "userId"])
sa = sa[sa.turns >= 5]
s3 = []
for t in ASSIGNMENTS:
    x = sa[sa.topic == t]
    row = {"assignment": t, "turns": int(turns[turns.topic == t].shape[0]),
           "students_using": int(turns[turns.topic == t].userId.nunique()),
           "students_ge5_turns": len(x)}
    for g in ["production", "write_code", "understanding", "verification"]:
        row[f"mean_share_{g}"] = x[f"share_{g}"].mean()
    s3.append(row)
pd.DataFrame(s3).to_csv(OUT / "S3_by_assignment.csv", index=False)

# ---------------------------------------------------------------- S4 assignment vs exam
s4 = []
for sem in SEMESTERS + ["all"]:
    g = grades if sem == "all" else grades[grades.semester == sem]
    w = stats.wilcoxon(g["llm"], g["no_llm"])
    rho = stats.spearmanr(g["llm"], g["no_llm"])
    lo, hi = boot_ci(g["gap"].values, fn=np.median)
    s4.append({
        "semester": sem, "n": len(g),
        "assign_mean": g.llm.mean(), "assign_sd": g.llm.std(), "assign_median": g.llm.median(),
        "exam_mean": g.no_llm.mean(), "exam_sd": g.no_llm.std(), "exam_median": g.no_llm.median(),
        "gap_median": g.gap.median(), "gap_ci_low": lo, "gap_ci_high": hi,
        "pct_assign_above_exam": (g.gap > 0).mean(),
        "pct_assign_ge_90": (g.llm >= .9).mean(), "pct_exam_ge_90": (g.no_llm >= .9).mean(),
        "wilcoxon_p": w.pvalue, "spearman_assign_exam": rho.correlation,
        "spearman_p": rho.pvalue,
    })
pd.DataFrame(s4).to_csv(OUT / "S4_assignment_vs_exam.csv", index=False)

per_item = []
for c in ASSIGNMENTS + EXAMS:
    for sem in SEMESTERS:
        x = grades.loc[grades.semester == sem, c]
        per_item.append({"item": c, "semester": sem, "ai_permitted": c in ASSIGNMENTS,
                         "n": len(x), "mean": x.mean(), "sd": x.std(), "median": x.median(),
                         "pct_ge_90": (x >= .9).mean()})
pd.DataFrame(per_item).to_csv(OUT / "S4b_per_item_scores.csv", index=False)

# ---------------------------------------------------------------- S5 usage vs outcomes
lk = stu[stu.linked].copy()
measures = ["log_turns", "share_production", "share_write_code",
            "share_understanding", "share_verification"]
outcomes = ["llm", "no_llm", "gap"]
s5 = []
for scope in ["all"] + SEMESTERS:
    d = lk if scope == "all" else lk[lk.semester == scope]
    for m in measures:
        for o in outcomes:
            x = d[[m, o]].dropna()
            r = stats.spearmanr(x[m], x[o])
            s5.append({"scope": scope, "measure": m, "outcome": o, "n": len(x),
                       "spearman_rho": r.correlation, "p": r.pvalue})
s5 = pd.DataFrame(s5)
s5["p_holm_within_scope"] = s5.groupby("scope")["p"].transform(lambda p: holm(p.values))
s5.to_csv(OUT / "S5_usage_outcome_correlations.csv", index=False)

# regression: does production share relate to exam score, holding assignment score fixed?
d = lk.dropna(subset=["share_production"]).copy()
d["s25"] = (d.semester == "s25").astype(float)
z = lambda s: (s - s.mean()) / s.std()
X = pd.DataFrame({"const": 1.0, "assign_z": z(d.llm), "share_production_z": z(d.share_production),
                  "log_turns_z": z(d.log_turns), "semester_s25": d.s25})
y = z(d.no_llm).values
beta, *_ = np.linalg.lstsq(X.values, y, rcond=None)
resid = y - X.values @ beta
dof = len(y) - X.shape[1]
cov_b = (resid @ resid / dof) * np.linalg.inv(X.values.T @ X.values)
se = np.sqrt(np.diag(cov_b))
tval = beta / se
r2 = 1 - (resid @ resid) / ((y - y.mean()) @ (y - y.mean()))
pd.DataFrame({"term": X.columns, "std_beta": beta, "se": se, "t": tval,
              "p": 2 * stats.t.sf(np.abs(tval), dof), "n": len(y), "r2": r2}
             ).to_csv(OUT / "S5b_exam_regression.csv", index=False)

# tertiles of production share
d["production_tertile"] = pd.qcut(d.share_production, 3, labels=["Low", "Middle", "High"])
s6 = d.groupby("production_tertile").agg(
    n=("userId", "size"), share_production_min=("share_production", "min"),
    share_production_max=("share_production", "max"),
    assign_mean=("llm", "mean"), exam_mean=("no_llm", "mean"), gap_mean=("gap", "mean"),
    exam_median=("no_llm", "median"), turns_median=("turns", "median")).reset_index()
kw_exam = stats.kruskal(*[g.no_llm for _, g in d.groupby("production_tertile")])
kw_gap = stats.kruskal(*[g.gap for _, g in d.groupby("production_tertile")])
s6["kruskal_exam_p"] = kw_exam.pvalue
s6["kruskal_gap_p"] = kw_gap.pvalue
s6.to_csv(OUT / "S6_production_tertiles.csv", index=False)

# ---------------------------------------------------------------- S7 per-assignment use vs score
used = turns.groupby(["semester", "userId", "topic"]).size().rename("turns").reset_index()
s7 = []
for sem in SEMESTERS:
    g = grades[grades.semester == sem]
    for t in ASSIGNMENTS:
        u = set(used[(used.semester == sem) & (used.topic == t)].userId)
        yes, no = g.loc[g.userId.isin(u), t], g.loc[~g.userId.isin(u), t]
        p = stats.mannwhitneyu(yes, no).pvalue if len(yes) > 4 and len(no) > 4 else np.nan
        s7.append({"semester": sem, "assignment": t, "n_used": len(yes), "n_not_used": len(no),
                   "mean_used": yes.mean(), "mean_not_used": no.mean(),
                   "mannwhitney_p": p})
s7 = pd.DataFrame(s7)
s7["p_holm"] = np.nan
ok = s7.mannwhitney_p.notna()
s7.loc[ok, "p_holm"] = holm(s7.loc[ok, "mannwhitney_p"].values)
s7.to_csv(OUT / "S7_assignment_use_vs_score.csv", index=False)

# ---------------------------------------------------------------- figures
# fig 1: what students ask for (student-level mean share by category)
f1 = s1.sort_values("student_mean_share")
fig, ax = plt.subplots(figsize=(6.2, 3.4))
colors = [ORANGE if c in GROUPS["production"] else BLUE if c in GROUPS["understanding"]
          else AQUA if c == "verification" else "#9a9893" for c in f1.category]
ax.barh([CATEGORY_LABEL.get(c, c) for c in f1.category], f1.student_mean_share * 100, color=colors,
        xerr=[(f1.student_mean_share - f1.ci_low) * 100, (f1.ci_high - f1.student_mean_share) * 100],
        error_kw={"ecolor": INK2, "lw": 0.8, "capsize": 2})
for i, (v, hi) in enumerate(zip(f1.student_mean_share * 100, f1.ci_high * 100)):
    ax.text(hi + 0.8, i, f"{v:.0f}%", va="center", color=INK, fontsize=9)
ax.set_xlabel("Mean share of a student's prompts (%)")
ax.set_title(f"What students asked the course chatbot for (n = {len(stu_cat)} students, "
             f"≥{MIN_TURNS} prompts)", fontsize=10, loc="left")
ax.grid(axis="y", visible=False)
fig.savefig(FIG / "StudyChat_fig1_dialogue_acts.png")
plt.close(fig)

# fig 2: assignment vs exam, per student
fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
for ax, sem in zip(axes, SEMESTERS):
    g = grades[grades.semester == sem]
    ax.scatter(g.llm * 100, g.no_llm * 100, s=14, color=SEM_COLOR[sem], alpha=.7, lw=0)
    ax.plot([30, 105], [30, 105], color=INK2, lw=0.8, ls="--")
    ax.set_xlim(45, 102); ax.set_ylim(30, 105)
    ax.set_xlabel("Assignment average, AI permitted (%)")
    ax.set_title(f"{SEM_LABEL[sem]} (n = {len(g)})", fontsize=10, loc="left")
    ax.text(47, 100, f"{(g.gap > 0).mean():.0%} score higher on\nassignments than exams",
            fontsize=8.5, color=INK2, va="top")
axes[0].set_ylabel("Exam average, proctored (%)")
fig.savefig(FIG / "StudyChat_fig2_assignment_vs_exam.png")
plt.close(fig)

# fig 3: production tertiles vs scores
fig, ax = plt.subplots(figsize=(5.4, 3.2))
xs = np.arange(3)
ax.bar(xs - .18, s6.assign_mean * 100, .34, color=BLUE, label="Assignments (AI permitted)")
ax.bar(xs + .18, s6.exam_mean * 100, .34, color=ORANGE, label="Exams (proctored)")
for i, r in s6.iterrows():
    ax.text(i - .18, r.assign_mean * 100 + 1, f"{r.assign_mean * 100:.0f}", ha="center", fontsize=8.5)
    ax.text(i + .18, r.exam_mean * 100 + 1, f"{r.exam_mean * 100:.0f}", ha="center", fontsize=8.5)
ax.set_xticks(xs)
ax.set_xticklabels([f"{t}\n{lo:.0%}, {hi:.0%}" for t, lo, hi in
                    zip(s6.production_tertile, s6.share_production_min, s6.share_production_max)])
ax.set_xlabel("Share of prompts asking the AI to write or edit (tertiles)")
ax.set_ylabel("Mean score (%)")
ax.set_ylim(60, 104)
ax.legend(frameon=False, fontsize=8.5, loc="lower left")
ax.grid(axis="x", visible=False)
ax.set_title(f"Scores by reliance on AI production (n = {int(s6.n.sum())})", fontsize=10, loc="left")
fig.savefig(FIG / "StudyChat_fig3_production_tertiles.png")
plt.close(fig)

# fig 4: write-code share by assignment
s3d = pd.DataFrame(s3)
fig, ax = plt.subplots(figsize=(5.8, 3.0))
ax.bar(s3d.assignment, s3d.mean_share_write_code * 100, color=ORANGE, label="Write code")
ax.bar(s3d.assignment, s3d.mean_share_understanding * 100,
       bottom=s3d.mean_share_write_code * 100, color=BLUE, label="Understanding (conceptual/contextual)")
ax.set_ylabel("Mean share of prompts (%)")
ax.set_xlabel("Assignment (students with ≥5 prompts on it)")
ax.legend(frameon=False, fontsize=8.5, loc="upper left", bbox_to_anchor=(0, 1.18), ncol=2)
ax.grid(axis="x", visible=False)
fig.savefig(FIG / "StudyChat_fig4_by_assignment.png")
plt.close(fig)

print("StudyChat analysis complete:", OUT)
