import time
import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import requests
import pandas as pd
import ta

# --- SERVIDOR FICTÍCIO PARA O RENDER (MANTÉM O WEB SERVICE ATIVO) ---
class DummyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot SUI Ativo!")

def run_dummy_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyServer)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# --- CONFIGURAÇÕES DO BOT ---
TELEGRAM_BOT_TOKEN = "8967950466:AAEAF4Mt2k7xu7tmGH0tXe02L1XAuZUZrd4"
TELEGRAM_CHAT_ID = "8670202643"
SYMBOL = "SUIUSDT"
INTERVAL = "15m"

def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

def get_klines(symbol, interval, limit=100):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval}&limit={limit}"
    response = requests.get(url, timeout=10)
    data = response.json()
    df = pd.DataFrame(data, columns=[
        'timestamp', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = df['close'].astype(float)
    return df

def calculate_rsi(df, period=14):
    rsi_indicator = ta.momentum.RSIIndicator(close=df['close'], window=period)
    df['rsi'] = rsi_indicator.rsi()
    return df

def main():
    send_telegram_message("🤖 *Bot da SUI Iniciado com Sucesso na Nuvem!*")
    last_signal = None

    while True:
        try:
            df = get_klines(SYMBOL, INTERVAL)
            df = calculate_rsi(df)
            
            current_rsi = df['rsi'].iloc[-1]
            current_price = df['close'].iloc[-1]
            
            print(f"SUI: ${current_price:.4f} | RSI (15m): {current_rsi:.2f}")

            # Alerta LONG (Sobrevenda)
            if current_rsi <= 30 and last_signal != "LONG":
                msg = (
                    f"🟢 *SINAL DE LONG (SUI)* 🟢\n\n"
                    f"💰 *Preço:* ${current_price:.4f}\n"
                    f"📊 *RSI (15m):* {current_rsi:.2f}\n"
                    f"⚠️ *Região de Sobrevenda (RSI <= 30)*"
                )
                send_telegram_message(msg)
                last_signal = "LONG"

            # Alerta SHORT (Sobrecompra)
            elif current_rsi >= 70 and last_signal != "SHORT":
                msg = (
                    f"🔴 *SINAL DE SHORT (SUI)* 🔴\n\n"
                    f"💰 *Preço:* ${current_price:.4f}\n"
                    f"📊 *RSI (15m):* {current_rsi:.2f}\n"
                    f"⚠️ *Região de Sobrecompra (RSI >= 70)*"
                )
                send_telegram_message(msg)
                last_signal = "SHORT"

            # Reseta o sinal se o RSI voltar para a zona neutra (entre 40 e 60)
            elif 40 < current_rsi < 60:
                last_signal = None

        except Exception as e:
            print(f"Erro no ciclo: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
