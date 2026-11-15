# Independent evidence and disagreement review

Retained review: workspace outputs/phase3-independent-imaf/review.html and
 demo/scenarios.json. The pure evaluator recomputes supplied anchors using raw
closed/received synthetic candles; it imports no Trading detection implementation.

Bullish fixture derives entry 106, stop 98, opposing session target 150. Mirrored
bearish derives 144/152/100. These are synthetic tick prices, not market signals.
Both research subsets pass but return REVIEW_REQUIRED because full IMAF is
INCOMPLETE. Midpoint location alone cannot prove higher-timeframe directional bias.

Adversarial case keeps platform displacement=true but changes candle 6 open to 117.
The independently calculated body is 1 against range 17, below the pinned research
body/range requirement. Result NON_COMPLIANT, displacement disagreement true/false.
Every disagreement links content-addressed observations with actual candle OHLCV,
timestamp, availability, levels and rule. Other checks are separately retained;
a declared setup does not manufacture canonical transition/narrative evidence.

Further executed contradictions: sweep without close break, break without sufficient
displacement, invalid gap, unsupported mapping, altered strategy metadata and future
availability. See evaluator.test.mjs and VALIDATION.md. Existing research thresholds
are explicitly labeled research policy, not manuscript-authorized definitions.
