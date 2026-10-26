with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()
idx = text.find('__hierarchy_tree__')
print("Position:", idx)
print(text[idx-200:idx+2500])
