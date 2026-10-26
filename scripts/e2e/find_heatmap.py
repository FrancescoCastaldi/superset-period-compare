b = open('scripts/e2e/3259.entry.js', encoding='utf-8').read()
idx = b.find('xAxis:{type:"category"')
print("idx:", idx)
if idx != -1:
    print(b[idx-120:idx+350])
