import time
import pandas as pd
import requests
import ta

# --- CONFIGURAÇÕES PRONTAS ---
TELEGRAM_TOKEN = "8967950466:AAEAF4Mt2k7xu7tmGH0tXe02L1XAuZUZrd4"
CHAT_ID = "8670202643"
SYMBOL = "SUIUSDT"
INTERVAL = "15m"  # Gráfico de 15 minutos


def enviar_mensagem_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")


def buscar_dados_binance():
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": SYMBOL, "interval": INTERVAL, "limit": 100}

    response = requests.get(url, params=params)
    data = response.json()

    df = pd.DataFrame(
        data,
        columns=[
            "open_time",
            "open",
            "high",
            "low",
            "close",
            "volume",
            "close_time",
            "quote_asset_volume",
            "number_of_trades",
            "taker_buy_base_asset_volume",
            "taker_buy_quote_asset_volume",
            "ignore",
        ],
    )
    df["close"] = df["close"].astype(float)
    return df


def monitorar_sui():
    ultimo_estado = None
    enviar_mensagem_telegram(
        f"🤖 *Bot da SUI Iniciado con Sucesso!*\nMonitorando gráfico de {INTERVAL}..."
    )

    while True:
        try:
            df = buscar_dados_binance()
            df["rsi"] = ta.momentum.RSIIndicator(
                close=df["close"], window=14
            ).rsi_series()

            preco_atual = df["close"].iloc[-1]
            rsi_atual = df["rsi"].iloc[-1]

            print(
                f"[{time.strftime('%H:%M:%S')}] SUI: US$ {preco_atual:.4f} | RSI: {rsi_atual:.2f}"
            )

            # Sinal de LONG (RSI <= 30)
            if rsi_atual <= 30 and ultimo_estado != "LONG":
                msg = (
                    f"🟢 *SINAL DE LONG (SUI)*\n\n"
                    f"• Preço Atual: US$ {preco_atual:.4f}\n"
                    f"• RSI (14): {rsi_atual:.2f}\n"
                    f"• Status: Sobrevendido (Moeda Barata)"
                )
                enviar_mensagem_telegram(msg)
                ultimo_estado = "LONG"

            # Sinal de SHORT (RSI >= 70)
            elif rsi_atual >= 70 and ultimo_estado != "SHORT":
                msg = (
                    f"🔴 *SINAL DE SHORT (SUI)*\n\n"
                    f"• Preço Atual: US$ {preco_atual:.4f}\n"
                    f"• RSI (14): {rsi_atual:.2f}\n"
                    f"• Status: Sobrecomprado (Moeda Esticada)"
                )
                enviar_mensagem_telegram(msg)
                ultimo_estado = "SHORT"

            elif 35 < rsi_atual < 65:
                ultimo_estado = "NEUTRO"

        except Exception as e:
            print(f"Erro no ciclo: {e}")

        time.sleep(60)


if __name__ == "__main__":
    monitorar_sui()
