SWING REVIEW DESK — LOCAL DATA HELPER
====================================

WHAT IT DOES
This desk imports Chartink scanner CSV exports, merges duplicate tickers, fetches historical daily candles via the local Python helper, and lets you mark stocks Keep / Skip / Later. It uses TradingView Lightweight Charts and is not a live market feed.

FIRST-TIME SETUP
1. Extract this whole ZIP into a normal folder, for example Desktop\SwingReviewDeskLocal.
2. You need Python 3.10 or newer. If it is not installed, download it from:
   https://www.python.org/downloads/windows/
   During installation, enable “Add Python to PATH” if that option appears.
3. Double-click start_swing_review.bat.
4. The first run installs the yfinance Python package. Allow it to finish. It needs an internet connection.
5. A browser tab should open at http://127.0.0.1:8765.
6. Import your Chartink scanner CSV files and review the stocks.
7. Keep the black Command Prompt window open while using the desk. Close it or press Ctrl+C there when finished.

RECENT FEATURES
- EMA 10, EMA 20, EMA 50 and EMA 200, drawn as thin 1-pixel lines, with separate color controls under Chart appearance.
- Start/end date selectors above the chart request the exact selected daily history range (end date inclusive); the chosen range is saved in the same browser. EMA 200 is calculated from the candles returned for that range, so for the most accurate EMA at the start of a review period, include at least 200 earlier trading sessions in the start date.
- Alt+R or the “Reset view” button fits the chart to all loaded candles and restores automatic price scaling.
- My Watchlist can save current tickers and manually added symbols. It persists in the same browser using local storage. Use symbols like RELIANCE or NSE:RELIANCE; selecting a saved symbol opens it for review.
- The Scanner review list remains separate from My Watchlist. Clicking a watchlist item not already imported adds it to the current review list as a “My Watchlist” source.
- Grid lines are off by default. Candle colors and EMA colors can be changed under Chart appearance, and preferences are saved in the same browser profile and site address (http://127.0.0.1:8765). Keep opening the desk through that same address; browser storage is separate for localhost and 127.0.0.1.
- Drawing toolbar: Horizontal line (one click), Trendline and Ray (two clicks), Rectangle (two opposite corners), Fibonacci retracement and extension (two swing points), Text note (one click then enter text), and Measure (two clicks for price/percentage change). Select Cursor or press Esc to return to normal chart pan/zoom.
- Drawings are saved locally per ticker in the same browser. Use Undo to remove the most recent drawing for the selected ticker, or Clear drawings to remove all drawings for that ticker. Clearing is permanent for that browser storage.
- These are a useful starter set of custom drawing tools, not the full proprietary TradingView drawing suite; drawing editing/dragging existing objects and other advanced tools are not included yet.

IMPORTANT
- Do NOT double-click index.html directly. Launch it through start_swing_review.bat so the local data helper is active.
- This provides daily historical data, not live market data.
- The helper obtains prices from Yahoo Finance using the community yfinance Python package. Requests are serialized, spaced out, retried after transient provider failures, and successful histories are cached for 30 minutes. Yahoo can still change access, rate-limit requests, or return no data for particular symbols, so this is a workaround for browser CORS, not a guaranteed institutional data feed.
- NSE symbols are mapped to .NS; BSE symbols to .BO. If a particular listing is not present on Yahoo Finance, open the TradingView chart.
- Use market data for research and cross-check important prices against your broker/data provider.
- The chart display also needs an internet connection to load TradingView Lightweight Charts from unpkg.com.

TROUBLESHOOTING
- “Python 3 was not found”: install Python 3.10+ and run the BAT file again.
- “Cannot connect to the local data helper”: make sure the black Command Prompt window is still open, then open or refresh http://127.0.0.1:8765. Do not double-click index.html.
- “Yahoo Finance returned no daily history…”: the local helper is reachable, but Yahoo may be rate-limiting the request or may not list the ticker. Wait briefly and use Reload daily data.
- “Could not download…”: check internet and try Reload daily data. Some symbols may not be available through Yahoo Finance.
- “Address already in use”: close another copy of Swing Review Desk first, or restart the computer and try again.
- If your network blocks Yahoo Finance or Python package downloads, this approach may still fail; use a licensed market-data API.
