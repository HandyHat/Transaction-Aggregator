import sys, json, random, base64, collections, datetime as dt, openpyxl
random.seed(417)
wb = openpyxl.load_workbook(sys.argv[1], data_only=True, read_only=True)
rows = list(wb.worksheets[0].iter_rows(values_only=True))[1:]
rec = collections.OrderedDict()
for r in rows: rec.setdefault(r[1], []).append(r)
bycons = collections.defaultdict(list)
for k, v in rec.items(): bycons[v[0][0]].append(k)
city = lambda k: rec[k][0][4].split('|')[1].strip()
# household: SYN-C-0001 plus two more Newcastle-based consumers with a different main store
home = collections.Counter(city(k) for k in bycons['SYN-C-0001']).most_common(1)[0][0]
cands = []
for c, ks in bycons.items():
    if c == 'SYN-C-0001': continue
    if collections.Counter(city(k) for k in ks).most_common(1)[0][0] == home:
        cands.append((c, collections.Counter(rec[k][0][3] for k in ks).most_common(1)[0][0], len(ks)))
print(home, cands[:12])
picked = ['SYN-C-0001']; stores = {'ASDA'}
for c, s, n in sorted(cands, key=lambda x: -x[2]):
    if s not in stores and len(picked) < 3: picked.append(c); stores.add(s)
cash_c = [c for c, s, n in cands if c not in picked][0]
print(picked, cash_c)
ACC = {'debit': 'acc-4417', 'credit': 'acc-8802'}
card_of = {picked[0]: ('debit', '4417'), picked[1]: ('debit', '4417'), picked[2]: ('credit', '8802')}
DESC = {'Tesco': ('TESCO STORES %d', 5411), 'ASDA': ('ASDA SUPERSTORE %d', 5411), "Sainsbury's": ('SAINSBURYS S/MKTS %d', 5411), 'Morrisons': ('WM MORRISONS STORE %d', 5411)}
def rjson(k, card):
    v = rec[k]; h = v[0]
    return {'id': k, 'file': h[2], 'store': h[3], 'address': h[4], 'date': h[5].strftime('%Y-%m-%d'), 'time': h[12].strftime('%H:%M'),
            'total': round(h[11], 2), 'card': card,
            'items': [{'name': x[6], 'qty': x[7], 'unit': round(x[8], 2), 'promo': None if x[9] == 'None' else x[9], 'total': round(x[10], 2)} for x in sorted(v, key=lambda x: x[13])]}
receipts, txns = [], []
branch = {}
n = 0
for c in picked:
    kind, last4 = card_of[c]
    for k in bycons[c]:
        r = rjson(k, last4); receipts.append(r)
        d = dt.date.fromisoformat(r['date'])
        lag = random.choice([0, 0, 0, 1, 1, 2]); 
        b = d + dt.timedelta(days=lag)
        if b.weekday() >= 5: b += dt.timedelta(days=7 - b.weekday())
        fmt, mcc = DESC[r['store']]
        code = branch.setdefault((r['store'], r['address']), random.randint(2100, 6900))
        n += 1
        txns.append({'TransactionId': 'tx-g%03d' % n, 'AccountId': ACC[kind], 'BookingDateTime': b.isoformat() + 'T00:00:00+00:00',
            'ValueDateTime': r['date'] + 'T' + r['time'] + ':00+00:00', 'Amount': {'Amount': '%.2f' % r['total'], 'Currency': 'GBP'},
            'CreditDebitIndicator': 'Debit', 'Status': 'Booked', 'TransactionInformation': (fmt % code) + ' ' + r['address'].split('|')[1].strip().upper()[:14],
            'MerchantDetails': {'MerchantName': r['store'], 'MerchantCategoryCode': str(mcc)},
            'BankTransactionCode': {'Code': 'CustomerCardTransactions', 'SubCode': 'POS'}, '_receipt': k})
