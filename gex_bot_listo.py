#!/usr/bin/env python3
"""
GEX Morning Briefing Bot — Telegram
Manda niveles gamma automáticamente cada mañana a las 8:00 AM ET
Autor: Claude AI para Jose Fernando
"""

import os
import json
import requests
import schedule
import time
from datetime import datetime
import pytz
import anthropic

# ─── CONFIGURACIÓN ────────────────────────────────────────────
TELEGRAM_TOKEN  = os.environ.get("TELEGRAM_TOKEN", "PEGA_TU_TOKEN_AQUI")
CHAT_ID         = os.environ.get("CHAT_ID", "1743882233")
ANTHROPIC_KEY   = os.environ.get("ANTHROPIC_API_KEY", "PEGA_TU_API_KEY_AQUI")
HORA_ENVIO      = "08:00"  # Hora ET para mandar el briefing

ET = pytz.timezone("America/New_York")

# ─── FUNCIÓN: Obtener niveles GEX con IA ─────────────────────
def get_gex_briefing():
    today = datetime.now(ET)
    date_str = today.strftime("%A %d de %B de %Y")
    weekday  = today.weekday()  # 0=lun, 4=vie

    # Detectar tipo de día
    day_note = ""
    if weekday == 2:
        day_note = "Hoy es MIÉRCOLES — hay vencimiento semanal de opciones SPX. Mencionar que no operar después de las 15:00 ET."
    elif weekday == 4:
        day_note = "Hoy es VIERNES — hay vencimiento semanal general. Mencionar que no operar después de las 15:00 ET."

    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        system=f"""Eres un analista profesional de futuros NQ/MNQ especializado en Gamma Exposure (GEX).
Hoy es {date_str}. {day_note}

Tu trabajo es buscar los niveles GEX actuales de SPX y QQQ/NQ y generar un briefing matutino profesional en español para un scalper de MNQ que opera la sesión NY (9:30-12:00 ET) con cuenta Apex Trader Funding.

El trader usa estos instrumentos:
- MNQU2026 en TradingView (precio ~29,000-30,500 rango actual)
- SPX como referencia macro
- Ratio conversión QQQ→MNQ: ×40.3

Busca y calcula:
1. Niveles SPX: Gamma Flip, Call Wall, Put Wall, Vol Trigger, Max Pain
2. Niveles MNQ: convierte desde QQQ usando ×40.3
3. VIX actual y su lectura
4. Régimen del día (Long/Short Gamma)
5. Sesgo direccional
6. Contexto macro del día (datos económicos, noticias relevantes)

Formato de respuesta — usa EXACTAMENTE este formato con emojis para Telegram:

🌅 *PRE-MARKET · {date_str}*
━━━━━━━━━━━━━━━━━━━━

📊 *SESGO: [ALCISTA/BAJISTA] con [cautela/convicción]*

📈 *MAPA DEL DÍA · SPX*
```
Nivel          Precio    Qué es
Call Wall      X,XXX     Techo del día
Vol Trigger    X,XXX     Resistencia intermedia
Precio actual  X,XXX     Spot ahora
Gamma Flip     X,XXX     Línea del sesgo ⚡
Put Wall       X,XXX     Piso del día
Max Pain       X,XXX     Imán OPEX
```

🎯 *NIVELES MNQ (MNQU2026)*
```
Gamma Flip:  XX,XXX
Call Wall:   XX,XXX
Put Wall:    XX,XXX
```

📉 *CONTEXTO*
• VIX: XX.X — [interpretación]
• Régimen: [Long/Short Gamma] — [qué significa hoy]
• Macro: [datos del día o "Sin datos de alto impacto"]

🎮 *QUÉ BUSCAR HOY*
• [Escenario A alcista con niveles concretos]
• [Escenario B bajista con niveles concretos]
• [Regla especial si es OPEX o dato macro]

⚠️ *REGLA DEL DÍA*
[Una regla concreta de gestión de riesgo para hoy]

_Niveles GEX · Claude AI · Solo uso educativo_""",
        messages=[{
            "role": "user",
            "content": f"Genera el briefing GEX completo para hoy {date_str}. Busca los niveles actuales y manda el análisis."
        }]
    )

    # Extraer texto de la respuesta
    briefing = ""
    for block in response.content:
        if block.type == "text":
            briefing += block.text

    return briefing if briefing else "❌ No se pudo generar el briefing hoy. Revisá manualmente."

# ─── FUNCIÓN: Mandar mensaje a Telegram ──────────────────────
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    
    # Telegram tiene límite de 4096 caracteres por mensaje
    chunks = [message[i:i+4000] for i in range(0, len(message), 4000)]
    
    for chunk in chunks:
        payload = {
            "chat_id": CHAT_ID,
            "text": chunk,
            "parse_mode": "Markdown"
        }
        try:
            r = requests.post(url, json=payload, timeout=30)
            r.raise_for_status()
            print(f"✅ Mensaje enviado: {datetime.now(ET).strftime('%H:%M ET')}")
        except Exception as e:
            print(f"❌ Error enviando a Telegram: {e}")
        time.sleep(0.5)

# ─── FUNCIÓN: Job diario ──────────────────────────────────────
def morning_job():
    now = datetime.now(ET)
    print(f"\n🌅 Generando briefing — {now.strftime('%A %d %b %Y %H:%M ET')}")
    
    # No mandar los fines de semana
    if now.weekday() >= 5:
        print("⏭️ Fin de semana — sin briefing")
        return
    
    try:
        send_telegram("⏳ *Generando briefing del día...*")
        briefing = get_gex_briefing()
        send_telegram(briefing)
    except Exception as e:
        error_msg = f"❌ Error en el briefing de hoy: {str(e)}"
        print(error_msg)
        send_telegram(error_msg)

# ─── FUNCIÓN: Comando /niveles manual ────────────────────────
def handle_manual_request():
    """Llama esto para pedir los niveles manualmente en cualquier momento"""
    print("📡 Solicitud manual de niveles...")
    send_telegram("📡 *Solicitud manual recibida — generando niveles...*")
    briefing = get_gex_briefing()
    send_telegram(briefing)

# ─── FUNCIÓN: Test de conexión ───────────────────────────────
def test_connection():
    msg = """✅ *Bot GEX conectado correctamente*

🤖 NQ · GEX Morning Briefing Bot
📅 Enviará niveles cada mañana a las 8:00 AM ET (lunes a viernes)

Comandos disponibles:
• El bot manda los niveles automáticamente cada mañana
• Para niveles manuales ejecutá: python bot.py --manual

_Claude AI · Apex Trader Funding · MNQU2026_"""
    send_telegram(msg)
    print("✅ Test de conexión exitoso")

# ─── SCHEDULER ───────────────────────────────────────────────
def run_scheduler():
    print(f"🚀 Bot iniciado — enviará briefing a las {HORA_ENVIO} ET (lun-vie)")
    print(f"📱 Chat ID: {CHAT_ID}")
    
    # Test inicial
    test_connection()
    
    # Programar envío diario
    schedule.every().day.at(HORA_ENVIO).do(morning_job)
    
    print(f"⏰ Próximo envío: {schedule.next_run()}")
    
    while True:
        schedule.run_pending()
        time.sleep(30)

# ─── MAIN ────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            test_connection()
        elif sys.argv[1] == "--manual":
            handle_manual_request()
        elif sys.argv[1] == "--now":
            morning_job()
    else:
        run_scheduler()
