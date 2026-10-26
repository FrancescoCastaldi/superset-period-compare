b = open('scripts/e2e/3259.entry.js', encoding='utf-8').read()
idx = 0
while True:
    idx = b.find('StratumHeatmap', idx)
    if idx == -1: break
    print("Found StratumHeatmap at:", idx)
    print(b[max(0, idx-400):min(len(b), idx+200)])
    idx += len('StratumHeatmap')
