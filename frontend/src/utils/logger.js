/**
 * Logger utility for consistent logging across the application
 * Only logs in development mode, except for errors which always log
 */

const isDev = process.env.NODE_ENV === 'development';

export const logger = {
  /**
   * Log informational messages (development only)
   */
  info: (...args) => {
    if (isDev) {
      console.log('[INFO]', ...args);
    }
  },

  /**
   * Log warning messages (development only)
   */
  warn: (...args) => {
    if (isDev) {
      console.warn('[WARN]', ...args);
    }
  },

  /**
   * Log error messages (always logs, even in production)
   */
  error: (...args) => {
    console.error('[ERROR]', ...args);
  },

  /**
   * Log debug messages (development only)
   */
  debug: (...args) => {
    if (isDev) {
      console.debug('[DEBUG]', ...args);
    }
  },

  /**
   * Log API requests (development only)
   */
  api: (method, url, status) => {
    if (isDev) {
      const statusColor = status >= 400 ? '🔴' : status >= 300 ? '🟡' : '🟢';
      console.log(`[API] ${statusColor} ${method?.toUpperCase()} ${url}`, status ? `(${status})` : '');
    }
  }
};

export default logger;
