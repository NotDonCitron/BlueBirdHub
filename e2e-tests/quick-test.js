const puppeteer = require('puppeteer');

class QuickTester {
  constructor() {
    this.baseUrl = 'http://localhost:5173';
    this.backendUrl = 'http://localhost:8000';
  }

  async checkServices() {
    console.log('🔍 Quick Service Check...\n');
    
    // Check backend
    try {
      const backendResponse = await fetch(`${this.backendUrl}/health`);
      const backendData = await backendResponse.json();
      console.log(`✅ Backend: ${backendData.status} (${this.backendUrl})`);
    } catch (error) {
      console.log(`❌ Backend: Not running (${this.backendUrl})`);
      return false;
    }

    // Check frontend
    try {
      const frontendResponse = await fetch(this.baseUrl);
      console.log(`✅ Frontend: Running (${this.baseUrl})`);
    } catch (error) {
      console.log(`❌ Frontend: Not running (${this.baseUrl})`);
      return false;
    }

    return true;
  }

  async quickBrowserTest() {
    console.log('\n🚀 Quick Browser Test...\n');
    
    const browser = await puppeteer.launch({
      headless: false,
      defaultViewport: { width: 1366, height: 768 }
    });
    
    const page = await browser.newPage();
    
    try {
      // Go to homepage
      await page.goto(this.baseUrl);
      await page.waitForSelector('body', { timeout: 5000 });
      console.log('✅ Page loads successfully');

      // Check for login form or dashboard
      const hasLoginForm = await page.$('form') !== null;
      const hasDashboard = await page.$('.dashboard, [class*="dashboard"]') !== null;
      
      if (hasLoginForm) {
        console.log('✅ Login form detected');
        
        // Try to login
        const usernameInput = await page.$('input[type="text"], input[name="username"]');
        const passwordInput = await page.$('input[type="password"], input[name="password"]');
        
        if (usernameInput && passwordInput) {
          await page.type('input[type="text"], input[name="username"]', 'admin');
          await page.type('input[type="password"], input[name="password"]', 'admin123');
          
          const submitButton = await page.$('button[type="submit"]');
          if (submitButton) {
            await submitButton.click();
            await page.waitForTimeout(3000);
            console.log('✅ Login attempted');
          }
        }
      } else if (hasDashboard) {
        console.log('✅ Dashboard already visible (likely authenticated)');
      } else {
        console.log('⚠️ Neither login form nor dashboard detected');
      }

      // Test navigation
      const currentUrl = page.url();
      console.log(`✅ Current URL: ${currentUrl}`);

      // Count interactive elements
      const buttons = await page.$$('button');
      const links = await page.$$('a');
      const inputs = await page.$$('input, textarea, select');
      
      console.log(`✅ Found ${buttons.length} buttons, ${links.length} links, ${inputs.length} inputs`);

      // Test a few clicks
      if (buttons.length > 0) {
        console.log('✅ Testing button clicks...');
        for (let i = 0; i < Math.min(3, buttons.length); i++) {
          try {
            await buttons[i].click();
            await page.waitForTimeout(500);
            console.log(`✅ Button ${i + 1} click successful`);
          } catch (error) {
            console.log(`⚠️ Button ${i + 1} click failed: ${error.message}`);
          }
        }
      }

      console.log('\n🎉 Quick test completed successfully!');
      
    } catch (error) {
      console.error(`❌ Quick test failed: ${error.message}`);
    } finally {
      await browser.close();
    }
  }

  async run() {
    const servicesOk = await this.checkServices();
    if (servicesOk) {
      await this.quickBrowserTest();
    } else {
      console.log('\n❌ Services not running. Please start:');
      console.log('   Backend: http://localhost:8000');
      console.log('   Frontend: http://localhost:5173');
    }
  }
}

if (require.main === module) {
  const tester = new QuickTester();
  tester.run().catch(console.error);
}

module.exports = QuickTester; 