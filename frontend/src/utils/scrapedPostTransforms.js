import localityCoordinates from '../data/localityCoordinates.json';

const DEFAULT_CENTER = { lat: 13.0827, lng: 80.2707 };

const urgencyOrder = { HIGH: 3, MEDIUM: 2, LOW: 1 };

const urgencyWeight = {
  HIGH: 1,
  MEDIUM: 0.6,
  LOW: 0.25,
};

// build a lookup from the provided locality coordinates (keys normalized to lowercase)
const locationCoordinates = Object.fromEntries(
  Object.entries(localityCoordinates).map(([k, v]) => [k.toLowerCase(), { lat: v.lat, lng: v.lng }])
);

const hashText = (text) => {
  let hash = 0;

  for (let index = 0; index < text.length; index += 1) {
    hash = (hash * 31 + text.charCodeAt(index)) >>> 0;
  }

  return hash;
};

const locationToCoordinates = (locationName) => {
  const normalizedLocation = (locationName || 'Unknown location').toLowerCase();

  if (localityCoordinates[normalizedLocation]) {
    return localityCoordinates[normalizedLocation];
  }

  if (locationCoordinates[normalizedLocation]) {
    return locationCoordinates[normalizedLocation];
  }

  const hash = hashText(normalizedLocation);
  const latOffset = ((hash % 200) - 100) / 10000;
  const lngOffset = (((Math.floor(hash / 200)) % 200) - 100) / 10000;

  return {
    lat: DEFAULT_CENTER.lat + latOffset,
    lng: DEFAULT_CENTER.lng + lngOffset,
  };
};

const formatTimestamp = (timestamp, fallbackId) => {
  if (timestamp) {
    return timestamp;
  }

  return new Date(Date.now() - fallbackId * 60 * 60 * 1000).toISOString();
};

export const normalizeScrapedPost = (record, index = 0) => {
  const locationName = (record.location || record.title || 'Unknown location').trim();
  const urgency = (record.urgency || 'LOW').toUpperCase();
  const sentiment = (record.sentiment || 'NEUTRAL').toUpperCase();
  const category = record.category || 'General';
  const text = record.cleaned_text || record.description || record.title || 'No text available';

  let lat;
  let lng;
  if (record.lat != null && record.lng != null) {
    lat = record.lat;
    lng = record.lng;
  } else {
    const coordinates = locationToCoordinates(locationName);
    lat = coordinates.lat;
    lng = coordinates.lng;
  }

  return {
    id: record.id ?? `${locationName}-${index}`,
    lat,
    lng,
    location_name: locationName,
    category,
    urgency,
    sentiment,
    summary: text,
    source: record.source || 'backend',
    urgency_weight: urgencyWeight[urgency] ?? 0.25,
    timestamp: formatTimestamp(record.scraped_at, Number(record.id) || index + 1),
    text,
    title: record.title,
    url: record.url,
  };
};

export const normalizeScrapedPosts = (records = []) => {
  const normalized = records.map((record, index) => normalizeScrapedPost(record, index));

  return normalized.sort((left, right) => {
    const urgencyDifference = urgencyOrder[right.urgency] - urgencyOrder[left.urgency];
    return urgencyDifference !== 0 ? urgencyDifference : left.location_name.localeCompare(right.location_name);
  });
};