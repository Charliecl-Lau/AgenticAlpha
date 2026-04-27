# Design Specification: Agent-Driven AI Analyst Module & Pitch Generator (Final)
**Date:** 2026-04-25 (Deadline: April 30, 2026)
**Project:** 2026 UBS Finance Challenge (CATL vs LGES Pair Trade)
**Core Research Question:** "How does the market's perception of globalization *quality* differ between CATL and LGES, and how does this translate to asymmetric, sustainable returns (ROIC/Margins)?"

## 1. System Architecture Overview

This agent-orchestrated evidence engine strictly separates **AI-driven perception scaling** from **human-driven fundamental causality**. It uses CLI agents for heavy lifting (ingestion and rendering) while strictly quarantining valuation conclusions to human analysts. 

**Core Tech Stack:**
* **Scraping & Ingestion:** `danielmiessler/Personal_AI_Infrastructure`
* **Signal Aggregation:** Python (Pandas, Plotly/Matplotlib)
* **Presentation Generation:** `NousResearch/hermes-agent` (PowerPoint skill)
* **LLM Processing:** GPT-4o-mini / Claude 3.5 Sonnet

---

## 2. Stage 1: Autonomous Hybrid Ingestion (Killing the Noise)

To prevent the AI from mistaking media noise (lagged headlines) for causality, the ingestion agent targets two separate streams.
* **Stream A (Perception):** Agent scrapes Bloomberg and Moomoo news URLs (last 12-24 months) to capture sentiment and narrative.
* **Stream B (Ground Truth):** Agent ingests official Investor Relations documents (Earnings Call Transcripts, Quarterly Capex Filings) to cross-verify execution realities.
* **Output:** Clean Markdown text files, separated by stream.

---

## 3. Stage 2: The Asymmetric Tagger (LLM Extraction)

The Python script passes the ingested Markdown to the LLM. The system prompt is heavily engineered to avoid "false symmetry" (e.g., treating LGES US localization and CATL European localization as identical strategies).

**JSON Schema:**
* `sentiment_score`: Integer (1-10)
* `direction`: Enum (`positive`, `negative`, `neutral`)
* `topic_cluster`: Enum (`Organic_Scale_vs_Export`, `Subsidy_Dependence`, `Geopolitical_Noise`, `Capex_Execution`, `Other`)
* `geo_exposure`: Array of Enums (`["US", "EU", "ASEAN", "LATAM", "China"]`)
* `summary`: String (Strict 1-sentence factual extraction)

---

## 4. Stage 3: The Signal Engine (Data Aggregation)

A lightweight Pandas script processes the JSONs into stark visual evidence, forcing a contrast between CATL's organic execution and LGES's policy reliance.

**Key Deliverables (Visual Charts):**
* **The Quality Divergence Matrix:** Graphs LGES "Subsidy/IRA" mention frequency vs. CATL "Volume/Capacity/Margin" mention frequency.
* **Trend Inflection (Cross-Checked):** Overlays media geopolitical panic spikes against management's actual capex guidance tone from Stream B to prove the market is mispricing headline risk.

---

## 5. Stage 4: The Human-in-the-Loop Financial Layer (The Bridge)

The AI provides the scaled perception data. The human analyst inputs the hard fundamental reality into a configuration file. **If the human inputs are shallow, the deck fails.**

**Human Input Template (Strict Enforcement):**
* **AI Signal:** "Market narrative overwhelmingly indexes LGES to IRA subsidies, while CATL indexes to LFP volume."
* **Human Input (Baseline):** [CATL reported overseas gross margin (e.g., 31.4%) vs. domestic (24%). LGES Q1 operating margin excluding IRA credits.]
* **Human Input (Shock Delta):** [Calculated basis point hit to ROIC if US EV demand slows 20% and IRA credits are capped.]
* **Human Input (Execution Edge):** [CATL Hungary/Germany ramp efficiency vs. LGES Ultium delay costs.]

---

## 6. Stage 5: Autonomous Presentation Rendering

The `hermes-agent` maps the provided content to a maximum-20-page slide deck. 

**Prohibited Behaviors (Strict Prompt Enforcement):**
* ❌ Must NOT write "we believe", "we conclude", or generate investment advice.
* ❌ Must NOT dilute human math; slides must visually prioritize human financial tables over AI word clouds.

**Mandatory Slide Logic:**
* **Slides 1-14 (Strategy, Outlook, Fundamentals):** Merges human DCF/Margin data with Top 3 AI signals. Proves that CATL's globalization is a *sustainable scale advantage*, while LGES is a *vulnerable policy arbitrage*.
* **Slides 15-18 (Probabilistic Counterfactuals):** Formats specific, return-tied risks (e.g., "X bps hit to CATL margins if EU enforces >40% retroactive local content rules"). 
* **Slides 19-20 (AI Disclosures & Limitations):** Explicitly outlines the use of agentic infrastructure. 
    * *Mandatory Disclaimer:* "The AI Analyst module was used strictly to scale the processing of unstructured perception data beyond manual capacity. It did NOT build valuation models, conduct channel checks, or generate fundamental forecasts. The AI surfaces narrative divergence; human analysts verified the sustainability of returns."
