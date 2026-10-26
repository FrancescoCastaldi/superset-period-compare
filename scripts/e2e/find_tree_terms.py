with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
for term in ['__hierarchy_tree__', 'showVarianceDelta', 'delta-badge', '___period_delta', '___delta']:
    matches = [m.start() for m in re.finditer(re.escape(term), text)]
    print(f"{term} matches: {len(matches)}")
    if matches:
        print(text[matches[0]-100:matches[0]+300])
        print("---")
