# Tillroll: transaction aggregator and receipt matcher

A browser prototype that pulls bank transactions, reads receipt photos with OCR, matches each receipt to its payment, and turns the receipt lines into budgets and brand reports.

Everything runs client-side. The bank feed is mocked and the receipts are synthetic.

## Run it

Serve the `site/` folder over HTTP and open it (the OCR worker will not load from `file://`):

```
cd site && python3 -m http.server 8000
```

## What is in `site/`

| File | Purpose |
|---|---|
| `index.html` | The whole app: mock Open Banking API, matching, receipt parsing, and the three views (Transactions, Budget, P&G products) |
| `cat.js` | Category rules for receipt lines, merchant category codes, and the P&G brand list |
| `data.js` | Mock accounts and transactions, plus sample receipts |
| `pg-panel.js` | Every P&G line from the full receipt spreadsheet, for the "Whole spreadsheet" scope |
| `tess/` | Tesseract.js 5.1.1, its LSTM core, and English language data, vendored so OCR works offline. `ocr-worker.js` serves the language data from `eng-traineddata.js` instead of a CDN |

## How it works

- **Bank feed:** `OpenBanking.get()` in `index.html` returns UK Open Banking Read/Write v3.1 shapes for `/accounts` and `/accounts/{id}/transactions`. Replace it with calls to a real provider.
- **Matching:** each receipt is scored out of 100 against every card payment on amount, date, merchant and card. Clear winners link automatically; the rest wait in an inbox.
- **Categorising:** a receipt line is categorised by product name, falling back to the shop's usual category from its merchant category code.
- **P&G report:** a line counts when a P&G brand name appears in the product text. The view exports the filtered lines as CSV.

## Rebuilding the data

The sample data is generated from a synthetic receipt spreadsheet (not included in this repo):

```
python3 tools/build_data.py receipts.xlsx          # writes site/data.js
python3 tools/dump_all.py receipts.xlsx all_rows.json
node tools/build_pg_panel.js all_rows.json         # writes site/pg-panel.js
```

`build_data.py` needs `openpyxl`. Supermarket receipts come from the spreadsheet; receipts for other shops are invented in the script and labelled as mock.

## Known limits

- Only tested on generated receipt images, not phone photos.
- Matches and scanned receipts are held in memory and reset on reload; budgets and category corrections are kept in `localStorage`.
- The "Re-read with Claude" and "Download CSV" buttons rely on the Claude artifact runtime and stay hidden elsewhere. "Copy CSV" works everywhere.

## Third-party

Tesseract.js and tesseract.js-core are Apache-2.0. The English language data is from the tessdata project (Apache-2.0).
