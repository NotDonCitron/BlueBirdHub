// Critical path resources for immediate rendering
// This module contains only the essential code needed for the initial page render

// Critical CSS imports - these will be inlined
import './styles/critical.css';

// Critical components for above-the-fold content
export { default as Header } from './components/Header/Header';
export { default as Layout } from './components/Layout/Layout';
export { default as LoadingSkeleton } from './components/LoadingSkeleton/LoadingSkeleton';

// Essential utilities for initial render
export { default as ErrorBoundary } from './components/ErrorBoundary';

// Critical context providers
export { ApiProvider } from './contexts/ApiContext';
export { ThemeProvider } from './contexts/ThemeContext';