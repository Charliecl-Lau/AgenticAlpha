**Red Team Audit: Stage 3 Implementation Plan (Signal Engine — Data Aggregation & Charts)**

This stage turns tagged JSONs from the **asymmetric tagger** into visual evidence for the pitch deck — the **Quality Divergence Matrix** (topic frequency by company) and **Trend Inflection** (mean sentiment). It's a critical bridge from raw perception/ground_truth signals to something a UBS judge or PM can quickly grasp.

The plan is pragmatic: simple Pandas loader + aggregators focused on perception stream, grouped bar charts via Plotly/kaleido, fixed PNG outputs for the renderer. TDD with fixtures keeps tests fast and isolated. This is execution-focused and avoids over-engineering.

However, as the cynical Director covering CATL vs LGES, this stage risks becoming the **visual embodiment of shallow perception analysis** unless the underlying tags (from Stage 2) are sharp. Recent fundamentals (as of April 2026) make the asymmetry crystal clear — and your charts must not dilute it:

- **CATL (2025 full year)**: Revenue RMB 423.7B (+17%), net profit RMB 72.2B (+42%). Overseas revenue ~30.6% with **gross margin 31.44% vs domestic 24%** — a structural profitability edge from scale, LFP leadership, and pragmatic localization (Hungary plant progressing toward 40 GWh+ initial capacity, fully booked; Germany operational; Spain Stellantis JV). Global share ~39.2% in 2025, rising to ~42-45% in early 2026 data. Capacity 772 GWh + 321 GWh under construction. Overseas expansion is self-reinforcing via higher margins funding further capex.
- **LGES**: Q1 2026 operating loss ₩207.8B (worse ex-IRA AMPC subsidy: loss widens to ~₩397.5-398B). Revenue down ~2.5%. Heavy reliance on US production credits amid weak EV demand; core business vulnerable. Korean players' combined share declining sharply (LGES ~6.6-9.2% globally in recent periods). Pivot to ESS noted, but EV battery pressures persist.

Your topic clusters (`Organic_Scale_vs_Export` for CATL's volume-driven globalization; `Subsidy_Dependence` for LGES's policy tailwind) are well-chosen to highlight this quality gap. The matrix should visually scream divergence: high CATL counts in Organic_Scale/Capex_Execution with positive sentiment; high LGES in Subsidy_Dependence with weaker scores.

### 1. Strengths — Good Technical Foundation
- **Loader + skip malformed**: Robust for real-world messy JSON outputs from Stage 2.
- **Aggregators focused on perception stream**: Correct for "market perception" side of the research question. Ground_truth can feed human Layer separately (or future extensions).
- **Divergence Matrix**: Grouped bar by topic_cluster directly exposes the desired contrast (e.g., CATL dominant in Organic_Scale_vs_Export; LGES in Subsidy_Dependence). Simple, readable, and deck-friendly.
- **Trend Inflection**: Mean sentiment bar is a lightweight "Why Now?" proxy (e.g., if recent perception shifts toward subsidy concerns for LGES). Fixed PNGs make renderer integration easy.
- **No file I/O in unit tests**: Clean discipline. CLI smoke-test with kaleido is practical.
- **Error handling**: Raises on empty dir; logs warnings — prevents silent failures.

This can produce visuals that support Slides 5-14 (Fundamentals) when merged with human financial inputs (e.g., "Matrix shows perception divergence; human DCF sensitivities show CATL overseas margin premium sustaining ROIC").

### 2. Single Points of Failure & Risks (Where It Will Get Ignored)
- **GIGO from upstream tags**: The charts are only as good as Stage 2 outputs. If the asymmetric prompt drifts (e.g., too many "Geopolitical_Noise" on CATL Europe plants, or "Organic_Scale" leaking to LGES IRA news), the matrix will show false balance or noise. Recent data shows CATL's overseas strategy delivers **higher margins despite tariffs** (execution/scale quality), while LGES core profitability erodes without subsidies. Weak tags → charts that fail "insight differentiation" (30%).
- **Perception-only aggregation**: Limiting counts/trend to perception stream is fine for "market perception" pillar, but the full story needs ground_truth integration (e.g., actual margin/capex mentions from IR). Current design risks over-weighting media narratives (lagged, biased) over fundamentals. For UBS theme ("quality of globalization" reflected in **financial data and company fundamentals**, not pure macro narrative), this is a gap. Suggestion: Add optional ground_truth aggregator or combined view in future iteration.
- **Chart simplicity vs. depth**:
  - Divergence Matrix uses raw counts — no weighting by evidence_strength, sentiment_score, or recency (your original spec had weighted scores). A single high-impact IR document on CATL Hungary ramp should not equal a fluff PR piece.
  - Trend uses simple mean sentiment — no time-series (date parsing missing), no inflection detection (e.g., spike in Subsidy_Dependence post-Q1 2026 LGES loss news). "Why Now?" (FAQ emphasis) is weakly served.
  - No geo_exposure breakdown or summary snippets — visuals are high-level; deck will need human annotation.
