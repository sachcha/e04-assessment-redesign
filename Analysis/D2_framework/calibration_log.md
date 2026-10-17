# D2 calibration log (17 Oct 2026)

Calibration makes sure the same rating means the same thing across all eight assessment types. Every change below has a rule and a reason.

## Automatic checks (all passed)
- Every cited Record ID is an included study, and every D/J code exists in dataset_evidence.md.
- There are no em dashes in the cell text.
- All 15 High-confidence cells meet the High rule: at least 3 supporting studies, including at least one Core or computing study with quality of 4 or more.
- Counts are standardised. n_supporting = key studies; computing_studies = computing "Y" only (Partial not counted); core_studies = team-log Core. low_conf_venue_studies has been added.

## Calibration rules
- **C1. Exposure under defining conditions.** GenAI exposure is rated for the assessment type under its defining conditions. For supervised assessment that means in-person invigilation. For oral assessment it means live, unscripted questioning. Weaker variants (online proctoring, lockdown browsers, scripted or remote orals) are named in the cell as exceptions.
- **C2. Mixed types are rated by their typical form.** When a type includes forms that differ a lot (for example projects versus online quizzes), rate the typical form as Moderate and name the variation.
- **C3. Feasibility includes cost.** Dimension 10, "Feasibility and cost", must also address implementation cost (staff time, invigilation, venues, platforms, licences). If staff burden is rated Weak under workload, feasibility cannot be Strong unless cheap infrastructure clearly outweighs it.

## Rating changes
| Type | Dimension | From | To | Rule | Reason |
|---|---|---|---|---|---|
| Supervised assessment | genai_exposure | Moderate / High | Strong / Medium | C1 | In-person invigilation blocks AI use, even though the questions themselves are highly AI-solvable (S009, S008, D03). Lockdown and online proctoring are bypassed (R25, R77), so they are named as exceptions. Confidence drops to Medium because no study directly tested covert AI use under in-person invigilation. This now matches the oral and practical-demonstration rows. |
| Unsupervised formats | authenticity | Strong / Medium | Moderate / Medium | C2 | The type covers online quizzes and structured homework as well as projects. Authenticity is high for projects and low for quizzes, and it rests on how authors frame their tasks, not on any test. |
| Staged submissions | feasibility | Strong / Medium | Moderate / Medium | C3 | Workload is rated Weak (multiple marking points), so feasibility including cost cannot be Strong. |

## Text edits requested in every row
1. Make the feasibility cell address cost explicitly, with citations, or state that cost evidence is limited.
2. Check any sample size quoted in a cell against the corrected packs (the sample field was missing in the first packs).
3. Keep [L], [D] and [I] separate. No em dashes. Plain, professional English.

