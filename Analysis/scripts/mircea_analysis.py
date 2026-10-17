"""
Secondary analysis of the Mircea et al. (2026) Software Engineering capstone GenAI dataset
(Zenodo, doi:10.5281/zenodo.18846544).

Run from the IRP Working Directory:
    python Analysis/scripts/mircea_analysis.py

Inputs (read only):  Datasets/Mircea et al. (2026) Capstone GenAI/
                       StudentSurveyResults.xlsx  (150 responses; identical IDs to the CSV)
                       ClientSurveyResults.csv    (11 responses; semicolon-delimited)
                       Results of Coding Procedure.xlsx (authors' coding of free-text advice)
Outputs:             Analysis/outputs/Mircea/*.csv, Analysis/figures/Mircea_*.png

All data are self-reported. Percentages use the full denominator stated in each table.
German answer labels are translated to English below; the translations are ours.
Correlations are exploratory, Holm-adjusted, and do not indicate causation.
"""
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "Datasets" / "Mircea et al. (2026) Capstone GenAI"
OUT = ROOT / "Analysis" / "outputs" / "Mircea"
FIG = ROOT / "Analysis" / "figures"
OUT.mkdir(parents=True, exist_ok=True)
FIG.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, GRID = "#0b0b0b", "#52514e", "#e4e3df"
ORDINAL5 = ["#86b6ef", "#5598e7", "#2a78d6", "#1c5cab", "#104281"]  # blue ramp, light to dark
plt.rcParams.update({
    "font.family": "Calibri", "font.size": 10, "axes.edgecolor": INK2,
    "axes.labelcolor": INK, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "savefig.dpi": 300, "savefig.bbox": "tight",
})

# ---------------------------------------------------------------- translations
SCALES = {
    "skill": (["Gering", "Mittel", "Hoch"], ["Low", "Medium", "High"]),
    "experience": (["Keine", "Weniger als 1 Jahr", "1 - 3 Jahre", "Mehr als 3 Jahre"],
                   ["No experience", "Less than 1 year", "1-3 years", "More than 3 years"]),
    "attitude": (["Sehr pessimistisch", "Eher pessimistisch", "Neutral", "Eher optimistisch",
                  "Sehr optimistisch"],
                 ["Very pessimistic", "Rather pessimistic", "Neutral", "Rather optimistic",
                  "Very optimistic"]),
    "use_freq": (["(1) Gar nicht", "(2) Selten", "(3) Hin und wieder", "(4) Oft", "(5) Durchgängig"],
                 ["Not at all", "Rarely", "Now and then", "Often", "Continuously"]),
    "ai_first": (["Nie", "Selten", "Gelegentlich", "Häufig", "Sehr Häufig"],
                 ["Never", "Rarely", "Occasionally", "Frequently", "Very frequently"]),
    "student_first": (["Nie", "Selten", "Gelegentlich", "Häufig", "Sehr Häufig"],
                      ["Never", "Rarely", "Occasionally", "Frequently", "Very frequently"]),
    "usefulness": (["Sehr Schädlich", "Eher schädlich", "Neutral (keine Meinung)", "Eher nützlich",
                    "Sehr Nützlich"],
                   ["Very harmful", "Rather harmful", "Neutral (no opinion)", "Rather useful",
                    "Very useful"]),
}
PURPOSES = {
    "Zu Lernzwecken": "Learning (e.g. new frameworks or languages)",
    "Anforderungserhebung": "Requirements elicitation or analysis",
    "Dokumentation": "Generating or improving documentation",
    "High-Level Design": "High-level design (architecture, technology choices)",
    "Code generieren oder debuggen": "Generating or debugging code",
    "Technische Probleme": "Solving technical problems (not code-related)",
    "Qualitative Verbessung": "Improving code quality or testing code",
}
TOOLS = {
    "Allgemeine Chatbots": "General chatbots (ChatGPT, Gemini, Claude, Le Chat)",
    "Integrierte Modelle": "Integrated or specialised tools (GitHub Copilot, Cursor)",
    "LUHKI": "University-hosted ChatGPT instance (LUHKI)",
}
CLIENT_CONCERNS = {
    "funktionale Korrektheit": "Lack of functional correctness",
    "Mangelnde Qualität": "Lack of quality of the result",
    "Urheberrechten": "Copyright or IP infringement",
    "Datenschutzrisiken": "Data privacy risks",
    "Nachvollziehbarkeit": "Lack of traceability or accountability",
    "eigenständiges Verständnis": "Students' lack of independent understanding in client meetings",
    "keine Bedenken": "No concerns",
}
CLIENT_WISH = {
    "aktiv unterstützt": "Students should be actively supported and encouraged to use GenAI",
    "selbst für angemessen": "Students should use GenAI as they see fit",
    "nur selten": "Students should use GenAI rarely and with appropriate caution",
}
CLIENT_SCALES = {
    "attitude": SCALES["attitude"],
    "risk": (["Bedenklich", "Eher bedenklich", "Neutral", "Eher unbedenklich", "Unbedenklich"],
             ["Concerning", "Rather concerning", "Neutral", "Rather unconcerning", "Unconcerning"]),
}


