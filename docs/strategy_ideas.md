# EoS Strategy: Pragmatic Alpha Feature Ideas

**Role:** Lead Product Strategist for EoS
**Objective:** Transform market volatility and internal performance data into a competitive advantage using the C.I.E. Framework (Creative, Implementable, EoS-Centric).

---

### Idea #1: Contextual Portfolio News Filtering
**Market Rationale:** Based on sudden geopolitical escalations in energy-producing regions, we identify extreme volatility risk in energy-heavy and cross-correlated asset portfolios. EoS historical data suggests that during such times, traders experience execution slippage due to the sheer volume of unfiltered news delaying their reaction time.
**Functional Feature:** A background LLM agent that continuously cross-references the EoS Intelligence Feed with a trader's active Resource IDs (Portfolios), filtering out noise and surfacing only the news that directly impacts their current positions.
**Usability Impact:** Radically reduces cognitive load. Removes the need for manual cross-referencing between generic news tabs and risk panes, allowing traders to focus instantly on actionable intelligence.
**Implementation Strategy:** Add a new backend `bq.get_relevant_news(portfolio_id)` function in `context_injector.py`. This uses the LLM to filter news against active positions and generates a `text` artifact that can be pinned as a Tab in the EoS header via the Panels system.

### Idea #2: Drawdown Signature Pulse
**Market Rationale:** Based on unexpected central bank rate shifts, we identify a rapid yield curve inversion risk. EoS historical data suggests that during such times, fixed-income strategies face severe drawdowns if duration adjustments aren't executed within a narrow 2-hour window.
**Functional Feature:** A background "Pulse" indicator that constantly compares real-time market data against historical PnL drawdown signatures, flashing a subtle, non-intrusive warning on affected portfolios when a known dangerous pattern begins to form.
**Usability Impact:** Transforms reactive risk management into proactive mitigation. It flags high-probability drawdown patterns *before* they recur, without cluttering the screen or interrupting the primary TUI workflow.
**Implementation Strategy:** Create a backend background process that periodically evaluates market conditions against historical PnL drops. Push alerts via WebSocket (`/ws/panels/{id}`) to trigger a subtle visual state change (e.g., a glowing border) on the active `ArtifactWindow` or `TabBar`.

### Idea #3: The /risk-impact Ad-Hoc Command
**Market Rationale:** Based on abrupt regulatory announcements affecting key sectors, we identify a severe cross-asset correlation shock. EoS historical data suggests that during such times, standard end-of-day VaR metrics severely underestimate the immediate ripple effect across related derivatives.
**Functional Feature:** A new ad-hoc command (`/risk-impact [event]`) entered directly into the EoS terminal that instantly runs a targeted stress test across the current portfolio based on the parameters of the specified event.
**Usability Impact:** Command-First Efficiency. Automates complex, multi-step scenario analysis into a single keystroke, allowing traders to instantly visualize the PnL blast radius of breaking news.
**Implementation Strategy:** Extend the GROQ/Gemini agent prompts in `app/services/agent_service.py` to recognize the `/risk-impact` intent. Use `code_executor.py` to calculate the simulated PnL shock and output a new `chart` artifact (e.g., a PnL Waterfall) rendered in a floating `ArtifactWindow`.

### Idea #4: Slippage Heatmap Overlay
**Market Rationale:** Based on highly anticipated macro-economic data releases (e.g., Non-Farm Payrolls), we identify a high probability of pre-announcement liquidity voids. EoS historical data suggests that during such times, execution slippage increases by up to 40% due to violently widening bid-ask spreads.
**Functional Feature:** A dynamic "Liquidity Void" heatmap overlay seamlessly integrated into the standard price chart, highlighting periods of dangerously low order book depth relative to historical norms.
**Usability Impact:** Solves an immediate high-stakes execution problem by preventing traders from blindly firing large orders into thin markets. It visually integrates execution risk directly into the price chart, maintaining EoS's aesthetic sophistication.
**Implementation Strategy:** Modify the mock data generators in `context_injector.py` to include liquidity density metrics alongside OHLCV data. Update the TradingView lightweight-charts wrapper in `GenericChart.svelte` to overlay a custom series or background color bands representing the liquidity heatmap.
