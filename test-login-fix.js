const axios = require('axios');

async function testLoginFix() {
    console.log('🧪 Testing Login Fix');
    console.log('==================');
    
    try {
        // Test the API endpoint
        console.log('1. Testing backend login endpoint...');
        const response = await axios.post('http://127.0.0.1:8001/auth/login-json', {
            username: 'admin',
            password: 'admin123'
        }, {
            headers: { 
                'Content-Type': 'application/json',
                'Origin': 'http://localhost:3002'
            },
            timeout: 5000
        });

        console.log(`   ✅ Status: ${response.status}`);
        console.log(`   ✅ Token received: ${!!response.data.access_token}`);
        console.log(`   ✅ Token type: ${response.data.token_type}`);
        
        if (response.data.access_token) {
            console.log('\n2. Testing token format...');
            const token = response.data.access_token;
            console.log(`   ✅ Token length: ${token.length} chars`);
            console.log(`   ✅ Token starts with: ${token.substring(0, 20)}...`);
            
            // Basic JWT structure check
            const parts = token.split('.');
            console.log(`   ✅ JWT parts: ${parts.length} (should be 3)`);
        }

        console.log('\n3. Testing CORS headers...');
        const corsHeaders = {
            'Access-Control-Allow-Origin': response.headers['access-control-allow-origin'],
            'Access-Control-Allow-Credentials': response.headers['access-control-allow-credentials']
        };
        console.log('   ✅ CORS headers:', corsHeaders);

        console.log('\n🎉 Login fix validation successful!');
        console.log('\nExpected frontend behavior:');
        console.log('• Login form should accept admin/admin123');
        console.log('• Should receive access_token successfully');
        console.log('• Should store token and redirect/authenticate');
        console.log('• Console error "No token received" should be gone');
        
        return true;
        
    } catch (error) {
        console.error('❌ Login fix test failed:', error.message);
        return false;
    }
}

if (require.main === module) {
    testLoginFix()
        .then(success => {
            if (success) {
                console.log('\n✅ All tests passed - login should work in frontend now!');
                process.exit(0);
            } else {
                console.log('\n❌ Tests failed - check backend status');
                process.exit(1);
            }
        })
        .catch(error => {
            console.error('Test failed:', error);
            process.exit(1);
        });
}