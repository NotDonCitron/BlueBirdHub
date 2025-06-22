const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const TerserPlugin = require('terser-webpack-plugin');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');

const isProduction = process.env.NODE_ENV === 'production';
const shouldAnalyze = process.env.ANALYZE === 'true';

module.exports = {
  mode: process.env.NODE_ENV || 'development',
  entry: {
    app: './src/frontend/react/index.tsx',
  },
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: isProduction 
      ? 'js/[name].[contenthash:8].js' 
      : 'js/[name].js',
    chunkFilename: isProduction
      ? 'js/[name].[contenthash:8].chunk.js'
      : 'js/[name].chunk.js',
    assetModuleFilename: 'assets/[name].[contenthash:8][ext]',
    clean: true,
    publicPath: '/',
  },
  
  optimization: {
    minimize: isProduction,
    minimizer: [
      new TerserPlugin({
        terserOptions: {
          compress: {
            drop_console: isProduction,
            drop_debugger: isProduction,
            pure_funcs: isProduction ? ['console.log', 'console.info'] : [],
          },
          mangle: {
            safari10: true,
          },
          format: {
            comments: false,
          },
        },
        extractComments: false,
      }),
      new CssMinimizerPlugin({
        minimizerOptions: {
          preset: [
            'default',
            {
              discardComments: { removeAll: true },
              normalizeWhitespace: true,
            },
          ],
        },
      }),
    ],
    splitChunks: {
      chunks: 'all',
      cacheGroups: {
        // React and React-DOM in separate chunk
        react: {
          test: /[\\/]node_modules[\\/](react|react-dom)[\\/]/,
          name: 'react',
          chunks: 'all',
          priority: 30,
          enforce: true,
        },
        // React Router in separate chunk
        router: {
          test: /[\\/]node_modules[\\/]react-router/,
          name: 'router',
          chunks: 'all',
          priority: 25,
          enforce: true,
        },
        // Other vendor libraries
        vendor: {
          test: /[\\/]node_modules[\\/](?!(react|react-dom|react-router))/,
          name: 'vendor',
          chunks: 'all',
          priority: 20,
          maxSize: 244000, // ~240KB
        },
        // Common chunks between async components
        common: {
          name: 'common',
          minChunks: 2,
          chunks: 'all',
          priority: 10,
          reuseExistingChunk: true,
          maxSize: 244000,
        },
        // Default chunk
        default: {
          minChunks: 2,
          priority: -20,
          reuseExistingChunk: true,
        },
      },
    },
    runtimeChunk: {
      name: 'runtime',
    },
    usedExports: true,
    sideEffects: false,
    providedExports: true,
    concatenateModules: isProduction,
  },
  
  resolve: {
    extensions: ['.tsx', '.ts', '.js', '.jsx'],
    alias: {
      '@': path.resolve(__dirname, 'src'),
      '@components': path.resolve(__dirname, 'src/frontend/react/components'),
      '@utils': path.resolve(__dirname, 'src/utils'),
      '@hooks': path.resolve(__dirname, 'src/frontend/react/hooks'),
      '@styles': path.resolve(__dirname, 'src/frontend/react/styles'),
    },
  },
  
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: [
          {
            loader: 'ts-loader',
            options: {
              transpileOnly: true,
              configFile: 'tsconfig.json',
            },
          },
        ],
        exclude: /node_modules/,
      },
      {
        test: /\.css$/i,
        use: [
          isProduction ? MiniCssExtractPlugin.loader : 'style-loader',
          {
            loader: 'css-loader',
            options: {
              importLoaders: 1,
              modules: {
                auto: true,
                localIdentName: isProduction 
                  ? '[hash:base64:8]'
                  : '[name]__[local]--[hash:base64:5]',
              },
            },
          },
        ],
        sideEffects: true,
      },
      {
        test: /\.(png|jpe?g|gif|svg|webp)$/i,
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
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/frontend/react/public/index.html',
      inject: 'body',
      scriptLoading: 'defer',
      minify: isProduction ? {
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
      } : false,
    }),
    
    // Extract CSS in production
    ...(isProduction ? [
      new MiniCssExtractPlugin({
        filename: 'css/[name].[contenthash:8].css',
        chunkFilename: 'css/[name].[contenthash:8].chunk.css',
      }),
    ] : []),
    
    // Compression for production
    ...(isProduction ? [
      new CompressionPlugin({
        filename: '[path][base].gz',
        algorithm: 'gzip',
        test: /\.(js|css|html|svg)$/,
        threshold: 8192,
        minRatio: 0.8,
      }),
      new CompressionPlugin({
        filename: '[path][base].br',
        algorithm: 'brotliCompress',
        test: /\.(js|css|html|svg)$/,
        compressionOptions: {
          level: 11,
        },
        threshold: 8192,
        minRatio: 0.8,
      }),
    ] : []),
    
    // Bundle analyzer
    ...(shouldAnalyze ? [
      new BundleAnalyzerPlugin({
        analyzerMode: 'static',
        openAnalyzer: false,
        reportFilename: 'bundle-report.html',
      }),
    ] : []),
  ],
  
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 3002,
    hot: true,
    open: true,
    historyApiFallback: true,
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
  },
  
  devtool: process.env.NODE_ENV === 'production' 
    ? 'source-map' 
    : 'eval-source-map',
  
  performance: {
    hints: isProduction ? 'error' : false,
    maxEntrypointSize: 244000, // 240KB target
    maxAssetSize: 244000, // 240KB target
    assetFilter: (assetFilename) => {
      return !/(\.map$|\.gz$|\.br$)/.test(assetFilename);
    },
  },
  
  stats: {
    modules: false,
    chunks: false,
    chunkModules: false,
    optimizationBailout: false,
  },
};