def col_with(df, text):
    hits = [c for c in df.columns if text in c]
    assert len(hits) == 1, (text, hits)
    return hits[0]


def freq_table(series, de, en, n_total):
    vc = series.value_counts()
    return pd.DataFrame({"response": en, "n": [int(vc.get(d, 0)) for d in de]}).assign(
        pct=lambda d: 100 * d.n / n_total, denominator=n_total)


# ---------------------------------------------------------------- student survey
s = pd.read_excel(DATA / "StudentSurveyResults.xlsx", sheet_name=0)
N = len(s)
cols = {
    "skill": col_with(s, "Programmierfähigkeit"),
    "experience": col_with(s, "berufliche"),
    "attitude": col_with(s, "generelle, persönliche Einstellung"),
    "use_freq": col_with(s, "Wie viel haben Sie selbst GenAI"),
    "ai_first": col_with(s, "[Lösungen von GenAI vorschlagen lassen"),
    "student_first": col_with(s, "[Eigene Lösungsansätze vorgeben"),
    "usefulness": col_with(s, "Insgesamt empfinde ich"),
}
for key, c in cols.items():
    de, en = SCALES[key]
    unknown = set(s[c].dropna()) - set(de)
    assert not unknown, (key, unknown)
    s[key] = s[c].map(dict(zip(de, range(1, len(de) + 1))))

# M0 sample + M1 use + M6 usefulness: one long frequency table
rows = []
for key in ["skill", "experience", "attitude", "use_freq", "ai_first", "student_first", "usefulness"]:
    de, en = SCALES[key]
    t = freq_table(s[cols[key]], de, en, N)
    t.insert(0, "question", key)
    rows.append(t)
likert = pd.concat(rows)
likert.to_csv(OUT / "M0_student_closed_questions.csv", index=False)

users = s.use_freq > 1
n_users = int(users.sum())
headline = pd.DataFrame([
    ("Student responses", N, N),
    ("Reported any GenAI use in the project (not 'not at all')", n_users, N),
    ("Used GenAI often or continuously", int((s.use_freq >= 4).sum()), N),
    ("AI-first mode (AI proposes, student reviews) frequently or very frequently",
     int((s.ai_first >= 4).sum()), N),
    ("Student-first mode (student proposes, AI reviews) frequently or very frequently",
     int((s.student_first >= 4).sum()), N),
    ("Rated student GenAI use as rather or very useful", int((s.usefulness >= 4).sum()), N),
    ("Rated student GenAI use as rather or very harmful", int((s.usefulness <= 2).sum()), N),
    ("Rated own programming skill as low", int((s.skill == 1).sum()), N),
    ("No professional programming experience", int((s.experience == 1).sum()), N),
], columns=["measure", "n", "denominator"]).assign(pct=lambda d: 100 * d.n / d.denominator)
headline.to_csv(OUT / "M1_headline_measures.csv", index=False)

