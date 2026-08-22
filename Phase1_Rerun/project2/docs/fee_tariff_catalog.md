# Fee evidence and tariff catalog

## Why this exists

Fees are part of spending, but they do not all have the same evidence quality.
Moneytiqx therefore stores and displays three states instead of silently
turning missing values into zero:

- **Confirmed:** reported by a provider message or reviewed by the user.
- **Estimated:** calculated from a dated, versioned public tariff band.
- **Unknown:** the source did not provide enough evidence.

The authenticated user's database records produce the dashboard totals. The
tariff catalog is a reference and calculator; it does not rewrite confirmed
historical fees.

## Current public sources

| Provider/service | Application treatment | Source |
|---|---|---|
| Airtel-to-Airtel | Published-band estimate: free | <https://www.airtelkenya.com/tariffs_charges> |
| Airtel to another network | Amount-band estimate | <https://www.airtelkenya.com/tariffs_charges> |
| Airtel agent withdrawal | Amount-band estimate | <https://www.airtelkenya.com/tariffs_charges> |
| Airtel Paybill / wallet-to-bank | Amount-band estimate; page was published 2 November 2023 | <https://airtelkenya.com/Airtel-Money-Reduces-Its-Paybill-And-Wallet-To-Bank-Charges> |
| Standard non-fuel M-PESA Buy Goods | Published customer fee is zero | <https://www.safaricom.co.ke/images/Downloads/mpesa-business-till.pdf> |
| KCB and Equity | Reference links only | <https://ke.kcbgroup.com/our-tariffs>, <https://equitygroupholdings.com/ke/images/docs/tariff-guide.pdf> |

Bank charges are not auto-estimated yet. They vary by bank, account, channel,
transaction type and sometimes tax. A made-up universal “bank fee” would be
more harmful than an honest unknown.

## API contract

All endpoints require authentication, derive ownership from the JWT, and send
`Cache-Control: private, no-store`.

- `GET /api/fees/summary` returns the current user's week/month totals,
  evidence split, provider totals and recent fee events.
- `GET /api/fees/tariffs` returns the versioned public catalog and sources.
- `POST /api/fees/estimate` accepts `provider`, `service` and `amount` and
  returns a labelled estimate.

The dashboard preview and Fees page both consume `/api/fees/summary`. Keeping
the calculation in one backend service prevents the same metric from acquiring
different meanings on different screens.

## Updating a tariff safely

1. Read the provider's official current material; do not copy an aggregator.
2. Record the URL and publication/effective date.
3. Resolve conflicts explicitly. Here, the later Airtel November 2023 Paybill
   announcement controls Paybill while the current tariff page controls
   general transfers and withdrawals.
4. Update the band table and bump `TARIFF_CATALOG_VERSION`.
5. Test both sides of every changed boundary, such as KES 100.00 and 100.01.
6. Run the backend and frontend suites, then review the mobile layout.

Tariffs are deliberately not scraped at request time. Runtime scraping would
make the financial result depend on a provider page being available and having
unchanged HTML at that exact moment. A reviewed, versioned catalog is slower to
update but reproducible and auditable.

