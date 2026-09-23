import apiClient from './apiClient';

/** Fetches the public Spring Boot readiness data shown on the landing page. */
export async function getApiStatus() {
  const response = await apiClient.get('/status');
  return response.data;
}
