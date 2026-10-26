with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    bundle = f.read()

# Let's find where flat columns are built in the bundle
target = 'if(!r.isPivotMode){let e=function(e,t){let r=[],a=[];for(let o of e)a.push(o),_b(o)||r.push({key:o,title:o.endsWith("___delta")?`\\u0394% ${o.replace("___delta","")}`:o,dataIndex:o,isMetric:!0,align:"right",width:160,formatter:_y(t,o)});return{columns:r,pivotHeaderGroups:[],metricKeys:a}}(a,o);return _w(e,r.tableCalculations,o,!1),e}'
print("Flat columns target in bundle:", target in bundle)

if not target in bundle:
    # Let's search substring
    idx = bundle.find('if(!r.isPivotMode)')
    print(bundle[idx:idx+400])