# M2 purposes and M3 tools
def yes_table(mapping, label):
    out = []
    for de_key, en in mapping.items():
        c = col_with(s, de_key)
        yes = s[c].eq("Ja")
        out.append({label: en, "n_yes": int(yes.sum()),
                    "pct_all_students": 100 * yes.mean(),
                    "n_yes_among_users": int(yes[users].sum()),
                    "pct_of_users": 100 * yes[users].mean(),
                    "n_yes_among_non_users": int(yes[~users].sum())})
    return pd.DataFrame(out).sort_values("n_yes", ascending=False).assign(
        denominator_all=N, denominator_users=n_users)

purposes = yes_table(PURPOSES, "purpose")
purposes.to_csv(OUT / "M2_purposes.csv", index=False)
tools = yes_table(TOOLS, "tool_type")
tools.to_csv(OUT / "M3_tools.csv", index=False)

purpose_cols = [col_with(s, k) for k in PURPOSES]
n_purposes = s[purpose_cols].eq("Ja").sum(axis=1)
pd.DataFrame({"n_purposes": n_purposes[users]}).value_counts().sort_index().rename(
    "n_students").reset_index().to_csv(OUT / "M2b_number_of_purposes_users.csv", index=False)

# M4 interaction modes (paired comparison of the two modes, same respondents)
diff = s.student_first - s.ai_first
w = stats.wilcoxon(s.student_first, s.ai_first)
modes = pd.DataFrame([
    ("Mean rating AI-first (1 = never, 5 = very frequently)", s.ai_first.mean()),
    ("Mean rating student-first", s.student_first.mean()),
    ("Median AI-first", s.ai_first.median()),
    ("Median student-first", s.student_first.median()),
    ("Students rating student-first higher than AI-first", int((diff > 0).sum())),
    ("Students rating both modes the same", int((diff == 0).sum())),
    ("Students rating AI-first higher than student-first", int((diff < 0).sum())),
    ("Students using AI-first frequently+ AND student-first never/rarely",
     int(((s.ai_first >= 4) & (s.student_first <= 2)).sum())),
    ("Students using both modes frequently+", int(((s.ai_first >= 4) & (s.student_first >= 4)).sum())),
    ("Students using neither mode more than rarely",
     int(((s.ai_first <= 2) & (s.student_first <= 2)).sum())),
    ("Wilcoxon signed-rank W (student-first vs AI-first)", w.statistic),
    ("Wilcoxon p", w.pvalue),
    ("Denominator", N),
], columns=["measure", "value"])
modes.to_csv(OUT / "M4_interaction_modes.csv", index=False)
pd.crosstab(s.ai_first.map(dict(zip(range(1, 6), SCALES["ai_first"][1]))),
            s.student_first.map(dict(zip(range(1, 6), SCALES["student_first"][1])))
            ).reindex(index=SCALES["ai_first"][1], columns=SCALES["student_first"][1]).fillna(0).astype(int
            ).rename_axis(index="AI-first (rows)", columns="Student-first (cols)"
            ).to_csv(OUT / "M4b_mode_crosstab.csv")

# M5 exploratory associations (Spearman, Holm-adjusted)
pairs = [("skill", "use_freq"), ("skill", "ai_first"), ("skill", "student_first"),
         ("experience", "use_freq"), ("attitude", "use_freq"), ("attitude", "usefulness"),
         ("use_freq", "usefulness"), ("use_freq", "ai_first"), ("use_freq", "student_first"),
         ("ai_first", "student_first")]
assoc = []
for a, b in pairs:
    r = stats.spearmanr(s[a], s[b])
    assoc.append({"variable_1": a, "variable_2": b, "n": N, "spearman_rho": r.correlation,
                  "p_raw": r.pvalue})
