from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_CATL_COLOR = "#0e5a9e"
_LGES_COLOR = "#ff7f0e"

_TOPIC_LABELS: dict[str, str] = {
    "Organic_Scale_vs_Export": "Organic Scale",
    "Subsidy_Dependence": "Subsidy Dep.",
    "Geopolitical_Noise": "Geo. Noise",
    "Capex_Execution": "Capex Exec.",
}


def build_divergence_matrix(
    counts_df: pd.DataFrame,
    trend_df: pd.DataFrame | None = None,
    sentiment_df: pd.DataFrame | None = None,
    human_metrics: dict | None = None,
) -> go.Figure:
    # Raises KeyError if required columns are missing — intentional validation
    _ = counts_df[["company", "topic_cluster", "count"]]

    if human_metrics is None:
        human_metrics = {"catl_margin": 31.4, "lges_margin": 2.1}

    fig = go.Figure()
    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = counts_df[counts_df["company"] == company]
        x_labels = [_TOPIC_LABELS.get(t, t) for t in sub["topic_cluster"]]

        if sentiment_df is not None and not sentiment_df.empty:
            text_labels = []
            for _, row in sub.iterrows():
                sent_row = sentiment_df[
                    (sentiment_df["company"] == company)
                    & (sentiment_df["topic_cluster"] == row["topic_cluster"])
                ]
                if not sent_row.empty:
                    col = "weighted_mean_sentiment" if "weighted_mean_sentiment" in sent_row.columns else "mean_sentiment"
                    s = sent_row[col].iloc[0]
                else:
                    s = None
                label = f"{row['count']:.1f}%" + (f"<br>★{s:.1f}" if s is not None else "")
                text_labels.append(label)
        else:
            text_labels = [f"{v:.1f}" for v in sub["count"]]

        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=sub["count"],
            text=text_labels,
            textposition="outside",
            marker_color=color,
        ))

    title = "Perception vs Reality: CATL Execution-Led Globalization vs LGES Subsidy Dependence"

    subtitle = (
        f"<br><sub>CATL: High sentiment on Organic/Capex → aligns with {human_metrics.get('catl_margin', 31.4)}% overseas margin premium. "
        f"LGES: Low sentiment on Subsidy Dep. → aligns with {human_metrics.get('lges_margin', 2.1)}% ex-IRA margin.</sub>"
    )

    if trend_df is not None and not trend_df.empty:
        catl_s = trend_df[trend_df["company"] == "CATL"]["mean_sentiment"]
        lges_s = trend_df[trend_df["company"] == "LGES"]["mean_sentiment"]
        if not catl_s.empty and not lges_s.empty:
            subtitle += (
                f"<br><sub>Mean sentiment — CATL: {catl_s.iloc[0]:.1f}/10"
                f" | LGES: {lges_s.iloc[0]:.1f}/10</sub>"
            )

    title += subtitle

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Share of Coverage (%)",
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=130),
    )
    return fig


def build_trend_inflection(sentiment_df: pd.DataFrame) -> go.Figure:
    """Grouped bars of mean sentiment per topic per company."""
    fig = go.Figure()

    # Filter out 'Other' topic
    filtered_df = sentiment_df[sentiment_df["topic_cluster"] != "Other"]
    topics = filtered_df["topic_cluster"].unique().tolist()
    x_labels = [_TOPIC_LABELS.get(t, t) for t in topics]

    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = filtered_df[filtered_df["company"] == company]
        y_vals = []
        for topic in topics:
            row = sub[sub["topic_cluster"] == topic]
            # Handle both mean_sentiment and weighted_mean_sentiment
            val_col = "weighted_mean_sentiment" if "weighted_mean_sentiment" in row.columns else "mean_sentiment"
            y_vals.append(row[val_col].iloc[0] if not row.empty else None)

        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=y_vals,
            text=[f"{v:.1f}" if v is not None else "" for v in y_vals],
            textposition="outside",
            marker_color=color,
        ))

    title = (
        "Signal Quality by Topic: Sentiment Divergence Between CATL and LGES<br>"
        "<sub>Sentiment divergence on execution topics supports human-verified margin premium for CATL.</sub>"
    )

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Mean Sentiment Score",
        yaxis=dict(range=[0, 10]),
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=110),
    )
    return fig
