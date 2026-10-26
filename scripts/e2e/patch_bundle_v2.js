const fs = require('fs');
const { execSync } = require('child_process');

let bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

// 1. Heatmap target
const hmap_target = 'grid:{top:s&&"top"===c?65:D?50:24,right:s&&"right"===c?80:35,bottom:s&&"bottom"===c?65:D?16:32,left:70,containLabel:!0},xAxis:{type:"category",position:u,data:t,splitArea:{show:!1},axisLine:{lineStyle:{color:"#cbd5e1"}},axisLabel:{color:"#334155",fontSize:11,fontWeight:600,interval:0,rotate:0,margin:10}}';
const hmap_replacement = 'grid:{top:s&&"top"===c?65:D?65:24,right:s&&"right"===c?80:35,bottom:s&&"bottom"===c?65:D?16:32,left:70,containLabel:!0},xAxis:{type:"category",position:u,data:t,splitArea:{show:!1},axisLine:{lineStyle:{color:"#cbd5e1"}},axisLabel:{color:"#334155",fontSize:11,fontWeight:600,interval:0,rotate:0,margin:12}}';

// Heatmap pin target
const pin_target = 'symbol:"pin",symbolSize:45';
const pin_replacement = 'symbol:"pin",symbolSize:30';

// 2. Row delta & badge targets
const row_delta_target = 'Q&&"number"==typeof W?(0,xA.jsx)("span",{className:wP(W,null==t?void 0:t.polarity),children:(null==t?void 0:t.formatter)?t.formatter(W):String(null!=W?W:"-")})';
const row_delta_replacement = 'Q&&"number"==typeof W?(t.key.endsWith("___delta")?(0,xA.jsxs)("span",{className:(0,wN.default)("delta-badge",wP(W,null==t?void 0:t.polarity)),children:[W>0?"▲ +":W<0?"▼ ":"",Math.abs(W).toFixed(1),"%"]}):(0,xA.jsx)("span",{className:wP(W,null==t?void 0:t.polarity),children:(null==t?void 0:t.formatter)?t.formatter(W):String(null!=W?W:"-")}))';

const row_variance_target = 'er=null;if(f&&!Q&&K){let r=t.key.includes("___")?t.key.replace(/^(.+?)___(.+)$/,"$1___delta_pct___$2"):null;';
const row_variance_replacement = 'er=null;if(f&&!Q&&K&&!t.key.endsWith("___comp")){let r=t.key.includes("___")?t.key.replace(/^(.+?)___(.+)$/,"$1___delta_pct___$2"):null;';

// 3. Grand Total targets
const gt_delta_target = 'h&&"number"==typeof g?(0,xA.jsx)("span",{className:wP(g,null==e?void 0:e.polarity),children:(null==e?void 0:e.formatter)?e.formatter(g):String(null!=g?g:"-")})';
const gt_delta_replacement = 'h&&"number"==typeof g?(e.key.endsWith("___delta")?(0,xA.jsxs)("span",{className:(0,wN.default)("delta-badge",wP(g,null==e?void 0:e.polarity)),children:[g>0?"▲ +":g<0?"▼ ":"",Math.abs(g).toFixed(1),"%"]}):(0,xA.jsx)("span",{className:wP(g,null==e?void 0:e.polarity),children:(null==e?void 0:e.formatter)?e.formatter(g):String(null!=g?g:"-")}))';

const gt_variance_target = 'y=null;if(R&&!h&&"number"==typeof g){let t=e.key.includes("___")?e.key.replace(/^(.+?)___(.+)$/,"$1___delta_pct___$2"):null;if(t){let e=null!=(s=null==(c=en.metrics)?void 0:c[t])?s:null==(u=en.subtotals)?void 0:u[t];"number"==typeof e&&Number.isFinite(e)&&(y=e)}if(null===y){let t=`${null!=(d=e.baseMetric)?d:e.key.split("___")[0]}___period_delta_pct`,r=null!=(p=null==(m=en.metrics)?void 0:m[t])?p:null==(f=en.subtotals)?void 0:f[t];"number"==typeof r&&Number.isFinite(r)&&(y=r)}}';
const gt_variance_replacement = 'y=null;if(R&&!h&&"number"==typeof g&&!e.key.endsWith("___comp")){let t=e.key.includes("___")?e.key.replace(/^(.+?)___(.+)$/,"$1___delta_pct___$2"):null;if(t){let e=null!=(s=null==(c=en.metrics)?void 0:c[t])?s:null==(u=en.subtotals)?void 0:u[t];"number"==typeof e&&Number.isFinite(e)&&(y=e)}if(null===y){let t=`${null!=(d=e.baseMetric)?d:e.key.split("___")[0]}___period_delta_pct`,r=null!=(p=null==(m=en.metrics)?void 0:m[t])?p:null==(f=en.subtotals)?void 0:f[t];"number"==typeof r&&Number.isFinite(r)&&(y=r)}if(null===y){let r=null!=(d=e.baseMetric)?d:e.key.split("___")[0];let a=null==(m=en.metrics)?void 0:m[r+"___delta"];if("number"==typeof a&&Number.isFinite(a)){y=a}}}';

bundle = bundle.replace(hmap_target, hmap_replacement);
bundle = bundle.replace(pin_target, pin_replacement);
bundle = bundle.replace(row_delta_target, row_delta_replacement);
bundle = bundle.replace(row_variance_target, row_variance_replacement);
bundle = bundle.replace(gt_delta_target, gt_delta_replacement);
bundle = bundle.replace(gt_variance_target, gt_variance_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.patched_v2.js', bundle, 'utf8');
console.log('Saved 3259.entry.patched_v2.js, size:', bundle.length);

try {
  execSync('node -c scripts/e2e/3259.entry.patched_v2.js');
  console.log('Syntax check on patched_v2: PASSED!');
  // If passed, overwrite 3259.entry.js
  fs.writeFileSync('scripts/e2e/3259.entry.js', bundle, 'utf8');
  console.log('Successfully updated scripts/e2e/3259.entry.js');
} catch (e) {
  console.error('Syntax check FAILED:', e);
  process.exit(1);
}
