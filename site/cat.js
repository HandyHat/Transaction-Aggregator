/* Budget categories for any purchase.
   A receipt line is categorised from its product name; if no rule fits, it takes the shop's usual category.
   Rules run in order: an exact pass first, then a one-typo pass for OCR slips. */
(function (root) {
  var GROUPS = [{ id: "food", name: "Food shop" }, { id: "home", name: "Home & personal" }, { id: "out", name: "Out & about" }, { id: "fixed", name: "Fixed costs" }];
  var CATS = [
    { id: "produce", name: "Fruit & veg", group: "food" }, { id: "meat", name: "Meat, fish & protein", group: "food" }, { id: "dairy", name: "Dairy & eggs", group: "food" },
    { id: "bakery", name: "Bakery", group: "food" }, { id: "cupboard", name: "Food cupboard", group: "food" }, { id: "frozen", name: "Frozen", group: "food" },
    { id: "drinks", name: "Drinks", group: "food" }, { id: "snacks", name: "Snacks & treats", group: "food" }, { id: "groceries", name: "Groceries, not split", group: "food" },
    { id: "household", name: "Household & cleaning", group: "home" }, { id: "toiletries", name: "Toiletries & personal care", group: "home" }, { id: "health", name: "Health & pharmacy", group: "home" },
    { id: "home", name: "Home & DIY", group: "home" }, { id: "electronics", name: "Electronics", group: "home" }, { id: "clothing", name: "Clothing", group: "home" },
    { id: "eating", name: "Eating out", group: "out" }, { id: "transport", name: "Transport & fuel", group: "out" }, { id: "leisure", name: "Leisure & subscriptions", group: "out" },
    { id: "shopping", name: "General shopping", group: "out" }, { id: "misc", name: "Everything else", group: "out" },
    { id: "housing", name: "Housing", group: "fixed" }, { id: "bills", name: "Bills & utilities", group: "fixed" }];
  /* Merchant category codes from the bank. kind "mixed": the shop sells across categories, so lines are read one by one.
     kind "single": everything bought there belongs to the shop's category (a restaurant bill is all eating out). */
  var MCC = {
    "5411": { cat: "groceries", kind: "mixed" }, "5912": { cat: "health", kind: "mixed" }, "5541": { cat: "transport", kind: "mixed" }, "5999": { cat: "shopping", kind: "mixed" },
    "5251": { cat: "home", kind: "mixed" }, "5200": { cat: "home", kind: "mixed" }, "5651": { cat: "clothing", kind: "mixed" }, "5732": { cat: "electronics", kind: "mixed" }, "5311": { cat: "shopping", kind: "mixed" },
    "5812": { cat: "eating", kind: "single" }, "5813": { cat: "eating", kind: "single" }, "5814": { cat: "eating", kind: "single" }, "7832": { cat: "leisure", kind: "single" },
    "4111": { cat: "transport", kind: "single" }, "4899": { cat: "leisure", kind: "single" }, "7997": { cat: "leisure", kind: "single" },
    "4900": { cat: "bills", kind: "single" }, "4814": { cat: "bills", kind: "single" }, "6513": { cat: "housing", kind: "single" }, "9311": { cat: "housing", kind: "single" } };
  var RULES = [
    ["transport", ["unleaded", "diesel", "petrol", "fuel", "screenwash", "car wash", "top up", "parking", "engine oil"]],
    ["toiletries", ["toothpaste", "soap", "shampoo", "shower gel", "colgate", "aquafresh", "oral b", "pantene", "shoulders", "alberto", "radox", "dove", "imperial leather", "deodorant", "razor", "gillette", "blades", "lip balm", "sunscreen", "moisturiser", "conditioner"]],
    ["household", ["tissue", "toilet", "kitchen roll", "wash", "bleach", "cleaner", "dishwasher", "fab cond", "pods", "non bio", "scent", "stain", "vanish", "cif", "dettol", "domestos", "flash", "finish", "ariel", "persil", "surf", "comfort", "lenor", "fairy", "andrex", "cushelle", "plenty", "bin bags", "foil"]],
    ["health", ["paracetamol", "ibuprofen", "tablets", "capsules", "plasters", "vitamin", "cough", "syrup", "hayfever", "antiseptic", "bandage", "lozenges", "prescription", "vicks", "vaporub"]],
    ["electronics", ["cable", "usb", "charger", "batteries", "headphones", "earbuds", "phone", "hdmi", "adapter", "speaker"]],
    ["home", ["screws", "paint", "roller", "bulb", "tape", "kettle", "gloves", "hammer", "drill", "sandpaper", "filler", "toaster", "compost", "hooks"]],
    ["clothing", ["shirt", "socks", "jeans", "jumper", "hoodie", "trainers", "jacket", "dress", "leggings"]],
    ["eating", ["meal deal", "sandwich", "takeaway"]],
    ["leisure", ["ticket", "novel", "paperback", "book", "yoga", "puzzle", "game"]],
    ["frozen", ["fish fingers", "garden peas", "ice cream", "pizza", "chips", "lollies", "frozen", "birds eye", "mccain"]],
    ["snacks", ["choc", "maltesers", "haribo", "crisps", "digestives", "hobnobs", "crackers", "biscuit", "sweets", "lindt", "cadbury", "walkers", "mcvities"]],
    ["dairy", ["milk", "butter", "cheddar", "cheese", "yoghurt", "yogurt", "eggs", "babybel", "spread", "flora", "alpro", "lurpak", "anchor", "activia", "muller"]],
    ["meat", ["mince", "chicken", "salmon", "beef", "tofu", "pork", "bacon", "sausage", "ham", "fillets"]],
    ["bakery", ["bread", "hovis", "kingsmill", "warburtons", "rolls", "bagel", "wrap", "loaf"]],
    ["produce", ["bananas", "spinach", "broccoli", "carrots", "peelers", "apples", "peppers", "grapes", "potatoes", "onions", "salad", "lettuce", "cucumber"]],
    ["drinks", ["juice", "coca cola", "cola", "pepsi", "squash", "tea", "tips", "coffee", "kenco", "nescafe", "water", "lemonade"]],
    ["cupboard", ["spaghetti", "fusilli", "penne", "pasta", "rice", "beans", "beanz", "ketchup", "mayonnaise", "sauce", "tomatoes", "flakes", "weetabix", "oats", "dolmio", "pataks", "heinz", "napolina", "barilla", "tilda", "cereal", "flour", "sugar", "soup"]]];
  function tokens(s) {
    return String(s || "").toLowerCase().split(/[^a-z0-9]+/).filter(Boolean).map(function (t) { return /[a-z]/.test(t) ? t.replace(/0/g, "o").replace(/1/g, "i") : t; });
  }
  function lev(a, b) {
    var p = [], i, j, prev, t; for (j = 0; j <= b.length; j++) p[j] = j;
    for (i = 1; i <= a.length; i++) { prev = p[0]; p[0] = i; for (j = 1; j <= b.length; j++) { t = p[j]; p[j] = Math.min(p[j] + 1, p[j - 1] + 1, prev + (a[i - 1] === b[j - 1] ? 0 : 1)); prev = t; } }
    return p[b.length];
  }
  function key(name) { return tokens(name).join(" "); }
  /* Returns a category id, or null when no rule recognises the product. */
  function categorise(name) {
    var toks = tokens(name), joined = " " + toks.join(" ") + " ", r, k, kw, hit;
    for (r = 0; r < RULES.length; r++) for (k = 0; k < RULES[r][1].length; k++) {
      kw = RULES[r][1][k];
      hit = kw.indexOf(" ") > 0 ? joined.indexOf(" " + kw) >= 0 : toks.some(function (t) { return t === kw || (kw.length >= 4 && t.indexOf(kw) === 0); });
      if (hit) return RULES[r][0];
    }
    for (r = 0; r < RULES.length; r++) for (k = 0; k < RULES[r][1].length; k++) {
      kw = RULES[r][1][k];
      if (kw.length >= 5 && kw.indexOf(" ") < 0 && toks.some(function (t) { return Math.abs(t.length - kw.length) <= 1 && lev(t, kw) <= 1; })) return RULES[r][0];
    }
    return null;
  }
  /* Procter & Gamble brands sold in the UK, with the product segment each belongs to.
     Short brand names must match exactly (FAIRY must not catch DAIRY); longer ones allow one OCR slip. */
  var PG_BRANDS = [
    ["Ariel", "Fabric care", ["ariel"]], ["Bold", "Fabric care", ["bold"]], ["Daz", "Fabric care", ["daz"]], ["Lenor", "Fabric care", ["lenor"]],
    ["Fairy", "Home care", ["fairy"]], ["Flash", "Home care", ["flash"]], ["Febreze", "Home care", ["febreze"]], ["Viakal", "Home care", ["viakal"]],
    ["Ambi Pur", "Home care", ["ambi pur", "ambipur"]], ["Swiffer", "Home care", ["swiffer"]],
    ["Pampers", "Baby care", ["pampers"]], ["Always", "Feminine care", ["always"]], ["Tampax", "Feminine care", ["tampax"]],
    ["Gillette", "Grooming", ["gillette"]], ["Venus", "Grooming", ["venus"]], ["Braun", "Grooming", ["braun"]],
    ["Oral-B", "Oral care", ["oral b", "oralb"]], ["Head & Shoulders", "Hair care", ["head and shoulders", "head shoulders", "shoulders"]],
    ["Pantene", "Hair care", ["pantene"]], ["Herbal Essences", "Hair care", ["herbal essences"]], ["Aussie", "Hair care", ["aussie"]],
    ["Olay", "Skin & personal care", ["olay"]], ["Old Spice", "Skin & personal care", ["old spice"]], ["Vicks", "Personal health", ["vicks"]]];
  function brandOf(name) {
    var toks = tokens(name), joined = " " + toks.join(" ") + " ", b, k, kw, hit;
    for (b = 0; b < PG_BRANDS.length; b++) for (k = 0; k < PG_BRANDS[b][2].length; k++) {
      kw = PG_BRANDS[b][2][k];
      hit = kw.indexOf(" ") > 0 ? joined.indexOf(" " + kw + " ") >= 0 : toks.some(function (t) { return t === kw || (kw.length >= 6 && Math.abs(t.length - kw.length) <= 1 && lev(t, kw) <= 1); });
      if (hit) return { brand: PG_BRANDS[b][0], segment: PG_BRANDS[b][0] === "Fairy" && /non bio|pods|fab|laundry/.test(joined) ? "Fabric care" : PG_BRANDS[b][1] };
    }
    return null;
  }
  function shop(mcc) { return MCC[mcc] || { cat: "misc", kind: "single" }; }
  root.TillCat = { GROUPS: GROUPS, CATS: CATS, categorise: categorise, key: key, shop: shop, brandOf: brandOf, PG_BRANDS: PG_BRANDS.map(function (b) { return { brand: b[0], segment: b[1] }; }) };
})(typeof window !== "undefined" ? window : globalThis);
