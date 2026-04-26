import pandas as pd


def extract_top_signals(df: pd.DataFrame, n: int = 3) -> dict[str, list[dict]]:
    """Return the top-N signals per company, weighted by stream.

    Ground-truth stream rows are scored at 2× their sentiment_score.
    Assumes sentiment_score is always positive (tagger enforces 1–10).
    """
    result: dict[str, list[dict]] = {}
    for company in df["company"].unique():
        sub = df[df["company"] == company].copy()
        # Ground-truth IR earnings data is weighted 2× over perception/news sentiment.
        # This prevents a bullish press release from outranking a dry but credible earnings release.
        sub["_weighted_score"] = sub.apply(
            lambda r: r["sentiment_score"] * (2 if r["stream"] == "ground_truth" else 1),
            axis=1,
        )
        top = sub.sort_values("_weighted_score", ascending=False).head(n)
        result[company] = top[["topic_cluster", "sentiment_score", "summary", "stream"]].to_dict("records")
    return result
