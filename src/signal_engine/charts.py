from __future__ import annotations
import pandas as pd
import plotly.graph_objects as go

_CATL_COLOR = "#1f77b4"
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


def build_differentiation_matrix_chart(
    diff_df: pd.DataFrame,
    output_path: str,
    human_metrics: dict | None = None,
) -> None:
    if diff_df.empty:
        go.Figure().update_layout(
            title="Differentiation Matrix (no data)", width=900, height=500,
        ).write_image(output_path)
        return

    if human_metrics is None:
        human_metrics = {"catl_margin": 31.4, "lges_margin": 2.1}

    df = diff_df.copy().dropna(subset=["delta"])
    df = df.reindex(df["delta"].abs().sort_values(ascending=False).index)

    factor_labels = {
        "subsidy_reliance": "Subsidy Reliance",
        "execution": "Execution Quality",
        "capex_efficiency": "Capex Efficiency",
        "margin_quality": "Margin Quality",
        "ROIC": "ROIC Signal",
        "localization": "Localization",
    }
    x_labels = [factor_labels.get(f, f) for f in df["factor"]]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        name="CATL", x=x_labels, y=df["CATL"],
        marker_color=_CATL_COLOR,
        text=[f"{v:.2f}" for v in df["CATL"]],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        name="LGES", x=x_labels, y=df["LGES"],
        marker_color=_LGES_COLOR,
        text=[f"{v:.2f}" for v in df["LGES"]],
        textposition="outside",
    ))

    catl_margin = human_metrics.get("catl_margin", 31.4)
    lges_margin = human_metrics.get("lges_margin", 2.1)
    subtitle = (
        f"<br><sub>CATL perception emphasizes execution-led organic globalization "
        f"(aligns with {catl_margin:.1f}% overseas margin premium). "
        f"LGES perception skewed toward subsidy dependence "
        f"(aligns with {lges_margin:.1f}% ex-IRA operating margin).</sub>"
    )

    fig.update_layout(
        title="Differentiation Matrix: CATL vs LGES (1–10 scale, ordered by delta)" + subtitle,
        barmode="group",
        yaxis=dict(range=[0, 11], title="Signal Score"),
        xaxis_title="Factor",
        template="plotly_white",
        font=dict(size=13),
        margin=dict(b=80, t=130),
        width=1000, height=540,
    )
    fig.write_image(output_path)


def build_why_now_timeline_chart(timeline_df: pd.DataFrame, output_path: str) -> None:
    if timeline_df.empty:
        go.Figure().update_layout(
            title="Why Now Timeline (no data)", width=900, height=400,
        ).write_image(output_path)
        return

    agg = (
        timeline_df[timeline_df["topic"] != "contradiction"]
        .groupby(["quarter", "company"])["mention_count"]
        .sum()
        .reset_index()
        .sort_values("quarter")
    )

    fig = go.Figure()
    for company, color in [("CATL", _CATL_COLOR), ("LGES", _LGES_COLOR)]:
        sub = agg[agg["company"] == company]
        fig.add_trace(go.Scatter(
            x=sub["quarter"],
            y=sub["mention_count"],
            mode="lines+markers",
            name=company,
            line=dict(color=color, width=2),
            marker=dict(size=8),
        ))

    _KEY_EVENTS = [
        ("2025Q1", "LGES IRA credits<br>exceed operating profit"),
        ("2025Q2", "CATL Hungary 50 GWh<br>run-rate achieved"),
    ]
    quarters = sorted(agg["quarter"].unique().tolist())
    max_y = int(agg["mention_count"].max()) + 2 if not agg.empty else 10
    for q, label in _KEY_EVENTS:
        if q in quarters:
            fig.add_vline(x=q, line_dash="dot", line_color="grey", line_width=1)
            fig.add_annotation(
                x=q, y=max_y, text=label,
                showarrow=False, font=dict(size=10, color="grey"),
                yanchor="top", align="center",
            )

    fig.update_layout(
        title=(
            "Why Now: AI Coverage Intensity by Quarter<br>"
            "<sub>Divergence in coverage momentum reflects shifting execution and subsidy narratives in 2025–26.</sub>"
        ),
        xaxis_title="Quarter",
        yaxis_title="Total Mentions",
        template="plotly_white",
        font=dict(size=13),
        legend_title="Company",
        margin=dict(b=60, t=120),
        width=1000,
        height=500,
    )
    fig.write_image(output_path)


