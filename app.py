import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner")
tf.write("RSI + Volym + MACD Filter")

# Lista med de 100 mest volatila/populära aktierna (Sverige + USA)
AKTIER = [
    # --- SVERIGE (OMX) ---
    "VOLV-B.ST", "AZN.ST", "EVO.ST", "INVE-B.ST", "SEB-A.ST", "SHB-A.ST", "SWED-A.ST", "NDA-SE.ST", "ERIC-B.ST", "TELIA.ST",
    "SAND.ST", "ATCO-A.ST", "SKF-B.ST", "ALIV-SDB.ST", "BOL.ST", "HEXA-B.ST", "ASSA-B.ST", "NIBE-B.ST", "SBB-B.ST", "SINCH.ST",
    "SAAB-B.ST", "GETI-B.ST", "ELUX-B.ST", "KINV-B.ST", "HM-B.ST", "FABG.ST", "BALD-B.ST", "WIHL.ST", "CAST.ST", "JM.ST",
    "KLED.ST", "TIGO-SDB.ST", "LOOM.ST", "MYCR.ST", "AAK.ST", "BIOT.ST", "LUND-B.ST", "NCC-B.ST", "BILI.ST", "BETCO.ST",
    "ANOT.ST", "SCA-B.ST", "STE-R.ST", "STOR-B.ST", "SKAF-B.ST", "PEAB-B.ST", "JM.ST", "WALL-B.ST", "SSAB-B.ST", "BOL.ST",
    # --- USA (S&P 500 / NASDAQ) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY", "V",
    "UNH", "JPM", "MA", "AVGO", "HD", "XOM", "PG", "COST", "AMD", "NFLX",
    "ADBE", "CRM", "INTC", "CSCO", "TXN", "AMAT", "QCOM", "MU", "PANW", "SNOW",
    "PLTR", "COIN", "MARA", "RIOT", "SOFI", "NIO", "XPEV", "LI", "BABA", "PDD",
    "PYPL", "SQ", "DIS", "BA", "CAT", "GE", "F", "GM", "UBER", "ABNB"
]

tab1, tab2 = tf.tabs(["🔍 Skanner", "💼 Mitt Innehav"])

with tab1:
    if tf.button("KÖR ULTRA-SKANNING ⚡", use_container_width=True):
        status_text = tf.empty()
        progress_bar = tf.progress(0)
        
        köp_lista = []
        sälj_lista = []
        
        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Analyserar {ticker}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            try:
                # Hämta data för de senaste 60 dagarna för att kunna beräkna MACD (26 dagar)
                data = yf.download(ticker, period="60d", interval="1d", progress=False)
                
                if len(data) < 30:
                    continue
                
                # Beräkna RSI (14 dagar)
                data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
                
                # Beräkna Volym-snitt (10 dagar)
                data['Volym_Snitt'] = data['Volume'].rolling(window=10).mean()
                
                # Beräkna MACD
                macd_object = ta.trend.MACD(data['Close'])
                data['MACD'] = macd_object.macd()
                data['MACD_Signal'] = macd_object.macd_signal()
                
                # Hämta de absolut senaste värdena
                senaste_stängning = float(data['Close'].iloc[-1])
                senaste_rsi = float(data['RSI'].iloc[-1])
                senaste_volym = float(data['Volume'].iloc[-1])
                snitt_volym = float(data['Volym_Snitt'].iloc[-1])
                nuvarande_macd = float(data['MACD'].iloc[-1])
                nuvarande_signal = float(data['MACD_Signal'].iloc[-1])
                
                # Kolla om MACD precis har korsat uppåt (idag eller igår)
                macd_korsat_upp = nuvarande_macd > nuvarande_signal and float(data['MACD'].iloc[-2]) <= float(data['MACD_Signal'].iloc[-2])
                macd_korsat_ner = nuvarande_macd < nuvarande_signal and float(data['MACD'].iloc[-2]) >= float(data['MACD_Signal'].iloc[-2])
                
                # --- STRATEGI: ULTRA-KÖP ---
                if senaste_rsi <= 35 and senaste_volym > snitt_volym and macd_korsat_upp:
                    köp_lista.append({
                        "Aktie": ticker, 
                        "Pris": f"{senaste_stängning:.2f}", 
                        "RSI": f"{senaste_rsi:.1f}",
                        "Volym-Ökning": f"+{((senaste_volym/snitt_volym)-1)*100:.0f}%"
                    })
                    
                # --- STRATEGI: ULTRA-SÄLJ ---
                elif senaste_rsi >= 70 or macd_korsat_ner:
                    sälj_lista.append({
                        "Aktie": ticker, 
                        "Pris": f"{senaste_stängning:.2f}", 
                        "RSI": f"{senaste_rsi:.1f}",
                        "Anledning": "Överköpt" if senaste_rsi >= 70 else "MACD Trendbrott"
                    })
                    
            except Exception:
                continue
                
        status_text.success("Skanning klar!")
        progress_bar.empty()
        
        # Visa resultat
        tf.subheader("🌟 FÖRESLAGNA ULTRA-KÖP (RSI + Volym + MACD)")
        if köp_lista:
            tf.dataframe(pd.DataFrame(köp_lista), use_container_width=True)
        else:
            tf.info("Inga aktier uppfyller alla tre kriterier just nu. Avvakta.")
            
        tf.subheader("🚨 FÖRESLAGNA SÄLJ/TA VINST")
        if sälj_lista:
            tf.dataframe(pd.DataFrame(sälj_lista), use_container_width=True)
        else:
            tf.info("Inga starka säljsignaler identifierade.")

with tab2:
    tf.subheader("Räkna på pågående trade")
    tf.write("Skriv in ditt köppris här för att snabbt få ut dina nivåer för traden.")
    
    köppris = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)
    
    if köppris > 0:
        target = köppris * 1.05
        stop_loss = köppris * 0.97
        
        tf.success(f"🎯 Målkurs (+5%): **{target:.2f}**")
        tf.error(f"🛑 Stop Loss (-3%): **{stop_loss:.2f}**")
