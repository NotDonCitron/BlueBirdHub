const path = require('path');

module.exports = [
  // Main process
  {
    mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
    entry: './src/main/main.js',
    target: 'electron-main',
    output: {
      path: path.resolve(__dirname, 'dist/main'),
      filename: 'main.js',
    },
    node: {
      __dirname: false,
      __filename: false,
    },
    externals: {
      electron: 'commonjs2 electron',
    },
  },
  // Preload script
  {
    mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
    entry: './src/preload/preload.js',
    target: 'electron-preload',
    output: {
      path: path.resolve(__dirname, 'dist/preload'),
      filename: 'preload.js',
    },
    node: {
      __dirname: false,
      __filename: false,
    },
  },
];