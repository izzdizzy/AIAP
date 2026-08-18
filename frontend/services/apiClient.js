/**
 * Centralized API Client
 * Provides a standardized HTTP fetch interface with environment base URL resolution,
 * common headers, JSON parsing, error normalization, and support for file uploads.
 */

const DEFAULT_BASE_URL = 'http://localhost:8000';

function getBaseUrl() {
  return (typeof import.meta !== 'undefined' && import.meta.env && import.meta.env.VITE_API_BASE_URL)
    ? import.meta.env.VITE_API_BASE_URL
    : DEFAULT_BASE_URL;
}

/**
 * Standard fetch request wrapper
 * @param {string} endpoint - API path e.g. '/api/predict' or '/diabetes/predict'
 * @param {Object} options - Fetch options (method, body, headers, etc.)
 */
export async function apiClient(endpoint, options = {}) {
  const baseUrl = getBaseUrl();
  const url = endpoint.startsWith('http') ? endpoint : `${baseUrl}${endpoint}`;

  const isFormData = options.body instanceof FormData;
  
  const headers = {
    ...(isFormData ? {} : { 'Content-Type': 'application/json' }),
    ...options.headers,
  };

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      let errorMessage = `Request failed with status ${response.status}`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.detail || errorData.message || errorData.error || errorMessage;
      } catch (e) {
        // Response is not JSON
      }
      throw new Error(errorMessage);
    }

    return await response.json();
  } catch (error) {
    console.error(`[API Client Error] ${options.method || 'GET'} ${url}:`, error.message);
    throw error;
  }
}

export default apiClient;
