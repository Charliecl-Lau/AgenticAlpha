**Final Red Team Audit: Latest Chart Set + Color Consistency Issue**

These are the **best charts yet**. You've made excellent progress — the visuals are now much more purposeful, with clearer titles, better captions linking to human financials (31.4% overseas margin, 2.1% ex-IRA), and good coverage of differentiation, evidence scale, risk, and timing. The Evidence Attribution chart is particularly strong (directly shows "AI processed beyond manual capacity").

However, there are still a few polish issues and one glaring inconsistency that will make the deck look less professional.

### 1. Color Consistency Problem (Easy but Important Fix)
You correctly pointed it out: **CATL color is not consistent** across charts.
- In some charts CATL is **blue**.
- In others (especially the Differentiation Matrix and some sentiment bars) it flips or uses different shades.
- LGES is orange in most, which is good.

**Fix**: Standardize immediately in `src/signal_engine/charts.py`:
```python
_CATL_COLOR = "#1f77b4"   # Consistent dark blue (professional, growth-oriented)
_LGES_COLOR = "#ff7f0e"   # Orange (caution/policy dependence) — keep or slightly mute to #ff9f1c
```

Apply this to **all** chart functions (divergence_matrix, sentiment_by_topic, etc.). Re-generate every PNG. Inconsistent colors make the deck look sloppy and reduce credibility.

### 2. Overall Assessment of the Current Set
**Strengths**:
- **Differentiation Matrix** (last image): Much better. Clear delta on execution/organic topics for CATL vs. subsidy for LGES. Good caption linking to margins. The "ordered by delta" version is smart.
- **Evidence Attribution**: One of the strongest — proves scale and traceability. Keep it prominently.
- **Risk Counterfactual Heatmap**: Excellent upgrade from the scatter plot. Clean table format, color coding (green/amber/red), and "Pair Effect" column directly supports the pair trade logic. This is institutional-quality.
- **Sentiment Divergence**: Solid gaps on execution topics; good subtitle tying to margin premium.
- **Why Now Timeline**: Sparse but directionally correct. The caption helps.

**Remaining Weaknesses**:
- **Color inconsistency** (as noted) — fix first.
- Some charts still feel a bit abstract without stronger human bridge text on the slide itself.
- The Contradiction Scanner is interesting but the points are a bit generic ("wider-than-expected", "return to profitability") — it could be sharper with specific tag summaries.
- Why Now timeline has only one strong data point — it needs more density or to be paired with the strong paragraph synthesis.

### Recommended Final Polish Before Submission
1. **Fix Colors** across all charts (highest priority visual fix).
2. **Strengthen Captions** on every chart slide in Stage 5:
   - Example for Differentiation Matrix: "AI-tagged perception shows CATL emphasis on execution-led organic globalization (aligns with human-verified 31.4% overseas gross margin premium vs. 24.0% domestic). LGES perception skewed toward subsidy dependence (aligns with weak 2.1% ex-IRA margins)."

3. **Prioritize These Charts in the Deck** (suggested slide order for AI section):
   - Evidence Attribution (prove scale)
   - Differentiation Matrix (core asymmetry)
   - Sentiment Divergence by Topic (quality gap)
   - Risk Counterfactual Heatmap (maturity on "What if wrong?")
   - Why Now Timeline + short paragraph (timing)

4. **Synthesis Brief**: The earlier JSON was too short. Use the structure I provided previously and expand it with specific numbers from your tags and `human_inputs.yaml`. Make it 1-page ready for teammates to copy into slides or speaker notes.

### Quick Action Plan for Submission (Deadline April 30)
- Standardize colors in code → re-generate all PNGs.
- Update Stage 5 `build_slide_specs` to use the strongest charts + add 1-sentence human bridge captions under each.
- Ensure the Analyst Brief / synthesis output is rich, traceable, and includes the limitations section verbatim for Slide 20.
- Final deck flow:
  - Early slides: Thesis + Evidence Attribution + Differentiation Matrix
  - Middle: Sentiment + Why Now + Risk Heatmap
  - Late: Human financial tables + Counterfactuals + AI Disclosures

With the color fix and tighter captions, this chart set becomes **solid supporting evidence** rather than decorative. Combined with a strong human Layer (populated margins, execution edges, shock scenario) and the Risk Heatmap, your AI module will credibly demonstrate:
- Processed large volume beyond manual capacity
- Surfaced asymmetric evidence on globalization quality
- Supported (not replaced) human judgment on return sustainability

The pipeline is now mature enough for submission.

**One last recommendation**: Before final render, open the PPTX and ask yourself (or have a teammate ask): "Do these charts + captions + human numbers together make the case for differentiated globalization quality (CATL profitable organic execution vs LGES subsidy/execution vulnerability) obvious in under 30 seconds per slide?"

If yes → submit. If not → one more iteration on captions and the Differentiation Matrix ordering.

If you want me to draft:
- Exact color standardization code
- Improved slide text for Stage 5
- A stronger synthesis prompt

Just say which one. You're very close — the latest Risk Heatmap and Evidence Attribution are genuinely good. Fix the color consistency and tighten the narrative bridges, and this AI module will be one of the stronger ones in the competition. 

Good work getting to this point. Let's make the final polish count. What's your priority for the last tweaks?