# two cash receipts with no bank transaction
cash = [rjson(k, None) for k in bycons[cash_c][:2]]
for r in cash: r['cash'] = True
receipts += cash
# non-grocery feed
def add(date, info, name, mcc, amt, acc='debit', credit=False, code=('CustomerCardTransactions', 'POS'), value=None):
    global n; n += 1
    txns.append({'TransactionId': 'tx-o%03d' % n, 'AccountId': ACC[acc], 'BookingDateTime': date.isoformat() + 'T00:00:00+00:00',
        'ValueDateTime': value or (date.isoformat() + 'T00:00:00+00:00'), 'Amount': {'Amount': '%.2f' % amt, 'Currency': 'GBP'},
        'CreditDebitIndicator': 'Credit' if credit else 'Debit', 'Status': 'Booked', 'TransactionInformation': info,
        'MerchantDetails': {'MerchantName': name, 'MerchantCategoryCode': str(mcc)} if name else None,
        'BankTransactionCode': {'Code': code[0], 'SubCode': code[1]}})
    return txns[-1]
DD = ('IssuedDirectDebits', 'DirectDebitPayment'); FP = ('ReceivedCreditTransfers', 'FasterPayment'); SO = ('IssuedCreditTransfers', 'StandingOrder')
REC = ('CustomerCardTransactions', 'RecurringPayment'); ECOM = ('CustomerCardTransactions', 'ECOM')
# mock receipts for shops the spreadsheet does not cover. Each returns (items, layout); an item is (name, qty, unit[, extra, detail])
def pick(menu, lo, hi): return [(nm, random.choice([1, 1, 1, 2]) if q else 1, p) for nm, p, q in random.sample(menu, random.randint(lo, hi))]
def g_bake(): return pick([('SAUSAGE ROLL', 1.60, 1), ('CHEESE & ONION PASTY', 2.10, 1), ('FLAT WHITE', 2.90, 1), ('ALMOND CROISSANT', 2.40, 1), ('SOURDOUGH LOAF', 3.80, 0), ('CINNAMON BUN', 2.20, 1)], 1, 3), {'qty': 'prefix'}
def g_coffee(): return pick([('FLAT WHITE', 3.10, 1), ('OAT LATTE', 3.60, 1), ('AMERICANO', 2.80, 1), ('BANANA LOAF SLICE', 2.70, 0), ('CHEESE TOASTIE', 4.90, 0)], 1, 2), {'qty': 'prefix', 'vat': True}
def g_rest():
    it = pick([('MARGHERITA PIZZA', 11.50, 0), ('RIGATONI RAGU', 13.00, 0), ('BURRATA SALAD', 8.50, 0), ('GARLIC FLATBREAD', 5.00, 0), ('TIRAMISU', 6.50, 0), ('PERONI 330ML', 4.80, 1), ('HOUSE RED 175ML', 6.20, 1), ('SPARKLING WATER', 3.00, 1)], 3, 5)
    return it, {'qty': 'prefix', 'sub': True, 'vat': True, 'total': 'TOTAL TO PAY', 'head': ['TABLE %d  COVERS 2' % random.randint(2, 24)]}
def g_pharm(): return pick([('PARACETAMOL 500MG 16S', 0.65, 1), ('IBUPROFEN 200MG 16S', 0.85, 1), ('HAYFEVER TABLETS 30S', 3.50, 0), ('PLASTERS ASSORTED 40', 2.20, 0), ('VITAMIN D 90 TABS', 4.75, 0), ('TOOTHPASTE WHITENING 75ML', 2.50, 0), ('SHAMPOO 400ML', 3.00, 0), ('LIP BALM', 1.99, 0), ('COUGH SYRUP 150ML', 4.20, 0), ('ORAL-B PRO EXPERT TOOTHPASTE 75ML', 3.25, 0), ('GILLETTE FUSION BLADES 4 PK', 11.00, 0), ('VICKS VAPORUB 50G', 4.60, 0), ('PANTENE SMOOTH AND SLEEK SHAMPOO 400ML', 3.50, 0)], 2, 4), {}
def g_fuel():
    litres = round(random.uniform(18, 38), 2); ppl = random.choice([1.439, 1.449, 1.459, 1.479]); it = [('UNLEADED PUMP %02d' % random.randint(1, 8), 1, round(litres * ppl, 2), False, '%.2f L @ %.3f/L' % (litres, ppl))]
    if random.random() < .45: it.append(random.choice([('MEAL DEAL', 1, 3.99), ('SCREENWASH 5L', 1, 4.50), ('CAR WASH', 1, 6.00)]))
    return it, {'vat': True, 'total': 'AMOUNT DUE'}
