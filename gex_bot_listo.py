#!/usr/bin/env python3
"""
GEX Morning Briefing Bot — Telegram
Bot de Jose Fernando — @gex_nq_fer_bot
Incluye: Niveles GEX + Mapa de Liquidez + Plan del dia
"""

import requests
import schedule
import time
from datetime import datetime
import pytz
import anthropic
import os
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "PEGA_TU_TOKEN_AQUI")
CHAT_ID        = os.environ.get("CHAT_ID", "1743882233")
ANTHROPIC_KEY  = os.environ.get("ANTHROPIC_API_KEY", "PEGA_TU_API_KEY_AQUI")
HORA_ENVIO     = "01:18"

ET = pytz.timezone("America/New_York")

def get_full_briefing():
    today    = datetime.now(ET)
    date_str = today.strftime("%A %d de %B de %Y")
    weekday  = today.weekday()

    day_note = ""
    if weekday == 2:
        day_note = "Hoy es MIERCOLES - vencimiento semanal SPX. No operar despues de las 15:00 ET."
    elif weekday == 4:
        day_note = "Hoy es VIERNES - vencimiento semanal. No operar despues de las 15:00 ET."
    elif weekday == 0:
        day_note = "Hoy es LUNES - primer dia de semana, niveles frescos post-weekend."

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=f"""Eres un analista profesional de futuros NQ/MNQ especializado en Gamma Exposure GEX y liquidez de mercado.
Hoy es {date_str}. {day_note}

El trader usa MNQU2026 en TradingView, cuenta Apex Trader Funding, sesion NY 9:30-12:00 ET.
Ratio conversion QQQ a MNQ: x40.3

Busca los niveles GEX actuales de SPX y QQQ. Tambien busca el precio actual de NQ futuros, VIX, y cualquier dato macro relevante del dia.

Responde con EXACTAMENTE este formato para Telegram (texto plano, sin markdown complejo):

PRE-MARKET - {date_str}
SESGO: ALCISTA/BAJISTA con cautela/conviccion

MAPA DEL DIA - SPX
Call Wall:     X,XXX  Techo del dia
Vol Trigger:   X,XXX  Resistencia intermedia
Precio:        X,XXX  Spot actual
Gamma Flip:    X,XXX  Linea del sesgo CLAVE
Put Wall:      X,XXX  Piso del dia
Max Pain:      X,XXX  Iman OPEX

NIVELES MNQ (MNQU2026)
Gamma Flip:  XX,XXX
Call Wall:   XX,XXX
Put Wall:    XX,XXX

CONTEXTO
VIX: XX.X - interpretacion breve
Regimen: Long/Short Gamma
Macro: datos del dia o Sin datos de alto impacto

---

MAPA DE LIQUIDEZ - ZONAS CLAVE

LIQUIDEZ ALTA (zonas donde el precio va a buscar stops):
1. [precio] - [nombre nivel] - [por que hay liquidez ahi]
2. [precio] - [nombre nivel] - [por que hay liquidez ahi]
3. [precio] - [nombre nivel] - [por que hay liquidez ahi]

LIQUIDEZ MEDIA:
4. [precio] - [nombre nivel] - [descripcion breve]
5. [precio] - [nombre nivel] - [descripcion breve]

NIVELES REDONDOS IMPORTANTES HOY:
[lista de niveles redondos relevantes en el rango del dia]

---

SETUPS DEL DIA

SETUP A - [nombre del setup]:
Zona entrada: XX,XXX - XX,XXX
Señal: [que buscar para entrar]
SL: XX,XXX ([referencia])
TP1: XX,XXX | TP2: XX,XXX
R:R: 1:X
Por que funciona: [confluencia de niveles]

SETUP B - [nombre del setup]:
Zona entrada: XX,XXX - XX,XXX
Señal: [que buscar para entrar]
SL: XX,XXX ([referencia])
TP1: XX,XXX | TP2: XX,XXX
R:R: 1:X
Por que funciona: [confluencia de niveles]

---

REGLA DEL DIA
[Una regla concreta de gestion de riesgo para hoy]

HORARIO
[Alertas de horario especial si aplica - OPEX, datos macro, etc]

Niveles GEX - Claude AI - Solo uso educativo""",
        messages=[{"role": "user", "content": f"Genera el briefing completo con niveles GEX, mapa de liquidez y setups para hoy {date_str}."}]
    )

    briefing = ""
    for block in response.content:
        if block.type == "text":
            briefing += block.text
    return briefing or "No se pudo generar el briefing hoy."

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    for chunk in chunks:
        try:
            r = requests.post(url, json={"chat_id": CHAT_ID, "text": chunk}, timeout=30)
            print(f"Enviado: {r.status_code}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(0.5)

def morning_job():
    now = datetime.now(ET)
    if now.weekday() >= 5:
        print("Fin de semana - sin briefing")
        return
    print(f"Generando briefing completo - {now.strftime('%A %d %b %H:%M ET')}")
    send_telegram("Generando briefing del dia con niveles GEX + liquidez + setups...")
    briefing = get_full_briefing()
    send_telegram(briefing)

def test_connection():
    send_telegram("Bot GEX actualizado! Ahora incluye niveles GEX + mapa de liquidez + setups del dia. Lunes a viernes 8:00 AM ET. Claude AI")
    print("Test OK")

if __name__ == "__main__":
    import os, sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_connection()
        elif sys.argv[1] in ("--manual", "--now"):
            morning_job()
    else:
       print(f"Bot iniciado - enviara briefing a las {HORA_ENVIO} ET")
        test_connection()
        last_run_date = None
        while True:
            now_et = datetime.now(ET)
            if now_et.strftime("%H:%M") == HORA_ENVIO and last_run_date != now_et.date():
                morning_job()
                last_run_date = now_et.date()
            time.sleep(20)
