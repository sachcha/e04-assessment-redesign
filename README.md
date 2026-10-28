# E04: Authentic and Secure Assessment in AI-Rich Computing Education

Code, protocols and outputs for Project C262W-5102, delivered for Adelaide University (client: David Menzies; supervisor: Wenhao Liang).

The project evaluates eight assessment types for computing higher education in the generative AI era and recommends redesigns by learning outcome and class size. It combines a structured systematic review (143 included studies) with secondary analysis of three public datasets. The final report and the full workbooks are provided separately to the client and assessors.

## Repository contents

| Folder | Contents |
|---|---|
| `Analysis/scripts/` | Dataset analyses (EPFL, Hannover capstone survey, StudyChat) and the dataset findings workbook builder |
| `Analysis/outputs/` | Aggregate result tables from the dataset analyses |
| `Analysis/figures/` | Figures from the dataset analyses |
| `Analysis/screening/` | Review protocol, screening decisions (both screeners and adjudication), agreement statistics, update search log, extraction records, PRISMA counts |
| `Analysis/D2_framework/` | Evaluation Framework: synthesis protocol, evidence packs, rated cells, calibration log, workbook builder |
| `Analysis/D3_recommendations/` | Recommendation Matrix: protocol, redesign index, outputs, calibration log, workbook builder |
| `Analysis/quality/` | Quality metrics and PRISMA 2020 checklist |
| `Analysis/methodology/` | Comparison of method choices and verified methods references |
| `Analysis/ethics/` | Verified ethical, legal and cultural frameworks and the considerations matrix |
| `Analysis/pm/` | Project management reflection and planned hours by member |

## Reproducing the results

Requirements: Python 3.8 or later with pandas, scipy, matplotlib and openpyxl (developed with Python 3.8.10, pandas 2.0.3, scipy 1.10.1, matplotlib 3.7.5, openpyxl 3.1.5).

1. Download the datasets into `Datasets/` (see below).
2. From the repository root, run the dataset analyses:
   ```
   python Analysis/scripts/epfl_analysis.py
   python Analysis/scripts/mircea_analysis.py
   python Analysis/scripts/studychat_analysis.py
   python Analysis/scripts/build_findings_workbook.py
   ```
3. Rebuild the review outputs:
   ```
   python Analysis/screening/compute_agreement.py
   python Analysis/screening/finalise_ta.py
   python Analysis/screening/merge_extraction.py
   python Analysis/screening/merge_update_search.py
   python Analysis/screening/build_review_workbook.py
   ```
4. Rebuild the deliverable workbooks and quality metrics:
   ```
   python Analysis/D2_framework/build_d2_workbook.py
   python Analysis/D3_recommendations/build_d3_workbook.py
   python Analysis/quality/quality_metrics.py
   ```

`Analysis/screening/openalex_search.py` and the venue check in `merge_update_search.py` query live web services, so their saved outputs (dated 17 October 2026) are the record used in the report. Re-running them today may return slightly different results.

## Datasets (not included; download from the original sources)

| Folder under `Datasets/` | Source | Licence |
|---|---|---|
| `EPFL Dataset/` (`courses.json`, `questions.json`, `grade_per_question.csv`) | github.com/epfl-nlp/NLP4Education; Borges et al., PNAS 121(49), 2024 | CC BY-NC-ND 4.0 |
| `Mircea et al. (2026) Capstone GenAI/` (`StudentSurveyResults.xlsx`, `ClientSurveyResults.csv`, `Results of Coding Procedure.xlsx`) | doi.org/10.5281/zenodo.18846544; Mircea, Schmid, Droste and Schneider, EASE 2026 | CC BY 4.0 |
| `StudyChat/` (`dialogues/`, `scores/`) | huggingface.co/datasets/wmcnicho/StudyChat; McNichols, Ikram and Lan, LAK '26 | CC BY 4.0 |

The EPFL data are licensed CC BY-NC-ND 4.0, which does not permit sharing adapted versions, so only aggregate results are included here. Full texts of the reviewed papers are not included for copyright reasons; each study is identified by its DOI in the screening and extraction files.

## Use of AI in this project

AI tools assisted screening, extraction, a replication of the dataset analyses and drafting. Screening used two independent, blinded runs of Anthropic Claude (Opus 5.5) with identical instructions, and a team member reviewed every disagreement and made the final decision. All protocols, decisions and changes are recorded in the folders above.

## Licence

The code in this repository is released under the MIT Licence (see `LICENSE`). Datasets and reviewed papers remain under their original licences and are not redistributed here.
