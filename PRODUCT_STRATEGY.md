# EoS Product Strategy: Pragmatic Alpha Feature Ideas

Based on the daily cross-correlation analysis of the EoS Intelligence Feed, Performance Analytics, and Real-Time Market Data, the following 4 feature ideas have been developed using the C.I.E. Framework (Creative, Implementable, EoS-Centric).

## Idea #1: Contextual News-to-Exposure Heatmap

**Market Rationale:** Based on the current news cycle featuring "Fed signals potential rate cut amid inflation concerns" and "Yield curve inversion deepens," we identify significant duration and spread risk in the Rates and Credit desks. EoS historical PnL data suggests that during such times, the `UST Buried` and `IG Corp` books experience heightened volatility and potential drawdowns due to rapid spread adjustments.

**Functional Feature:** A dynamic, floating Heatmap Artifact that overlays current news keywords (e.g., "Fed", "Yield Curve") directly onto the active portfolio's positions. It automatically highlights positions (like `US0010Y` or `LQD`) whose historical PnL negatively correlates with these specific macroeconomic triggers, calculating a real-time "News Exposure Score."

**Usability Impact:** Removes the cognitive load of manually cross-referencing between the news feed and the position grid. Traders immediately see which specific instruments in their active Resource IDs (Portfolios) are mathematically most sensitive to the breaking headlines, allowing for instant hedging decisions.

**Implementation Strategy:** Add a new `bq.get_news_exposure` function to `context_injector.py` that correlates the output of `mock_news()` with `mock_positions()`. The orchestrator agent will call this and pass the data to the CodeExecutorAgent, generating a `chart` Artifact (specifically a heatmap or color-coded table) displayed in an `ArtifactWindow` which the user can pin to the `TabBar`.

---

## Idea #2: Ad-Hoc Stress Test Command (`/risk-impact`)

**Market Rationale:** Based on news that "Oil prices surge on supply disruption fears" and "Volatility spikes in FX markets," we identify a risk of correlated shocks across Commodities and EM Spot FX. EoS historical data suggests that during such liquidity-tightening events, cross-asset correlations break down, leading to unexpected slippage in supposedly unrelated books.

**Functional Feature:** A new terminal command, `/risk-impact [event]`, which instantly runs a historical scenario analysis. For example, `/risk-impact "Oil Supply Shock"`. It finds the nearest historical match to the event, applies those market moves to the current `mock_positions()`, and outputs a simulated PnL impact summary.

**Usability Impact:** Automates complex, multi-step risk analysis into a single, command-first interaction. It empowers the trader to quantify headline risk in seconds without leaving the terminal or manually configuring a scenario engine.

**Implementation Strategy:** Introduce a new explicit intent in the agent orchestrator (or a direct command parser in the backend). This will trigger a backend service that fetches historical OHLCV data for the event period, calculates percentage moves, applies them to current positions, and generates a `table` Artifact showing projected P&L changes by desk and book.

---

## Idea #3: "Pulse" Drawdown Warning System

**Market Rationale:** Based on current market conditions showing "Liquidity conditions tighten in short-term funding markets," we identify execution risk and widened bid-ask spreads. EoS historical data suggests that during such times, active high-frequency trading strategies suffer from accumulated slippage leading to silent, incremental drawdowns.

**Functional Feature:** A background "Pulse" indicator that continuously runs correlation checks between current market metrics (volatility/liquidity) and historical periods of similar conditions where the current portfolio experienced a drawdown. When the correlation threshold is breached, a transient warning indicator appears in the active panel.

**Usability Impact:** Transforms risk management from reactive to proactive. Instead of waiting for the end-of-day PnL attribution report to reveal a drawdown, the system flags the mathematical probability of a specific pattern recurring, keeping the trader focused on execution rather than monitoring background analytics.

**Implementation Strategy:** Utilize the WebSocket streaming capability (`/ws/panels/{id}`). Implement a background task (e.g., using ARQ as mentioned in the README roadmap) that periodically compares real-time data against historical PnL vectors. When a match is found, push a specific `warning` payload via the active WebSocket connection to trigger a transient visual update in the frontend UI.

---

## Idea #4: AI-Filtered, Portfolio-Specific Intelligence Feed

**Market Rationale:** Based on the high volume of daily macroeconomic news (e.g., ECB policy, German manufacturing, central bank shifts), we identify a risk of information overload. EoS historical data suggests that during high-news-flow days, traders miss granular, instrument-specific events because they are drowned out by macro headlines, leading to missed alpha opportunities.

**Functional Feature:** An LLM-driven filtering mechanism that intercepts the `mock_news()` stream and cross-references it *only* with the instruments currently held in the user's active `mock_positions()`. It generates a concise, bulleted summary of only the news that directly impacts the trader's active risk.

**Usability Impact:** Drastically reduces cognitive load. The trader no longer has to scan a generic news feed. The system acts as a personalized analyst, delivering only "Pragmatic Alpha"—actionable intelligence directly relevant to their specific book.

**Implementation Strategy:** Modify the agent orchestration flow. Create a specific prompt template that takes the user's current positions (from `bq.mock_positions`) and the raw news feed (from `bq.mock_news`) as inputs. The GROQ/Gemini agent will filter and summarize the news. Output this as a `text` Artifact (Markdown content) in a dedicated, pinnable Intelligence panel.