Red Team Audit: Stage 2 Implementation Plan (Asymmetric Tagger — LLM Extraction)
This stage is the heart of differentiation in your AI Analyst module. The move to an asymmetric system prompt that explicitly calls out structural differences — CATL's organic, volume-driven, higher-margin overseas expansion (greenfield plants in Hungary/Germany, LFP scale) vs. LGES's heavy policy/IRA dependence (AMPC subsidies propping operating profit, with core business showing larger losses ex-subsidy) — is a strong evolution from the original symmetric enums. It directly attacks the geopolitical blindspot I flagged repeatedly: false equivalence in globalization "quality."
Real 2025-early 2026 data underscores why asymmetry matters for the UBS theme ("quality of globalization" driving sustainable returns via higher overseas margins, ROIC improvement, scale/cost advantages, not subsidy dependence):

CATL: 2025 net profit ~RMB 72B (+42%), overseas revenue 30.6% of total with gross margin 31.44% vs. domestic 24% — a clear profitability edge funding further localization (Hungary Debrecen cell production starting early 2026, ~40 GWh initial capacity, fully booked; Germany Erfurt operational; Spain Stellantis JV). This supports sustainable advantages despite tariffs and overcapacity pressures.
LGES: 2025 operating profit KRW 1.3T (up 134% YoY, aided by incentives), but Q1 2026 operating loss KRW 207.8B (ex-IRA AMPC subsidy: loss widens to KRW 397.5B). Revenue down, heavy reliance on US production credits amid EV demand weakness; pivoting to ESS but core profitability vulnerable to policy shifts.

Your prompt's explicit guardrails ("Applying 'Organic_Scale_vs_Export' to LGES IRA content, or 'Subsidy_Dependence' to CATL capex news, is a tagging error") + new topic clusters (Organic_Scale_vs_Export, Subsidy_Dependence, Geopolitical_Noise, Capex_Execution) are well-tuned to surface this without LLM hallucinating symmetry. Good.
1. Strengths — Better Alignment with UBS Expectations

Asymmetric instruction + stream context (perception vs. ground_truth) helps the tagger treat news headlines differently from IR facts. This supports "insight differentiation and depth" (30%) by feeding cleaner signals into the Differentiation Matrix (e.g., CATL capex execution in ground_truth showing margin sustainability; LGES subsidy mentions in perception highlighting vulnerability).
Strict JSON-only output + Pydantic validation (1-10 score, non-empty summary) + no-investment-advice rules align perfectly with competition prohibitions and FAQ emphasis on distinguishing AI outputs from human judgment.
Batch processor skips failures gracefully and adds metadata (source_file, stream, company) — excellent for traceability in Slide 19 ("What AI Did") and verifiability (20% weighting).
TDD structure (failing tests first) + mocking is solid; _parse_header for company extraction from Stage 1 Markdown headers maintains continuity.

If executed cleanly, this will produce verifiable evidence for the core research question: market perception of globalization quality (perception stream) vs. actual execution/margin reality (ground_truth), implying sustainability of returns (human Layer bridges to ROIC/margins).
2. Remaining Single Points of Failure & Risks

