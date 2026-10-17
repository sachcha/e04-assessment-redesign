"""
Agreement between Screener A and Screener B at title/abstract stage.

    python Analysis/screening/compute_agreement.py

Outputs Analysis/screening/ta_agreement.csv (kappa) and ta_disagreements.csv.
"""
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent
import json
a = pd.concat([pd.read_csv(D / "ta_decisions_first_pass.csv"),
               pd.read_csv(D / "ta_new_records_screenerA.csv")], ignore_index=True)  # + R89-R96 (team-supplied papers)
nb = pd.DataFrame([{"Record ID": r["record_id"], "ta_decision": r["ta_decision_B"], "exclusion_code": r.get("ta_exclusion_code_B", ""),
                    "reason": r.get("ta_reason_B", "")}
                   for r in json.load(open(D / "extraction" / "new_records_extraction.json", encoding="utf-8"))])
b = pd.concat([pd.read_csv(D / "ta_decisions_screener_B.csv"), nb], ignore_index=True)
m = a.merge(b, on="Record ID", suffixes=("_A", "_B"))
assert len(m) == len(a) == len(b), (len(a), len(b), len(m))


def kappa(x, y):
    cats = sorted(set(x) | set(y))
    n = len(x)
    po = (x == y).mean()
    pe = sum((x == c).mean() * (y == c).mean() for c in cats)
    return po, (po - pe) / (1 - pe)


po3, k3 = kappa(m.ta_decision_A, m.ta_decision_B)
# binary: forward to full text (Include or Maybe) vs exclude
fa, fb = m.ta_decision_A.ne("Exclude"), m.ta_decision_B.ne("Exclude")
po2, k2 = kappa(fa, fb)
pd.DataFrame([
    {"comparison": "3 categories (Include / Maybe / Exclude)", "n": len(m), "pct_agreement": po3, "cohens_kappa": k3},
    {"comparison": "Forward to full text vs exclude", "n": len(m), "pct_agreement": po2, "cohens_kappa": k2},
]).to_csv(D / "ta_agreement.csv", index=False)
print(pd.crosstab(m.ta_decision_A, m.ta_decision_B, margins=True))
print(f"3-cat agreement {po3:.3f} kappa {k3:.3f}; binary agreement {po2:.3f} kappa {k2:.3f}")
dis = m[m.ta_decision_A != m.ta_decision_B]
dis[[c for c in ["Record ID", "ta_decision_A", "reason_A", "ta_decision_B", "exclusion_code_B", "reason_B"] if c in dis.columns]].to_csv(
    D / "ta_disagreements.csv", index=False)
print(dis[["Record ID", "ta_decision_A", "ta_decision_B", "reason_B"]].to_string(index=False))
