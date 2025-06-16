const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const TerserPlugin = require('terser-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');

module.exports = {
  mode: 'production',
  
  entry: {
    main: './src/frontend/react/index.tsx',
    vendor: ['react', 'react-dom'] // Split vendor chunks
  },
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'js/[name].[contenthash:8].js',
    chunkFilename: 'js/[name].[contenthash:8].chunk.js',
    publicPath: './',
    clean: true, // Clean output directory
    
    // Optimize chunk loading
    asyncChunks: true,
    pathinfo: false,
  },
  
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src/frontend/react'),
      '@components': path.resolve(__dirname, 'src/frontend/react/components'),
      '@hooks': path.resolve(__dirname, 'src/frontend/react/hooks'),
      '@utils': path.resolve(__dirname, 'src/frontend/react/utils'),
      '@styles': path.resolve(__dirname, 'src/frontend/react/styles')
    },
    
    // Optimize module resolution
    modules: ['node_modules'],
    symlinks: false,
    cacheWithContext: false,
  },
  
  module: {
    rules: [
      {
        test: /\.(ts|tsx)$/,
        use: [
          {
            loader: 'ts-loader',
            options: {
              transpileOnly: true, // Faster compilation
              configFile: 'tsconfig.json'
            }
          }
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.css$/,
        use: [
          MiniCssExtractPlugin.loader,
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              modules: {
                auto: true,
                localIdentName: '[hash:base64:8]' // Shorter class names in production
              }
            }
          },
          'postcss-loader'
        ],
      },
      {
        test: /\.(png|jpg|jpeg|gif|svg|ico)$/i,
        type: 'asset',
        parser: {
          dataUrlCondition: {
            maxSize: 8 * 1024, // 8KB - inline smaller images
          },
        },
        generator: {
          filename: 'images/[name].[contenthash:8][ext]',
        },
      },
      {
        test: /\.(woff|woff2|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: {
          filename: 'fonts/[name].[contenthash:8][ext]',
        },
      },
    ],
  },
  
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          parse: {
            ecma: 8,
          },
          compress: {
            ecma: 5,
            warnings: false,
            comparisons: false,
            inline: 2,
            drop_console: true, // Remove console.log in production
            drop_debugger: true,
            pure_funcs: ['console.log', 'console.warn'], // Remove specific console methods
          },
          mangle: {
            safari10: true,
          },
          output: {
            ecma: 5,
            comments: false,
            ascii_only: true,
          },
        },
        parallel: true,
        extractComments: false,
      }),
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              discardComments: { removeAll: true },
            },
          ],
        },
      }),
    ],
    
    // Code splitting configuration
    splitChunks: {
      chunks: 'all',
      maxInitialRequests: 10,
      maxAsyncRequests: 10,
      cacheGroups: {
        // Vendor chunk for React and core libraries
        vendor: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'vendor',
          priority: 20,
          chunks: 'all',
          enforce: true,
        },
        
        // Common chunk for shared components
        common: {
          name: 'common',
          minChunks: 2,
          priority: 10,
          chunks: 'all',
          enforce: true,
        },
        
        // CSS chunks
        styles: {
          name: 'styles',
          test: /\.css$/,
          chunks: 'all',
          enforce: true,
        },
      },
    },
    
    // Runtime chunk
    runtimeChunk: {
      name: 'runtime',
    },
    
    // Module concatenation (scope hoisting)
    concatenateModules: true,
    
    // Tree shaking
    usedExports: true,
    sideEffects: false,
  },
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/frontend/index.html',
      filename: 'index.html',
      inject: true,
      minify: {
        removeComments: true,
        collapseWhitespace: true,
        removeRedundantAttributes: true,
        useShortDoctype: true,
        removeEmptyAttributes: true,
        removeStyleLinkTypeAttributes: true,
        keepClosingSlash: true,
        minifyJS: true,
        minifyCSS: true,
        minifyURLs: true,
      },
    }),
    
    // Extract CSS to separate files
    new MiniCssExtractPlugin({
      filename: 'css/[name].[contenthash:8].css',
      chunkFilename: 'css/[name].[contenthash:8].chunk.css',
    }),
    
    // Gzip compression
    new CompressionPlugin({
      algorithm: 'gzip',
      test: /\.(js|css|html|svg)$/,
      threshold: 8192,
      minRatio: 0.8,
    }),
    
    // Production optimizations
    new webpack.DefinePlugin({
      'process.env.NODE_ENV': JSON.stringify('production'),
      'process.env.ANALYZE_BUNDLE': JSON.stringify(process.env.ANALYZE_BUNDLE),
    }),
    
    // Bundle analyzer (run with ANALYZE_BUNDLE=true)
    ...(process.env.ANALYZE_BUNDLE ? [
      new BundleAnalyzerPlugin({
        analyzerMode: 'static',
        openAnalyzer: false,
        reportFilename: 'bundle-analysis.html',
      })
    ] : []),
    
    // Ignore moment.js locales to reduce bundle size
    new webpack.IgnorePlugin({
      resourceRegExp: /^\.\/locale$/,
      contextRegExp: /moment$/,
    }),
  ],
  
  // Performance budgets
  performance: {
    maxAssetSize: 512000, // 500KB
    maxEntrypointSize: 512000, // 500KB
    hints: 'warning',
    assetFilter: function (assetFilename) {
      return assetFilename.endsWith('.js') || assetFilename.endsWith('.css');
    },
  },
  
  // Stats configuration
  stats: {
    assets: true,
    chunks: false,
    modules: false,
    colors: true,
    timings: true,
    builtAt: true,
    version: false,
  },
  
  // Source maps for production debugging
  devtool: 'source-map',
  
  // Cache configuration for faster rebuilds
  cache: {
    type: 'filesystem',
    buildDependencies: {
      config: [__filename],
    },
  },
  
  // Target Electron renderer process
  target: 'electron-renderer',
  
  // Node configuration for Electron
  node: {
    __dirname: false,
    __filename: false,
  },
};