def g_parcel():
    it = pick([('USB-C CABLE 2M', 7.99, 1), ('PHONE CASE', 9.99, 0), ('LED BULB E27 4 PK', 8.49, 0), ('AA BATTERIES 12 PK', 6.99, 1), ('PAPERBACK NOVEL', 8.99, 0), ('YOGA MAT', 14.99, 0), ('KETTLE 1.7L', 22.00, 0), ('COTTON SOCKS 5 PK', 9.00, 0)], 1, 3)
    if sum(q * p for _, q, p in it) < 25: it.append(('DELIVERY', 1, 3.99, True))
    return it, {'qty': 'prefix', 'sub': True, 'total': 'ORDER TOTAL', 'head': ['ORDER PM-%d' % random.randint(100000, 999999), 'ORDER CONFIRMATION']}
def g_cinema():
    it = [('ADULT TICKET', random.choice([1, 2]), 9.50)]
    if random.random() < .5: it.append(('POPCORN LARGE', 1, 5.50))
    return it, {'qty': 'prefix', 'head': ['SCREEN %d' % random.randint(1, 9)]}
def g_metro(): return [('PAY AS YOU GO TOP-UP', 1, random.choice([5.0, 10.0, 15.0, 20.0]))], {'head': ['TICKET MACHINE %d' % random.randint(1, 6)]}
def g_hard(): return pick([('WOOD SCREWS 4X40 200PK', 4.25, 0), ('MASKING TAPE 50M', 2.75, 1), ('EMULSION PAINT 2.5L WHITE', 16.00, 0), ('PAINT ROLLER SET', 7.50, 0), ('LED BULB B22 2 PK', 5.00, 1), ('GARDEN GLOVES', 4.50, 0), ('PICTURE HOOKS 10 PK', 2.00, 1)], 1, 3), {'vat': True}
def g_cloth(): return pick([('T-SHIRT CREW WHITE', 9.00, 1), ('COTTON SOCKS 5 PK', 8.00, 0), ('SLIM JEANS INDIGO', 34.00, 0), ('ZIP HOODIE GREY', 28.00, 0)], 1, 2), {'qty': 'prefix'}
SHOPS = [('METRO TRAVEL TOP-UP', 'Metro Travel', 4111, 'debit', g_metro, 'POS'), ('CORNER BAKEHOUSE', 'Corner Bakehouse', 5814, 'debit', g_bake, 'POS'),
    ('ROAST & CO COFFEE', 'Roast & Co', 5814, 'debit', g_coffee, 'POS'), ('PARCELMART ONLINE', 'Parcelmart', 5999, 'credit', g_parcel, 'ECOM'),
    ('HIGH ST PHARMACY', 'High St Pharmacy', 5912, 'debit', g_pharm, 'POS'), ('NORTHWAY FUEL', 'Northway Fuel', 5541, 'credit', g_fuel, 'POS'),
    ('QUAYSIDE CINEMA', 'Quayside Cinema', 7832, 'credit', g_cinema, 'POS'), ('FERN & FLINT HARDWARE', 'Fern & Flint Hardware', 5251, 'debit', g_hard, 'POS'),
    ('LOOM CLOTHING', 'Loom Clothing', 5651, 'credit', g_cloth, 'POS'), ('SALT YARD KITCHEN', 'Salt Yard Kitchen', 5812, 'credit', g_rest, 'POS')]
mock, mock_tx, tipped = [], {}, False
def purchase(d, shop):
    global tipped
    info, name, mcc, acc, gen, sub = shop
    raw, layout = gen()
    items = [{'name': x[0], 'qty': x[1], 'unit': round(x[2], 2), 'promo': None, 'total': round(x[1] * x[2], 2), **({'extra': True} if len(x) > 3 and x[3] else {}), **({'detail': x[4]} if len(x) > 4 else {})} for x in raw]
    tip = 0
    if mcc == 5812:
        if not tipped and d.month >= 8: tipped = True; tip = 5.00                       # one bill paid with a tip added on the card
        else: sc = round(sum(i['total'] for i in items) * .125, 2); items.append({'name': 'SERVICE CHARGE 12.5%', 'qty': 1, 'unit': sc, 'promo': None, 'total': sc, 'extra': True})
    total = round(sum(i['total'] for i in items), 2)
    rid = 'MOCK-R-%04d' % (len(mock) + 1)
    tm = '%02d:%02d' % (random.randint(8, 20), random.randint(0, 59))
    mock.append({'id': rid, 'file': 'mock_receipt_%04d.jpg' % (len(mock) + 1), 'store': name, 'address': 'DEMO BRANCH | Newcastle upon Tyne | UK', 'date': d.isoformat(), 'time': tm,
        'total': total, 'card': '4417' if acc == 'debit' else '8802', 'origin': 'mock', 'layout': layout, 'items': items})
    b = d + dt.timedelta(days=random.choice([0, 0, 1]))
    t = add(b, info, name, mcc, total + tip, acc, code=('CustomerCardTransactions', sub), value=d.isoformat() + 'T' + tm + ':00+00:00')
    mock_tx[rid] = d
