// Builds site/pg-panel.js: every Procter & Gamble line in the whole spreadsheet.
// Usage: python3 tools/dump_all.py <receipts.xlsx> all_rows.json && node tools/build_pg_panel.js all_rows.json
require("../site/cat.js");
const fs = require("fs"), path = require("path");
const rows = JSON.parse(fs.readFileSync(process.argv[2], "utf8")), C = globalThis.TillCat;
const pg = [], den = {}, seen = {};
rows.forEach(r => {
  const k = r[4].slice(0, 7) + "|" + r[2]; den[k] = den[k] || [0, 0];
  if (!seen[r[1]]) { seen[r[1]] = 1; den[k][1]++; }
  if (["household", "toiletries", "health"].includes(C.categorise(r[5]))) den[k][0] += r[9];
  if (C.brandOf(r[5])) pg.push(r);
});
const out = { shoppers: new Set(rows.map(r => r[0])).size, receipts: Object.keys(seen).length, lines: rows.length, rows: pg,
  denom: Object.entries(den).map(([k, v]) => [...k.split("|"), +v[0].toFixed(2), v[1]]) };
fs.writeFileSync(path.join(__dirname, "../site/pg-panel.js"), "window.TILL_PG_PANEL=" + JSON.stringify(out) + ";");
console.log(pg.length, "P&G lines of", rows.length);
