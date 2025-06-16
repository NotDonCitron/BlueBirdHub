const { add } = require('./src/calculator');

// Simple test
console.log('Running simple test...');
console.log('2 + 3 =', add(2, 3));

// Verify the function works as expected
const result = add(2, 3);
if (result === 5) {
  console.log('✅ Test passed!');
} else {
  console.error('❌ Test failed!');
}
