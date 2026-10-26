with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'StratumHeatmap', text)]
print("StratumHeatmap matches:", len(matches))
for m in matches:
    print("Match at", m)
    print(text[m-200:m+400])
    print("---")
