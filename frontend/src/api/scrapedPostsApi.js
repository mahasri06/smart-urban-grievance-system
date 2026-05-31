export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? '';

const buildUrl = (path, params = {}) => {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && value !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
    .join('&');

  const base = API_BASE_URL || window.location.origin;
  return query ? `${base}${path}?${query}` : `${base}${path}`;
};

const parseJson = async (response) => {
  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(errorText || `Request failed with status ${response.status}`);
  }

  return response.json();
};

export async function fetchScrapedPosts({ limit = 200, minCredibility = 0 } = {}) {
  const response = await fetch(buildUrl('/analytics/scraped-posts', {
    limit,
    min_credibility: minCredibility,
  }));

  return parseJson(response);
}