assoc = pd.DataFrame(assoc).sort_values("p_raw").reset_index(drop=True)
m = len(assoc)
holm = np.maximum.accumulate([(m - i) * p for i, p in enumerate(assoc.p_raw)])
assoc["p_holm"] = np.minimum(holm, 1)
assoc.to_csv(OUT / "M5_exploratory_correlations.csv", index=False)

# code generation/debugging use by self-rated skill
code_col = col_with(s, "Code generieren oder debuggen")
ct = pd.crosstab(s.skill.map({1: "Low", 2: "Medium", 3: "High"}), s[code_col].eq("Ja"))
ct.columns = ["No", "Yes"]
ct = ct.reindex(["Low", "Medium", "High"])
ct["pct_yes"] = 100 * ct.Yes / ct.sum(axis=1)
chi = stats.chi2_contingency(ct[["No", "Yes"]])
ct.attrs = {}
ct.to_csv(OUT / "M5b_code_generation_by_skill.csv")
pd.DataFrame([{"test": "chi-square, code generation/debugging x self-rated skill",
               "chi2": chi[0], "df": chi[2], "p": chi[1],
               "min_expected_count": chi[3].min()}]).to_csv(OUT / "M5c_code_by_skill_test.csv",
                                                             index=False)

# M7 coded free-text advice (authors' coding)
cod = pd.read_excel(DATA / "Results of Coding Procedure.xlsx", sheet_name=0)
cod.columns = ["statement", "use_cases", "directives"]
cod = cod.dropna(subset=["statement"])
n_statements = len(cod)


def count_codes(series):
    codes = (series.dropna().astype(str).str.split(",").explode().str.strip()
             .replace("", np.nan).dropna().str.title())
    return codes.value_counts()

code_rows = []
for kind in ["directives", "use_cases"]:
    vc = count_codes(cod[kind])
    for code, n in vc.items():
        code_rows.append({"category": kind, "code": code, "n_statements": int(n),
                          "pct_of_statements": 100 * n / n_statements,
                          "denominator": n_statements})
codes = pd.DataFrame(code_rows)
codes.to_csv(OUT / "M7_coded_advice.csv", index=False)
pd.DataFrame([
    ("Coded statements", n_statements),
    ("Statements with at least one directive code", int(cod.directives.notna().sum())),
    ("Statements with at least one use-case code", int(cod.use_cases.notna().sum())),
    ("Statements with no code", int((cod.directives.isna() & cod.use_cases.isna()).sum())),
], columns=["item", "n"]).to_csv(OUT / "M7b_coding_coverage.csv", index=False)

# ---------------------------------------------------------------- client survey
c = pd.read_csv(DATA / "ClientSurveyResults.csv", sep=";", encoding="utf-8")
NC = len(c)
cc = {
    "attitude": col_with(c, "allgemeine"),
    "genai_in_project": col_with(c, "Beinhaltete"),
    "risk": col_with(c, "Wie bewerten Sie"),
    "wish": col_with(c, "Was würden Sie sich wünschen"),
}
client_rows = []
for key in ["attitude", "risk"]:
    de, en = CLIENT_SCALES[key]
    unknown = set(c[cc[key]].dropna()) - set(de)
    assert not unknown, (key, unknown)
    t = freq_table(c[cc[key]], de, en, NC)
    t.insert(0, "question", key)
    client_rows.append(t)
t = freq_table(c[cc["genai_in_project"]], ["Ja", "Nein"], ["Yes", "No"], NC)
t.insert(0, "question", "project_included_genai_component")
client_rows.append(t)
wish = c[cc["wish"]]
t = pd.DataFrame([{"question": "wish_for_next_year", "response": en,
                   "n": int(wish.str.contains(k, regex=False).sum())} for k, en in CLIENT_WISH.items()])
t["pct"] = 100 * t.n / NC
t["denominator"] = NC
client_rows.append(t)
pd.concat(client_rows).to_csv(OUT / "M8_client_closed_questions.csv", index=False)

