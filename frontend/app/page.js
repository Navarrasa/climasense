"use client";
import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, CartesianGrid, ResponsiveContainer, Legend,
} from "recharts";

const API = process.env.NEXT_PUBLIC_API || "http://127.0.0.1:8010";
const Mapa = dynamic(() => import("./Mapa"), { ssr: false });

const INDICADORES = [
  ["temperatura", "Temperatura", "°C"],
  ["umidade", "Umidade", "%"],
  ["pressao", "Pressão", "hPa"],
  ["qualidade_ar", "Qualidade do ar (AQI)", ""],
  ["luminosidade", "Luminosidade", "%"],
  ["chuva_mm", "Chuva", "mm"],
];

export default function Home() {
  const [estacoes, setEstacoes] = useState([]);
  const [sel, setSel] = useState(1);
  const [serie, setSerie] = useState([]);
  const [stats, setStats] = useState(null);
  const [grafico, setGrafico] = useState("temperatura");
  const [proxima, setProxima] = useState(null);
  const [erro, setErro] = useState(null);

  async function carregar() {
    try {
      const [e, l, s] = await Promise.all([
        fetch(`${API}/estacoes`).then((r) => r.json()),
        fetch(`${API}/leituras?estacao_id=${sel}&horas=24`).then((r) => r.json()),
        fetch(`${API}/estatisticas?estacao_id=${sel}&horas=24`).then((r) => r.json()),
      ]);
      setEstacoes(e);
      setSerie(l.map((x) => ({ ...x, hora: x.criado_em.slice(11, 16) })));
      setStats(s);
      setErro(null);
    } catch {
      setErro("Não foi possível conectar à API. O backend está rodando?");
    }
  }

  useEffect(() => {
    carregar();
    const t = setInterval(carregar, 5000); // atualizacao automatica
    return () => clearInterval(t);
  }, [sel]);

  function localizar() {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(async (p) => {
      const r = await fetch(
        `${API}/estacao-mais-proxima?lat=${p.coords.latitude}&lon=${p.coords.longitude}`
      ).then((r) => r.json());
      setProxima(r);
      setSel(r.id);
    });
  }

  const atual = estacoes.find((e) => e.id === sel);
  const ind = INDICADORES.find((i) => i[0] === grafico);

  return (
    <main>
      <header>
        <h1>🌦️ Estação Meteorológica Inteligente</h1>
        <p>Monitoramento ambiental urbano em tempo real — dados abertos ao cidadão.</p>
      </header>

      {erro && <div className="alert" role="alert">{erro}</div>}

      <div className="row">
        <label htmlFor="est">Estação:</label>
        <select id="est" value={sel} onChange={(e) => setSel(Number(e.target.value))}>
          {estacoes.map((e) => <option key={e.id} value={e.id}>{e.nome}</option>)}
        </select>
        <button onClick={localizar}>📍 Estação mais próxima de mim</button>
        {proxima && <span>{proxima.nome} a {proxima.distancia_km} km</span>}
      </div>

      {atual?.alertas?.length
        ? atual.alertas.map((a) => <div key={a} className="alert" role="alert">⚠️ {a}</div>)
        : atual && <div className="ok">✅ Sem alertas climáticos no momento.</div>}

      <section className="grid" aria-label="Indicadores atuais">
        {INDICADORES.map(([k, nome, un]) => (
          <div className="card" key={k}>
            <div className="lbl">{nome}</div>
            <div className="val">{atual?.[k] ?? "--"} <small>{un}</small></div>
          </div>
        ))}
      </section>

      <div className="two">
        <section className="card">
          <div className="row" style={{ marginBottom: 8 }}>
            <b>Últimas 24 h</b>
            <select value={grafico} onChange={(e) => setGrafico(e.target.value)} aria-label="Variável do gráfico">
              {INDICADORES.map(([k, n]) => <option key={k} value={k}>{n}</option>)}
            </select>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={serie}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="hora" minTickGap={30} />
              <YAxis domain={["auto", "auto"]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey={grafico} name={`${ind[1]} ${ind[2]}`} stroke="#1f7a5c" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </section>
        <section className="card">
          <b>Mapa das estações</b>
          <Mapa estacoes={estacoes} selecionada={sel} onSelect={setSel} />
        </section>
      </div>

      {stats && (
        <section className="card" style={{ marginTop: 12 }}>
          <b>Estatísticas (24 h)</b> — {stats.total_validas} leituras válidas,{" "}
          {stats.total_invalidas} descartadas pela validação
          <table>
            <thead><tr><th>Variável</th><th>Mín</th><th>Máx</th><th>Média</th><th>Mediana</th><th>Desvio</th></tr></thead>
            <tbody>
              {INDICADORES.map(([k, n]) => stats[k] && (
                <tr key={k}><td>{n}</td><td>{stats[k].min}</td><td>{stats[k].max}</td>
                  <td>{stats[k].media}</td><td>{stats[k].mediana}</td><td>{stats[k].desvio}</td></tr>
              ))}
            </tbody>
          </table>
        </section>
      )}

      <footer>Dados simulados para fins acadêmicos · Atualização automática a cada 5 s</footer>
    </main>
  );
}
