 Proposed Fix Plan

  Step 1 — Fix the data (blocker): Stage 2 needs to be re-run against LGES source material. Do you have a catl.md-equivalent for LGES (e.g., earnings
  call transcript, IR release, news article)? I can see data/raw/perception/catl.md exists — is there a corresponding LGES file, or should we create
  representative tag JSONs directly?

  Step 2 — Fix the divergence matrix: Add per-bar sentiment annotation (color intensity or text label per company-topic bar). Rename to make the "quality
   gap" framing explicit: "Perception Topic Emphasis: CATL Organic Execution vs LGES Subsidy Dependence (% coverage share, annotated with mean
  sentiment)."

  Step 3 — Replace build_trend_inflection: Instead of company-level mean, show a perception vs ground_truth sentiment comparison per topic or a scatter
  of coverage share (x) vs sentiment (y) per company-topic — something that answers "does more coverage mean higher or lower quality signal?"

  Step 4 — Enhance the aggregator: Add compute_weighted_sentiment(df) that applies ground_truth 2× weighting before averaging, feed it to the new chart.

  Before I start coding: Do you have LGES source material we can run through Stage 2 to get real tags, or should I generate a representative set of
  LGES/ground_truth tag JSONs directly to unblock the charts? The former gives more defensible data for the competition; the latter is faster.