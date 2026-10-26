with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for potentialPivotedKeys
import re
matches = [m.start() for m in re.finditer(r'potentialPivotedKeys', text)]
print("potentialPivotedKeys matches:", len(matches))
for m in matches:
    print("Match at", m)
    print(text[m-100:m+300])
    print("---")
