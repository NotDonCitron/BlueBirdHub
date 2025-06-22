/**
 * Console Filter - Suppress browser extension errors while keeping app logs clean
 */

// Store original console methods
const originalError = console.error;
const originalWarn = console.warn;

// Extension error patterns to filter out
const EXTENSION_ERROR_PATTERNS = [
  /H\.config is undefined/,
  /content_script\.js/,
  /moz-extension:\/\//,
  /chrome-extension:\/\//,
  /Request Autofill\./,
  /wasn't found.*devtools/
];

// Custom error filter
console.error = (...args: any[]) => {
  const message = args.join(' ');
  
  // Skip extension-related errors
  if (EXTENSION_ERROR_PATTERNS.some(pattern => pattern.test(message))) {
    return;
  }
  
  // Log our app errors normally
  originalError.apply(console, args);
};

// Custom warning filter
console.warn = (...args: any[]) => {
  const message = args.join(' ');
  
  // Skip extension-related warnings
  if (EXTENSION_ERROR_PATTERNS.some(pattern => pattern.test(message))) {
    return;
  }
  
  // Log our app warnings normally
  originalWarn.apply(console, args);
};

// Export a function to restore original console if needed
export const restoreConsole = () => {
  console.error = originalError;
  console.warn = originalWarn;
};

// Export filtered console for explicit use
export const filteredConsole = {
  error: console.error,
  warn: console.warn,
  log: console.log,
  info: console.info
};

export default {
  restoreConsole,
  filteredConsole
}; 