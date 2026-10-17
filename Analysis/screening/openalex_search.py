"""
Documented supplementary update search in OpenAlex (E04 literature review).

    python Analysis/screening/openalex_search.py counts   # hit counts only
    python Analysis/screening/openalex_search.py fetch    # retrieve all records for every string

Outputs (Analysis/screening/search/):
  search_log.csv        string id, purpose, exact query, filters, run date/time, hits
  search_results.csv    every retrieved record with the string(s) that found it
OpenAlex indexes most content in Scopus, Web of Science, ACM DL, IEEE Xplore and ERIC, but not identically;
this is reported as a supplementary update search, not a replacement for those databases.
"""
import csv
import datetime as dt
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent / "search"
OUT.mkdir(exist_ok=True)
UA = {"User-Agent": "E04-IRP-search/1.0 (university student project)"}

AI = ('("generative AI" OR "generative artificial intelligence" OR ChatGPT OR "large language model" '
      'OR "large language models" OR LLM OR GenAI OR Copilot)')
ASSESS = '(assessment OR assessments OR exam OR exams OR examination OR "academic integrity" OR cheating)'
CS = ('(programming OR "computer science" OR computing OR "software engineering" OR "information technology" '
      'OR "CS1")')
HE = '(university OR "higher education" OR undergraduate OR postgraduate OR tertiary)'
FILTERS = "publication_year:2022-2026,language:en,type:article|review|book-chapter"

# (id, purpose, title-search part, title+abstract-search part)
STRINGS = [
    ("S1", "Core: GenAI and assessment in computing HE",
     f"{AI} AND {ASSESS}", f"{CS} AND {HE}"),
    ("S2", "Supervised assessment",
     AI, f'("supervised assessment" OR invigilated OR proctored OR "in-person exam" OR "closed-book") AND {HE}'),
    ("S3", "Unsupervised formats",
     AI, f'("take-home" OR "programming assignment" OR "programming assignments" OR "coursework" '
         f'OR "unsupervised assessment") AND {ASSESS} AND {HE}'),
    ("S4", "Oral assessments",
     AI, f'("oral assessment" OR viva OR "viva voce" OR "oral exam" OR "oral examination" OR "interactive oral") '
         f'AND {HE}'),
    ("S5", "Practical demonstrations",
     AI, f'("live coding" OR "practical demonstration" OR "code walkthrough" OR "demonstration" OR "checkoff") '
         f'AND {ASSESS} AND {CS}'),
    ("S6", "Staged submissions",
     AI, f'("staged submission" OR "staged assessment" OR checkpoint OR checkpoints OR "multi-stage" '
         f'OR milestones OR "scaffolded assessment") AND {ASSESS} AND {HE}'),
    ("S7", "Process evidence",
     AI, f'("version control" OR "commit history" OR keystroke OR "process evidence" OR "process-oriented" '
         f'OR "chat logs" OR "prompt history" OR "learning analytics") AND {ASSESS} AND {HE}'),
    ("S8", "Personalised tasks",
     AI, f'(personalised OR personalized OR individualised OR contextualised OR "authentic assessment") '
         f'AND {ASSESS} AND {CS}'),
    ("S9", "AI-use declarations",
     AI, f'(declaration OR disclosure OR "AI use statement" OR "AI Assessment Scale" OR acknowledgement) '
         f'AND {ASSESS} AND {HE}'),
]


def call(params):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(params)
    for attempt in range(6):
        try:
            return json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(2 + 3 * attempt)
                continue
            raise
    raise RuntimeError("rate limited")


def filt(title_q, ta_q):
    return f"title.search:{title_q},title_and_abstract.search:{ta_q},{FILTERS}"


mode = sys.argv[1] if len(sys.argv) > 1 else "counts"
log, found = [], {}
for sid, purpose, tq, aq in STRINGS:
    f = filt(tq, aq)
    meta = call({"filter": f, "per-page": 1})["meta"]
    run = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    log.append({"string_id": sid, "purpose": purpose, "title_search": tq, "title_abstract_search": aq,
                "filters": FILTERS, "run_at": run, "hits": meta["count"]})
    print(sid, purpose, meta["count"])
    if mode == "fetch":
        cursor = "*"
        while cursor:
            r = call({"filter": f, "per-page": 200, "cursor": cursor,
                      "select": "id,doi,title,publication_year,primary_location,type,authorships"})
            for w in r["results"]:
                key = w["id"]
                if key not in found:
                    src = ((w.get("primary_location") or {}).get("source") or {}).get("display_name") or ""
                    found[key] = {"openalex_id": key, "doi": (w.get("doi") or "").replace("https://doi.org/", ""),
                                  "title": w.get("title") or "", "year": w.get("publication_year"),
                                  "type": w.get("type"), "venue": src,
                                  "authors": "; ".join(a["author"]["display_name"] for a in w.get("authorships", [])[:6]),
                                  "strings": sid}
                else:
                    found[key]["strings"] += ";" + sid
            cursor = r["meta"].get("next_cursor")
            time.sleep(0.5)
    time.sleep(1)

with open(OUT / ("search_log.csv" if mode == "fetch" else "search_counts.csv"), "w", newline="",
          encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(log[0])); w.writeheader(); w.writerows(log)
if mode == "fetch":
    with open(OUT / "search_results.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(next(iter(found.values())))); w.writeheader()
        w.writerows(found.values())
    print("unique records:", len(found))
