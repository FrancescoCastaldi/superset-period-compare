with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    bundle = f.read()

gt_target = 'return{key:"__grand_total__",id:"__grand_total__",name:"Grand Total",depth:0,path:["Grand Total"],isLeaf:!0,metrics:o,subtotals:o}'
print("GT target in bundle:", gt_target in bundle)
idx = bundle.find(gt_target)
print("Before GT target:\n", bundle[idx-500:idx])
