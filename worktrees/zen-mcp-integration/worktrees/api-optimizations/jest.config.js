module.exports = {
  testEnvironment: 'node',
  testMatch: [
    '**/tests/**/*.js',
    '**/tests/**/*.test.js'
  ],
  testPathIgnorePatterns: [
    '/node_modules/',
    '/venv/',
    '/.taskmaster/'
  ],
  collectCoverage: true,
  coverageDirectory: 'coverage',
  coveragePathIgnorePatterns: [
    '/node_modules/',
    '/tests/'
  ]
};