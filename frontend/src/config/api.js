/**
 * Central API Configuration & Endpoints
 * Automatically selects the base URL according to the current environment (dev/prod).
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

export const API_ENDPOINTS = {
  GENERATE_QUIZ: `${API_BASE_URL}/api/generate-quiz`,
  SUBMIT_ANSWERS: `${API_BASE_URL}/api/submit-answers`,
  SUBMIT_EMAIL: `${API_BASE_URL}/api/submit-email`,
  DOWNLOAD_REPORT: (filename) => `${API_BASE_URL}/api/download-report/${filename}`,
}

export { API_BASE_URL }
export default API_ENDPOINTS
