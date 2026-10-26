const fs = require('fs');
const { execSync } = require('child_process');

let bundle = fs.readFileSync('scripts/e2e/3259.entry.js', 'utf8');

// 1. Skip ghost delta columns in flat columns loop
const loop_target = 'for(let m of metrics){if(_b(m))continue;';
const loop_replacement = 'for(let m of metrics){if(_b(m)||m.endsWith("___delta")||m.endsWith("___diff")||m.endsWith("___comp"))continue;';

// 2. Hierarchy column width: 160px
const h_target = 'isHierarchyDimension:!0,align:"left",width:200';
const h_replacement = 'isHierarchyDimension:!0,align:"left",width:160';

console.log('Loop target found:', bundle.includes(loop_target));
console.log('Hierarchy target found:', bundle.includes(h_target));

if (!bundle.includes(loop_target) || !bundle.includes(h_target)) {
  console.error('Target not found! Aborting.');
  process.exit(1);
}

bundle = bundle.replace(loop_target, loop_replacement);
bundle = bundle.replace(h_target, h_replacement);

fs.writeFileSync('scripts/e2e/3259.entry.patched_v5.js', bundle, 'utf8');
console.log('Saved 3259.entry.patched_v5.js');

try {
  execSync('node -c scripts/e2e/3259.entry.patched_v5.js');
  console.log('Syntax check on patched_v5: PASSED!');
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

console.log('Bundle patch v5 deployed successfully!');
