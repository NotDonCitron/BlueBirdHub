import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  root: '.',
  publicDir: 'src/frontend/react/public',
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    sourcemap: true,
    rollupOptions: {
      input: {
        main: path.resolve(__dirname, 'index.html')
      }
    }
  },
  server: {
    port: 3002,
    host: true,
    open: false
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src/frontend/react'),
      '@components': path.resolve(__dirname, 'src/frontend/react/components'),
      '@lib': path.resolve(__dirname, 'src/frontend/react/lib'),
      '@types': path.resolve(__dirname, 'src/frontend/react/types'),
      '@hooks': path.resolve(__dirname, 'src/frontend/react/hooks'),
      '@utils': path.resolve(__dirname, 'src/frontend/react/utils'),
      '@styles': path.resolve(__dirname, 'src/frontend/react/styles'),
    }
  },
  define: {
    'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'development')
  }
}) 