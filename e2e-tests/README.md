# OrdnungsHub E2E Test Suite

Human-like automated testing for the OrdnungsHub frontend using Puppeteer.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Run quick smoke test (5 seconds)
npm run quick-test

# Verify all bug fixes are working
npm run verify-fixes

# Run full comprehensive test suite (2-5 minutes)
npm test

# Run tests in headless mode (faster)
npm run test:headless
```

## 📋 Prerequisites

- **Backend running**: http://localhost:8000
- **Frontend running**: http://localhost:5173
- **Node.js**: Version 18+

## 🧪 Test Coverage

### Authentication Tests
- ✅ Login form detection
- ✅ Credential validation (admin/admin123)
- ✅ Authentication flow
- ✅ Token handling

### Dashboard Tests  
- ✅ Statistics cards display
- ✅ Action button functionality
- ✅ Navigation from dashboard
- ✅ Data loading verification

### Navigation Tests
- ✅ All route accessibility
- ✅ URL validation
- ✅ Page content loading
- ✅ Cross-navigation flow

### Interactive Element Tests
- ✅ Button clicking
- ✅ Form submissions
- ✅ Search functionality
- ✅ Header actions

### API Integration Tests
- ✅ Backend health monitoring
- ✅ API request/response validation
- ✅ Error handling verification
- ✅ Authentication headers

## 🎯 Test Types

### Quick Test (`npm run quick-test`)
- Service availability check
- Basic page loading
- Simple interaction testing
- **Duration**: ~30 seconds

### Full Test Suite (`npm test`)
- Comprehensive functionality testing
- All routes and components
- Error scenario testing
- **Duration**: 2-5 minutes

## 📊 Test Reports

Results are saved to `test-results.json` with:
- Test execution summary
- Pass/fail statistics
- Detailed error logs
- Timestamp information

## 🔧 Configuration

Edit these variables in test files:
- `baseUrl`: Frontend URL (default: http://localhost:5173)
- `backendUrl`: Backend URL (default: http://localhost:8000)

## 🐛 Troubleshooting

**Backend not running:**
```bash
# Start backend first
cd ../
python -m src.backend.main
```

**Frontend not running:**
```bash
# Start frontend
cd ../packages/web
npm run dev
```

**Authentication issues:**
- Ensure admin user exists (admin/admin123)
- Check backend seed data
- Verify /auth/login-json endpoint

**Puppeteer issues:**
```bash
# Reinstall Puppeteer
npm uninstall puppeteer
npm install puppeteer
```

## 🎮 Human-like Testing Features

- **Realistic timing**: Random delays between actions
- **Natural interactions**: Typing with realistic speed
- **Visual browser**: Non-headless mode for observation
- **Error resilience**: Continues testing on individual failures
- **Comprehensive logging**: Detailed console output

## 📝 Adding New Tests

```javascript
// Example test method
async testMyFeature() {
  console.log('\n🧪 Testing My Feature...');
  try {
    await this.page.goto(`${this.baseUrl}/my-route`);
    await this.humanClick('.my-button', 'My Button');
    await this.logTest('My Feature Test', true);
  } catch (error) {
    await this.logTest('My Feature Test', false, error.message);
  }
}

// Add to test suite in runAllTests()
const tests = [
  () => this.testMyFeature(),
  // ... other tests
];
```

## 🚦 Status Indicators

- ✅ **Test Passed**: Functionality working correctly
- ❌ **Test Failed**: Issue detected, check details
- ⚠️ **Warning**: Minor issue, functionality may still work
- 📡 **API Call**: Backend request logged
- 👆 **User Action**: Interactive element clicked/typed

## 🔧 Fixed Issues

The following issues were identified and resolved:

### Backend API Fixes
- **✅ Added missing search router**: Included `/search` endpoints in main FastAPI app
- **✅ Fixed `/search/tags` endpoint**: Now returns `{success: true, tags: [...]}` format with error handling
- **✅ Fixed `/search/categories` endpoint**: Made `user_id` parameter optional, provides defaults
- **✅ Improved error handling**: APIs return graceful responses instead of 404s

### Frontend Integration Fixes  
- **✅ Updated SmartSearch component**: Handles new API response format with fallbacks
- **✅ Updated FileManager component**: Robust error handling for search API calls
- **✅ Added default data**: Components show useful defaults when APIs fail
- **✅ Improved authentication handling**: Better timing for API calls after login

### UI/UX Fixes
- **✅ Fixed header button clickability**: Added proper z-index and pointer-events CSS
- **✅ Enhanced button interaction**: Added visual feedback for all header buttons
- **✅ Improved responsive behavior**: Better mobile interaction handling

### Authentication Improvements
- **✅ Workspace auth validation**: Proper 401 responses for unauthenticated requests
- **✅ Token handling**: Improved JWT token management in frontend
- **✅ Login flow**: Better error handling and user feedback

## 📝 Verification

Run `npm run verify-fixes` to test all fixes:
- Search API endpoints functionality
- Authentication flow validation  
- Frontend integration health
- Backend router inclusion 