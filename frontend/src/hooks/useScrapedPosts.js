import { useEffect, useState } from 'react';
import { fetchScrapedPosts } from '../api/scrapedPostsApi.js';
import { normalizeScrapedPosts } from '../utils/scrapedPostTransforms.js';

const CACHE_KEY = 'scraped-posts-cache-v1';
const CACHE_TTL_MS = 5 * 60 * 1000;

const readCache = () => {
  if (typeof window === 'undefined') {
    return null;
  }

  try {
    const rawValue = window.localStorage.getItem(CACHE_KEY);

    if (!rawValue) {
      return null;
    }

    const parsed = JSON.parse(rawValue);

    if (!parsed?.records || !parsed?.savedAt) {
      return null;
    }

    if (Date.now() - parsed.savedAt > CACHE_TTL_MS) {
      return null;
    }

    return parsed.records;
  } catch {
    return null;
  }
};

const writeCache = (records) => {
  if (typeof window === 'undefined') {
    return;
  }

  try {
    window.localStorage.setItem(
      CACHE_KEY,
      JSON.stringify({ records, savedAt: Date.now() })
    );
  } catch {
    // Ignore storage failures and keep the live fetch working.
  }
};

export function useScrapedPosts({ limit = 200 } = {}) {
  const [complaints, setComplaints] = useState(() => {
    const cachedRecords = readCache();

    if (cachedRecords) {
      return normalizeScrapedPosts(cachedRecords);
    }

    return [];
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [source, setSource] = useState(() => (readCache() ? 'cache' : 'backend'));

  useEffect(() => {
    let isActive = true;

    const loadPosts = async () => {
      const cachedRecords = readCache();

      if (cachedRecords) {
        setComplaints(normalizeScrapedPosts(cachedRecords));
        setSource('cache');
      }

      setIsLoading(true);

      try {
        const records = await fetchScrapedPosts({ limit });

        if (!isActive) {
          return;
        }

        setComplaints(normalizeScrapedPosts(records));
        setSource('backend');
        setError(null);
        writeCache(records);
      } catch (loadError) {
        if (!isActive) {
          return;
        }

        const message = loadError instanceof Error ? loadError.message : 'Failed to fetch backend data.';

        if (!cachedRecords) {
          setComplaints([]);
          setSource('error');
        } else {
          setSource('cache');
        }

        setError(message);
      } finally {
        if (isActive) {
          setIsLoading(false);
        }
      }
    };

    loadPosts();

    return () => {
      isActive = false;
    };
  }, [limit]);

  return { complaints, isLoading, error, source };
}