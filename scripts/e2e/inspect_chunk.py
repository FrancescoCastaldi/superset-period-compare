with open('scripts/e2e/3259.entry.js', 'r', encoding='utf-8') as f:
    content = f.read()

idx = content.find('let _t1=')
end_idx = content.find('cols.push({key:m+"___delta"', idx) + 140
print('Target chunk extended:')
print(content[idx:end_idx])