## Editor notes
- Supervised assessment, genai_exposure: rating changed Moderate/High to Strong/Medium under C1; literature, dataset, interpretation and conflicts rewritten around in-person invigilation [S097], [R03], [R54], with item solvability [S009], [S008], [S030], [D03], [J3] and lockdown or online exceptions [R25], [R77], [S001]; conflicts now state that no study tested covert AI use under in-person invigilation; key studies now S097, R03, R54, S009, S008, S030, R25, R77, S001 (R08 removed); counts 9/4/1.
- Supervised assessment, capability_verification: added pack sample sizes (R81 60 students, S101 eight students) and the role of the S009 random vivas, which was a key study with no text.
- Supervised assessment, scalability: corrected R25, which the cell called "in-person" exams; the pack gives automated MC grading for 120-150 students mostly in online semesters. R77's 200 concurrent users now described as a load test.
- Supervised assessment, scalability cohort note: removed the claim that R82 and R72 show live checkoffs at small scale (neither reports checkoffs); now cites R82 paper exams for smaller schools and R72 lockdown exams in a 25-35 student course.
- Supervised assessment, feasibility: rewritten to cover invigilation, facilities, timetabling and staff time [R84], [R95], [R25], custom platforms [R77], [R89] and resource trade-offs [R68]; states that no study gave venue or licence costs in money terms; R84 and R95 added to key studies; counts 9/6/6.
- Supervised assessment, top fields: evaluation_finding, strengths, limitations and practical_considerations updated for the Strong exposure rating (in-person only) and for cost; evidence gaps add covert-use testing and monetary costs.
- Unsupervised formats, authenticity: rating changed Strong/Medium to Moderate/Medium under C2; literature now covers projects [R72], [R08], [R82], [R91], [R80], [R09] and quizzes or structured homework [R72], [R25], [R12]; interpretation names the variation; conflicts state the rating rests on author framing; R25 added to key studies; counts 7/6/5.
- Unsupervised formats, authenticity: R80 partner-school app corrected to "to be trialled"; added the R09 finding that only 2 of 13 industry respondents used GenAI at work.
- Unsupervised formats, genai_exposure conflicts: corrected R90; the 35% accuracy after 10 prompts was the hardest original CS1 lab, not a flowchart-based lab.
- Unsupervised formats, capability_verification: added R81 cohort size (60).
- Unsupervised formats, scalability: R91 corrected to "typical enrolment of 150-250" (exact n not reported); R25 described as a statistics lecture; R72 "typically 25-35".
- Unsupervised formats, feasibility: rating kept Strong/Medium; added cost content (no invigilation or venues; staff time for question writing [R25], marking AI conversations [S123] and interview add-ons [R84]; purpose-built platforms [R71]; tool access [R20], [R15]; [D14]); states that no study reported licence or platform costs in money; R25 and S123 added to key studies; counts 7/5/4.
- Unsupervised formats, top fields: evaluation_finding no longer calls the type authentic without qualification; strengths, limitations and practical_considerations updated for the Moderate authenticity rating and staff-time costs; workload evidence gap now includes monetary costs.
- Staged submissions, feasibility: rating changed Strong/Medium to Moderate/Medium under C3; literature and interpretation rewritten to cover staff marking time [R82], [R24], [R04], low infrastructure [R47], [R23] and low-cost hardware [R79]; states that cost evidence is limited; R04 added to key studies; counts 6/2/2; conflicts filled.
- Staged submissions, scalability cohort note: corrected R82, which was placed under Medium (50-200) but reports about 30 students; Medium now says no staged computing deployment of that size was reported.
- Staged submissions, scalability and capability_verification: added pack sample sizes (R82 about 30; R79 cohorts of 14 and 15; R47 identified as a psychology course).
- Staged submissions, workload: S192 no longer cited as showing "substantial teacher time"; it only flags workload sustainability; S105 kept for that claim.
- Staged submissions, top fields: evaluation_finding, strengths, limitations and practical_considerations updated to reflect Moderate feasibility and marking cost.
- Oral assessments, feasibility: added implementation cost (about 1,000 staff minutes per 100 students [R84], 80% of TA office-hour time and Docker environments [R95], two evaluators per session and an automated viva platform [S156]); states cost evidence is limited to staff-time estimates; R84 and S156 added to key studies; counts 9/6/4; conflicts filled.
- Oral assessments, scalability cohort note: removed R93 from Small (<50), because the pack reports more than 50 students; R93 now under Medium.
- Oral assessments, authenticity: R80 partner-school app corrected to "selected apps to be trialled".
- Oral assessments, practical_considerations: second item now gives the staff-time budget from R84.
- Practical demonstrations, feasibility: added implementation cost (TA time and Docker environments [R95], low-cost hardware [R79], screencast rubric marking [R82]); states cost evidence is limited; R82 added to key studies; counts 8/7/5; conflicts filled.
- Practical demonstrations, scalability: corrected "about 25-60 students" (R79 cohorts are 14 and 15); cohort note no longer places R93 (more than 50 students) under Small; R93 moved to Medium.
- Practical demonstrations, authenticity: R80 partner-school app corrected to "to be trialled".
- Practical demonstrations, practical_considerations: third item now budgets TA time.
- Personalised tasks, feasibility: added platform and licence cost content (custom platforms [R71], [R89], [S156]; free tools versus premium access [R15], [R20]); states cost evidence is limited; S156 added to key studies; counts 6/3/3; conflicts filled.
- Personalised tasks, scalability: corrected "30-44 students" for R94; the pack reports a maximum class size of 30 across 194 students over four semesters.
- Personalised tasks, practical_considerations: platform and institutional access items updated for cost.
- Process evidence, feasibility: added staff-time, platform, licence and privacy costs [S123], [R77], [R17], [R28], [R16], [R15]; states cost evidence is limited; R16 and S123 added to key studies; counts 9/6/5; conflicts note that Weak workload rules out Strong.
- Process evidence, scalability: R91 corrected to typical enrolment of 150-250; R77 described as a load test; S123 cohort (119) added.
- Process evidence, scalability cohort note: corrected R81 (60 students), which was placed under Small (<50); Small now cites R72 and R79, and Medium cites R81, R15 and S123.
- Process evidence, practical_considerations: platform and institutional tool access added.
- AI-use declarations, feasibility: rating kept Strong/Medium; added cost content (no invigilation, venues or platforms; staff time for policy rollout [S069] and training [S331], [R27]; workload rarely reported [S423]; tool access [R20], [R15]; [D14]); states cost evidence is limited; S423 added to key studies; counts 6/2/1.
- AI-use declarations, scalability: R91 corrected to typical enrolment of 150-250; R80 to "over 750"; cohort note adds pack sample sizes (R72 25-35, R15 88).
- AI-use declarations, top fields: evaluation_finding now says "low-infrastructure" with limited cost evidence instead of "low-cost"; last practical consideration now covers budget for tool access and training.
- All files: Every Record ID re-checked against the type's pack and every D/J code against dataset_evidence.md; no em or en dashes; key-study counts recomputed; the High-confidence rule re-checked; json.load passes.
- Not changed, for the team to consider: personalised_tasks authenticity (Strong/Medium) and process_evidence authenticity (Strong/Medium) rest on author framing, the same reason given for the C2 change to unsupervised formats; unsupervised_formats and ai_use_declarations keep feasibility Strong although their cost evidence is limited.

