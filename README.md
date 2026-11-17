# Estação Meteorológica Inteligente — PD-II

```
TinkerCAD (Arduino + sensores) ──JSON──► simulador.py (gateway / "MQTT") ──HTTP──► FastAPI + SQLite ──► Dashboard Next.js
```

## Como rodar (3 terminais)

**1. Backend** (porta 8010)
```bash
cd backend
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python -m uvicorn main:app --port 8010
```
Documentação automática da API: http://127.0.0.1:8010/docs

**2. Dados simulados**
```bash
cd backend
.venv\Scripts\python simulador.py --historico   # 24 h de histórico
.venv\Scripts\python simulador.py               # ao vivo, a cada 5 s
```

**3. Dashboard** (porta 3010)
```bash
cd frontend
npm install
npm run dev
```
Abra http://localhost:3010

> Se o `import pydantic` falhar no Windows, a pasta está num caminho longo demais
> (limite de 260 caracteres). Mova o projeto para algo curto, ex. `C:\pd2`.

## Circuito
Veja `firmware/MONTAGEM_TINKERCAD.md` e cole `firmware/estacao_tinkercad.ino` no TinkerCAD.

## Requisitos × onde estão
| Requisito do manual | Onde |
|---|---|
| Circuito com sensores (2ª etapa) | TinkerCAD: TMP36, LDR, potenciômetros, botão-pluviômetro, LEDs, buzzer |
| Álgebra de Boole | `estacao_tinkercad.ino`: alerta `S = A·B + C + D` → LEDs/buzzer |
| Leitura periódica, filtragem, validação (3ª etapa) | firmware: média móvel de 5 amostras + checagem de faixas |
| Comunicação serial / MQTT | saída JSON na serial; `simulador.py` faz o papel do gateway MQTT |
| API Python + banco (4ª etapa) | `backend/main.py` (FastAPI) + `estacao.db` (SQLite, tabelas `estacoes` e `leituras`) |
| Lógica matemática na validação | `validar()`: conjunção de `min ≤ x ≤ max`; leituras inválidas ficam marcadas e são descartadas |
| Estatística | `/estatisticas`: mín, máx, média, mediana, desvio padrão |
| Geometria analítica / geolocalização | `haversine_km()` + `/estacao-mais-proxima`; mapa Leaflet |
| Dashboard público (5ª etapa) | gráficos interativos, indicadores, mapa, alertas, responsivo, `aria-*` |
| Educação ambiental | mensagens de alerta orientando o cidadão (calor, ar ruim, chuva) |

## Endpoints
`POST /leituras` · `GET /estacoes` · `GET /leituras?estacao_id=1&horas=24` ·
`GET /estatisticas?estacao_id=1` · `GET /estacao-mais-proxima?lat=..&lon=..`
