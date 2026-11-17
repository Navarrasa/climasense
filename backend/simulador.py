"""Simula o gateway MQTT: gera leituras como o firmware e envia para a API.

Uso:
    py simulador.py --historico   # popula as ultimas 24 h (1 leitura a cada 15 min)
    py simulador.py               # modo ao vivo: 1 leitura por estacao a cada 5 s
"""
import argparse
import json
import math
import random
import time
import urllib.request
from datetime import datetime, timedelta

API = "http://127.0.0.1:8010/leituras"
OFFSETS = {1: 0.0, 2: -1.2, 3: 0.8}  # microclimas de cada estacao


def gerar(estacao_id: int, quando: datetime) -> dict:
    h = quando.hour + quando.minute / 60
    ciclo = math.sin((h - 9) / 24 * 2 * math.pi)  # pico ~15h
    temp = 24 + 7 * ciclo + OFFSETS[estacao_id] + random.gauss(0, 0.6)
    leitura = {
        "estacao_id": estacao_id,
        "temperatura": round(temp, 1),
        "umidade": round(max(15, min(98, 60 - 25 * ciclo + random.gauss(0, 3))), 1),
        "pressao": round(1013 + 3 * math.cos(h / 24 * 2 * math.pi) + random.gauss(0, 0.5), 1),
        "qualidade_ar": max(0, int(60 + 50 * max(0, math.sin((h - 6) / 12 * math.pi)) + random.gauss(0, 10))),
        "luminosidade": round(max(0, 100 * math.sin((h - 6) / 12 * math.pi)) if 6 <= h <= 18 else 0, 1),
        "chuva_mm": round(max(0, random.gauss(-2, 3)), 1),
        "criado_em": quando.isoformat(timespec="seconds"),
    }
    if random.random() < 0.03:  # ~3% de leituras com defeito de sensor
        leitura["temperatura"] = random.choice([-127.0, 85.0, 999.0])
    return leitura


def enviar(d: dict):
    req = urllib.request.Request(API, json.dumps(d).encode(), {"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--historico", action="store_true")
    a = p.parse_args()
    if a.historico:
        agora = datetime.now()
        t = agora - timedelta(hours=24)
        n = 0
        while t <= agora:
            for e in OFFSETS:
                enviar(gerar(e, t)); n += 1
            t += timedelta(minutes=15)
        print(f"{n} leituras históricas enviadas.")
        return
    print("Modo ao vivo (Ctrl+C para parar)")
    while True:
        for e in OFFSETS:
            d = gerar(e, datetime.now())
            r = enviar(d)
            print(e, d["temperatura"], "°C", "OK" if r["valido"] else "INVÁLIDA", r["alertas"])
        time.sleep(5)


if __name__ == "__main__":
    main()