## Coordinator follow-up (17 Oct 2026)
- Rule C4: where a rating rests only on how authors frame their designs (untested), confidence is capped at Low. Applied to Personalised tasks / authenticity (Strong/Medium to Strong/Low) and Process evidence / authenticity (Strong/Medium to Strong/Low). Unsupervised formats and AI-use declarations keep feasibility Strong/Medium: workload is Moderate, so C3 does not apply, and infrastructure needs are low; their cost evidence is thin and the cells say so.

## Revision after team review (17 Oct 2026)
- Process evidence / capability verification split by form: Weak (Medium) for unassessed or student-kept records; Moderate (Low) for system-captured interaction records assessed by staff. Reason: the StudyChat evidence [D26], [J6] comes from an optional, ungraded course chatbot analysed as automated prompt counts, so it cannot speak to assessed interaction records; R17 (graded logs, r = 0.54, non-computing) supports the assessed form. Interpretation, evaluation finding, strengths and limitations updated; D26 annotated in dataset_evidence.md.

## Full-text citation check (17 Oct 2026)
Scope: Every statement citing S040, S113, S199, S423, S006 or S119 in the eight D2 cell files and in D3 partA, partB and partC, checked against the full-text re-extractions (screening/search/ft_reextract_requested.json) and full texts. 37 statements checked, 15 changed, 2 key-study removals. No rating or confidence changed.

