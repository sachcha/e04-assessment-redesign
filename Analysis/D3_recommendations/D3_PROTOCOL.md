# D3 Computing Assessment Recommendation Matrix / Decision Guide: protocol (approved 17 Oct 2026)

D3 turns the D2 evaluation into practical redesign recommendations. It answers RQ3 (suitability by learning outcome and cohort size) and RQ5 (which combinations to recommend), and the brief's request for "suitable assessment combinations for different computing learning outcomes and class sizes".

## Inputs (use only these)
- `../D2_framework/cells/*.json`: the calibrated D2 ratings and evidence for the 8 assessment types. This is the main input. Every "Identified Problem" must come from D2.
- `../D2_framework/type_definitions.json`: what each type includes and excludes.
- `../D2_framework/packs/<type>.md`: the full evidence for each type.
- `tested_redesigns.md`: the 44 empirical studies that implemented or evaluated a redesign. Use it to decide Evidence status.
- `../D2_framework/dataset_evidence.md`: [D01], [D28] and [J1], [J6].
- `../project_context.txt`, section 11: the team's preliminary Strategies A-F, and section 13: cohort size. Strategies A-F are working proposals. Evaluate them against the evidence; never assume they work.

Never cite anything else. Never invent studies, figures or citations. Cite as [R81], [S119], [D24], [J1].

## Evidence levels (Project Context section 16)
- **Level 1, finding:** what a study or dataset shows.
- **Level 2, interpretation:** what it suggests for design.
- **Level 3, recommendation:** what we propose. Every recommendation carries an **Evidence status**:
  - **Tested in computing:** a similar redesign was implemented and its outcomes reported in a computing course (from tested_redesigns.md, computing = Y).
  - **Tested in another discipline:** implemented and evaluated, but outside computing.
  - **Proposal (not yet tested):** supported only by D2 ratings, author recommendations or reasoning. Say what would be needed to validate it.
- A study showing that AI can complete an assessment does not show that a redesign works.

## Vocabulary
- **Learning outcomes:**
  - LO1 Foundational knowledge
  - LO2 Programming and implementation skill
  - LO3 Analysis, design and problem solving
  - LO4 Professional and collaborative practice
  - LO5 Critical and responsible use of AI
- **Cohorts:** small (<50), medium (50-200), large (>200).
- **Combination layers:**
  1. **Main assessment:** what the student produces.
  2. **Verification layer:** how individual understanding is checked.
  3. **AI-use level:** what is permitted and how it is recorded. Name the level plainly, e.g. "No AI (supervised)", "AI for ideas and feedback only", "AI permitted with declaration", "AI integrated and assessed (critique or correction of AI output)". The AIAS [R10] may be referenced where it fits.

## Design principles to check every recommendation against (from D2)
- No single type does everything. Combine a scalable main assessment with a proportionate verification layer.
- Verification should be proportionate to stakes. Programme-level security at key points, rather than securing every task, is supported by R68 and R04. Check that the packs say this before relying on it.
- Logs and declarations improve transparency but do not on their own establish understanding: [D26], [J6], [J1] and the D2 process-evidence and declarations rows.
- Question or task wording is not a security measure [J3].
- For large cohorts, prefer sampled or risk-based live verification over universal vivas, and give the staff-time evidence (e.g. R84).
- Consider accessibility and equity: alternatives for students with disabilities, anxiety or English as an additional language, and equal access to AI tools.

## Writing style
Simple, clear, professional English. No em dashes. Short sentences. Citations go inside the text.

## Outputs (JSON; each file must parse with json.load)
### Part A: `out/partA_<type_file_name>.json` (one per type)
```
{"assessment_type": "...",
 "identified_problem": "2-3 sentences drawn from D2 weak ratings, with citations",
 "recommended_redesign": ["specific change 1", "specific change 2", "..."],   // 2-4 items
 "justification": "2-4 sentences with citations, separating finding from interpretation",
 "implementation_considerations": ["cohort, staff time, cost, equity, policy items with citations"],  // 3-5
 "evidence_status": "Tested in computing | Tested in another discipline | Proposal (not yet tested)",
 "evidence_status_basis": "which studies, and what they tested",
 "related_team_strategy": "A-F letters from Project Context section 11 that this matches, or \"\"",
 "risks_and_limits": "what the redesign cannot guarantee"}
```
### Part B: `out/partB_decision_guide.json`
```
{"cells": [ // 15 = LO1..LO5 x small, medium, large
  {"learning_outcome": "LO1 Foundational knowledge", "cohort": "Small (<50)",
   "main_assessment": "...", "verification_layer": "...", "ai_use_level": "...",
   "rationale": "1-3 sentences with citations", "trade_offs": "1-2 sentences",
   "evidence_status": "...", "key_studies": ["R81", "..."]}],
 "cross_cutting_principles": ["5-7 principles with citations"]}
```
### Part C: `out/partC_monitoring_framework.json`
```
{"purpose": "...", "status": "Conceptual proposal (approved scope change, not a deployed system)",
 "components": [{"component": "...", "description": "...", "what_it_can_evidence": "...", "what_it_cannot": "...", "evidence": "with citations"}],
 "how_it_combines_with_verification": "...",
 "privacy_ethics_legal_requirements": ["..."],
 "implementation_steps": ["..."],
 "open_questions_and_validation_needed": ["..."]}
```
