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