_RISK_SCENARIOS = [
    ("IRA credit reduction",   "Mild negative",  "Major negative",  "Widens spread — favors CATL"),
    ("Hungary ramp delay",     "Negative",        "Neutral",         "Compresses spread"),
    ("Europe EV rebound",      "Positive",        "Positive",        "Neutral — both benefit"),
    ("Tariff escalation",      "Moderate",        "Mild",            "Mixed — CATL more exposed on exports"),
    ("US EV demand -20% YoY",  "Moderate",        "Severe",          "Widens spread — IRA cliff hits LGES"),
]

_IMPACT_COLORS = {
    "Mild negative":   "#FEF3C7",
    "Major negative":  "#FCA5A5",
    "Negative":        "#FCA5A5",
    "Moderate":        "#FDE68A",
    "Mild":            "#FEF3C7",
    "Positive":        "#BBF7D0",
    "Severe":          "#DC2626",
    "Neutral":         "#F3F4F6",
    "Neutral — both benefit": "#BBF7D0",
}


def build_risk_tree_chart(risk_df: pd.DataFrame, output_path: str) -> None:
    scenarios, catl_impacts, lges_impacts, pair_effects = zip(*_RISK_SCENARIOS)

    header_color = "#1E3A5F"
    catl_fill  = [_IMPACT_COLORS.get(v, "#F3F4F6") for v in catl_impacts]
    lges_fill  = [_IMPACT_COLORS.get(v, "#F3F4F6") for v in lges_impacts]

    fig = go.Figure(go.Table(
        columnwidth=[220, 140, 140, 240],
        header=dict(
            values=["<b>Scenario</b>", "<b>CATL Impact</b>", "<b>LGES Impact</b>", "<b>Pair Effect</b>"],
            fill_color=header_color,
            font=dict(color="white", size=13),
            align="left",
            height=36,
        ),
        cells=dict(
            values=[list(scenarios), list(catl_impacts), list(lges_impacts), list(pair_effects)],
            fill_color=[
                ["#F9FAFB"] * len(scenarios),
                catl_fill,
                lges_fill,
                ["#F9FAFB"] * len(scenarios),
            ],
            font=dict(size=12),
            align="left",
            height=32,
        ),
    ))

    fig.update_layout(
        title=(
            "Risk Counterfactual Heatmap: Scenario Impact on CATL vs LGES<br>"
            "<sub>Green = positive, amber = moderate, red = negative. Pair effect shows spread direction.</sub>"
        ),
        template="plotly_white",
        font=dict(size=13),
        margin=dict(l=20, r=20, t=110, b=20),
        width=820,
        height=340,
    )
    fig.write_image(output_path)


def build_contradiction_chart(contradictions_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if contradictions_df.empty:
        go.Figure().update_layout(
            title="Contradiction Scanner (no contradictions identified)", width=900, height=300,
        ).write_image(output_path)
        return

    fig = go.Figure()
    colors = {"CATL": _CATL_COLOR, "LGES": _LGES_COLOR}
    for company, sub in contradictions_df.groupby("company"):
        fig.add_trace(go.Scatter(
            x=sub["sentiment_score"],
            y=sub["claim_summary"].str[:60],
            mode="markers+text",
            name=company,
            marker=dict(size=14, color=colors.get(company, "grey")),
            text=sub["contradiction_reason"].str[:40],
            textposition="top center",
        ))

    fig.update_layout(
        title="Contradiction Scanner: Evidence Challenging Bull Thesis",
        xaxis=dict(title="Sentiment Score (lower = more bearish)", range=[0, 10]),
        template="plotly_white",
        width=1000,
        height=max(400, len(contradictions_df) * 60),
    )
    fig.write_image(output_path)


def build_evidence_scale_chart(attribution_df: pd.DataFrame, output_path: str) -> None:
    import plotly.graph_objects as go

    if attribution_df.empty:
        go.Figure().write_image(output_path)
        return

    colors = {
        "perception": "#60A5FA",
        "ground_truth": "#1D4ED8",
        "policy": "#A78BFA",
        "operations": "#34D399",
    }

    fig = go.Figure()
    for stream, group in attribution_df.groupby("stream"):
        fig.add_trace(go.Bar(
            name=stream,
            x=group["company"],
            y=group["doc_count"],
            marker_color=colors.get(stream, "grey"),
            text=group["avg_confidence"].apply(lambda c: f"conf: {c:.0%}" if c else ""),
            textposition="outside",
        ))

    fig.update_layout(
        title="Evidence Attribution: Documents by Company and Stream",
        barmode="stack",
        yaxis_title="Document Count",
        template="plotly_white",
        width=800,
        height=500,
    )
    fig.write_image(output_path)
