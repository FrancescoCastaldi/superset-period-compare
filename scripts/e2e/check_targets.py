with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    bundle = f.read()

# 1. StratumBar label fix
# Find T.push({name:e,key:e,color:u(e,r)
sbar_target = 'T.push({name:e,key:e,color:u(e,r),data:o,items:n,yAxisIndex:0,seriesType:"bar"})'
print("StratumBar target in bundle:", sbar_target in bundle)

# 2. StratumHeatmap header overlap fix
# Find grid and xAxis in heatmap
hmap_target = 'grid:{top:s&&"top"===c?65:D?42:24,right:s&&"right"===c?80:28,bottom:s&&"bottom"===c?65:D?16:32,left:60,containLabel:!0},xAxis:{type:"category",position:u,data:t,splitArea:{show:!1},axisLine:{lineStyle:{color:"#cbd5e1"}},axisLabel:{color:"#334155",fontSize:11,fontWeight:600,interval:0}}'
print("StratumHeatmap target in bundle:", hmap_target in bundle)
