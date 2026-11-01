# Unsent email draft

**To:** gilad@crowdwisdomtrading.com
**Status:** draft only. The recipient is taken from the assessment PDF and has not
been independently mailbox-verified. Do not send credentials in email.

**Subject:** X sentiment and BTC price forecasting assignment — repository and results

Hello Gilad,

I have prepared the repository and a reproducible price-only evaluation. The current
branch is `feat/availability-basis-and-preflight` in
https://github.com/rajaryan1111/x-sentiment-price-predictor, with PR #14 kept open
as a draft. The package includes source archives, checksums, the normalized snapshot,
per-row predictions, metrics, report, standalone offline dashboard, outlook and SVG chart.

The price sample is Binance Vision BTCUSDT daily data (USDT quote), 2026-05-05 to
2026-10-31 UTC. It is not exact BTC-USD. The naive mean MAE is 1,824.23 USDT and
price-only mean MAE is 2,378.50 USDT. No real X posts were accepted or scored, so
the sentiment model's contribution cannot be measured. One bounded Tavily finance
search returned five results without publication dates; Exa is implemented but was
not live-verified because no key is configured.

Could you please clarify the following so I can close the remaining assessment
requirements?

1. Can I use the included BTCUSDT (USDT quote) market sample, or do you require an
   exact BTC-USD source? Coinbase's current terms prohibit ML evaluation and
   redistribution of derived analytics without written permission.
2. Can you provide an approved, rights-cleared 180-day X export, or approve a
   specific Apify Actor/plan, query modes, terms and maximum item/USD spend? The
   currently configured Actor is not available over API on the account's Free plan.
3. Is Exa mandatory in addition to Tavily? If so, please provide an approved key
   route and credit cap.
4. Please confirm the n+0 issue/target convention and the calendar due date; the
   PDF gives both “within 1 week” and “5–7 days.”
5. If provider credentials need to be shared, please provide a verified secure
   private channel. I will not send tokens in plaintext email or include them in the
   repository/package.

The Binance Vision data and derived artifacts are licensed CC BY-NC-SA 4.0,
attributed in the report folder, and non-commercial only. I have not sent this email
or submitted the assignment externally.

Regards,

Raj
