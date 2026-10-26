with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    bundle = f.read()

import re
matches = [m.start() for m in re.finditer(r'Grand Total', bundle)]
print("Grand Total matches:", len(matches))
for m in matches:
    print(bundle[m-100:m+300])
    print("---")
