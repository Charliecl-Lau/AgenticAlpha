Layer 1: Quick Code Fixes (Do This Today – Highest ROI)
Goal: Make the existing synthesis produce richer, more structured output without major rewrites.

Enhance the synthesis prompt (most important single change)
Update the prompt you send to Claude in your synthesis step with the compact version I gave earlier (or the full structured one).
Add explicit instructions for:
Using specific numbers from human_inputs.yaml (margins, ROIC shock, execution edges).
Referencing chart names in the output.
Producing clean markdown tables for the Differentiation Matrix.
Keeping tone strictly neutral and evidence-based.


Improve data feeding to synthesis
In your synthesis function (add if missing), pass:
Aggregated topic counts + sentiment from Stage 3
Top 5–7 tagged examples (with summaries) per key factor
Human inputs dictionary
Chart file paths/names

This gives the LLM concrete material instead of vague JSON.

Fix color consistency in charts.py (you already noted this)Python_CATL_COLOR = "#1f77b4"   # Consistent CATL blue
_LGES_COLOR = "#ff7f0e"   # LGES orange (caution)Re-generate all charts after the change.

Layer 2: Medium-Term Code Upgrades (Next 1–2 Days)
Goal: Make the pipeline output a ready-to-use briefing automatically.

Add a dedicated synthesis.py module in src/human_layer/ or a new src/synthesis/ folder.
Function: generate_analyst_brief(deck_input, charts_dict) that calls Claude with a strong structured prompt and returns clean Markdown + JSON.
Save output as output/briefing/analyst_brief.md and analyst_brief.json.

Enhance DeckInput in merger.py to include:Pythonanalyst_brief: str          # full markdown report
key_tables: dict            # differentiation_matrix, risk_heatmap etc.
Update Stage 5 renderer (content_map.py):
Add 2–3 dedicated slides that pull sections from the analyst_brief:
Slide: "AI Differentiation Evidence" → Differentiation Matrix table + chart
Slide: "Why Now? Timing" → Timeline chart + paragraph
Slide: "Risk Counterfactuals" → Heatmap/table + short note
Slide 19/20: Use the Limitations section verbatim



Layer 3: Advanced Improvements (For Maximum Quality)

Multi-step synthesis:
Stage 3 → compute rich aggregates (normalized shares, weighted sentiment, time-series if dates available).
Stage 4 → human inputs validation.
New synthesis step → Claude call with very detailed system prompt that forces table output, chart references, and evidence attribution.
Post-process: Clean markdown, ensure neutrality.

Add traceability:
In the Differentiation Matrix table, add a column "Key Supporting Tags" with 1–2 example summaries from actual tags.

Version the briefing:
Save dated versions so teammates can see improvements as you add more URLs.