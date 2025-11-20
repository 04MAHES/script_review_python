import pandas as pd

def write_results_to_excel(json_obj: dict, out_path):
    tool = json_obj.get("tool")
    score = json_obj.get("compliance_score")
    issues = json_obj.get("issues", [])
    recs = json_obj.get("recommendations", [])

    # Determine how many rows needed
    max_len = max(len(issues), len(recs))

    # Pad the lists so they align row-by-row
    issues = issues + [""] * (max_len - len(issues))
    recs = recs + [""] * (max_len - len(recs))

    rows = []

    for i in range(max_len):
        if i == 0:
            # Fill tool + score ONLY in the first row
            rows.append({
                "Tool": tool,
                "Compliance Score": score,
                "Issue": issues[i],
                "Recommendation": recs[i]
            })
        else:
            # Leave tool + score empty for remaining rows
            rows.append({
                "Tool": "",
                "Compliance Score": "",
                "Issue": issues[i],
                "Recommendation": recs[i]
            })

    df = pd.DataFrame(rows)

    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
