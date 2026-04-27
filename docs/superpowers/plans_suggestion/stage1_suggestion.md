1. Strengths (What Actually Helps Alignment with UBS Theme)

Hybrid streams explicitly separate market perception (news sentiment on localization/export, policy risk, subsidies) from fundamentals (IR docs on actual overseas margins, capex cycles, ROIC drivers, shipment volumes). This is crucial for the core research question on "globalization quality" — e.g., does localization deliver sustainable higher margins/ROIC, or is it subsidy-dependent execution risk?
Recent real data illustrates why this matters:
CATL 2025: Revenue RMB 423.7B (+17%), net profit RMB 72.2B (+42%), overseas revenue 30.6% with gross margin 31.44% vs. domestic 24%. 661 GWh sales, 39.2% global share (Jan-Feb 2026: 42.1%), Europe plants ramping (Germany operational, Hungary Debrecen early 2026 start, Spain Stellantis JV). Overseas profitability funding expansion despite tariffs.
LGES: 2025 revenue down ~7.6%, operating profit propped by IRA incentives; Q1 2026 operating loss ₩207.8B (worse ex-subsidy at ₩397.5B), revenue down, share erosion to ~8.7% globally. Heavy reliance on US subsidies amid EV demand weakness; pivoting to ESS.

Your cleaner (extract_article_text preferring <article>/<main>, stripping nav/footer/ads) and slug-based filenames with source headers improve traceability — good for Slide 19-20 disclosures.
Test-driven development (failing tests first) + mocking with responses is professional and avoids live-network CI flakiness. Skipping failed URLs gracefully prevents one paywall/403 from killing the run.
CLI + YAML config is simple and extensible — perfect for non-technical team members to update URLs without code changes.

This stage can credibly feed a "Differentiation Matrix" that contrasts news narratives (e.g., "LGES subsidy dependence" spikes) against ground-truth IR (CATL's actual overseas margin premium and capacity ramps).
2. Causality & Blindspot Risks Still Lurk in Execution
Even with hybrid data, the pipeline as specified risks perception-heavy bias if ground_truth URLs are sparse or poorly chosen:

Bloomberg/Moomoo articles are still lagged, headline-driven, and regionally biased (Western sources hammer CATL "geopolitical risk"; Chinese/ company PR push scale wins).
IR pages (e.g., your sample https://www.catl.com/en/news/661.html or LGES investor page) often contain earnings releases, but raw HTML may include boilerplate, tables, or PDFs that your current BeautifulSoup + markdownify won't fully handle well (tables can become messy Markdown; PDFs would require separate handling like pdfminer or pymupdf, which aren't in requirements).
Geopolitical asymmetry: The tagger (downstream) will still see CATL localization as "pragmatic scale-driven" in IR but "risky state-backed" in news. Without explicit company tagging and later human review in the financial layer, the Signal Engine may produce false symmetry on "Localization_vs_Export" or "Geopolitical_and_Policy_Risk".

Failure mode: If ground_truth ingestion yields mostly PR-fluff Markdown while perception floods with tariff headlines, your Top 3 signals will over-weight media noise. Judges will ask in Q&A: "How does this prove sustainable return differentiation (higher overseas margins? ROIC improvement? execution on capex cycles) vs. just perception divergence?"
3. Technical Single Points of Failure in the Current Plan

Boilerplate & site-specific fragility: html_to_markdown strips common selectors (nav, footer, .ad, cookie banners) — decent for generic pages, but Bloomberg/Moomoo have dynamic paywalls, infinite scrolls, or anti-bot measures. Your User-Agent is polite but may still get blocked or served lite versions. Real-world runs often need Selenium/Playwright for JS-heavy sites (not in stack). Test with actual sample URLs before committing.
No PDF handling: Many IR "documents" (earnings PDFs, annual reports) aren't clean HTML. Your pipeline will fail or produce garbage on them. Add fallback detection (if content-type PDF or URL ends .pdf) or expand stack.
Rate limiting / ethics / compliance: Sequential requests with no delays/backoff risks IP bans or legal issues scraping Bloomberg (terms often prohibit). Add time.sleep(random.uniform(1,3)) or exponential backoff. For UBS submission, document this as a limitation (Slide 20: "AI ingestion respects robots.txt where possible but cannot replace proprietary data terminals").
Output organization: Files dumped flat in data/raw/perception/ and ground_truth/. For 50+ articles, this becomes unmanageable. Consider subdirs by company/date or a manifest JSON with metadata.
Validation gaps: Config test checks company field, but no URL validation (e.g., schema for http/https). Pipeline doesn't dedup identical URLs across streams.
Logging & observability: Basic logger.warning on failures is ok, but no summary report (e.g., "Ingested 12/15 perception articles; 3 skipped due to 403/timeout").
Dependencies: kaleido for Plotly static exports and python-pptx are in requirements but unused in Stage 1 — fine for future stages, but bloat.

The TDD approach is good, but the tests are toy examples. Real robustness requires testing against actual Bloomberg paywall snippets, LGES IR tables, and CATL earnings HTML.
4. "So What?" for UBS Submission & Downstream Pipeline
This Stage 1 is foundational. If it works, it enables:

Tagger to produce cleaner JSON on perception (sentiment on subsidies vs. scale) vs. ground_truth (actual margin deltas, capex payback).
Signal Engine charts showing "Why Now?" (e.g., subsidy mention spikes in news coinciding with LGES Q1 2026 loss ex-IRA; CATL overseas margin stability in IR).
Human Layer to input verifiable sensitivities (e.g., "CATL: +7.44pp overseas margin premium funds localization without cash strain").
Counterfactuals grounded in data (e.g., "If EU tariffs >40%, CATL Hungary ramp mitigates X bps vs. pure export").

But: Without strong ground_truth volume, the module risks being 80% perception clustering — exactly the shallow "AI hype" that gets low scores on research judgment. Judges expect AI to support (not drive) the pair trade logic on globalization quality (scale/cost advantages, margin sustainability, not subsidy dependence).
Brutal Recommendations to Harden Before Proceeding to Tagger/Signal

Expand ground_truth aggressively: Include CATL/LGES latest earnings releases, annual reports, capacity announcements, and factory updates (e.g., Hungary Debrecen ramp). Prioritize pages with numbers (margins, GWh, ROIC proxies).
Add PDF support or note limitation explicitly. Consider pypdf or external tool integration.
Enhance robustness: Add retry logic (3 attempts), random delays, and a post-ingestion summary log/JSON manifest.
Test with real data now: Run the CLI against your sample urls.yaml (update with live 2025-2026 earnings URLs). Inspect output Markdown for cleanliness — especially tables and financial sections.
Document limitations early: In any deck prototype, call out: "Hybrid ingestion scales unstructured + structured sources beyond manual review but cannot access paywalled terminals, real-time transcripts, or proprietary models. Perception data lags fundamentals."
Next-stage tie-in: Ensure filenames/metadata preserve company + date for easy grouping in Pandas aggregation.

This Stage 1 plan is executable and a step up from v1. Implement the tasks as written (TDD is solid discipline), but immediately smoke-test with 5-10 real URLs (mix news + IR). If the Markdown outputs are noisy or incomplete, the downstream tagger will amplify errors.