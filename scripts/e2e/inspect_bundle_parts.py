with open(r'D:\Actual\03_Sviluppo_Software\Repositories\superset-period-compare\scripts\e2e\3259.entry.js', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's search for stratum_bar code
idx = text.find('stratum_bar')
print("Around stratum_bar (first match):")
print(text[max(0, idx-200):idx+300])

# Let's search for hierarchical_table code
idx2 = text.find('hierarchical_table')
print("\nAround hierarchical_table (first match):")
print(text[max(0, idx2-200):idx2+300])

# Let's search for buildHeatmapOption or stratum_heatmap
idx3 = text.find('stratum_heatmap')
print("\nAround stratum_heatmap (first match):")
print(text[max(0, idx3-200):idx3+300])