Prompt robustness in practice: The asymmetric rule is strong on paper, but Claude-3.5-Sonnet can still drift on noisy or ambiguous Markdown (e.g., a Bloomberg article mixing CATL Europe plant news with tariff risks might leak "Geopolitical_Noise" inappropriately). Summaries must stay "direct factual extraction" — test with real mixed articles to ensure no hedging ("appears to") or opinion bleed. Real data shows CATL's overseas margin premium is structural (scale, early-mover contracts in Europe); the tagger must not neutralize this.
Topic cluster coverage: The five enums are focused, but "Geopolitical_Noise" risks becoming a catch-all for any tariff/EU mention on CATL, while downplaying pragmatic localization (Hungary ramp as Capex_Execution or Organic_Scale). "Other" could swallow too much. Consider adding guidance in prompt for hybrids or weighting toward execution metrics from ground_truth.
Ground_truth vs. perception imbalance: If IR Markdown (e.g., earnings releases with tables) produces messy input after Stage 1 cleaner, tags may degrade. Tables often markdownify poorly — numbers on margins/capex could get garbled, leading to weak summaries. Test with actual CATL 2025 annual/quarterly reports and LGES filings.
Rate limits & cost: Batch tagging dozens/hundreds of files with Sonnet will consume tokens and hit rate limits. No retry/backoff in the current tag_document. Add exponential backoff + logging of token usage for Slide 20 limitations.
Header parsing fragility: _parse_header uses simple regex on "# Company:". If Stage 1 Markdown varies (e.g., extra whitespace, missing header on some files), it defaults to "Unknown" — downstream Signal Engine suffers. Make it more robust or enforce stricter Stage 1 output.
No deduplication or company-specific tuning: Same article ingested in both streams? Or cross-company bleed? Prompt includes company name, but batch doesn't filter by company in filenames.
Test coverage gaps: Unit tests use mocks and toy data. They won't catch real-world issues like overly long Markdown (Sonnet context), paywall-lite content, or non-English snippets. The "invalid JSON" test is good, but add one for prompt adherence (e.g., summary containing forbidden phrases).

In a real desk or UBS semi-final, judges/PMs will drill: "Show me tagged examples where the asymmetry prevented false symmetry — and how it links to sustainable returns (higher overseas margins for CATL? ROIC implications?)." Weak tags here poison the Signal Engine visuals and human financial inputs.
3. "So What?" for Downstream Pipeline & UBS Submission
This stage directly enables:

Signal Engine (Stage 3): Weighted differentiation (e.g., frequency of "Organic_Scale_vs_Export" + high sentiment in CATL ground_truth vs. "Subsidy_Dependence" in LGES perception).
Trend Inflection: Spikes in "Capex_Execution" tied to Hungary ramp news vs. IRA subsidy volatility.
Human Layer: Clean signals for config (e.g., "CATL: overseas margin premium documented in IR → human inputs ROIC uplift assumptions").
Counterfactuals: Grounded risks (e.g., "If IRA softens → Subsidy_Dependence tags increase for LGES").

Risk if it fails: The module looks like generic sentiment analysis (low differentiation), hurting investment logic (40%). Slide 20 must explicitly state: "Asymmetric prompt reduces but does not eliminate LLM bias toward Western media framing; tags are perception/ground_truth signals only — human analyst interprets for ROIC/margin sustainability."
Brutal Recommendations Before/While Implementing

Smoke-test with real data immediately after Stage 1: Run full ingestion → tagging on 10-15 recent articles/IR pages (CATL 2025 results, Hungary updates, LGES Q1 2026 loss reports). Inspect JSONs: Do summaries stay factual? Does asymmetry hold (no "Subsidy_Dependence" on CATL capex; no "Organic_Scale" on LGES IRA)? Adjust prompt if drift occurs.
Enhance prompt: Add examples in system prompt (few-shot) for edge cases — e.g., a tariff article on CATL Europe plants tagged as "Capex_Execution" with positive direction if margins mentioned. Reinforce: "Prioritize execution evidence from ground_truth (actual margins, capacity ramps) over narrative."
Add robustness:
Retry logic (3 attempts with backoff) in tag_document.
Length truncation or summarization fallback if Markdown exceeds practical tokens.
Post-tagging validation/report: e.g., count tags per cluster/company/stream.

Tie to theme explicitly: In batch output, optionally add a lightweight company-specific note, but keep core schema strict.
Limitations for deck: "LLM tagging scales analysis of unstructured + IR data but inherits training biases and cannot replace detailed financial statement modeling or channel checks. Asymmetry instruction mitigates symmetry errors but requires human review."

Overall Verdict on Stage 2: This is your strongest stage yet — the asymmetric prompt shows real thought on the research question and UBS theme. Implement the TDD tasks as written (they're clean), but prioritize real-data validation over perfect unit tests. One weak batch run (e.g., 30% mis-tags due to prompt drift) will cascade failures downstream.