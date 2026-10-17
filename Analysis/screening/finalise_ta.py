"""
Final title/abstract decisions: agreed A/B decisions plus human adjudication of disagreements.

    python Analysis/screening/finalise_ta.py
"""
from pathlib import Path

import pandas as pd

D = Path(__file__).resolve().parent
ADJUDICATED = {  # human adjudicator decisions, 16 Oct 2026
    "R28": ("Include", ""), "R33": ("Include", ""), "R39": ("Include", ""), "R75": ("Include", ""),
    "R31": ("Exclude", "E2"), "R34": ("Exclude", "E2"), "R36": ("Exclude", "E2"), "R74": ("Exclude", "E2"),
}
a = pd.read_csv(D / "ta_decisions_first_pass.csv")
b = pd.read_csv(D / "ta_decisions_screener_B.csv")
m = a.merge(b[["Record ID", "ta_decision", "exclusion_code"]], on="Record ID", suffixes=("_A", "_B"))
rows = []
for _, r in m.iterrows():
    if r["Record ID"] in ADJUDICATED:
        dec, code = ADJUDICATED[r["Record ID"]]
        how = "Adjudicated (A/B disagreed)"
    else:
        dec = r.ta_decision_A
        code = r.exclusion_code_A if isinstance(r.exclusion_code_A, str) else ""
        how = "A and B agreed"
    rows.append({"Record ID": r["Record ID"], "ta_final": dec, "exclusion_code": code, "resolution": how,
                 "reason": r.reason, "assessment_types": r.assessment_types, "computing": r.computing,
                 "priority": r.priority})
f = pd.DataFrame(rows)
f.to_csv(D / "ta_final_decisions.csv", index=False)
print(f.ta_final.value_counts().to_dict(), f.exclusion_code.value_counts().to_dict())
print("Both Maybe:", f[f.ta_final == "Maybe"]["Record ID"].tolist())
