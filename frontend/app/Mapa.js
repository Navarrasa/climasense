"use client";
import { MapContainer, TileLayer, CircleMarker, Popup } from "react-leaflet";

function cor(t) {
  if (t == null) return "#999";
  if (t >= 30) return "#b3261e";
  if (t >= 25) return "#e08a00";
  return "#1f7a5c";
}

export default function Mapa({ estacoes, selecionada, onSelect }) {
  return (
    <MapContainer center={[-23.56, -46.63]} zoom={12} className="map" scrollWheelZoom={false}>
      <TileLayer
        attribution='&copy; OpenStreetMap'
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {estacoes.map((e) => (
        <CircleMarker
          key={e.id}
          center={[e.lat, e.lon]}
          radius={e.id === selecionada ? 16 : 11}
          pathOptions={{ color: cor(e.temperatura), fillOpacity: 0.7 }}
          eventHandlers={{ click: () => onSelect(e.id) }}
        >
          <Popup>
            <b>{e.nome}</b><br />
            {e.temperatura ?? "--"} °C · {e.umidade ?? "--"}% umidade<br />
            AQI {e.qualidade_ar ?? "--"}
          </Popup>
        </CircleMarker>
      ))}
    </MapContainer>
  );
}