Changes:
- ai_use_declarations, capability_verification literature: "staff could not reliably tell whether work was independently produced [S006]" -> one fully AI-generated essay judged by 28 staff in a computer science faculty with no human-written control; 53.57% judged it AI-written at once, 35.72% suspicious only later, 10.72% little or no suspicion; marker suspicion is a weak check.
- ai_use_declarations, authorship_assurance literature: "A scoping review found..." -> "A multidisciplinary scoping review of 11 studies (only one from computing) found..." [S423]. Percentages (27.3%, 18.2%) confirmed as 3/11 and 2/11.
- ai_use_declarations, workload literature: "Workload evidence ... rarely reported (63.6% of studies)" -> workload or acceptability evidence not reported in 7 of 11 studies (63.6%) in a multidisciplinary scoping review [S423] (the old wording could be read as 63.6% reporting it).
- ai_use_declarations, feasibility literature: same 63.6% rewording as above [S423].
- staged_submissions, capability_verification literature: "triangulation of staged work with oral explanation and live demonstration [S113]" -> a narrative review's proposed, untested triangulation (S113 proposes this; it does not test it).
- staged_submissions, authorship_assurance key_studies: S199 removed (it reports no cohort, data or evaluation, so it cannot support the Moderate rating); n_supporting 5 -> 4, computing_studies 1 -> 0. Rating Moderate/Medium kept; it rests on R01, R79, R24 and R68.
- staged_submissions, authenticity literature: "a group project portfolio treats GenAI as a professional, collaborative tool [S199]" -> one computing group-project module design, described without any evaluation, frames GenAI that way.
- staged_submissions, authenticity key_studies: S199 removed (design description only); n_supporting 5 -> 4, computing_studies 2 -> 1. Rating Moderate/Medium kept; it rests on R82, R79 and R47.
- supervised_assessment, capability_verification literature: "sharply higher failure rates after a move to a supervised in-person exam [S119]" -> in a non-computing business course, failures rose from 2.1-5.7% to 18.4% after a take-home to supervised closed-book switch, which also removed all resources and added time pressure.
- supervised_assessment, authenticity literature: "one natural experiment notes a tension..." -> "a natural experiment in a business course notes a tension..." [S119].
- supervised_assessment, evaluation_finding: S119 moved out of the list showing supervised results "repeatedly revealed gaps" -> cited as confounded non-computing support.
- supervised_assessment, strengths[0]: same change; S119 now cited as confounded grade data from a non-computing course.
- unsupervised_formats, capability_verification literature: S119 removed from the list on submitted code and take-home grades -> separate clause giving the business-course failure rise (2.1-5.7% to 18.4%) and its confounds.
- unsupervised_formats, integrity_security literature: S006 removed from "markers could not reliably tell AI from student work" -> separate clause: with one fully AI-generated essay and no human control, only 53.57% judged it AI-written at once.
- unsupervised_formats, authenticity conflicts: S113 removed from "authentic tasks were still easily reproduced with GenAI" -> a narrative review argues realistic take-home tasks stay open to undisclosed AI help (S113 argues this; it does not test reproduction).
- unsupervised_formats, limitations[1]: S119 moved out of the main list -> confounded non-computing grade data point the same way.
- D3 partA_ai_use_declarations, implementation_considerations[1]: "marking time that has not been measured [S423], [S108]" -> "has rarely been measured" (S423 found workload reported or inferable in 4 of 11 studies).

Checked and correct (no change):
- ai_use_declarations: genai_exposure literature (logs can be fabricated or mimicked [S006]: GPT-4o produced a plausible fake log; staff distrusted disclosed links); process_visibility literature (logs mimicked or curated [S006]); authorship_assurance remainder; feasibility conflicts (inconsistent policies [S006]); evaluation_finding (both S423 sentences); limitations[0] and [2].
- staged_submissions: genai_exposure literature and conflicts (S113 argues take-home tasks stay open to AI help; already flagged as low-confidence venue); authenticity last sentence [S113]; evaluation_finding; limitations[0]; practical_considerations[0] (S113 recommends an oral or explanation checkpoint).
- unsupervised_formats: process_visibility literature (records open to fabrication [S006]).
- D3 partA_ai_use_declarations identified_problem and risks_and_limits [S423]; partA_staged_submissions identified_problem, recommended_redesign[1] and justification [S113]; partB cells[10] trade_offs and cross_cutting_principles[2] [S423]; partC privacy_ethics_legal_requirements[4] (matches the S423 abstract and discussion wording).
- S040 is not cited in any of the 12 files, so nothing to check. S119 was already counted as non-computing (Partial) in computing_studies, so no count changed for it.
- All edited files parse with json.load; no em or en dashes added.
