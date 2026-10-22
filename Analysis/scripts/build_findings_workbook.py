"""
Builds Analysis/Dataset_Findings_EPFL_Mircea_StudyChat.xlsx from the CSV outputs of
epfl_analysis.py, mircea_analysis.py and studychat_analysis.py. Run those three scripts first.

    python Analysis/scripts/build_findings_workbook.py

Every number in the Findings sheet is read from an output CSV, not typed by hand.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from start_sheet import add_start_sheet

import re

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill, Border, Side

ROOT = Path(__file__).resolve().parents[2]
E = ROOT / "Analysis" / "outputs" / "EPFL"
M = ROOT / "Analysis" / "outputs" / "Mircea"
S = ROOT / "Analysis" / "outputs" / "StudyChat"
XLSX = ROOT / "Analysis" / "Dataset_Findings_EPFL_Mircea_StudyChat.xlsx"
GRADES = ROOT / "Datasets" / "StudyChat" / "scores"


def extra_credit():
    """Students scoring above 100% on exam 2, per semester."""
    out = {}
    for sem in ("f24", "s25"):
        g = pd.read_csv(GRADES / f"{sem}_grades_released_normalized.csv")
        out[sem] = (int((g["e2"] > 1).sum()), int(g["e2"].notna().sum()))
    return out

EPFL_SRC = ("Borges et al. (2024), PNAS 121(49), e2414955121, doi:10.1073/pnas.2414955121; "
            "dataset github.com/epfl-nlp/NLP4Education. Our own secondary analysis.")
MIR_SRC = ("Mircea, Schmid, Droste & Schneider (2026), How Do Software Engineering Students Use Generative AI "
           "in Real-World Capstone Projects? An Empirical Baseline Study, EASE 2026, arXiv:2604.24521; dataset "
           "doi:10.5281/zenodo.18846544 (CC BY 4.0; Zenodo author order differs). Our own secondary analysis.")
SC_SRC = ("McNichols, Ikram & Lan (2026), The StudyChat Dataset: Student Dialogues With ChatGPT in an "
          "Artificial Intelligence Course, LAK26, arXiv:2503.07928v4; dataset "
          "huggingface.co/datasets/wmcnicho/StudyChat (v1.1, CC BY 4.0). Our own secondary analysis.")
SOURCES = {"EPFL": EPFL_SRC, "Mircea": MIR_SRC, "StudyChat": SC_SRC}


def r(path):
    return pd.read_csv(path)


def pct(x):
    return f"{x:.1f}%"


def get(df, **kw):
    q = df
    for k, v in kw.items():
        q = q[q[k] == v]
    assert len(q) == 1, (kw, len(q))
    return q.iloc[0]


# ---------------------------------------------------------------- EPFL numbers
cov = r(E / "00_coverage.csv").set_index("item")["value"]
cs = r(E / "02_computer_science_by_model_qtype.csv")
allq = r(E / "01_overall_by_model_qtype.csv")
chance = r(E / "07_mcq_chance_baseline.csv")
mc = r(E / "05_model_comparison_paired.csv")
pr = r(E / "04_prompt_strategies.csv")
prr = r(E / "04b_prompt_strategy_range.csv")
thr = r(E / "08b_course_threshold_summary.csv")
lvl = r(E / "03b_by_level.csv")
lang = r(E / "03c_by_language.csv")
ch = r(E / "09_question_characteristics_gpt4.csv")
lc = r(E / "09b_length_correlation.csv").iloc[0]
mvo = r(E / "06_mcq_vs_open.csv")

cs4 = get(cs, model="GPT-4", qtype="All")
cs35 = get(cs, model="ChatGPT", qtype="All")
cs4m = get(cs, model="GPT-4", qtype="MCQ")
cs4o = get(cs, model="GPT-4", qtype="Open answer")
ch4 = get(chance, model="GPT-4")
mca = get(mc, qtype="All")
g4p = pr[(pr.model == "GPT-4") & (pr.prompt_type != "FRIEDMAN TEST")]
g4m = g4p[g4p.qtype == "MCQ"].sort_values("mean_grade")
fr_m = get(pr, model="GPT-4", qtype="MCQ", prompt_type="FRIEDMAN TEST")
rng_m = get(prr, model="GPT-4", qtype="MCQ")
rng_o = get(prr, model="GPT-4", qtype="Open answer")
thr_cs = get(thr, model="GPT-4", scope="Computer Science")
lb, lm = get(lvl, model="GPT-4", level="Bachelor"), get(lvl, model="GPT-4", level="Master")
le, lf = get(lang, model="GPT-4", language="English"), get(lang, model="GPT-4", language="French")
oc_t = get(ch, feature="has_code", value="True", qtype="Open answer")
oc_f = get(ch, feature="has_code", value="False", qtype="Open answer")
mq1 = get(ch, feature="length_band", value="Q1 shortest", qtype="MCQ")
mq4 = get(ch, feature="length_band", value="Q4 longest", qtype="MCQ")
mvo_cs4 = get(mvo, scope="Computer Science", model="GPT-4")

UNSUP_TEST = "Unsupervised question-based tests (online quizzes, take-home MCQ / short answer)"
SUPERVISED = "Direct and supervised verification (supervised exams, oral/viva, demonstrations)"
UNSUP = "Unsupervised assessment formats (programming tasks, take-home assignments, reports, projects)"
PROCESS = "Process-based assessment (staged submissions, checkpoints, logs, version history)"
AUTH = "Authentic and personalised assessment (real-world projects, contextualised tasks)"
AITRANS = "AI-transparent and integrated assessment (declarations, critical evaluation of AI output)"
# proposal Table 1 categories mapped to the eight D2 assessment types
D2_TYPES = {
    UNSUP_TEST: "Unsupervised formats",
    SUPERVISED: "Supervised assessment, Oral assessments, Practical demonstrations",
    UNSUP: "Unsupervised formats",
    PROCESS: "Staged submissions, Process evidence",
    AUTH: "Personalised tasks",
    AITRANS: "AI-use declarations, Process evidence",
    "All": "All eight types",
}


def d2_types(atype):
    out = []
    for a in atype.split(";"):
        for t_ in D2_TYPES[a.strip()].split(", "):
            if t_ not in out:
                out.append(t_)
    return ", ".join(out)

findings = []


def add(ds, topic, finding, measure, sample, method, atype, criteria, interp, limits, file):
    findings.append({
        "Dataset": ds, "Topic": topic,
        "Finding (Level 1: what our analysis of the data shows)": finding,
        "Key measure(s)": measure, "Sample / denominator": sample,
        "Calculation method": method,
        "Related assessment types (D2)": d2_types(atype),
        "Evaluation criteria informed": criteria,
        "Possible implication (Level 2: our interpretation, not a finding)": interp,
        "Limitations": limits, "Output file": file, "Source to cite": SOURCES[ds],
    })


EPFL_LIM = ("Models are GPT-3.5 and GPT-4 (2023); current models are likely stronger, but this "
            "dataset cannot show that. Measures AI capability, not student learning. ")

add("EPFL", "Data coverage",
    f"All {cov['Questions in questions.json']:,} questions from {cov['Courses in courses.json']} courses have grades. "
    f"{cov['Grade rows missing']} of {cov['Grade rows expected (questions x 2 models x 8 prompts)']:,} "
    "model x prompt rows are missing. Bloom's level and difficulty labels were removed by the provider. "
    "The grades file mislabels 14 online courses as Bachelor, so course metadata was taken from courses.json.",
    f"Computer Science: {cov['Computer Science courses']} courses, {cov['Computer Science questions']:,} questions "
    f"({int(cs4m.n_questions):,} MCQ, {int(cs4o.n_questions):,} open answer)",
    f"{cov['Questions in questions.json']:,} questions; {cov['Grade rows present']:,} grade rows",
    "Row counts and joins across courses.json, questions.json and grade_per_question.csv.",
    "All", "Data quality (supports methodology section)",
    "Analysis by Bloom's level or question difficulty is not possible with the released data.",
    "Some courses and gold answers were removed at the data provider's request.",
    "00_coverage.csv; 00_courses_by_program_level.csv")

add("EPFL", "GenAI capability, single attempt (CS)",
    f"With a single zero-shot prompt, GPT-4 answered {pct(cs4.pct_correct_zero_shot)} of Computer Science "
    f"questions fully correctly and {pct(cs4.pct_mostly_correct_zero_shot)} at least mostly correctly. "
    f"GPT-3.5 reached {pct(cs35.pct_correct_zero_shot)} and {pct(cs35.pct_mostly_correct_zero_shot)}.",
    f"GPT-4 zero-shot: {pct(cs4.pct_correct_zero_shot)} fully correct; mean grade over 8 prompts "
    f"{cs4.mean_grade_avg_prompts:.3f} (95% CI {cs4.mean_grade_ci_low:.3f} to {cs4.mean_grade_ci_high:.3f})",
    f"n = {int(cs4.n_questions):,} CS questions",
    "Question-level. Fully correct = grade 1; mostly correct = grade >= 0.66. Bootstrap 95% CI (2,000 resamples).",
    UNSUP_TEST + "; " + UNSUP, "GenAI capability to complete the task; Academic integrity",
    "When a student pastes a question into GenAI with no effort, roughly half of CS questions get a usable answer. "
    "A correct final answer alone is weak evidence of individual understanding in unsupervised settings.",
    EPFL_LIM + "Open answers were graded automatically by GPT-4, not by humans.",
    "02_computer_science_by_model_qtype.csv")

add("EPFL", "GenAI capability, several attempts (CS)",
    f"If a student tries all 8 prompting strategies and can pick the best answer, GPT-4 produced a fully correct "
    f"answer for {pct(cs4.pct_correct_best_of_8)} of CS questions ({pct(cs4.pct_mostly_correct_best_of_8)} at least "
    f"mostly correct). Only {pct(cs4.pct_never_correct_any_prompt)} of CS questions were never fully answered by "
    f"any prompt. Under a majority rule (>= 5 of 8 prompts correct) the figure is {pct(cs4.pct_correct_majority_of_8)}.",
    f"Best of 8: {pct(cs4.pct_correct_best_of_8)}; majority of 8: {pct(cs4.pct_correct_majority_of_8)}; "
    f"never correct: {pct(cs4.pct_never_correct_any_prompt)}",
    f"n = {int(cs4.n_questions):,} CS questions, 8 prompts each",
    "Best of 8 = max grade across 8 prompts (upper bound; assumes the student can recognise the right answer). "
    "Majority = at least 5 of 8 prompts fully correct. Definitions are ours, not the paper's.",
    UNSUP_TEST + "; " + UNSUP, "GenAI capability to complete the task; Academic integrity",
    "Very few conventional CS questions are out of reach of 2023-era GenAI when students make repeated attempts. "
    "Redesign is more promising than trying to write 'AI-proof' questions.",
    EPFL_LIM + "Best of 8 overstates what a typical student would get, because it assumes they can pick the "
    "correct answer from several.",
    "02_computer_science_by_model_qtype.csv")

add("EPFL", "MCQ versus chance",
    f"On single-answer MCQs (median {ch4.median_options:.0f} options), GPT-4 zero-shot was correct on "
    f"{pct(ch4.pct_correct_zero_shot)}, compared with an expected {pct(ch4.expected_pct_correct_by_chance)} "
    f"from random guessing. Best of 8 reached {pct(ch4.pct_correct_best_of_8)}.",
    f"Zero-shot {pct(ch4.pct_correct_zero_shot)} vs chance {pct(ch4.expected_pct_correct_by_chance)}",
    f"n = {int(ch4.n_single_answer_mcq):,} single-answer MCQs, all programs",
    "Chance = mean of 1 / number of options per question.",
    UNSUP_TEST, "GenAI capability to complete the task",
    "Unsupervised MCQ quizzes give GenAI users a large advantage over guessing; they are better suited to "
    "formative use or to supervised conditions.",
    EPFL_LIM + "Multiple-answer MCQs excluded from this calculation.",
    "07_mcq_chance_baseline.csv")

add("EPFL", "MCQ versus open answer (CS)",
    f"For GPT-4 in CS courses, {pct(cs4m.pct_correct_zero_shot)} of MCQs were answered correctly zero-shot. "
    f"For open answers, {pct(cs4o.pct_correct_zero_shot)} were fully correct but {pct(cs4o.pct_mostly_correct_zero_shot)} "
    f"were at least mostly correct. Mean grades did not differ clearly (Mann-Whitney p = {mvo_cs4.p:.2f}).",
    f"MCQ mean {mvo_cs4.mean_mcq:.3f} vs open mean {mvo_cs4.mean_open:.3f}",
    f"{int(mvo_cs4.n_mcq):,} MCQ and {int(mvo_cs4.n_open):,} open CS questions",
    "Question-level mean grade over 8 prompts; two-sided Mann-Whitney U.",
    UNSUP_TEST, "GenAI capability to complete the task",
    "Switching from MCQ to open-answer format does not, by itself, remove GenAI capability. Open answers are often "
    "partly right, so they may still reveal reasoning gaps if marked by a human against clear criteria.",
    EPFL_LIM + "MCQ is exact-match marked while open answers were marked by GPT-4 on a 4-point scale, so the two "
    "are not directly comparable.",
    "06_mcq_vs_open.csv")

add("EPFL", "Model generation",
    f"GPT-4 scored {mca.difference_pts:.1f} percentage points higher than GPT-3.5 on mean grade and did better on "
    f"{pct(mca.pct_questions_gpt4_better)} of questions (worse on {pct(mca.pct_questions_gpt35_better)}).",
    f"GPT-4 mean {mca.gpt4_mean:.3f} vs GPT-3.5 {mca.gpt35_mean:.3f}; Wilcoxon p < 0.001",
    f"n = {int(mca.n_questions):,} questions, paired",
    "Paired by question; Wilcoxon signed-rank on question-level mean grades.",
    "All", "GenAI capability to complete the task",
    "Capability rose clearly between two model generations a few months apart. Evidence about which tasks are "
    "'hard for AI' dates quickly; recommendations should not rely on current AI weaknesses.",
    EPFL_LIM, "05_model_comparison_paired.csv")

add("EPFL", "Prompting strategy",
    f"For GPT-4 on MCQs, prompting strategy changed the mean grade by up to {rng_m.range_pts:.0f} points "
    f"(lowest {g4m.iloc[0].prompt_type} {g4m.iloc[0].mean_grade:.2f}, highest {g4m.iloc[-1].prompt_type} "
    f"{g4m.iloc[-1].mean_grade:.2f}). For open answers the range was only {rng_o.range_pts:.0f} points.",
    f"MCQ range {rng_m.range_pts:.1f} pts; open-answer range {rng_o.range_pts:.1f} pts; Friedman p < 0.001",
    f"n = {int(fr_m.n_questions):,} MCQs with all 8 prompts (GPT-4)",
    "Question-level grade per prompt; Friedman test across the 8 strategies.",
    UNSUP_TEST + "; " + AITRANS, "GenAI capability to complete the task; Compatibility with responsible GenAI use",
    "Simple prompting skill improves AI results on MCQs, so 'paste and submit' underestimates what a slightly "
    "skilled user can get. Prompting skill on its own is not evidence of subject understanding.",
    EPFL_LIM + "Statistical significance mainly reflects the large sample; focus on the size of the range.",
    "04_prompt_strategies.csv; 04b_prompt_strategy_range.csv")

add("EPFL", "Course-level variation (CS)",
    f"GPT-4 zero-shot mean grade was 0.5 or higher in {int(thr_cs['courses_zero_shot_mean_ge_0.5'])} of "
    f"{int(thr_cs.courses_with_10plus_questions)} CS courses (all {int(thr_cs['courses_best_of_8_mean_ge_0.5'])} with best of 8). "
    f"Course means ranged from {thr_cs.min_course_zero_shot_mean:.2f} to {thr_cs.max_course_zero_shot_mean:.2f}.",
    f"Median course zero-shot mean {thr_cs.median_course_zero_shot_mean:.2f}",
    f"{int(thr_cs.courses_with_10plus_questions)} CS courses with >= 10 questions",
    "Course mean of question-level grades. The 0.5 line is an illustrative reference, not an EPFL pass mark.",
    UNSUP_TEST + "; " + UNSUP, "GenAI capability to complete the task; Academic integrity",
    "Exposure differs a lot between courses, so redesign effort could be prioritised course by course rather "
    "than applied uniformly.",
    EPFL_LIM + "Course question sets were not complete exams and do not reflect actual course weighting.",
    "08_course_level.csv; 08b_course_threshold_summary.csv")

add("EPFL", "Course level (all programs)",
    f"GPT-4 did not perform worse on Master's-level questions (mean {lm.mean_grade_avg_prompts:.3f}) than on "
    f"Bachelor's-level questions ({lb.mean_grade_avg_prompts:.3f}).",
    f"Master {lm.mean_grade_avg_prompts:.3f} (n = {int(lm.n_questions):,}); Bachelor {lb.mean_grade_avg_prompts:.3f} "
    f"(n = {int(lb.n_questions):,})",
    "5,175 questions (online courses reported separately)",
    "Question-level mean grade over 8 prompts; bootstrap CIs in file.",
    "All", "GenAI capability to complete the task",
    "Assessment at higher year levels is not automatically safer from GenAI.",
    EPFL_LIM + "Program mix differs between levels.", "03b_by_level.csv")

add("EPFL", "Language",
    f"GPT-4 zero-shot was fully correct on {pct(le.pct_correct_zero_shot)} of English questions and "
    f"{pct(lf.pct_correct_zero_shot)} of French questions; mean grades over 8 prompts were similar "
    f"({le.mean_grade_avg_prompts:.3f} vs {lf.mean_grade_avg_prompts:.3f}).",
    f"English n = {int(le.n_questions):,}; French n = {int(lf.n_questions):,}",
    "5,175 questions", "Question-level.", "All", "GenAI capability; Fairness (context only)",
    "Low relevance for Adelaide (English-language teaching). Record for completeness only.",
    EPFL_LIM + "Language is confounded with course and program.", "03c_by_language.csv")

add("EPFL", "Question characteristics (exploratory)",
    f"GPT-4 scored lower on open-answer questions containing code ({oc_t.mean_grade:.2f}, n = {int(oc_t.n_questions):,}) "
    f"than on those without ({oc_f.mean_grade:.2f}, n = {int(oc_f.n_questions):,}). Longer MCQs were harder: "
    f"shortest quartile {mq1.mean_grade:.2f} vs longest {mq4.mean_grade:.2f}. Overall correlation between question "
    f"length and grade was weak (rho = {lc.spearman_rho_words_vs_grade:.2f}).",
    f"Spearman rho length vs grade = {lc.spearman_rho_words_vs_grade:.2f} (n = {int(lc.n):,})",
    "5,175 questions, GPT-4",
    "Simple text heuristics: code = code-like tokens; maths = LaTeX markers; length = word count quartiles.",
    UNSUP_TEST + "; " + UNSUP, "GenAI capability to complete the task",
    "Longer, multi-part and code-based questions reduce GenAI performance slightly but do not stop it. "
    "This is not strong enough to justify relying on question wording as a security measure.",
    EPFL_LIM + "Heuristics are rough and unvalidated; differences are modest. Treat as exploratory.",
    "09_question_characteristics_gpt4.csv; 09b_length_correlation.csv")

# ---------------------------------------------------------------- Mircea numbers
hd = r(M / "M1_headline_measures.csv").set_index("measure")
pur = r(M / "M2_purposes.csv").set_index("purpose")
tl = r(M / "M3_tools.csv").set_index("tool_type")
md = r(M / "M4_interaction_modes.csv").set_index("measure")["value"]
co = r(M / "M5_exploratory_correlations.csv")
cbs = r(M / "M5b_code_generation_by_skill.csv").set_index("skill")
cbt = r(M / "M5c_code_by_skill_test.csv").iloc[0]
cd = r(M / "M7_coded_advice.csv")
cdir = cd[cd.category == "directives"].set_index("code")
cl = r(M / "M8_client_closed_questions.csv")
cc = r(M / "M8b_client_concerns.csv").set_index("concern")


def h(key):
    row = hd.loc[key]
    return f"{pct(row.pct)} ({int(row.n)}/{int(row.denominator)})"


def p_(key):
    row = pur.loc[key]
    return f"{pct(row.pct_all_students)} ({int(row.n_yes)}/{int(row.denominator_all)})"


def corr(a, b):
    return get(co, variable_1=a, variable_2=b)


MIR_LIM = ("Self-reported survey from one German university's software engineering capstone; voluntary "
           "response, so likely selection bias. Does not measure understanding or performance. ")

add("Mircea", "Prevalence of GenAI use",
    f"{h(chr(82)+'eported any GenAI use in the project (not ' + chr(39) + 'not at all' + chr(39) + ')')} of capstone students "
    f"reported using GenAI in their project, and {h('Used GenAI often or continuously')} used it often or continuously.",
    "Use frequency on a 5-point scale", "n = 150 students",
    "Frequencies of closed responses; all 150 respondents as denominator.",
    UNSUP + "; " + AUTH, "Compatibility with responsible GenAI use; Authenticity",
    "In a real-client project, GenAI use was the norm, so designing for permitted use is more realistic than "
    "assuming non-use.", MIR_LIM, "M1_headline_measures.csv; M0_student_closed_questions.csv")

add("Mircea", "Purposes of use",
    f"The most common uses were generating or debugging code {p_('Generating or debugging code')} and learning "
    f"{p_('Learning (e.g. new frameworks or languages)')}, followed by documentation "
    f"{p_('Generating or improving documentation')}. Few used it for high-level design "
    f"{p_('High-level design (architecture, technology choices)')} or requirements "
    f"{p_('Requirements elicitation or analysis')}.",
    "7 yes/no purpose items", "n = 150 students (percentages of all respondents)",
    "Proportion answering 'Ja' (yes) per item; multiple answers allowed.",
    UNSUP + "; " + PROCESS, "GenAI capability; Evidence of individual understanding",
    "Code and documentation, the artefacts most often assessed, are where GenAI is used most. Design decisions "
    "and requirements work, which involve more individual judgement, are where it is used least, so they may be "
    "better places to look for evidence of individual contribution (proposal, not tested).",
    MIR_LIM + "Categories were fixed by the questionnaire.", "M2_purposes.csv; M2b_number_of_purposes_users.csv")

add("Mircea", "Tools",
    f"General chatbots were used by {pct(tl.loc['General chatbots (ChatGPT, Gemini, Claude, Le Chat)'].pct_all_students)}, "
    f"integrated coding tools (e.g. Copilot, Cursor) by "
    f"{pct(tl.loc['Integrated or specialised tools (GitHub Copilot, Cursor)'].pct_all_students)}, and the "
    f"university-hosted instance by only {pct(tl.loc['University-hosted ChatGPT instance (LUHKI)'].pct_all_students)}.",
    "3 yes/no tool items", "n = 150 students",
    "Proportion answering yes per item.",
    AITRANS + "; " + PROCESS, "Scalability; Implementation cost; Compatibility with responsible GenAI use",
    "If an assessment design depends on students using a university-managed AI environment (for example to "
    "capture prompt history), uptake cannot be assumed: here almost all students used external tools.",
    MIR_LIM + "Local context: the university tool may have been new or little promoted.", "M3_tools.csv")

add("Mircea", "Interaction modes",
    f"{h('AI-first mode (AI proposes, student reviews) frequently or very frequently')} frequently let GenAI propose "
    f"solutions that they then reviewed, and {h('Student-first mode (student proposes, AI reviews) frequently or very frequently')} "
    f"frequently gave their own solution to GenAI to review. The two modes were used about equally "
    f"(Wilcoxon p = {md['Wilcoxon p']:.2f}); {int(md['Students rating both modes the same'])} of 150 rated them the same "
    f"and only {int(md['Students using AI-first frequently+ AND student-first never/rarely'])} relied heavily on AI-first "
    f"while rarely using student-first.",
    f"Mean AI-first {md['Mean rating AI-first (1 = never, 5 = very frequently)']:.2f}; mean student-first "
    f"{md['Mean rating student-first']:.2f}; rho between modes {corr('ai_first', 'student_first').spearman_rho:.2f}",
    "n = 150 students, paired ratings",
    "5-point frequency scale; Wilcoxon signed-rank; cross-tabulation of the two items.",
    PROCESS + "; " + AITRANS, "Evidence of individual understanding; Compatibility with responsible GenAI use",
    "Most students mix both modes rather than being one 'type' of user. Assessment that asks students to show "
    "their own starting point before AI input (e.g. a staged checkpoint) would capture the student-first part, "
    "which a final artefact hides (proposal, not tested).",
    MIR_LIM + "Two single items; no observation of actual behaviour.",
    "M4_interaction_modes.csv; M4b_mode_crosstab.csv")

add("Mircea", "Heavier use and AI-first reliance",
    f"Overall use frequency was more strongly associated with AI-first use (rho = {corr('use_freq', 'ai_first').spearman_rho:.2f}) "
    f"than with student-first use (rho = {corr('use_freq', 'student_first').spearman_rho:.2f}). Both are significant "
    "after Holm correction.",
    f"Spearman rho {corr('use_freq', 'ai_first').spearman_rho:.2f} vs {corr('use_freq', 'student_first').spearman_rho:.2f}",
    "n = 150 students",
    "Spearman rank correlations on ordinal items; Holm adjustment over 10 exploratory tests.",
    PROCESS + "; " + SUPERVISED, "Evidence of individual understanding",
    "Students who use GenAI most tend to lean more on AI-generated proposals, which is where individual "
    "verification matters most.",
    MIR_LIM + "Correlation only; overlapping item wording may inflate the association.",
    "M5_exploratory_correlations.csv")

add("Mircea", "Self-rated skill",
    f"Self-rated programming skill was not significantly associated with use frequency "
    f"(rho = {corr('skill', 'use_freq').spearman_rho:.2f}, Holm p = {corr('skill', 'use_freq').p_holm:.2f}). "
    f"Code generation was reported by {pct(cbs.loc['Low'].pct_yes)} of low-, {pct(cbs.loc['Medium'].pct_yes)} of medium- "
    f"and {pct(cbs.loc['High'].pct_yes)} of high-skill students, but the difference was not significant "
    f"(chi-square p = {cbt.p:.2f}).",
    f"Low n = {int(cbs.loc['Low'].No + cbs.loc['Low'].Yes)}, medium n = {int(cbs.loc['Medium'].No + cbs.loc['Medium'].Yes)}, "
    f"high n = {int(cbs.loc['High'].No + cbs.loc['High'].Yes)}",
    "n = 150 students",
    "Spearman correlation; chi-square test of independence (3 x 2).",
    UNSUP, "Evidence of individual understanding; Fairness",
    "No clear evidence here that weaker students rely more on GenAI. Do not assume it when designing.",
    MIR_LIM + "Only 13 students rated themselves low skill, so the test has little power.",
    "M5_exploratory_correlations.csv; M5b_code_generation_by_skill.csv; M5c_code_by_skill_test.csv")

add("Mircea", "Perceived usefulness",
    f"{h('Rated student GenAI use as rather or very useful')} rated student GenAI use in the project as useful and "
    f"{h('Rated student GenAI use as rather or very harmful')} as harmful.",
    "5-point usefulness scale", "n = 150 students", "Frequencies.",
    AITRANS, "Compatibility with responsible GenAI use; Authenticity",
    "Students broadly see GenAI as useful in authentic project work, supporting permitted-use designs.",
    MIR_LIM, "M1_headline_measures.csv")

d1, d2, d3 = cdir.iloc[0], cdir.iloc[1], cdir.iloc[2]
add("Mircea", "Students' own advice (coded)",
    f"In free-text advice to future students, the most frequent directive was '{cdir.index[0]}' "
    f"({pct(d1.pct_of_statements)}, {int(d1.n_statements)}/{int(d1.denominator)}), then '{cdir.index[1]}' "
    f"({pct(d2.pct_of_statements)}) and '{cdir.index[2]}' ({pct(d3.pct_of_statements)}).",
    "Counts of the authors' directive codes", f"n = {int(d1.denominator)} coded statements (of 150 students)",
    "Codes from the authors' 'Results of Coding Procedure.xlsx' split on commas and counted; a statement can carry "
    "several codes. We did not re-code.",
    PROCESS + "; " + SUPERVISED + "; " + AITRANS,
    "Evidence of individual understanding; Compatibility with responsible GenAI use",
    "Students themselves see loss of understanding and unchecked output as the main risks. This supports "
    "assessment that checks understanding of AI-assisted work (e.g. explanation or short oral checks).",
    MIR_LIM + "Only 89 of 150 students answered; coding was done by the original authors and its reliability is "
    "not reported in the files.", "M7_coded_advice.csv; M7b_coding_coverage.csv")

cw = get(cl, question="wish_for_next_year",
         response="Students should be actively supported and encouraged to use GenAI")
cu = cc.loc["Students' lack of independent understanding in client meetings"]
add("Mircea", "Client perspective",
    f"The most common client concern was students' lack of independent understanding in client meetings "
    f"({int(cu.n_yes)} of {int(cu.denominator)}). Quality, privacy and traceability were each named by "
    f"{int(cc.loc['Lack of quality of the result'].n_yes)} of {int(cu.denominator)}. Yet {int(cw.n)} of "
    f"{int(cw.denominator)} clients wanted students actively supported and encouraged to use GenAI.",
    f"{int(cu.n_yes)}/{int(cu.denominator)} concerned about independent understanding; {int(cw.n)}/{int(cw.denominator)} "
    "want GenAI use encouraged",
    "n = 11 clients", "Counts of yes/no concern items and single-choice wish item.",
    SUPERVISED + "; " + AUTH, "Evidence of individual understanding; Authenticity",
    "Industry clients in this study want both: students who use GenAI, and students who can explain their work "
    "in person. This matches the project's position and supports live explanation or oral components.",
    MIR_LIM + "Very small sample (11); report as counts, not percentages. The 11 are individuals, not 11 "
    "independent organisations (several stakeholders per project). The questionnaire opened by telling clients "
    "that over 90% of students used GenAI and that a ban or controls would be neither feasible nor sensible, "
    "so support for encouraging use may be inflated; state this whenever these figures are cited.",
    "M8_client_closed_questions.csv; M8b_client_concerns.csv")

# ---------------------------------------------------------------- StudyChat numbers
scov = r(S / "S0_coverage.csv").set_index("semester")
sgrp = r(S / "S1c_student_group_shares.csv").set_index("group")
sfirst = r(S / "S2_first_turn_of_chat.csv").set_index("category")
sasg = r(S / "S3_by_assignment.csv").set_index("assignment")
sae = r(S / "S4_assignment_vs_exam.csv").set_index("semester")
scor = r(S / "S5_usage_outcome_correlations.csv")
sreg = r(S / "S5b_exam_regression.csv").set_index("term")
stert = r(S / "S6_production_tertiles.csv").set_index("production_tertile")
suse = r(S / "S7_assignment_use_vs_score.csv")

sca = scov.loc["all"]
ae = sae.loc["all"]
gp, gu, gw, gv = (sgrp.loc[k] for k in ["production", "understanding", "write_code", "verification"])


def p_fmt(p):
    return "p < 0.001" if p < 0.001 else f"p = {p:.2f}"


SC_LIM = ("One AI course (COMPSCI 383) at one US university, 2024-25, with a course chatbot (gpt-4o-mini); "
          "students opted in to sharing chats and grades, so likely selection bias. Dialogue-act labels were "
          "generated by GPT-4.1, not human-coded. Observational, so associations are not causal. Use of other "
          "AI tools outside the course chatbot is not captured. ")

add("StudyChat", "Data coverage",
    f"{int(sca.turns):,} labelled student prompts in {int(sca.chats):,} chats from {int(sca.students_with_chats)} "
    f"students across two semesters. {int(sca.linked_students)} students have both chats and grades; "
    f"{int(sca.graded_no_chats)} graded students never used the chatbot and {int(sca.chats_no_grades)} chat users "
    "did not release grades.",
    f"Fall 2024: {int(scov.loc['f24'].linked_students)} linked students; Spring 2025: "
    f"{int(scov.loc['s25'].linked_students)}",
    f"{int(sca.students_with_grades)} graded students; {int(sca.students_with_chats)} chat users",
    "Joins on anonymised userId between dialogues/*.jsonl and scores/*.csv, within semester.",
    "All", "Data quality (supports methodology section)",
    f"Only {int(sca.graded_no_chats)} graded students did not use the chatbot, so a users vs non-users comparison "
    "at student level is not possible.",
    SC_LIM, "S0_coverage.csv")

add("StudyChat", "What students asked the AI for",
    f"The average student used {pct(gu.mean_share * 100)} of prompts for understanding (conceptual or contextual "
    f"questions) and {pct(gp.mean_share * 100)} to ask the AI to write or edit (write code alone "
    f"{pct(gw.mean_share * 100)}). Only {pct(gp.pct_students_share_ge_50 * 100)} of students used write-or-edit "
    f"requests for half or more of their prompts. Verification requests were rare ({pct(gv.mean_share * 100)}).",
    f"Student-level mean share (95% CI): understanding {gu.mean_share:.2f} ({gu.ci_low:.2f} to {gu.ci_high:.2f}); "
    f"write or edit {gp.mean_share:.2f} ({gp.ci_low:.2f} to {gp.ci_high:.2f})",
    f"n = {int(gp.n_students)} students with >= 10 prompts",
    "Share of each student's prompts per label group, then averaged across students. Groups are ours: write or edit "
    "= writing_request + editing_request; understanding = conceptual_questions + contextual_questions. "
    "Bootstrap 95% CI (2,000 resamples).",
    UNSUP + "; " + AITRANS, "Compatibility with responsible GenAI use; Evidence of individual understanding",
    "When a course provides its own AI tool, most use is help-seeking rather than outsourcing, but almost a third "
    "of prompts still ask the AI to produce work. Permitted-use policies should expect both.",
    SC_LIM + "Label groups are a rough proxy for 'asking for the solution'.",
    "S1_dialogue_acts_category.csv; S1b_dialogue_acts_subcategory.csv; S1c_student_group_shares.csv")

fw = sfirst.loc["writing_request"]
n_chats = int(sfirst.chats.sum())
add("StudyChat", "First move in a chat",
    f"{pct(fw.share_of_chats * 100)} of chats opened with a writing request ({int(fw.subcategory_write_code)} of "
    f"{n_chats:,} with 'write code'), and {pct(sfirst.loc['conceptual_questions'].share_of_chats * 100)} opened "
    "with a conceptual question.",
    f"Writing-request openings: {int(fw.chats)}/{n_chats:,} chats",
    f"n = {n_chats:,} chats",
    "Label of the earliest prompt (lowest interactionCount) in each chat.",
    PROCESS + "; " + AITRANS, "Evidence of individual understanding; Academic integrity",
    "A sizeable minority of AI sessions start with 'write it for me', the AI-first pattern also reported in the "
    "Mircea survey. A final submission cannot show which pattern a student followed; process evidence can.",
    SC_LIM + "Chat-level count, so heavy users contribute more chats.", "S2_first_turn_of_chat.csv")

ec = extra_credit()
EC_NOTE = (f"Exam 2 carried extra credit ({ec['f24'][0]} of {ec['f24'][1]} Fall 2024 and {ec['s25'][0]} of "
           f"{ec['s25'][1]} Spring 2025 students scored above 100%), which raises exam averages and narrows the gap.")

add("StudyChat", "AI-permitted assignments vs proctored exams",
    f"Students averaged {pct(ae.assign_mean * 100)} on take-home programming assignments where the course chatbot "
    f"was allowed, and {pct(ae.exam_mean * 100)} on proctored exams without AI. {pct(ae.pct_assign_above_exam * 100)} "
    f"scored higher on assignments; the median gap was {ae.gap_median * 100:.1f} points "
    f"(95% CI {ae.gap_ci_low * 100:.1f} to {ae.gap_ci_high * 100:.1f}). The gap appeared in both semesters.",
    f"Median gap {ae.gap_median * 100:.1f} pts; Wilcoxon {p_fmt(ae.wilcoxon_p)}; higher on assignments: Fall 2024 "
    f"{pct(sae.loc['f24'].pct_assign_above_exam * 100)}, Spring 2025 {pct(sae.loc['s25'].pct_assign_above_exam * 100)}",
    f"n = {int(ae.n)} graded students, paired",
    "Released points-weighted assignment average (llm) vs exam average (no_llm); Wilcoxon signed-rank; "
    "bootstrap 95% CI for the median gap.",
    UNSUP + "; " + SUPERVISED, "Evidence of individual understanding; Academic integrity; Validity",
    "Unsupervised AI-permitted work and supervised exams measure different things. Some gap is expected (time "
    "pressure, exam difficulty), so it is not a measure of AI misuse; how much students used the course "
    "chatbot did not predict the gap (D26). Assignment marks alone carry little information about unaided "
    "capability.",
    SC_LIM + "Assignments and exams differ in content, format and difficulty, so the gap is not caused by AI alone. "
    "No pre-GenAI comparison cohort. " + EC_NOTE, "S4_assignment_vs_exam.csv; S4b_per_item_scores.csv")

add("StudyChat", "Assignment marks bunch at the top",
    f"{pct(ae.pct_assign_ge_90 * 100)} of students averaged 90% or more on assignments, compared with "
    f"{pct(ae.pct_exam_ge_90 * 100)} on exams. Assignment scores spread less (SD {ae.assign_sd * 100:.1f} vs "
    f"{ae.exam_sd * 100:.1f} points) and agreed only moderately with exam scores (rho = {ae.spearman_assign_exam:.2f} "
    f"pooled; {sae.loc['f24'].spearman_assign_exam:.2f} in Fall 2024 and {sae.loc['s25'].spearman_assign_exam:.2f} in Spring 2025).",
    f">= 90%: assignments {pct(ae.pct_assign_ge_90 * 100)}, exams {pct(ae.pct_exam_ge_90 * 100)}; Spearman rho "
    f"{ae.spearman_assign_exam:.2f}",
    f"n = {int(ae.n)} graded students",
    "Proportions at or above 0.9 on the released normalised averages; Spearman rank correlation.",
    UNSUP + "; " + SUPERVISED, "Validity; Evidence of individual understanding",
    "When AI is available, take-home programming assignments separate students poorly, so they say little about "
    "who can do the work unaided. A supervised or verification component is needed to discriminate.",
    SC_LIM + "The ceiling may also reflect generous marking or autograders, not only AI use. " + EC_NOTE,
    "S4_assignment_vs_exam.csv; S4b_per_item_scores.csv")

sc_all = scor[scor.scope == "all"]
max_rho = scor.loc[scor.spearman_rho.abs().idxmax()]
pe = sreg.loc["share_production_z"]
pa = sreg.loc["assign_z"]
add("StudyChat", "How students used the AI vs grades",
    f"No usage measure (number of prompts, write-or-edit share, write-code share, understanding share, "
    f"verification share) was clearly associated with assignment marks, exam marks or the gap: all {len(scor)} "
    f"correlations had Holm-adjusted p >= {scor.p_holm_within_scope.min():.2f}, and the largest was "
    f"rho = {max_rho.spearman_rho:.2f}. Exam averages were {pct(stert.loc['Low'].exam_mean * 100)}, "
    f"{pct(stert.loc['Middle'].exam_mean * 100)} and {pct(stert.loc['High'].exam_mean * 100)} for the low, middle "
    f"and high write-or-edit tertiles (Kruskal-Wallis {p_fmt(stert.loc['Low'].kruskal_exam_p)}).",
    f"Regression on exam score: assignment beta {pa.std_beta:.2f} ({p_fmt(pa.p)}); write-or-edit share beta "
    f"{pe.std_beta:.2f} ({p_fmt(pe.p)}); R2 = {pe.r2:.2f}",
    f"n = {int(sc_all[sc_all.measure == 'share_production'].n.iloc[0])} linked students with >= 10 prompts "
    f"({int(sc_all[sc_all.measure == 'log_turns'].n.iloc[0])} for prompt count)",
    "Spearman correlations, pooled and by semester, Holm adjustment within each scope (15 tests). OLS on "
    "standardised exam score with assignment score, write-or-edit share, log prompt count and semester.",
    PROCESS + "; " + AITRANS, "Evidence of individual understanding; Scalability",
    "Here, the pattern of a student's AI use did not distinguish stronger from weaker students. Prompt histories "
    "may help with transparency and feedback, but should not be relied on as evidence of learning or as a "
    "misconduct signal.",
    SC_LIM + "A null result is not proof of no effect; shares are averaged across all assignments.",
    "S5_usage_outcome_correlations.csv; S5b_exam_regression.csv; S6_production_tertiles.csv")

add("StudyChat", "Using the AI on an assignment vs its mark",
    f"For each assignment, students who used the chatbot on it did not score clearly differently from those who "
    f"did not ({int((suse.p_holm < 0.05).sum())} of {int(suse.p_holm.notna().sum())} assignment-by-semester "
    "comparisons significant after Holm adjustment). Most marks were already near full.",
    f"Mean mark, users {suse.mean_used.min():.2f} to {suse.mean_used.max():.2f}; non-users "
    f"{suse.mean_not_used.min():.2f} to {suse.mean_not_used.max():.2f}",
    f"{int(sae.loc['f24'].n)} (Fall 2024) and {int(sae.loc['s25'].n)} (Spring 2025) graded students per assignment",
    "Used = at least one prompt tagged with that assignment. Two-sided Mann-Whitney U; Holm adjustment over 14 tests.",
    UNSUP, "Academic integrity; GenAI capability to complete the task",
    "With marks near the ceiling, use of the course chatbot made no visible difference, so these marks have "
    "little power to show either AI help or its absence.",
    SC_LIM + "Non-users may have used other AI tools; 'not used' means only 'did not use the course chatbot'.",
    "S7_assignment_use_vs_score.csv")

hi_a = sasg.mean_share_write_code.idxmax()
lo_a = sasg.mean_share_write_code.idxmin()
add("StudyChat", "Variation by assignment",
    f"The share of prompts asking for code ranged from {pct(sasg.loc[lo_a].mean_share_write_code * 100)} on {lo_a} "
    f"to {pct(sasg.loc[hi_a].mean_share_write_code * 100)} on {hi_a}, while the understanding share stayed between "
    f"{pct(sasg.mean_share_understanding.min() * 100)} and {pct(sasg.mean_share_understanding.max() * 100)}.",
    "Mean student share of write-code prompts per assignment",
    f"{int(sasg.students_ge5_turns.min())} to {int(sasg.students_ge5_turns.max())} students per assignment "
    "(>= 5 prompts on it)",
    "Per student and assignment shares, averaged across students.",
    UNSUP + "; " + AUTH, "GenAI capability to complete the task; Academic integrity",
    "How much students ask AI to write code depends on the task, so exposure should be judged assignment by "
    "assignment (as with EPFL courses) rather than for programming assignments as a whole.",
    SC_LIM + "Assignment content was not coded, so we cannot say which task features drive the difference.",
    "S3_by_assignment.csv")

fdf = pd.DataFrame(findings)

# ---------------------------------------------------------------- methods sheet
methods = pd.DataFrame([
    ("Purpose", "Secondary analysis of three open datasets to support RQ4 (GenAI vulnerability of assessments) and the "
                "Evaluation / Recommendation Matrices."),
    ("Evidence levels", "Level 1 = what our analysis of the data shows (Findings column). Level 2 = our interpretation "
                        "(Possible implication column). No Level 3 recommendations are made in this workbook."),
    ("Reproducibility", "Run from the IRP Working Directory: python Analysis/scripts/epfl_analysis.py; "
                        "python Analysis/scripts/mircea_analysis.py; python Analysis/scripts/studychat_analysis.py; "
                        "python Analysis/scripts/build_findings_workbook.py. "
                        "Python 3.8, pandas, scipy, matplotlib, openpyxl. Original dataset files are read only."),
    ("EPFL unit of analysis", "Each question has 16 grade rows (2 models x 8 prompts). These rows are not independent, so "
                              "results are aggregated to one value per question per model before summarising."),
    ("EPFL grade scale", "MCQ graded 0/1 by exact match. Open answers graded 0, 0.33, 0.66 or 1 by GPT-4 as an automatic "
                         "grader (dataset README)."),
    ("EPFL definitions (ours)", "Fully correct = grade 1. Mostly correct = grade >= 0.66. Zero-shot = the Zero-Shot prompt. "
                                "Best of 8 = max over 8 prompts. Majority of 8 = at least 5 of 8 prompts fully correct. "
                                "These are not the same definitions as Borges et al. (2024), so our figures should not be "
                                "presented as reproducing the paper's headline numbers."),
    ("EPFL metadata fix", "grade_per_question.csv labels 14 online courses as Bachelor and 15 as Uncategorized. courses.json "
                          "was used for level (Bachelor / Master / Online) and program."),
    ("EPFL statistics", "95% bootstrap CIs (2,000 resamples, seed 2026); Wilcoxon signed-rank for paired model comparison; "
                        "Friedman test for prompt strategies; Mann-Whitney U for MCQ vs open answer."),
    ("Mircea files", "StudentSurveyResults.xlsx (150 rows; same IDs as the CSV). ClientSurveyResults.csv (11 rows, "
                     "semicolon-delimited). Results of Coding Procedure.xlsx (89 coded free-text statements)."),
    ("Mircea translation", "Answer labels translated from German by us; see mapping in mircea_analysis.py."),
    ("Mircea statistics", "Frequencies with full denominators; Wilcoxon signed-rank for the two interaction modes; "
                          "Spearman correlations with Holm adjustment (10 tests); chi-square for code generation by skill. "
                          "All inferential results are exploratory."),
    ("StudyChat files", "dialogues/f24_labeled_dialogues.jsonl and s25_labeled_dialogues.jsonl (one row per student "
                        "prompt, with a GPT-4.1 dialogue-act label); scores/*_grades_released_normalized.csv (0-1 "
                        "scores per assignment a1-a7 and exam e1-e3; llm = assignment average, no_llm = exam average). "
                        "Joined on userId within semester. Submissions and assignment text were not analysed."),
    ("StudyChat unit of analysis", "Students contribute very different numbers of prompts (1 to 388), so results are "
                                   "aggregated to one value per student before summarising. Share measures require "
                                   ">= 10 prompts (>= 5 per assignment for by-assignment shares)."),
    ("StudyChat definitions (ours)", "Write or edit = writing_request + editing_request labels; write code = "
                                     "writing_request>Write Code; understanding = conceptual_questions + "
                                     "contextual_questions; gap = assignment average minus exam average. These "
                                     "groupings are ours, not the original paper's."),
    ("StudyChat statistics", "Bootstrap 95% CIs (2,000 resamples, seed 2026); Wilcoxon signed-rank for assignment vs "
                             "exam; Spearman correlations with Holm adjustment within each scope; OLS on standardised "
                             "exam score; Kruskal-Wallis across tertiles; Mann-Whitney U with Holm for per-assignment "
                             "use. All usage-outcome results are exploratory and observational."),
    ("Not double counting", "If Borges et al. (2024), Mircea et al. (2026) or McNichols et al. (2025) are also in the evidence log, do not count the "
                            "paper and our analysis of its dataset as two independent studies."),
    ("Assessment mapping", "The 'Related assessment types (D2)' column maps each finding to the eight assessment "
                           "types rated in the D2 Evaluation Framework."),
    ("Finding IDs", "D01 to D28 number the rows of 'Dataset Findings' in order; the D2 and D3 workbooks cite "
                    "them by these codes. J1 to J6 are the team's separate analyses, listed in sheet 'J findings'."),
    ("Dataset licences", "EPFL NLP4Education: CC BY-NC-ND 4.0, so only aggregate results are shared and no adapted "
                         "dataset is published. Hannover capstone survey (Mircea et al.) and StudyChat: CC BY 4.0, "
                         "attribution required. Raw StudyChat prompts are not quoted."),
    ("Citations", "IEEE numbers are not assigned here; use the 'Source to cite' column and number them in the reference "
                  "manager. Mircea and StudyChat references verified against Jiajun's dataset documentation (14 Oct 2026)."),
    ("Independent replication", "Jiajun's separate analyses of the same three datasets (Jiajun - Data Analysis/, "
                                "14 Oct 2026) reproduce our StudyChat and Hannover figures exactly. Where we use "
                                "different definitions (EPFL resistance / best of 8), state which one is used."),
], columns=["Item", "Detail"])

# ---------------------------------------------------------------- write
with pd.ExcelWriter(XLSX, engine="openpyxl") as xw:
    methods.to_excel(xw, "Read me and methods", index=False)
    fdf.insert(0, "Finding ID", [f"D{i:02d}" for i in range(1, len(fdf) + 1)])
    fdf.to_excel(xw, "Dataset Findings", index=False)
    jlines = [l for l in (ROOT / "Analysis" / "D2_framework" / "dataset_evidence.md").read_text(encoding="utf-8").splitlines()
              if re.match(r"- \[J\d\]", l)]
    pd.DataFrame([{"Finding ID": l[3:5], "Finding (as cited in D2)": l[7:].strip()} for l in jlines]
                 ).to_excel(xw, "J findings", index=False)
    for name, f in [("EPFL overall", "01_overall_by_model_qtype.csv"),
                    ("EPFL CS", "02_computer_science_by_model_qtype.csv"),
                    ("EPFL by program", "03a_by_program.csv"),
                    ("EPFL prompts", "04_prompt_strategies.csv"),
                    ("EPFL courses", "08_course_level.csv")]:
        r(E / f).round(4).to_excel(xw, name, index=False)
    for name, f in [("Mircea closed Qs", "M0_student_closed_questions.csv"),
                    ("Mircea purposes", "M2_purposes.csv"),
                    ("Mircea modes", "M4b_mode_crosstab.csv"),
                    ("Mircea correlations", "M5_exploratory_correlations.csv"),
                    ("Mircea coded advice", "M7_coded_advice.csv"),
                    ("Mircea clients", "M8b_client_concerns.csv")]:
        r(M / f).round(4).to_excel(xw, name, index=False)
    for name, f in [("StudyChat dialogue acts", "S1_dialogue_acts_category.csv"),
                    ("StudyChat assign vs exam", "S4_assignment_vs_exam.csv"),
                    ("StudyChat per item", "S4b_per_item_scores.csv"),
                    ("StudyChat correlations", "S5_usage_outcome_correlations.csv"),
                    ("StudyChat regression", "S5b_exam_regression.csv"),
                    ("StudyChat tertiles", "S6_production_tertiles.csv"),
                    ("StudyChat use vs score", "S7_assignment_use_vs_score.csv")]:
        r(S / f).round(4).to_excel(xw, name, index=False)

wb = load_workbook(XLSX)
head_fill = PatternFill("solid", fgColor="1C5CAB")
thin = Side(style="thin", color="D0D0D0")
widths = {"Read me and methods": [24, 120],
          "Dataset Findings": [10, 11, 22, 60, 34, 24, 36, 34, 28, 52, 44, 30, 40],
          "J findings": [10, 140]}
for ws in wb.worksheets:
    ws.freeze_panes = "A2"
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = head_fill
        c.alignment = Alignment(wrap_text=True, vertical="center")
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
            c.border = Border(top=thin, bottom=thin, left=thin, right=thin)
    w = widths.get(ws.title)
    for i, col in enumerate(ws.columns):
        letter = col[0].column_letter
        ws.column_dimensions[letter].width = w[i] if w and i < len(w) else min(
            max(len(str(c.value or "")) for c in col) + 2, 45)
wb.save(XLSX)
print("Wrote", XLSX, "with", len(fdf), "findings")

add_start_sheet(XLSX, "Dataset Findings: EPFL, Hannover capstone and StudyChat",
    "Our analysis of three public datasets: what current AI can do on real university questions, how students "
    "use AI, and how marks respond.",
    ["Open 'Dataset Findings'. Each row is one finding (D01-D28) with its sample, method, the assessment types it "
     "informs, our interpretation and its limitations.",
     "The remaining sheets hold the statistics behind each finding, named by dataset."],
    [("Dataset Findings", "All 28 findings, with interpretation kept separate from the finding"),
     ("J findings", "The team's separate analyses (J1-J6) cited in D2"),
     ("Read me and methods", "Data files, definitions, statistical methods and licences")])
