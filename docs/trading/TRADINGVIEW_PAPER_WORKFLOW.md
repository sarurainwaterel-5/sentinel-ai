# First testing ground: TradingView Paper Trading

Owner direction, November 15, 2026: begin with TradingView Paper Trading. The first
Sentinel increment is **manual evidence capture and offline advisory review**.
There is no TradingView login, broker connection, data scraping, webhook, order
submission or order modification in this implementation.

## Operator workflow

1. In TradingView Supercharts, use **Paper Trading** as the testing account. Record
   a local account alias, the account/reset epoch, capture time and timezone. Keep
   real brokerage accounts outside this exercise. Sentinel does not connect or
   place a demonstration trade for you.
2. Use the paper account manager's download/export function. TradingView documents
   separate tabs for Positions, Orders, History, Account history and Trading
   journal; export the relevant tabs separately and retain originals. A history
   export alone does not prove current open positions or working orders.
3. Save exports in an owned local folder outside Git. Record which tab each file
   represents, its coverage, whether the account was reset, the instrument's exact
   contract and price/money units, commission/slippage settings and observed data
   delay. Do not send account passwords, browser cookies or API keys.
4. Capture the CSVs locally with the command below. This preserves exact bytes,
   hashes and CSV framing counts in a private evidence bundle. It does **not**
   infer fills, trade counts, flat positions, risk compliance or an authenticated
   market source. Row count is not trade count.
5. The first real export needs a reviewed schema/mapping against actual headers,
   clock/units and coverage. The normalized oversight snapshot is a distinct closed
   contract; a TradingView CSV is not silently relabeled as that snapshot. Until
   mapping is implemented, the capture manifest states `NOT_IMPLEMENTED`, position
   UNKNOWN, account risk UNVERIFIED and source unauthenticated.
6. Use the synthetic normalized snapshot to inspect the advisory report today.
   Supply an actual normalized artifact only after a separate reviewed mapping and
   independently configured account/policy expectations. Review accept/reject/defer
   applies only to the exact advisory artifact and cannot authorize trading.

From `backend`, using the project's Python environment (shown as `python`):

```sh
python -m evaluation.trading_oversight.tradingview capture \
  --input /absolute/private/history.csv --tab HISTORY \
  --input /absolute/private/positions.csv --tab POSITIONS \
  --organization-id default --account-id rain-tv-paper \
  --captured-at 2026-11-15T16:00:00.000Z \
  --output-dir /absolute/private/NEW-paper-evidence
```

Evidence manifest v0.2 records a tab label for each input. If `--tab` is supplied,
provide one label per input in matching order: `POSITIONS`, `ORDERS`, `HISTORY`,
`ACCOUNT_HISTORY`, `TRADING_JOURNAL` or `UNKNOWN`. Omission records `UNKNOWN`.
Labels are operator assertions, not inferred or verified from CSV contents.
Coverage stays UNKNOWN and semantic mapping stays NOT_IMPLEMENTED regardless of
the label. Earlier v0.1 artifacts remain historical evidence; they are not rewritten.

The timestamp and account alias above are examples to replace with actual capture
labels. The output parent must exist; the final directory must not exist. Inputs
are regular local UTF-8 CSV files, not URLs or symlinks. Up to eight unique files,
one MiB per file and four MiB total, bounded rows/columns. These are local
conformance limits, not TradingView platform limits. The original bytes are copied
without spreadsheet evaluation; no CSV value is executed. Credential-shaped
headers and malformed framing reject before output creation.

## Run the synthetic oversight demonstration

```sh
python -m evaluation.trading_oversight.cli inspect \
  --input evaluation/trading_oversight/fixtures/snapshot.json \
  --expectations evaluation/trading_oversight/fixtures/expectations.json \
  --now 2026-11-15T12:00:00.000Z \
  --output-dir /absolute/private/NEW-oversight-demo
```

The fixture is synthetic, not a TradingView account export or real market history.
Its policy digests are synthetic identifiers. A blocked advisory report is the
expected result: IMAF definitions, source authenticity, strategy reconstruction
and actual account-risk configuration remain unverified. This does not represent
an approved TradingView trade, current platform health or account activation.

To record an explicit human decision on the generated report:

```sh
python -m evaluation.trading_oversight.cli review \
  --report-dir /absolute/private/NEW-oversight-demo \
  --decision accept --reviewer Rain --at 2026-11-15T16:05:00.000Z
```

Use the actual reviewed-at time and decision (`accept`, `reject` or `defer`). This
command requires an explicit reviewer identity but does not authenticate a remote
person. It writes one exclusive receipt bound to the exact report hashes; no
receipt is created automatically and no execution authority follows from it.

## Keep the two paper environments distinct

TradingView's paper account is the first human testing ground. Sentinel Trading
AI's existing PostgreSQL/OHLC paper engine is a separate local research system.
Its one-MNQ/$50-risk/$100-loss research configuration is not proof of the selected
TradingView account's instrument settings, protection, costs or risk enforcement.
Existing IMAF entry locks in Sentinel Trading AI remain intact. Manual paper
activity is outside Sentinel's control and is not automatically genuine forward
validation under the engine's version-specific gate.

Paper account data, chart data, Pine strategy backtests and historical replay
results must retain distinct provenance. No export or hash establishes entitlement
to automated/non-display market data, platform identity, complete history or an
execution-capable API. A future live-data/API proposal needs separate provider
rights and a separate threat-model review.

## Official sources checked November 15, 2026

- [Paper Trading main functionality](https://www.tradingview.com/support/solutions/43000516466-paper-trading-main-functionality/): Paper Trading is a simulated-money testing environment; its connection is selected by the human in TradingView.
- [Account manager](https://www.tradingview.com/support/solutions/43000786138-what-is-the-account-manager/): account-manager tabs distinguish active positions/orders, order history, closed-position history and journal.
- [Download trading data](https://www.tradingview.com/support/solutions/43000663814-how-can-i-download-trading-data/): CSV download is available, with each selected tab exported separately.

These sources support the manual export workflow. They do not establish a
Sentinel-specific API, a licensed automated data feed or real-fill conformance.
The offline implementation does not inspect or change TradingView accounts.
A separate authorized manual browser inspection on November 15 observed the selected
paper account and settings. Its empty account view exposed no CSV export control;
no actual export or schema mapping was obtained. Private observation artifacts stay
outside Git. See [Sprint 22 status](../sprints/Sprint-22-Completion-Status.md).
