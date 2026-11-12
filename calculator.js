/* Core computations: prediction and permutation SHAP (probability scale).
   Works in the browser (window.SACalc) and in Node (module.exports) for testing. */
(function (root) {
  "use strict";

  function termFns(model) {
    var fns = {};
    model.numeric.forEach(function (n) {
      fns[n.var] = function (v) { return n.coef * (Number(v) - n.mean) / n.scale; };
    });
    model.categorical.forEach(function (c) {
      fns[c.var] = function (v) {
        var k = String(v);
        if (!(k in c.coefs)) throw new Error("Unknown level " + k + " for " + c.var);
        return c.coefs[k];
      };
    });
    return fns;
  }

  function sigmoid(z) { return 1 / (1 + Math.exp(-z)); }

  function predict(model, x) {
    var fns = termFns(model), z = model.intercept;
    model.vars.forEach(function (v) { z += fns[v](x[v]); });
    return sigmoid(z);
  }

  // Small seeded PRNG so explanations are reproducible for the same input.
  function mulberry32(a) {
    return function () {
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  /* Permutation SHAP with antithetic (forward + reverse) passes, interventional
     masking with the background sample, explained on the probability scale. */
  function shap(model, x, nPerm, seed) {
    nPerm = nPerm || 500; seed = seed || 2026;
    var vars = model.vars, p = vars.length, fns = termFns(model), bg = model.background, R = bg.length;
    var cx = vars.map(function (v) { return fns[v](x[v]); });
    var cb = bg.map(function (row) { return vars.map(function (v) { return fns[v](row[v]); }); });
    var baseLogit = bg.map(function (row, r) {
      var z = model.intercept; for (var j = 0; j < p; j++) z += cb[r][j]; return z;
    });
    function meanProb(lg) { var s = 0; for (var r = 0; r < R; r++) s += sigmoid(lg[r]); return s / R; }
    var phi = new Array(p).fill(0), rnd = mulberry32(seed);
    var base = meanProb(baseLogit), fx = predict(model, x);
    for (var it = 0; it < nPerm; it++) {
      var perm = vars.map(function (_, j) { return j; });
      for (var i = p - 1; i > 0; i--) { var k = Math.floor(rnd() * (i + 1)); var t = perm[i]; perm[i] = perm[k]; perm[k] = t; }
      [perm, perm.slice().reverse()].forEach(function (order) {
        var lg = baseLogit.slice(), prev = base;
        order.forEach(function (j) {
          var d = cx[j]; for (var r = 0; r < R; r++) lg[r] += d - cb[r][j];
          var cur = meanProb(lg); phi[j] += cur - prev; prev = cur;
        });
      });
    }
    phi = phi.map(function (v) { return v / (2 * nPerm); });
    return { values: phi, base: base, fx: fx, vars: vars };
  }

  var api = { predict: predict, shap: shap };
  if (typeof module !== "undefined" && module.exports) module.exports = api; else root.SACalc = api;
})(this);
