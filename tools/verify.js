global.window = {}; require('../model.js'); const M = window.SA_MODEL;
const C = require('../calculator.js');
const fs = require('fs');
const rows = fs.readFileSync('/home/claude/web/verify_test_rows.csv','utf8').trim().split('\n');
const h = rows[0].split(','); let maxd = 0, n = 0, agree = 0;
for (const line of rows.slice(1)) {
  const v = line.split(','); const x = {}; h.forEach((k,i)=> x[k]= k==='raceeth'? v[i] : Number(v[i]));
  const p = C.predict(M, x), d = Math.abs(p - x.p_sklearn); maxd = Math.max(maxd, d); n++;
  if ((p>=0.36) === (x.p_sklearn>=0.36)) agree++;
}
console.log(`test rows ${n}, max |JS - sklearn| = ${maxd.toExponential(2)}, threshold agreement ${agree}/${n}`);
const cases = fs.readFileSync('/home/claude/web/verify_shap_cases.csv','utf8').trim().split('\n');
const ch = cases[0].split(',');
for (const line of cases.slice(1)) {
  const v=line.split(','); const x={}; ch.forEach((k,i)=> x[k]= k==='raceeth'? v[i] : Number(v[i]));
  const t0=Date.now(); const s=C.shap(M,x,500,2026); const ms=Date.now()-t0;
  const sum=s.values.reduce((a,b)=>a+b,0);
  console.log(`fx=${s.fx.toFixed(4)} base=${s.base.toFixed(4)} base+sum=${(s.base+sum).toFixed(4)} time=${ms}ms`);
  console.log(s.vars.map((k,i)=>k+':'+s.values[i].toFixed(4)).join(' '));
  const s2=C.shap(M,x,500,7); let md=0; s.values.forEach((a,i)=>md=Math.max(md,Math.abs(a-s2.values[i]))); console.log('seed-to-seed max diff', md.toFixed(4));
}
