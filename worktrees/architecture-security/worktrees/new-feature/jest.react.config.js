module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/src/frontend/react/setupTests.ts'],
  globals: {
    TextEncoder: require('util').TextEncoder,
    TextDecoder: require('util').TextDecoder,
  },
  testMatch: [
    '<rootDir>/tests/react/**/*.(test|spec).(ts|tsx|js)',
    '<rootDir>/src/frontend/react/**/__tests__/**/*.(ts|tsx|js)',
    '<rootDir>/src/frontend/react/**/*.(test|spec).(ts|tsx|js)'
  ],
  moduleNameMapper: {
    '^@/(.*)$': '<rootDir>/src/frontend/react/$1',
    '^@components/(.*)$': '<rootDir>/src/frontend/react/components/$1',
    '^@hooks/(.*)$': '<rootDir>/src/frontend/react/hooks/$1',
    '^@utils/(.*)$': '<rootDir>/src/frontend/react/utils/$1',
    '^@types/(.*)$': '<rootDir>/src/frontend/react/types/$1',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  transform: {
    '^.+\\.(ts|tsx)$': 'ts-jest',
  },
  collectCoverageFrom: [
    'src/frontend/react/**/*.(ts|tsx)',
    '!src/frontend/react/**/*.d.ts',
    '!src/frontend/react/index.tsx',
  ],
};