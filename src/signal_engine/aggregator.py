import pandas as pd


def compute_topic_counts(df: pd.DataFrame, stream: str, normalize: bool = False) -> pd.DataFrame:
    filtered = df[df["stream"] == stream]
    if filtered.empty:
        return pd.DataFrame(columns=["company", "topic_cluster", "count"])
    counts = (
        filtered.groupby(["company", "topic_cluster"])
        .size()
        .reset_index(name="count")
    )
    if normalize:
        totals = filtered.groupby("company").size().rename("total")
        counts = counts.join(totals, on="company")
        counts["count"] = (counts["count"] / counts["total"] * 100).round(1)
        counts = counts.drop(columns="total")
    return counts


def compute_sentiment_trend(df: pd.DataFrame, stream: str) -> pd.DataFrame:
    filtered = df[df["stream"] == stream]
    if filtered.empty:
        return pd.DataFrame(columns=["company", "mean_sentiment"])
    trend = (
        filtered.groupby("company")["sentiment_score"]
        .mean()
        .reset_index()
        .rename(columns={"sentiment_score": "mean_sentiment"})
    )
    return trend


def compute_topic_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment per company per topic across all streams."""
    if df.empty:
        return pd.DataFrame(columns=["company", "topic_cluster", "mean_sentiment"])
    result = (
        df.groupby(["company", "topic_cluster"])["sentiment_score"]
        .mean()
        .round(1)
        .reset_index()
        .rename(columns={"sentiment_score": "mean_sentiment"})
    )
    return result


def compute_weighted_sentiment(df: pd.DataFrame) -> pd.DataFrame:
    """Mean sentiment per company per topic, weighting ground_truth 2× over perception."""
    if df.empty:
        return pd.DataFrame(columns=["company", "topic_cluster", "weighted_mean_sentiment"])
    d = df.copy()
    d["_weight"] = d["stream"].map(lambda s: 2 if s == "ground_truth" else 1)
    d["_weighted"] = d["sentiment_score"] * d["_weight"]
    agg = (
        d.groupby(["company", "topic_cluster"])
        .agg(_ws=("_weighted", "sum"), _w=("_weight", "sum"))
        .reset_index()
    )
    agg["weighted_mean_sentiment"] = (agg["_ws"] / agg["_w"]).round(1)
    return agg[["company", "topic_cluster", "weighted_mean_sentiment"]]


_DIFF_FACTORS: dict[str, str] = {
    "localization":     "localization_score",
    "subsidy_reliance": "subsidy_dependency",
    "execution":        "execution_quality",
    "capex_efficiency": "capex_signal",
    "margin_quality":   "margin_signal",
    "ROIC":             "ROIC_signal",
}


def compute_differentiation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for factor_name, col in _DIFF_FACTORS.items():
        if col not in df.columns:
            continue
        catl_vals = df[df["company"] == "CATL"][col]
        lges_vals = df[df["company"] == "LGES"][col]
        if catl_vals.empty and lges_vals.empty:
            continue
        catl_mean = round(float(catl_vals.mean()), 2) if not catl_vals.empty else None
        lges_mean = round(float(lges_vals.mean()), 2) if not lges_vals.empty else None
        delta = round(catl_mean - lges_mean, 2) if (catl_mean is not None and lges_mean is not None) else None
        rows.append({"factor": factor_name, "CATL": catl_mean, "LGES": lges_mean, "delta": delta})
    return pd.DataFrame(rows)


def compute_timeline(df: pd.DataFrame) -> pd.DataFrame:
    if "date" not in df.columns:
        return pd.DataFrame(columns=["quarter", "company", "topic", "mention_count"])

    df2 = df.copy()
    df2["_dt"] = pd.to_datetime(df2["date"], errors="coerce")
    df2 = df2.dropna(subset=["_dt"])
    if df2.empty:
        return pd.DataFrame(columns=["quarter", "company", "topic", "mention_count"])

    df2["quarter"] = df2["_dt"].dt.to_period("Q").astype(str)

    rows = []
    for (quarter, company, topic), group in df2.groupby(["quarter", "company", "topic_cluster"]):
        rows.append({"quarter": quarter, "company": company, "topic": topic, "mention_count": len(group)})

    if "contradiction_flag" in df2.columns:
        for (quarter, company), group in df2.groupby(["quarter", "company"]):
            contra = int(group["contradiction_flag"].sum())
            if contra > 0:
                rows.append({"quarter": quarter, "company": company, "topic": "contradiction", "mention_count": contra})

    return pd.DataFrame(rows)


def compute_contradictions(df: pd.DataFrame) -> pd.DataFrame:
    if "contradiction_flag" not in df.columns:
        return pd.DataFrame(columns=["company", "claim_summary", "contradiction_reason", "sentiment_score"])
    flagged = df[df["contradiction_flag"] == True].copy()
    keep = [c for c in ["company", "claim_summary", "contradiction_reason", "sentiment_score", "contradiction_flag"] if c in flagged.columns]
    return flagged[keep].reset_index(drop=True)


_RISK_MAP: dict[str, tuple[str, bool]] = {
    # (column_name, True if high score = high risk)
    "policy_risk":    ("subsidy_dependency", True),
    "execution_risk": ("execution_quality",  False),
    "capex_risk":     ("capex_signal",       False),
    "margin_risk":    ("margin_signal",      False),
    "ROIC_risk":      ("ROIC_signal",        False),
}


def compute_risk_tree(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for company, group in df.groupby("company"):
        for risk_cat, (col, risk_when_high) in _RISK_MAP.items():
            if col not in df.columns:
                continue
            avg = group[col].mean()
            likelihood = round(avg / 10.0 if risk_when_high else (10.0 - avg) / 10.0, 2)
            rows.append({
                "company": company,
                "risk_category": risk_cat,
                "likelihood": likelihood,
                "impact": 0.7,
            })
    return pd.DataFrame(rows)


def compute_evidence_attribution(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (company, stream), group in df.groupby(["company", "stream"]):
        avg_conf = round(float(group["confidence"].mean()), 3) if "confidence" in df.columns else None
        rows.append({
            "company": company,
            "stream": stream,
            "doc_count": len(group),
            "avg_confidence": avg_conf,
        })
    return pd.DataFrame(rows)
