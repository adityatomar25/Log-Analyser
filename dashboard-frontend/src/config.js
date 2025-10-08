// API configuration for different environments with Safari compatibility
const config = {
  // Use environment variable if available, otherwise try multiple endpoints for browser compatibility
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://127.0.0.1:8000',
  
  // Fallback URLs for different browsers (especially Safari)
  FALLBACK_URLS: [
    'http://127.0.0.1:8000',
    'http://localhost:8000'
  ]
};

export default config;