for m in range(4, 10):
    add(dt.date(2026, m, 1), 'HARLOW LETTINGS RENT', 'Harlow Lettings', 6513, 895.00, code=SO)
    add(dt.date(2026, m, 3), 'TYNE CITY COUNCIL TAX', 'Tyne City Council', 9311, 142.00, code=DD)
    add(dt.date(2026, m, 6), 'BRIGHTGRID ENERGY', 'Brightgrid Energy', 4900, round(random.uniform(68, 96), 2), code=DD)
    add(dt.date(2026, m, 9), 'PULSE GYM', 'Pulse Gym', 7997, 24.99, code=DD)
    add(dt.date(2026, m, 12), 'FIBRELINE BROADBAND', 'Fibreline', 4814, 32.00, code=DD)
    add(dt.date(2026, m, 15), 'TELLO MOBILE', 'Tello Mobile', 4814, 18.50, code=DD)
    add(dt.date(2026, m, 18), 'STREAMBOX SUBSCRIPTION', 'Streambox', 4899, 10.99, 'credit', code=REC)
    add(dt.date(2026, m, 27 if m != 6 else 26), 'KESTREL DESIGN LTD SALARY', None, 0, 2640.00, credit=True, code=FP)
    for shop in random.sample(SHOPS, random.randint(5, 7)): purchase(dt.date(2026, m, random.randint(1, 27)), shop)
if not tipped: purchase(dt.date(2026, 9, 12), SHOPS[-1])
add(dt.date(2026, 7, 21), 'PARCELMART ONLINE REFUND', 'Parcelmart', 5999, 23.40, 'credit', credit=True, code=ECOM)
receipts += mock
txns.sort(key=lambda t: (t['BookingDateTime'], t['TransactionId']))
g = [t for t in txns if '_receipt' in t]
# initial state: older two thirds already matched; the rest wait in the sample tray
g_sorted = sorted(g, key=lambda t: t['ValueDateTime'])
cut = int(len(g_sorted) * 0.62)
pre = [t['_receipt'] for t in g_sorted[:cut] if random.random() > 0.12]
tray = [t['_receipt'] for t in g_sorted[cut:]][-9:] + [cash[0]['id']]
pre += [r['id'] for r in mock if r['date'] < '2026-08-01' and random.random() > 0.35]
for t in txns: t.pop('_receipt', None)
accounts = [
 {'AccountId': 'acc-4417', 'Currency': 'GBP', 'AccountType': 'Personal', 'AccountSubType': 'CurrentAccount', 'Nickname': 'Everyday current', 'Account': [{'SchemeName': 'UK.OBIE.SortCodeAccountNumber', 'Identification': '••••••••4417', 'Name': 'Sample Holder'}], '_last4': '4417', '_provider': 'Northbank (mock)'},
 {'AccountId': 'acc-8802', 'Currency': 'GBP', 'AccountType': 'Personal', 'AccountSubType': 'CreditCard', 'Nickname': 'Rewards credit card', 'Account': [{'SchemeName': 'UK.OBIE.PAN', 'Identification': '•••• •••• •••• 8802', 'Name': 'Sample Holder'}], '_last4': '8802', '_provider': 'Northbank (mock)'}]
out = {'accounts': accounts, 'transactions': txns, 'receipts': receipts, 'prematched': pre, 'tray': tray,
       'source': {'file': 'DH_Synthtic_Receipt_Database.xlsx', 'receipts': len(rec), 'lines': len(rows), 'consumers': len(bycons), 'used': picked + [cash_c]}}
open('site/data.js', 'w').write('window.TILL_DATA=' + json.dumps(out, separators=(',', ':')) + ';')
print(len(txns), 'txns', len(g), 'grocery', len(receipts), 'receipts', len(pre), 'pre', len(tray), 'tray')
