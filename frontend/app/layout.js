import "leaflet/dist/leaflet.css";
import "./globals.css";

export const metadata = {
  title: "Estação Meteorológica Inteligente",
  description: "Dashboard público de monitoramento ambiental urbano",
};

export default function RootLayout({ children }) {
  return (
    <html lang="pt-BR">
      <body>{children}</body>
    </html>
  );
}
