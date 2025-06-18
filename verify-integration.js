const fs = require('fs');
const path = require('path');

function verifyIntegration() {
  const report = {
    settingsOK: false,
    loaderOK: false,
    bmadBundleOK: false,
    routingOK: false
  };

  try {
    // 1. Verify settings
    const settingsPath = path.join(__dirname, '.claude', 'settings.json');
    if (fs.existsSync(settingsPath)) {
      const settings = JSON.parse(fs.readFileSync(settingsPath));
      report.settingsOK = !!settings.plugins?.bmad?.enabled;
    }

    // 2. Verify loader
    const loaderPath = path.join(__dirname, 'bmad-loader.js');
    report.loaderOK = fs.existsSync(loaderPath);

    // 3. Verify BMAD bundle
    const bmadPath = "c:/Users/pasca/Documents/bmad-project";
    report.bmadBundleOK = fs.existsSync(bmadPath);

    // 4. Verify routing
    if (report.settingsOK) {
      const settings = JSON.parse(fs.readFileSync(settingsPath));
      report.routingOK = settings.autoAgentRouting && 
                         Object.keys(settings.agentRoutingRules || {}).length > 0;
    }

    return report;
  } catch (e) {
    return { error: e.message };
  }
}

// Run verification
const results = verifyIntegration();
console.log('\n=== BMAD Integration Report ===');
console.log(`Settings: ${results.settingsOK ? '✅' : '❌'}`);
console.log(`Loader: ${results.loaderOK ? '✅' : '❌'}`);
console.log(`BMAD Bundle: ${results.bmadBundleOK ? '✅' : '❌'}`);
console.log(`Routing: ${results.routingOK ? '✅' : '❌'}`);

if (results.error) {
  console.log('\n⚠️ Error:', results.error);
} else if (results.settingsOK && results.loaderOK && results.bmadBundleOK && results.routingOK) {
  console.log('\n🎉 BMAD fully integrated with Claude!');
} else {
  console.log('\n⚠️ Configuration issues detected');
}
