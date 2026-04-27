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
