b = open('scripts/e2e/3259.entry.js', encoding='utf-8').read()
idx = b.find('markPoint:', 836000)
print("markPoint idx:", idx)
if idx != -1:
    print(b[idx-50:idx+250])
