# EoS Strategy Agent: Product Innovation Ideas

**Idea #1: EoS Pulse: Pre-emptive Volatility Overlay**
*   **Market Rationale:** Based on recent macroeconomic inflation data (Current News), we identify a heightened risk of rate-driven volatility spikes across FX and short-end rates. EoS historical data suggests that during such times, portfolios heavily weighted in emerging market currencies experience significant slippage before stop-losses are triggered.
*   **Functional Feature:** A background "Pulse" indicator that constantly cross-references real-time news sentiment (via LLM) with historical PnL volatility signatures, creating an ambient heat-map over the main Position Grid for at-risk assets.
*   **Usability Impact:** Reduces cognitive load by pre-filtering news impact directly onto the trading positions, eliminating the need to manually map news events to portfolio risk.
*   **Implementation Strategy:** Implement a background task (using ARQ) to poll news and correlate with historical VaR. Create a new Artifact Mutation that updates the `PositionGrid` rows with a subtle warning color gradient based on the "Pulse" score via WebSocket streaming.

**Idea #2: Ad-Hoc `/risk-impact` Scenario Explorer**
*   **Market Rationale:** Based on sudden geopolitical escalations (Current News), we identify liquidity evaporation risks in commodity markets. EoS historical data suggests that during such times, manual scenario analysis is too slow, leading to missed hedging opportunities and increased drawdowns.
*   **Functional Feature:** A new conversational ad-hoc command (`/risk-impact [event]`) in the AI Agent panel that instantly generates a transient stress-test artifact, projecting the PnL impact of the event across all active books.
*   **Usability Impact:** Empowers traders with instant, command-first complex analysis without needing to navigate complex risk modeling forms.
*   **Implementation Strategy:** Add an LLM intent in the backend agent orchestrator to parse `/risk-impact` commands, trigger a mock stress-test via `financial_api.py`, and return a new `RiskGauge` or `PnLWaterfall` transient Artifact via the Panels System.

**Idea #3: Smart Slippage Guardrails (Contextual Stops)**
*   **Market Rationale:** Based on central bank surprise announcements (Current News), we identify periods of extreme cross-asset correlation breakdowns. EoS historical data suggests that during such times, static stop-losses fail due to widened spreads, resulting in excessive execution costs.
*   **Functional Feature:** An actionable overlay on the PnL Attribution pane that suggests dynamic adjustments to order execution logic (e.g., switching to TWAP or widening limits) when the LLM detects "correlation breakdown" themes in the Intelligence Feed.
*   **Usability Impact:** Transforms retrospective PnL analysis into proactive execution advice, closing the loop between risk identification and trade action.
*   **Implementation Strategy:** Introduce a new transient Pane view that appears alongside the `PnLWaterfall` chart. The backend strategy agent will push suggested execution parameters via the EoS Artifact-Pane architecture when specific market condition thresholds are breached.

**Idea #4: Portfolio-Specific Noise Filter (Targeted Intel)**
*   **Market Rationale:** Based on the overwhelming volume of daily earnings reports and macro releases (Current News), we identify "information overload" as a risk to trader reaction times. EoS historical data suggests that during such times, profitable alpha opportunities in non-focus assets are missed.
*   **Functional Feature:** An LLM-powered filter that explicitly ties the EoS Intelligence Feed to the trader's currently active Resource IDs (Portfolios/Desks), muting irrelevant news and highlighting high-impact events with estimated PnL variance.
*   **Usability Impact:** Drastically reduces cognitive load by ensuring that the only news presented is directly correlated with the trader's active exposure, creating a hyper-focused environment.
*   **Implementation Strategy:** Modify the EoS Agent store to pass the active `portfolio_id` alongside queries. The backend will filter the news feed and only push relevant updates to the frontend via the `ArtifactIndex`, rendered as pinned intel cards.
