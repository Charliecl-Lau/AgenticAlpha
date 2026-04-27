import pandas as pd


def build_audit_table(df: pd.DataFrame) -> list[dict]:
    if df.empty:
        return []

    rows = []
    for _, row in df.iterrows():
        conf = row.get("confidence")
        if conf is not None:
            conf_str = f"{float(conf):.0%}"
        else:
            conf_str = "unknown"

        caveat = row.get("contradiction_reason")
        caveat_str = str(caveat) if caveat else "None identified"

        rows.append({
            "claim": str(row.get("claim_summary", "")),
            "docs":  str(row.get("source_file", "")),
            "confidence": conf_str,
            "caveat": caveat_str,
        })
    return rows


def format_audit_table_rows(audit_rows: list[dict]) -> list[list[str]]:
    header = ["Claim", "Source", "Confidence", "Caveat"]
    data = [
        [
            row["claim"][:80],
            row["docs"],
            row["confidence"],
            row["caveat"][:60],
        ]
        for row in audit_rows
    ]
    return [header] + data
