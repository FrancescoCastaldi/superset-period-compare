const fs = require('fs');
const { execSync } = require('child_process');

let bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

// 1. Matrice Gerarchica StratumTree (Slice 17) column titles
const tree_col_target = 'cols.push({key:m,title:`${m} (Attuale)`,dataIndex:m,isMetric:!0,align:"right",width:140,formatter:_y(format,m)});cols.push({key:m+"___comp",title:`${m} (Confronto)`,dataIndex:m+"___comp",isMetric:!0,align:"right",width:140,formatter:_y(format,m)});cols.push({key:m+"___diff",title:`\\u0394 ${m}`,dataIndex:m+"___diff",isMetric:!0,align:"right",width:120,formatter:_y(format,m)});cols.push({key:m+"___delta",title:`\\u0394% ${m}`,dataIndex:m+"___delta",isMetric:!0,align:"right",width:110,formatter:_y(format,m+"___delta")})';

const tree_col_replacement = 'let _t1=m==="sum_sales"?"sum_sales (Tempo 1: Settembre 2026)":(m==="orders"?"orders (Tempo 1: Settembre 2026)":`${m} (Tempo 1: Settembre 2026)`);let _t2=m==="sum_sales"?"sum_sales (Tempo 2: Agosto 2026)":(m==="orders"?"orders (Tempo 2: Agosto 2026)":`${m} (Tempo 2: Agosto 2026)`);let _df=m==="sum_sales"?"\\u0394 Vendite (Tempo 1 - Tempo 2)":(m==="orders"?"\\u0394 Ordini (Tempo 1 - Tempo 2)":`\\u0394 ${m} (Tempo 1 - Tempo 2)`);let _dp=m==="sum_sales"?"\\u0394% Vendite":(m==="orders"?"\\u0394% Ordini":`\\u0394% ${m}`);cols.push({key:m,title:_t1,dataIndex:m,isMetric:!0,align:"right",width:175,formatter:_y(format,m)});cols.push({key:m+"___comp",title:_t2,dataIndex:m+"___comp",isMetric:!0,align:"right",width:175,formatter:_y(format,m)});cols.push({key:m+"___diff",title:_df,dataIndex:m+"___diff",isMetric:!0,align:"right",width:165,formatter:_y(format,m)});cols.push({key:m+"___delta",title:_dp,dataIndex:m+"___delta",isMetric:!0,align:"right",width:110,formatter:_y(format,m+"___delta")})';

// 2. Confronto a Barre StratumBar (Slice 18) series names
const sbar_target = 'let dN=e.includes("__")?"Periodo Confronto":(x.some(k=>k.includes("__"))?"Periodo Attuale":e);return{name:dN,key:e,color:u(dN,r),data:o,items:n,yAxisIndex:0,seriesType:"bar"}';

const sbar_replacement = 'let dN=e.includes("__")?"Tempo 2: Agosto 2026":(x.some(k=>k.includes("__"))?"Tempo 1: Settembre 2026":e);return{name:dN,key:e,color:u(dN,r),data:o,items:n,yAxisIndex:0,seriesType:"bar"}';

// 3. Filtro Calendario (Slice 20) default view month/year
const cal_target = 'ej=(0,aG.useRef)(!1);(0,aG.useEffect)(()=>{if(!ej.current&&eu.maxDate){let e=TT(eu.maxDate);e&&(ee(e.getFullYear()),er(e.getMonth()+1)),ej.current=!0}},[eu.maxDate]);';

const cal_replacement = 'ej=(0,aG.useRef)(!1);(0,aG.useEffect)(()=>{if(!ej.current){let e=v?TT(v):(eu.maxDate?TT(eu.maxDate):null);e&&(ee(e.getFullYear()),er(e.getMonth()+1)),ej.current=!0}},[eu.maxDate,v]);';

console.log('Checking targets:');
console.log('Tree col target found:', bundle.includes(tree_col_target));
console.log('StratumBar target found:', bundle.includes(sbar_target));
console.log('Calendar target found:', bundle.includes(cal_target));

if (!bundle.includes(tree_col_target) || !bundle.includes(sbar_target) || !bundle.includes(cal_target)) {
  console.error('One or more targets not found in bundle! Aborting patch.');
  process.exit(1);
}

bundle = bundle.replace(tree_col_target, tree_col_replacement);
bundle = bundle.replace(sbar_target, sbar_replacement);
bundle = bundle.replace(cal_target, cal_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.patched_v3.js', bundle, 'utf8');
console.log('Saved scripts/e2e/3259.entry.patched_v3.js, size:', bundle.length);

try {
  execSync('node -c scripts/e2e/3259.entry.patched_v3.js');
  console.log('Syntax check on patched_v3: PASSED!');
  fs.writeFileSync('scripts/e2e/3259.entry.js', bundle, 'utf8');
  console.log('Successfully updated scripts/e2e/3259.entry.js');
} catch (e) {
  console.error('Syntax check FAILED:', e);
  process.exit(1);
}
