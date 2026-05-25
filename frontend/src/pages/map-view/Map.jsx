import 'leaflet/dist/leaflet.css';
import { MapContainer, TileLayer } from 'react-leaflet';

function MapView() {

  return (
    <>
      <div className='map-wrapper'>
        <MapContainer center={[13.0827, 80.2707]} zoom={12} scrollWheelZoom={true} style={{ height: '400px', width: '100%' }}>
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          />
        </MapContainer>
      </div>
    </>
  )
}

export default MapView