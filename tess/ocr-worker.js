/* Wraps Tesseract's worker so the English language data comes from a file shipped with the page instead of a CDN. */
var realFetch = self.fetch.bind(self);
self.fetch = function (url, opts) {
  if (/eng\.traineddata/.test(String(url))) {
    importScripts('eng-traineddata.js');
    var bin = atob(self.TILL_ENG_GZ_B64), bytes = new Uint8Array(bin.length);
    for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
    self.TILL_ENG_GZ_B64 = null;
    return Promise.resolve(new Response(bytes));
  }
  return realFetch(url, opts);
};
importScripts('worker.min.js');
