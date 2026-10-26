with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = [m.start() for m in re.finditer(r'buildFlatColumns', text)]
print("buildFlatColumns matches:", len(matches))
for m in matches:
    print(text[m-100:m+500])
    print("---")

matches2 = [m.start() for m in re.finditer(r'buildTreeData', text)]
print("buildTreeData matches:", len(matches2))
for m in matches2:
    print(text[m-100:m+500])
    print("---")
