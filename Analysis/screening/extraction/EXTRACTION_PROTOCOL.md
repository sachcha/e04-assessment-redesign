# Full-text screening and data-extraction protocol (E04)

Review topic: authentic and secure assessment in computing / IT higher education in the GenAI era.
Search cut-off date: 16 October 2026.

## 1. Retrieve the full text, by legal routes only
In order:
1. The `oa_url` in the queue.
2. The DOI landing page.
3. OpenAlex: `https://api.openalex.org/works/doi:<DOI>`, using its `open_access.oa_url` and `locations[].pdf_url`.
4. Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/DOI:<DOI>?fields=openAccessPdf,externalIds`.
5. arXiv or SSRN preprints.
6. Author or institutional repositories, and the authors' personal pages.

Never use Sci-Hub, LibGen or other shadow libraries. Never try to get past CAPTCHAs, logins or paywalls.

For PDFs, fetch with WebFetch, or download with curl into the `extraction/pdfs/` folder and read them. `pdftotext` or Python `pypdf` may be available. Never run or execute anything you download.

Record `fulltext_status` as one of:
- `full text (publisher OA)`
- `full text (author/repository copy)`
- `abstract only`: No legal copy found. Then extract from the abstract and landing page only, and say so.

## 2. Full-text eligibility
Apply all of the criteria below.

- **IC1:** a higher-education context.
- **IC2:** assessment design, assessment validity or academic integrity is a primary or substantial focus.
- **IC3:** GenAI or LLMs, or AI in assessment more broadly.
- **IC4:** peer reviewed, or a formal framework paper.
- **IC5:** 2022 to 2026, in English.

Set `ft_decision` to Include or Exclude.
If excluding, give one code. E1 = not HE; E2 = not about assessment or integrity; E3 = no AI; E4 = not peer reviewed; E5 = date; E6 = language; E7 = full text unavailable.
Use E7 only if the abstract is too thin to extract anything usable. Otherwise keep the paper as `abstract only`.

## 3. Extraction
Extract only what the paper actually says. Never invent numbers, quotes or page numbers. If you are unsure, write "not reported". Give the location (page, section, table) for each key finding when you have the full text.

The eight assessment types are:
1. Supervised assessment
2. Unsupervised formats
3. Oral assessments
4. Practical demonstrations
5. Staged submissions
6. Process evidence
7. Personalised tasks
8. AI-use declarations

The framework dimensions are: authenticity, capability_verification, integrity_security, lo_alignment, appropriate_ai_use, scalability, workload, feasibility, process_visibility, accessibility_equity.

Quality appraisal: answer each item Y, N or Unclear. The checklist is adapted from MMAT 2018 and CASP. Count the Ys to get `quality_score` out of 5.
- **q1:** the research question or aim is clear.
- **q2:** the method is appropriate to the question. For a conceptual or framework paper, the argument is grounded in cited evidence.
- **q3:** the data or sample is adequately described: n, context and how it was collected.
- **q4:** the findings are supported by the data or analysis presented.
- **q5:** limitations are acknowledged.

## 4. Output
Write one JSON file per batch: `extraction/batch_<k>.json`. It is a JSON array with one object per record, using exactly these keys:

```
record_id, title, authors, year, venue, doi, fulltext_status, source_used,
ft_decision, ft_exclusion_code, ft_reason,
study_design, country, discipline, computing (Y/N/Partial), level, sample, genai_tools,
assessment_types (list of the eight type names that the paper gives evidence on),
key_findings (list of 2-5 objects: {"finding": "...", "location": "p. X / Sec Y / Table Z / abstract"}),
evidence_type ("empirical" | "review" | "conceptual/framework" | "guidance"),
dimensions (object with the 10 dimension keys; each a one-sentence note of what the paper shows, or "" if nothing),
author_recommendations (list of strings; what the authors propose, marking "(not tested)" when the paper did not evaluate it),
limitations (string),
quality: {"q1":..,"q2":..,"q3":..,"q4":..,"q5":..,"quality_score":int, "note": "..."}
```

Keep each finding to one or two sentences, in your own words. Short quotes (under 15 words) are allowed only when the exact wording matters.

## Addendum (17 Oct 2026): local full texts
The team supplied full texts in the project's Papers/ folder.
- Plain-text copies are in `extraction/text/<RecordID>.txt`. Read these first; no web download is needed.
- Page locations: pypdf separates pages without markers. Give section headings, table numbers or figure numbers as locations. Give a page number only if it is printed in the text, e.g. a journal page header.
- Never send any personal information (names, emails, accounts) to any web service. Unpaywall or any other service that requires an email must not be used.

## Addendum 2 (17 Oct 2026): update-search records and light extraction
Records from the documented OpenAlex update search have IDs S001-S494. Their queue files are in `screening/search/`.

### Full extraction (computing Y or Partial)
Follow the full protocol above.

### Light extraction (non-computing)
These records serve only as Supporting corroboration. Fill these keys properly: record_id, title, authors, year, venue, doi, fulltext_status, source_used, ft_decision, ft_exclusion_code, ft_reason, study_design, discipline, computing, level, sample, assessment_types, evidence_type, quality.
- Give exactly 1-2 key_findings, each with its location.
- Set "dimensions" to an object with the 10 keys. Fill only the dimensions the paper clearly speaks to and leave the rest "".
- Set author_recommendations to at most 2 items.
- Keep limitations to one sentence.
- Set country and genai_tools to "not extracted (light)" unless they are obvious.

### Both levels
- Full texts come from legal open access only: the oa_url, the DOI landing page, OpenAlex locations, author repositories, or arXiv.
- If no legal copy is reachable, set fulltext_status to "abstract only" and decide eligibility from the abstract. You can find the abstract at https://api.openalex.org/works/doi:<DOI>, which returns an abstract_inverted_index.
- Never bypass bot checks or paywalls. Never send personal data to any service.

## Amendment 3 (17 Oct 2026): IC2 sharpened to assessment redesign (applies to all records)
IC2 (revised): the study proposes, implements or evaluates an assessment (re)design for the GenAI era, or it gives evidence that directly informs how assessment should be redesigned. Examples of the second kind: how vulnerable assessment formats are to GenAI, the limits of detection or marker judgement, or how students use GenAI in assessed work.

Add a key "redesign_relevance" to every record, with exactly one of these values:
- "a_redesign": proposes, implements or evaluates a specific assessment design or redesign, or a framework for one.
- "b_informs_redesign": gives evidence that a redesign must respond to. Examples: vulnerability or AI capability on real assessment tasks, detection or marker limits, how students actually use GenAI on assessed work, or outcomes of permitted-use policies.
- "c_not_redesign": none of the above. Examples: integrity attitudes or perceptions only, AI grading or feedback tools, literacy instruments, general adoption. Set ft_decision = "Exclude" and ft_exclusion_code = "E2" for these.

Add a key "redesign_note": one sentence on what the paper offers for redesign.
