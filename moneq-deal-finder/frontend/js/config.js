window.MONEQ_CONFIG = {
  API_BASE_URL: window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
    ? 'http://localhost:8000'
    : 'http://localhost:8000',
  REFRESH_INTERVAL_MS: 60000
};
