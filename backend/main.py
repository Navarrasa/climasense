"""API da Estacao Meteorologica Inteligente (FastAPI + SQLite)."""
import math
import sqlite3
import statistics
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DB = Path(__file__).with_name("estacao.db")

# Faixas fisicamente plausiveis (validacao por logica proposicional)
LIMITES = {
    "temperatura": (-10, 60),
    "umidade": (0, 100),
    "pressao": (900, 1100),
    "qualidade_ar": (0, 500),
    "luminosidade": (0, 100),
    "chuva_mm": (0, 300),
}

ESTACOES = [
    # id, nome, lat, lon  (bairros de Sao Paulo, mockados)
    (1, "Estação Paulista", -23.5614, -46.6559),
    (2, "Estação Ibirapuera", -23.5874, -46.6576),
    (3, "Estação Tatuapé", -23.5405, -46.5766),
]

app = FastAPI(title="Estação Meteorológica Inteligente")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@contextmanager
def conn():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def init_db():
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS estacoes (
                id INTEGER PRIMARY KEY, nome TEXT NOT NULL, lat REAL NOT NULL, lon REAL NOT NULL);
            CREATE TABLE IF NOT EXISTS leituras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estacao_id INTEGER NOT NULL REFERENCES estacoes(id),
                criado_em TEXT NOT NULL,
                temperatura REAL, umidade REAL, pressao REAL,
                qualidade_ar REAL, luminosidade REAL, chuva_mm REAL,
                valido INTEGER NOT NULL);
            CREATE INDEX IF NOT EXISTS idx_leit ON leituras(estacao_id, criado_em);
            """
        )
        c.executemany("INSERT OR IGNORE INTO estacoes VALUES (?,?,?,?)", ESTACOES)


init_db()


class Leitura(BaseModel):
    estacao_id: int
    temperatura: float
    umidade: float
    pressao: float
    qualidade_ar: float
    luminosidade: float
    chuva_mm: float
    criado_em: datetime | None = None


def validar(d: dict) -> bool:
    """valido = AND de (min <= x <= max) para todos os campos."""
    return all(lo <= d[k] <= hi for k, (lo, hi) in LIMITES.items())


def alertas_para(d: dict) -> list[str]:
    a = []
    if d["temperatura"] > 35 and d["umidade"] < 30:
        a.append("Calor extremo com ar seco: hidrate-se e evite sol forte.")
    if d["qualidade_ar"] > 150:
        a.append("Qualidade do ar ruim: evite exercícios ao ar livre.")
    if d["chuva_mm"] > 10:
        a.append("Chuva forte: risco de alagamentos.")
    if d["umidade"] < 20:
        a.append("Umidade crítica (abaixo de 20%).")
    return a


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    """Distancia entre dois pontos na esfera (geometria analitica)."""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


@app.post("/leituras", status_code=201)
def criar_leitura(l: Leitura):
    d = l.model_dump()
    ok = validar(d)
    ts = (l.criado_em or datetime.now()).isoformat(timespec="seconds")
    with conn() as c:
        if not c.execute("SELECT 1 FROM estacoes WHERE id=?", (l.estacao_id,)).fetchone():
            raise HTTPException(404, "Estação não encontrada")
        c.execute(
            "INSERT INTO leituras (estacao_id, criado_em, temperatura, umidade, pressao,"
            " qualidade_ar, luminosidade, chuva_mm, valido) VALUES (?,?,?,?,?,?,?,?,?)",
            (l.estacao_id, ts, l.temperatura, l.umidade, l.pressao,
             l.qualidade_ar, l.luminosidade, l.chuva_mm, int(ok)),
        )
    return {"valido": ok, "alertas": alertas_para(d) if ok else []}


@app.get("/estacoes")
def listar_estacoes():
    with conn() as c:
        rows = c.execute(
            """SELECT e.*, l.temperatura, l.umidade, l.pressao, l.qualidade_ar,
                      l.luminosidade, l.chuva_mm, l.criado_em
               FROM estacoes e LEFT JOIN leituras l ON l.id = (
                   SELECT id FROM leituras WHERE estacao_id=e.id AND valido=1
                   ORDER BY criado_em DESC LIMIT 1)"""
        ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        d["alertas"] = alertas_para(d) if d["temperatura"] is not None else []
        out.append(d)
    return out


@app.get("/leituras")
def listar_leituras(estacao_id: int = 1, horas: int = 24):
    desde = (datetime.now() - timedelta(hours=horas)).isoformat(timespec="seconds")
    with conn() as c:
        rows = c.execute(
            "SELECT * FROM leituras WHERE estacao_id=? AND valido=1 AND criado_em>=?"
            " ORDER BY criado_em",
            (estacao_id, desde),
        ).fetchall()
    return [dict(r) for r in rows]


@app.get("/estatisticas")
def estatisticas(estacao_id: int = 1, horas: int = 24):
    dados = listar_leituras(estacao_id, horas)
    with conn() as c:
        invalidas = c.execute(
            "SELECT COUNT(*) FROM leituras WHERE estacao_id=? AND valido=0", (estacao_id,)
        ).fetchone()[0]
    res = {"total_validas": len(dados), "total_invalidas": invalidas}
    for campo in LIMITES:
        vals = [d[campo] for d in dados]
        if vals:
            res[campo] = {
                "min": round(min(vals), 1),
                "max": round(max(vals), 1),
                "media": round(statistics.mean(vals), 1),
                "mediana": round(statistics.median(vals), 1),
                "desvio": round(statistics.pstdev(vals), 2),
            }
    return res


@app.get("/estacao-mais-proxima")
def mais_proxima(lat: float, lon: float):
    with conn() as c:
        est = [dict(r) for r in c.execute("SELECT * FROM estacoes")]
    for e in est:
        e["distancia_km"] = round(haversine_km(lat, lon, e["lat"], e["lon"]), 2)
    return min(est, key=lambda e: e["distancia_km"])
