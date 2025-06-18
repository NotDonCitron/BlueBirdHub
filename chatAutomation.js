const puppeteer = require('puppeteer');

async function automateChat() {
  try {
    // Launch browser
    const browser = await puppeteer.launch({
      headless: false, // Set to true for headless mode
      args: [
        '--no-sandbox',
        '--disable-setuid-sandbox',
      ],
    });
    page.setUserAgent('Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36');
    const page = await browser.newPage();

    // Navigate to chat page
    await page.goto('https://www.chat-avenue.com/general/', { waitUntil: 'networkidle2' });

    // Login/Registration (Modify selectors as needed)
    const username = 'hornifabi25';
    const password = 'Quaso1!12';
    const email = 'claracouve342@gmail.com';
    const age = '20';
    const gender = 'Male';

    // Click login or register button (adjust selector as needed)
    await page.click('#loginButton');

    // Fill in login form (adjust selectors as needed)
    await page.type('#username', username);
    await page.type('#password', password);

    // Click submit button (adjust selector as needed)
    await page.click('#submitButton');

    // Wait for navigation after login
    await page.waitForNavigation({ waitUntil: 'networkidle2' });

    // Wait for chat interface to load (adjust selector if needed)
    await page.waitForSelector('#chat-container', { timeout: 30000 });

    // Find and click message input (adjust selector as needed)
    const inputSelector = await page.evaluate(() => {
      // Try to find message input by common attributes
      const input = document.querySelector('input, textarea');
      return input ? input.id : null;
    });

    if (inputSelector) {
      await page.focus(`#${inputSelector}`);
      await page.keyboard.type('#' + inputSelector, 'Hello, this is an automated message!');
      
      // Find send button and click it (adjust selector as needed)
      const buttonSelector = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('button')).find(btn => 
          btn.textContent && btn.textContent.toLowerCase().includes('send') || 
          btn.textContent.toLowerCase().includes('message') ||
          btn.textContent.toLowerCase().includes('chat')
        )?.id;
      });

      if (buttonSelector) {
        await page.click('#' + buttonSelector);
      } else {
        console.log('Could not find send button. Page HTML:', await page.evaluate(() => document.documentElement.outerHTML));
      }
    } else {
      console.log('Could not find message input. Page HTML:', await page.evaluate(() => document.documentElement.outerHTML));
    }

    // Wait to see the message sent
    await page.waitForTimeout(2000);

    // Close browser
    await browser.close();
    return 'Message sent successfully!';
  } catch (error) {
    console.error('Error:', error.message);
    return 'Failed to send message: ' + error.message;
  }
}

// Run the automation
automateChat().then(result => console.log(result));