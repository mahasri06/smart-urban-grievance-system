import { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer, useMap, useMapEvents } from 'react-leaflet';
import { useScrapedPosts } from '../../hooks/useScrapedPosts.js';
import './Map.css';

import L from 'leaflet';
import 'leaflet.heat';

const toHeatPoints = (complaints) =>
  complaints.map((c) => [c.lat, c.lng, c.urgency_weight ?? 0.25]);

function HeatLayer({ complaints }) {
  const map = useMap();

  useEffect(() => {
    const points = toHeatPoints(complaints);

    const heat = L.heatLayer(points, {
      radius: 35,
      blur: 25,
      maxZoom: 14,
      max: 1.0,
      gradient: {
        0.0: '#1a1aff', // low   — blue
        0.4: '#00e5ff', // low-mid — cyan
        0.6: '#ffff00', // mid   — yellow
        0.8: '#ff6600', // high  — orange
        1.0: '#ff0000', // critical — red
      },
    });

    heat.addTo(map);

    // cleanup on unmount
    return () => {
      map.removeLayer(heat);
    };
  }, [map, complaints]);

  return null;
}

function HeatmapClickHandler({ complaints, onSelectComplaint }) {
  useMapEvents({
    click(event) {
      const nearestComplaint = complaints.reduce(
        (closest, complaint) => {
          const distance = event.target.distance(
            event.latlng,
            L.latLng(complaint.lat, complaint.lng)
          );

          if (!closest || distance < closest.distance) {
            return { complaint, distance };
          }

          return closest;
        },
        null
      );

      if (nearestComplaint && nearestComplaint.distance < 2500) {
        onSelectComplaint({
          complaint: nearestComplaint.complaint,
          point: event.containerPoint,
        });
      } else {
        onSelectComplaint(null);
      }
    },
  });

  return null;
}

function MapView() {
  const chennaiCenter = [13.0827, 80.2707];
  const { complaints, isLoading, source, error } = useScrapedPosts({ limit: 200 });
  const [selectedSpot, setSelectedSpot] = useState(null);
  const [cardPosition, setCardPosition] = useState(null);
  const [showInputForm, setShowInputForm] = useState(false);

  return (
    <div className="map-wrapper">
      <button
        type="button"
        className="map-fab"
        onClick={() => setShowInputForm((prev) => !prev)}
        aria-label="Toggle report form"
      >
        [+]
      </button>

      {showInputForm && (
        <div className="map-form-panel">
          <button type="button" className="image-placeholder" aria-label="Take a picture placeholder">
            <span className="image-placeholder-icon">📷</span>
            <span className="image-placeholder-text">Take a picture</span>
          </button>
          <button type="button" className="location-placeholder" aria-label="Location placeholder">
            <span className="location-pin">📍</span>
            <span className="location-placeholder-text">Location</span>
          </button>
        </div>
      )}

      {/* status pill removed per UI update; map shows full viewport */}

      {selectedSpot && (
        <div
          className="complaint-card"
          style={{
            left: cardPosition ? `${cardPosition.x}px` : '18px',
            top: cardPosition ? `${cardPosition.y}px` : '18px',
          }}
        >
          <button
            type="button"
            className="complaint-card-close"
            onClick={() => {
              setSelectedSpot(null);
              setCardPosition(null);
            }}
            aria-label="Close complaint details"
          >
            ×
          </button>
          <span className="category-tag">{selectedSpot.complaint.category}</span>
          <h3>{selectedSpot.complaint.location_name}</h3>
          <p className="summary-text">{selectedSpot.complaint.summary}</p>
          <div className="meta-row">
              <span>Urgency: <strong>{selectedSpot.complaint.urgency}</strong></span>
            <span>Source: <strong className="source-highlight">{selectedSpot.complaint.source}</strong></span>
          </div>
        </div>
      )}
      <MapContainer
        center={chennaiCenter}
        zoom={12}
        scrollWheelZoom={true}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png" />
        <HeatLayer complaints={complaints} />
        <HeatmapClickHandler
          complaints={complaints}
          onSelectComplaint={(spot) => {
            setSelectedSpot(spot);
            setCardPosition(spot ? { x: spot.point.x, y: spot.point.y } : null);
          }}
        />
      </MapContainer>
    </div>
  );
}

export default MapView;