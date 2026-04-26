from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_CATL_COLOR = "#1f77b4"
_LGES_COLOR = "#d62728"

_TOPIC_LABELS: dict[str, str] = {
    "Organic_Scale_vs_Export": "Organic Scale",
    "Subsidy_Dependence": "Subsidy Dep.",
    "Geopolitical_Noise": "Geo. Noise",
    "Capex_Execution": "Capex Exec.",
    "Other": "Other",
}


def build_divergence_matrix(
    counts_df: pd.DataFrame,
    trend_df: pd.DataFrame | None = None,
) -> go.Figure:
    # Raises KeyError if required columns are missing — intentional validation
    _ = counts_df[["company", "topic_cluster", "count"]]

    fig = go.Figure()
    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = counts_df[counts_df["company"] == company]
        x_labels = [_TOPIC_LABELS.get(t, t) for t in sub["topic_cluster"]]
        fig.add_trace(go.Bar(
            name=company,
            x=x_labels,
            y=sub["count"],
            text=[f"{v:.1f}" for v in sub["count"]],
            textposition="outside",
            marker_color=color,
        ))

    title = "Quality Divergence Matrix: Topic Coverage Share by Company (%)"
    if trend_df is not None and not trend_df.empty:
        catl_s = trend_df[trend_df["company"] == "CATL"]["mean_sentiment"]
        lges_s = trend_df[trend_df["company"] == "LGES"]["mean_sentiment"]
        if not catl_s.empty and not lges_s.empty:
            title += (
                f"<br><sub>Mean sentiment — CATL: {catl_s.iloc[0]:.1f}/10"
                f" | LGES: {lges_s.iloc[0]:.1f}/10</sub>"
            )

    fig.update_layout(
        title=title,
        xaxis_title="Topic Cluster",
        yaxis_title="Share of Coverage (%)",
        barmode="group",
        legend_title="Company",
        template="plotly_white",
        font=dict(size=13),
        xaxis=dict(tickangle=-35),
        margin=dict(b=90, t=90),
    )
    return fig


def build_trend_inflection(trend_df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    colors = {"CATL": _CATL_COLOR, "LGES": _LGES_COLOR}
    fig.add_trace(go.Bar(
        x=trend_df["company"].tolist(),
        y=trend_df["mean_sentiment"].tolist(),
        text=[f"{v:.1f}" for v in trend_df["mean_sentiment"]],
        textposition="outside",
        marker_color=[colors.get(c, "grey") for c in trend_df["company"]],
    ))

    fig.update_layout(
        title="Mean Perception Sentiment by Company (1–10 scale)",
        yaxis_title="Mean Sentiment Score",
        yaxis=dict(range=[0, 10]),
        template="plotly_white",
        font=dict(size=13),
        showlegend=False,
    )
    return fig
