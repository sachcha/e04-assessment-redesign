# D2 Assessment Strategy Evaluation Framework: synthesis protocol (approved 17 Oct 2026)

Purpose: rate one assessment type on 11 dimensions for computing higher education in the GenAI era (2026). Every judgement must be traceable to evidence.

## Inputs
- `packs/<type>.md`: Every included study tagged with this assessment type. It lists Core studies first, then computing studies, then the rest by quality.
- `dataset_evidence.md`: our own dataset findings [D01], [D28] and Jiajun's team analysis [J1], [J6].
- Use only these sources. Never cite anything else. Never invent a figure, study or citation.

## Citation format inside cell text
- Cite studies by Record ID in square brackets: [R81], [S119]. Cite dataset findings as [D24] or [J1]. Several citations look like [R81], [R80], [D24]. (IEEE numbers are assigned later.)
- Every factual sentence needs at least one citation.

## Evidence labels (keep them separate)
- **[L]** = what the literature shows, as findings of the cited studies.
- **[D]** = what our dataset analysis shows.
- **[I]** = our interpretation or judgement. It must not introduce new facts.

## The 11 dimensions and what "Strong" means (Strong is always the favourable end)
| # | Key | Dimension | Strong = | Weak = |
|---|---|---|---|---|
| 1 | capability_verification | Capability verification | gives credible evidence of the individual's own understanding (they can explain, justify or extend their work) | a correct artefact says little about individual understanding |
| 2 | genai_exposure | GenAI exposure | GenAI cannot complete the task, even with repeated attempts by a capable student | GenAI can complete most of the task |
| 3 | authorship_assurance | Authorship assurance | staff can be confident who produced the work and how AI was used | authorship and AI use cannot be established |
| 4 | lo_alignment | Learning-outcome alignment | measures the intended computing outcome, including process and reasoning | measures only a final product or a narrow skill |
| 5 | authenticity | Authenticity | resembles professional computing practice with AI available | artificial conditions unlike practice |
| 6 | appropriate_ai_use | Appropriate AI use | permits and develops responsible, critical GenAI use | excludes AI, or allows unexamined use |
| 7 | process_visibility | Process visibility | makes the working process, including AI interactions, visible and assessable | only the product is seen |
| 8 | scalability | Scalability | workable for large cohorts (>200) | only feasible for small cohorts (<50) |
| 9 | workload | Staff workload | low marking, supervision and preparation burden | high burden |
| 10 | feasibility | Feasibility | little infrastructure, skill or policy change needed | major resources or policy change needed |
| 11 | accessibility_equity | Accessibility and equity | fair for students with disabilities, anxiety, English as an additional language or unequal AI access | systematic disadvantage for some groups |

Use **Moderate** when performance is mixed or depends on how the type is designed. Say what it depends on.

## Confidence (simplified GRADE-CERQual)
Base confidence on how many studies, how good, how relevant, and how consistent.
- **High:** at least 3 studies directly support the rating, including at least one Core or computing study with quality of 4 or more. The findings are broadly consistent. Agreement with our dataset evidence ([D]/[J]) can lift Medium to High.
- **Medium:** 2 or more supporting studies with some inconsistency, or mostly conceptual or lower-quality evidence, or only one strong computing study.
- **Low:** 0-1 studies, or only conceptual papers, author recommendations that weren't tested, or low-confidence venues, or conflicting evidence.

Rules:
- Studies marked LOW-CONFIDENCE VENUE can corroborate but never raise confidence on their own.
- Abstract-only records count as weaker evidence.
- Author recommendations marked "(not tested)" are proposals, not evidence of effectiveness.
- If no study speaks to a dimension, give the rating "Insufficient evidence" with Low confidence, and say that plainly. Don't guess.

## Computing calibration
Ratings are for computing and IT higher education. Evidence from other disciplines counts as transferable support. Note it when a rating rests mainly on non-computing evidence.

## Scalability
In the scalability cell, also give a cohort note covering small (<50), medium (50-200) and large (>200) cohorts.

## Output
Write one JSON file: `cells/<type_file_name>.json`. It is an object with these keys:
```
{
 "assessment_type": "...",
 "n_studies_in_pack": int,
 "cells": [  // exactly 11, in the dimension order above
   {"dimension": "<key>", "rating": "Strong|Moderate|Weak|Insufficient evidence",
    "confidence": "High|Medium|Low",
    "literature": "[L] 1-3 sentences with citations",
    "dataset": "[D] 0-2 sentences with [Dxx]/[Jx] citations, or \"\"",
    "interpretation": "[I] 1 sentence",
    "key_studies": ["R81", "S119", ...],      // the studies the rating mainly rests on
    "n_supporting": int, "computing_studies": int, "core_studies": int,
    "conflicts": "short note or \"\"",
    "cohort_note": "only for scalability, else \"\""}
 ],
 "evaluation_finding": "2-3 sentence overall evaluation with citations",
 "strengths": ["... [cites]", ...],          // 3-5 items
 "limitations": ["... [cites]", ...],        // 3-5 items
 "practical_considerations": ["... [cites]", ...],  // 3-5 items: cohort size, workload, implementation
 "evidence_gaps": ["..."]                     // what the review could not establish
}
```
Write in plain, professional British/Australian English, short sentences. Make sure the file parses with json.load.

## Amendment (17 Oct 2026, from the team's Project Context handover)
- Dimension 10 is renamed **Feasibility and cost** (key stays "feasibility"). It must also cover **implementation cost**: staff time, invigilation, venues, platforms and licences.
- Writing style: simple, clear, professional English. **Do not use em dashes** (use commas, colons or full stops). No filler.
