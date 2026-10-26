const fs = require('fs');
const { execSync } = require('child_process');

let bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

// Target 1: Hierarchy column width
const h_target = 'isHierarchyDimension:!0,align:"left",width:320';
const h_replacement = 'isHierarchyDimension:!0,align:"left",width:200';

// Target 2: StratumTree column headers and widths
const col_target = 'let _t1=m==="sum_sales"?"sum_sales (Tempo 1: Settembre 2026)":(m==="orders"?"orders (Tempo 1: Settembre 2026)":`${m} (Tempo 1: Settembre 2026)`);let _t2=m==="sum_sales"?"sum_sales (Tempo 2: Agosto 2026)":(m==="orders"?"orders (Tempo 2: Agosto 2026)":`${m} (Tempo 2: Agosto 2026)`);let _df=m==="sum_sales"?"\\u0394 Vendite (Tempo 1 - Tempo 2)":(m==="orders"?"\\u0394 Ordini (Tempo 1 - Tempo 2)":`\\u0394 ${m} (Tempo 1 - Tempo 2)`);let _dp=m==="sum_sales"?"\\u0394% Vendite":(m==="orders"?"\\u0394% Ordini":`\\u0394% ${m}`);cols.push({key:m,title:_t1,dataIndex:m,isMetric:!0,align:"right",width:175,formatter:_y(format,m)});cols.push({key:m+"___comp",title:_t2,dataIndex:m+"___comp",isMetric:!0,align:"right",width:175,formatter:_y(format,m)});cols.push({key:m+"___diff",title:_df,dataIndex:m+"___diff",isMetric:!0,align:"right",width:165,formatter:_y(format,m)});cols.push({key:m+"___delta",title:_dp,dataIndex:m+"___delta",isMetric:!0,align:"right",width:110,formatter:_y(format,m+"___delta")})';

const col_replacement = 'let _s=m==="sum_sales",_o=m==="orders";let _t1=_s?"sum_sales (Tempo 1: Settembre 2026)":(_o?"orders (Tempo 1)":`${m} (Tempo 1)`);let _t2=_s?"sum_sales (Tempo 2: Agosto 2026)":(_o?"orders (Tempo 2)":`${m} (Tempo 2)`);let _df=_s?"\\u0394 Vendite (Tempo 1 - Tempo 2)":(_o?"\\u0394 Ordini (Tempo 1 - Tempo 2)":`\\u0394 ${m} (Tempo 1 - Tempo 2)`);let _dp=_s?"\\u0394% Vendite":(_o?"\\u0394% Ordini":`\\u0394% ${m}`);let _w1=_s?155:110,_w2=_s?155:110,_wf=_s?145:135,_wp=_s?90:85;cols.push({key:m,title:_t1,dataIndex:m,isMetric:!0,align:"right",width:_w1,formatter:_y(format,m)});cols.push({key:m+"___comp",title:_t2,dataIndex:m+"___comp",isMetric:!0,align:"right",width:_w2,formatter:_y(format,m)});cols.push({key:m+"___diff",title:_df,dataIndex:m+"___diff",isMetric:!0,align:"right",width:_wf,formatter:_y(format,m)});cols.push({key:m+"___delta",title:_dp,dataIndex:m+"___delta",isMetric:!0,align:"right",width:_wp,formatter:_y(format,m+"___delta")})';

console.log('Hierarchy width target found:', bundle.includes(h_target));
console.log('Column target found:', bundle.includes(col_target));

if (!bundle.includes(h_target) || !bundle.includes(col_target)) {
  console.error('One or more targets not found! Aborting.');
  process.exit(1);
}

bundle = bundle.replace(h_target, h_replacement);
bundle = bundle.replace(col_target, col_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.patched_v4.js', bundle, 'utf8');
console.log('Saved 3259.entry.patched_v4.js');

try {
  execSync('node -c scripts/e2e/3259.entry.patched_v4.js');
  console.log('Syntax check on patched_v4: PASSED!');
  fs.writeFileSync('scripts/e2e/3259.entry.js', bundle, 'utf8');
  console.log('Successfully updated scripts/e2e/3259.entry.js');
} catch (e) {
  console.error('Syntax check FAILED:', e);
  process.exit(1);
}

// Copy into docker container locations
const targets = [
  '/app/superset/static/assets/3259.17d47733767525cb3d84.entry.js',
  '/app/build/lib/superset/static/assets/3259.17d47733767525cb3d84.entry.js',
  '/app/.venv/lib/python3.11/site-packages/superset/static/assets/3259.17d47733767525cb3d84.entry.js'
];

for (const t of targets) {
  execSync(`docker cp scripts/e2e/3259.entry.js superset_app:${t}`);
  console.log(`Copied bundle to ${t}`);
}

console.log('Bundle patch v4 deployed successfully!');
