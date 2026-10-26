const fs = require('fs');

const bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

// Test 1: StratumBar target
const sbar_target = 'T.push({name:e,key:e,color:u(e,r),data:o,items:n,yAxisIndex:0,seriesType:"bar"})';
const sbar_replacement = 'T.push((()=>{let dN=e.includes("__")?"Periodo Confronto":(x.some(k=>k.includes("__"))?"Periodo Attuale":e);return{name:dN,key:e,color:u(dN,r),data:o,items:n,yAxisIndex:0,seriesType:"bar"}})())';

// Test 2: StratumHeatmap target
const hmap_target = 'grid:{top:s&&"top"===c?65:D?42:24,right:s&&"right"===c?80:28,bottom:s&&"bottom"===c?65:D?16:32,left:60,containLabel:!0},xAxis:{type:"category",position:u,data:t,splitArea:{show:!1},axisLine:{lineStyle:{color:"#cbd5e1"}},axisLabel:{color:"#334155",fontSize:11,fontWeight:600,interval:0}}';
const hmap_replacement = 'grid:{top:s&&"top"===c?65:D?65:24,right:s&&"right"===c?80:35,bottom:s&&"bottom"===c?65:D?16:32,left:70,containLabel:!0},xAxis:{type:"category",position:u,data:t,splitArea:{show:!1},axisLine:{lineStyle:{color:"#cbd5e1"}},axisLabel:{color:"#334155",fontSize:11,fontWeight:600,interval:0,rotate:-25,margin:12}}';
console.log('StratumHeatmap target found:', bundle.includes(hmap_target));

// Test 3: Grand Total target
const gt_target = 'return{key:"__grand_total__",id:"__grand_total__",name:"Grand Total",depth:0,path:["Grand Total"],isLeaf:!0,metrics:o,subtotals:o}';
const gt_replacement = 'for(let k in o){if(k.endsWith("___comp")){let bK=k.replace("___comp","");if(typeof o[bK]==="number"){o[bK+"___diff"]=o[bK]-o[k];o[bK+"___delta"]=o[k]!==0?((o[bK]-o[k])/o[k])*100:0;}}};return{key:"__grand_total__",id:"__grand_total__",name:"Grand Total",depth:0,path:["Grand Total"],isLeaf:!0,metrics:o,subtotals:o}';
console.log('Grand Total target found:', bundle.includes(gt_target));

// Test 4: Flat columns target
const flat_target = 'if(!r.isPivotMode){let e=function(e,t){let r=[],a=[];for(let o of e)a.push(o),_b(o)||r.push({key:o,title:o.endsWith("___delta")?`\\u0394% ${o.replace("___delta","")}`:o,dataIndex:o,isMetric:!0,align:"right",width:160,formatter:_y(t,o)});return{columns:r,pivotHeaderGroups:[],metricKeys:a}}(a,o);return _w(e,r.tableCalculations,o,!1),e}';
const flat_replacement = 'if(!r.isPivotMode){let e_layout=function(metrics,format){let cols=[],mKeys=[];let hasComp=Boolean(t&&t.length>0&&Object.keys(t[0]).some(k=>k.includes("__")));let compMap={};if(hasComp){for(let m of metrics){let k=Object.keys(t[0]).find(key=>key.startsWith(m+"__"));if(k)compMap[m]=k}function rollupNode(node){if(!node.children||node.children.length===0){node.metrics=node.metrics||{};for(let m of metrics){if(compMap[m]){let compVal=(node.rawData&&node.rawData[compMap[m]]!==undefined)?Number(node.rawData[compMap[m]]):0;node.metrics[m+"___comp"]=compVal;let curVal=Number(node.metrics[m]||0);let diff=curVal-compVal;let delta=compVal!==0?(diff/compVal)*100:0;node.metrics[m+"___diff"]=diff;node.metrics[m+"___delta"]=delta}}node.subtotals=Object.assign({},node.metrics)}else{for(let c of node.children){rollupNode(c)}node.metrics=node.metrics||{};for(let m of metrics){if(compMap[m]){let curSum=0,compSum=0;for(let c of node.children){curSum+=Number((c.metrics&&c.metrics[m])||0);compSum+=Number((c.metrics&&c.metrics[m+"___comp"])||0)}node.metrics[m]=curSum;node.metrics[m+"___comp"]=compSum;let diff=curSum-compSum;let delta=compSum!==0?(diff/compSum)*100:0;node.metrics[m+"___diff"]=diff;node.metrics[m+"___delta"]=delta}}node.subtotals=Object.assign({},node.metrics)}}for(let root of e){rollupNode(root)}}for(let m of metrics){if(_b(m))continue;if(hasComp&&compMap[m]){mKeys.push(m,m+"___comp",m+"___diff",m+"___delta");cols.push({key:m,title:`${m} (Attuale)`,dataIndex:m,isMetric:!0,align:"right",width:140,formatter:_y(format,m)});cols.push({key:m+"___comp",title:`${m} (Confronto)`,dataIndex:m+"___comp",isMetric:!0,align:"right",width:140,formatter:_y(format,m)});cols.push({key:m+"___diff",title:`\\u0394 ${m}`,dataIndex:m+"___diff",isMetric:!0,align:"right",width:120,formatter:_y(format,m)});cols.push({key:m+"___delta",title:`\\u0394% ${m}`,dataIndex:m+"___delta",isMetric:!0,align:"right",width:110,formatter:_y(format,m+"___delta")})}else{mKeys.push(m);cols.push({key:m,title:m.endsWith("___delta")?`\\u0394% ${m.replace("___delta","")}`:m,dataIndex:m,isMetric:!0,align:"right",width:160,formatter:_y(format,m)})}}return{columns:cols,pivotHeaderGroups:[],metricKeys:mKeys}}(a,o);return _w(e_layout,r.tableCalculations,o,!1),e_layout}';
console.log('Flat target found:', bundle.includes(flat_target));

let patched = bundle;
patched = patched.replace(sbar_target, sbar_replacement);
patched = patched.replace(hmap_target, hmap_replacement);
patched = patched.replace(gt_target, gt_replacement);
patched = patched.replace(flat_target, flat_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.js', patched, 'utf8');
console.log('Saved 3259.entry.js successfully, size:', patched.length);

const { execSync } = require('child_process');
execSync('node -c scripts/e2e/3259.entry.js');
console.log('Syntax check on patched 3259.entry.js: PASSED');
