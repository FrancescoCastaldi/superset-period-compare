const fs = require('fs');
const { execSync } = require('child_process');

let bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

const css_target = '.hierarchical-table th,.hierarchical-table td{white-space:nowrap}.hierarchical-table th{background:#f3f4f6;color:#374151;font-weight:600;padding:10px 14px;';
const css_replacement = '.hierarchical-table td{white-space:nowrap}.hierarchical-table th{white-space:normal;line-height:1.25;vertical-align:bottom;background:#f3f4f6;color:#374151;font-weight:600;padding:8px 8px;';

console.log('CSS target found:', bundle.includes(css_target));

if (!bundle.includes(css_target)) {
  console.error('Target not found! Aborting.');
  process.exit(1);
}

bundle = bundle.replace(css_target, css_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.patched_v6.js', bundle, 'utf8');
console.log('Saved 3259.entry.patched_v6.js');

try {
  execSync('node -c scripts/e2e/3259.entry.patched_v6.js');
  console.log('Syntax check on patched_v6: PASSED!');
  fs.writeFileSync('scripts/e2e/3259.entry.js', bundle, 'utf8');
  console.log('Successfully updated scripts/e2e/3259.entry.js');
} catch (e) {
  console.error('Syntax check FAILED:', e);
  process.exit(1);
}

// Copy into docker container locations
const targets = [
  '/app/superset/static/assets/3259.17d47733767525cb3d84.entry.js',
  '/app/build/lib/superset/static/assets/3259.17d47733767525cb3d84.entry.js',
  '/app/.venv/lib/python3.11/site-packages/superset/static/assets/3259.17d47733767525cb3d84.entry.js'
];

for (const t of targets) {
  execSync(`docker cp scripts/e2e/3259.entry.js superset_app:${t}`);
  console.log(`Copied bundle to ${t}`);
}

console.log('Bundle patch v6 deployed successfully!');