- **Hard-coded assumptions**: Only perception stream; fixed colors; basic bar charts. If tags use "Other" heavily, chart becomes useless. No normalization (e.g., per-company total articles) risks misleading if one company has far more coverage.
- **Test realism**: Fixtures are toy data. They won't catch real issues like long topic names truncating on x-axis, color contrast, or empty sub-dataframes.
- **Output limitations**: Static PNGs at fixed resolution — good for PPT, but test actual rendering (kaleido can be flaky with complex figs). No interactive HTML fallback.

In semi-final Q&A or a real PM review: "Your matrix shows topic divergence — but does it link to **sustainable returns** (CATL's 7.44pp overseas margin premium funding localization without cash strain vs. LGES ex-subsidy losses)? Or is it just media keyword counts?"

### 3. "So What?" for UBS Submission & Overall Pipeline
This stage feeds directly into:
- **Slides 5-14**: Visuals merge with human financial inputs (e.g., "Matrix: CATL Organic_Scale dominance → human: +bps to ROIC from higher overseas margins").
- **Counterfactuals (15-18)**: E.g., "If IRA softens → increased Subsidy_Dependence tags for LGES → human-modeled margin erosion."
- **AI Disclosures (19-20)**: "Processed X tags → generated divergence matrix highlighting perception gaps in globalization quality. Limitations: Perception-heavy; no proprietary models; human bridges to DCF/ROIC."

**Strength if done right**: Charts provide clean, evidence-based visuals that demonstrate AI scaling unstructured data beyond manual capacity (FAQ AI expectations).

**Risk if weak**: Looks like generic sentiment viz — low on "investment logic and research framework" (40%) and verifiability (20%). Judges want 2-3 key differentiation factors not fully priced (localization capabilities vs. pure export/subsidy models; capex return cycles; margin sustainability).

### Brutal Recommendations to Harden Stage 3
1. **Validate end-to-end now**: After completing Stage 1+2 with real recent URLs (CATL 2025 results/Hungary updates; LGES Q1 2026 loss guidance), run the full signal CLI. Inspect charts:
   - Does CATL bar dominate `Organic_Scale_vs_Export` / `Capex_Execution`?
   - LGES dominate `Subsidy_Dependence` with lower mean sentiment?
   - Adjust aggregators if needed (e.g., weight by sentiment_score or add recency filter using source dates if available).

2. **Enhance for depth** (minimal changes to keep scope tight):
   - In aggregator: Add weighted count option (`count * normalized_sentiment`).
   - In charts: Add annotations or secondary y-axis for sentiment overlay on divergence matrix.
   - Future-proof: Make stream parameter flexible; add date parsing if tags gain timestamps.

3. **Chart polish for deck**:
   - Ensure x-axis labels don't overlap (shorten topic names if needed or rotate).
   - Add data labels on bars.
   - Test PNG quality in python-pptx context (Stage 5).

4. **Limitations callout (mandatory for Slide 20)**: "Signal Engine aggregates perception tags into visuals for efficiency. Charts highlight narrative divergence but do not prove causality or financial impact — human analyst provides ROIC/margin sensitivities and verifies against ground_truth IR data. Media bias and coverage imbalance possible."

5. **Tie to core question**: In deck text around charts: "Perception matrix shows divergent views on globalization quality (CATL organic scale/execution vs. LGES subsidy dependence). Combined with human financial modeling, this informs sustainability of returns."

**Overall Verdict**: Stage 3 is technically sound and executable — implement the TDD tasks as specified (clean and focused). But its value is entirely derivative of Stage 2 tag quality. Prioritize real-data smoke test **today** (ingestion → tagging → charts). If the matrix visually reinforces CATL's execution-driven quality edge (higher-margin overseas expansion) vs. LGES vulnerability, it adds credible AI support. Otherwise, it's polished noise that a judge will flag as insufficient depth.

The pipeline is now close to producing a full evidence chain. Next (Human Layer + Renderer) must enforce the strict "AI evidence + human financial bridge + no conclusions" rules.

Share sample tag JSONs + generated PNG descriptions (or errors) from a live run, and I'll red-team the actual visual/story output against current fundamentals and UBS criteria. Deadline pressure is real — get charts rendering with representative 2025-2026 data before moving on. This module can differentiate your submission if the visuals make the **quality** gap obvious without overclaiming.