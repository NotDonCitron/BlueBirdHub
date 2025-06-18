const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

module.exports = {
  mode: process.env.NODE_ENV === 'production' ? 'production' : 'development',
  entry: './src/frontend/react/index.tsx',
  
  output: {
    path: path.resolve(__dirname, 'dist'),
    filename: 'bundle.js',
    clean: true,
  },
  
  module: {
    rules: [
      {
        test: /\.tsx?$/,
        use: {
          loader: 'ts-loader',
          options: {
            compilerOptions: {
              noEmit: false,
            },
          },
        },
        exclude: [/node_modules/, /setupTests\.ts$/, /\.test\.tsx?$/, /\.spec\.tsx?$/],
      },
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
      },
    ],
  },
  
  resolve: {
    extensions: ['.tsx', '.ts', '.js'],
    alias: {
      '@': path.resolve(__dirname, 'src/frontend/react'),
      '@components': path.resolve(__dirname, 'src/frontend/react/components'),
      '@hooks': path.resolve(__dirname, 'src/frontend/react/hooks'),
      '@utils': path.resolve(__dirname, 'src/frontend/react/utils'),
      '@types': path.resolve(__dirname, 'src/frontend/react/types'),
    },
  },
  
  plugins: [
    new HtmlWebpackPlugin({
      template: './src/frontend/react/public/index.html',
      filename: 'index.html',
      meta: {
        'Content-Security-Policy': "default-src 'self'; \
          style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; \
          font-src 'self' https://fonts.gstatic.com data:; \
          img-src 'self' data: blob:; \
          connect-src 'self' http://localhost:8001 http://127.0.0.1:8001 ws:; \
          script-src 'self' 'unsafe-eval' 'unsafe-inline'; \
          frame-ancestors 'self';"
      }
    }),
  ],
  
  devServer: {
    static: {
      directory: path.join(__dirname, 'dist'),
    },
    compress: true,
    port: 3001,
    hot: true,
    open: true,
    historyApiFallback: true,
    allowedHosts: 'all',
    client: {
      overlay: {
        errors: true,
        warnings: false,
      },
    },
    devMiddleware: {
      writeToDisk: false,
    },
  },
  
  target: 'web',
  node: {
    global: true,
    __dirname: true,
    __filename: true,
  },
  
  devtool: process.env.NODE_ENV === 'production' ? 'source-map' : 'eval-source-map',
};