concerns = pd.DataFrame([{"concern": en, "n_yes": int(c[col_with(c, k)].eq("Ja").sum())}
                         for k, en in CLIENT_CONCERNS.items()])
concerns["pct"] = 100 * concerns.n_yes / NC
concerns["denominator"] = NC
concerns = concerns.sort_values("n_yes", ascending=False)
concerns.to_csv(OUT / "M8b_client_concerns.csv", index=False)

# ---------------------------------------------------------------- figures
def hbar(ax, labels, values, ns, denom, color=BLUE, xmax=100):
    y = np.arange(len(labels))[::-1]
    ax.barh(y, values, 0.62, color=color)
    for yi, v, n in zip(y, values, ns):
        ax.text(v + 1, yi, f"{v:.0f}%  ({n}/{denom})", va="center", fontsize=8, color=INK)
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.set_xlim(0, xmax)
    ax.grid(axis="y", visible=False)


# Fig 1 purposes
fig, ax = plt.subplots(figsize=(8, 3.4))
hbar(ax, purposes.purpose, purposes.pct_all_students, purposes.n_yes, N)
ax.set_xlabel(f"% of all student respondents (n = {N})")
ax.set_title("What capstone students used GenAI for", loc="left", fontsize=12, color=INK)
fig.savefig(FIG / "Mircea_fig1_purposes.png")
plt.close(fig)

# Fig 2 interaction modes, 100% stacked ordinal bars
fig, ax = plt.subplots(figsize=(8, 2.6))
labels5 = SCALES["ai_first"][1]
rows_ = [("AI proposes, student\nreviews or adapts", s.ai_first),
         ("Student proposes, AI\nreviews or improves", s.student_first)]
for i, (lab, ser) in enumerate(rows_[::-1]):
    left = 0
    for k in range(1, 6):
        v = 100 * (ser == k).mean()
        ax.barh(i, v, 0.55, left=left, color=ORDINAL5[k - 1], edgecolor="white", linewidth=2,
                label=labels5[k - 1] if i == 0 else None)
        if v >= 7:
            ax.text(left + v / 2, i, f"{v:.0f}%", ha="center", va="center", fontsize=8,
                    color="white" if k >= 3 else INK)
        left += v
ax.set_yticks([0, 1])
ax.set_yticklabels([r[0] for r in rows_[::-1]])
ax.set_xlim(0, 100)
ax.set_xlabel(f"% of student respondents (n = {N})")
ax.grid(False)
ax.legend(ncol=5, frameon=False, loc="lower left", bbox_to_anchor=(0, 1.0), fontsize=8)
ax.set_title("How often students used each interaction mode", loc="left", fontsize=12,
             color=INK, pad=24)
fig.savefig(FIG / "Mircea_fig2_interaction_modes.png")
plt.close(fig)

# Fig 3 client concerns
fig, ax = plt.subplots(figsize=(8, 3.0))
hbar(ax, concerns.concern, concerns.pct, concerns.n_yes, NC, color=ORANGE)
ax.set_xlabel(f"% of client respondents (n = {NC})")
ax.set_title("Client concerns about student GenAI use", loc="left", fontsize=12, color=INK)
fig.savefig(FIG / "Mircea_fig3_client_concerns.png")
plt.close(fig)

# Fig 4 coded directives in student advice
d = codes[codes.category == "directives"].sort_values("n_statements", ascending=False)
fig, ax = plt.subplots(figsize=(8, 3.2))
hbar(ax, d.code, d.pct_of_statements, d.n_statements, n_statements, color=AQUA, xmax=60)
ax.set_xlabel(f"% of coded free-text statements (n = {n_statements}); a statement can carry several codes")
ax.set_title("Advice students would give next year's cohort (directive codes)", loc="left",
             fontsize=12, color=INK)
fig.savefig(FIG / "Mircea_fig4_coded_directives.png")
plt.close(fig)

print("Mircea analysis complete. Outputs in", OUT)
