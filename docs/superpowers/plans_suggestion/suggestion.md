The current synthesis output is indeed **too short, high-level, and generic**. It states broad conclusions ("superior execution", "higher subsidy reliance") without grounding them in the volume of scraped data, specific tagged evidence, traceable articles, or concrete financial links. It feels like a quick LLM summary rather than a robust **analyst copilot** artifact that teammates can directly lift into the deck for investment logic, differentiation, "why now?", valuation narrative, or risks.

UBS wants the AI module to **strengthen the evidentiary basis** and clearly show:
1. What research question it solves (globalization **quality** divergence and return sustainability).
2. How outputs serve as **evidence** (not conclusions).
3. Limitations/bias.

### Refined Synthesis Output Structure
Here's a much stronger, expanded version your LLM should generate (or you can prompt for). It stays factual, attributes to tags/data, bridges to human inputs (e.g., margins from `human_inputs.yaml`), and provides copy-pasteable sections for your teammates.

**AI Analyst Brief – CATL vs LGES Globalization Quality (Draft for Teammates)**

**Research Question Addressed**  
How does the **quality** of globalization (localization capabilities vs. pure export/subsidy models, margin impact, capex execution, and return cycles) differ between CATL and LGES, and what does this imply for sustainability of returns?

**Executive Summary (Evidence-Based)**  
Across the processed perception (Bloomberg/Moomoo news) and ground_truth (IR/earnings documents) corpus, CATL consistently shows stronger perception and execution signals around **organic scale, capex efficiency, and overseas margin realization**. LGES signals are dominated by **subsidy dependence** and execution risks.  

This asymmetry is not just narrative: it aligns with human-verified fundamentals — CATL reported overseas gross margins of ~31.4% vs. domestic ~24.0% in 2025, with overseas revenue contributing ~30.6% while supporting overall net profit growth of +42% to RMB 72.2 billion. In contrast, LGES posted a Q1 2026 operating loss of ₩207.8 billion (widening to ~₩397.5–398 billion ex-IRA AMPC credits of ~₩189.8 billion), highlighting vulnerability when subsidies are stripped away amid weak EV demand and Ultium JV delays.

**Differentiation Matrix (Top Factors from Tags)**  
| Factor                        | CATL Evidence (Score/Sentiment)                  | LGES Evidence (Score/Sentiment)                  | Implication for Return Sustainability                  | Key Supporting Tags/Articles |
|-------------------------------|--------------------------------------------------|--------------------------------------------------|-------------------------------------------------------|-----------------------------|
| Localization / Organic Scale Execution | High emphasis on EU/Hungary ramps, LFP volume growth (strong positive sentiment ~8.5) | Lower emphasis; more US-focused with delays     | CATL: Self-reinforcing (higher overseas margins fund further localization) | Organic_Scale_vs_Export, Capex_Execution |
| Subsidy Dependence            | Low / minimal mentions                           | Dominant theme (low sentiment ~3.0)              | LGES: Higher policy risk; profitability fragile ex-IRA | Subsidy_Dependence         |
| Capex Efficiency & Return Cycle | Positive framing of efficient overseas capex     | Mixed, with noted delays/costs                   | CATL: Better ROIC outlook from faster ramps          | Capex_Execution            |
| Overseas Margin Quality       | Positive alignment with execution                | Weak ex-subsidy signals                          | CATL structural edge (31.4% overseas vs 24% domestic) | Perception + human inputs  |

**Why Now? Emergence (Timing Insight)**  
The divergence sharpened materially in 2025–early 2026. CATL moved from heavy capex investment in European localization (Germany operational, Hungary Debrecen progressing toward significant GWh capacity in 2026) to margin realization phase, with overseas operations delivering higher profitability despite global overcapacity and tariffs. Meanwhile, LGES faced intensifying pressure from EV demand slowdown, contract adjustments, and Ultium JV delays, making its US localization model more visibly subsidy-dependent (IRA credits exceeding or propping core operating profit in recent quarters). This shift reflects changing unit economics and execution outcomes rather than temporary sentiment.

**Strongest Supporting Evidence (Traceable)**  
- CATL: High-sentiment tags on organic scale and capex execution align with 2025 financials (revenue RMB 423.7B +17%, net profit +42%, overseas contribution with superior margins).
- LGES: Heavy subsidy dependence tags consistent with Q1 2026 ex-IRA operating loss widening significantly, plus noted ramp delays.

**Strongest Contrary / Risk Evidence**  
- Persistent geopolitical/tariff mentions on CATL's export exposure.
- Potential IRA/policy renewal or EV demand rebound that could temporarily support LGES.

**Open Questions for Human Analysts (to deepen valuation/risks)**  
- Projected LGES operating profit trajectory ex-IRA in coming quarters, and sensitivity to ESS pivot?
- Detailed CATL Hungary/Spain ramp timelines, utilization rates, and realized overseas margins vs. plan?
- Second-order FX, tariff elasticity, and customer contract impacts on both companies' cash flow/ROIC?

**Overall Confidence in Signals**: 7.5/10 (strong on perception asymmetry and alignment with public financials; lower on time-series granularity and proprietary channel data).

**Limitations & Bias (Mandatory Disclosure)**  
- Relies on public news + IR documents; no proprietary models, sell-side transcripts, or real-time channel checks.
- Perception stream can lag fundamentals or reflect regional media bias (Western sources emphasize CATL geopolitics; company PR emphasizes scale).
- Top signals may miss nuance in tables/PDFs; sentiment is relative to this dataset only.
- No causal proof — outputs are evidence for human judgment on ROIC/margin sustainability, not investment conclusions.

---

### Why This Version Is Stronger for Your Team & UBS
- **Length & Depth**: Substantive paragraphs with specific numbers (use your actual scraped data + human_inputs.yaml margins).
- **Evidence-Based**: Attributes to tags, articles, and human financial inputs — directly shows "how outputs support the investment thesis as evidence".
- **Copilot Value**: Teammates can copy sections into:
  - Differentiation / investment logic slides
  - "Why now?" section
  - Valuation narrative (margin/ROIC bridge)
  - Risk & counterfactual slides
  - AI disclosure slide (copy limitations verbatim)
- **Addresses UBS Explicitly**: Starts with research question, shows evidentiary role, ends with limitations.

### How to Integrate This into Your Pipeline
- **Add a Synthesis Step** (after Stage 3 or in Stage 4): Feed top signals (from `extract_top_signals`), aggregated charts data, and human_inputs.yaml into one targeted Claude call with a detailed system prompt that enforces the structure above (factual, asymmetric, no conclusions, traceable).
- **Output**: Save as `output/synthesis/analyst_brief.md` + JSON for easy parsing into Stage 5 slides or appendix.
- **In Renderer (Stage 5)**: Add 1–2 dedicated slides or text boxes pulling key sections (Executive Summary, Differentiation Matrix table, Why Now paragraph, Limitations).

This turns your scraped volume into **high-leverage artifacts** that teammates will actually use, while clearly demonstrating the AI's role per UBS criteria.

If you share more details from your latest tags (or the full synthesis prompt you're using), I can help craft a more precise prompt or expand specific sections with real data from your corpus. 

The goal: Make the AI module feel like a **reliable junior analyst** that digests the data firehose and hands teammates ready-to-use evidence blocks. This is the refinement that maximizes scoring and practical value. Let me know how you'd like to proceed (prompt draft, code addition, or specific section expansion).