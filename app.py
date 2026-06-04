import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner")
tf.write("RSI + Volym + MACD Filter")

# Lista med de 100 mest volatila/populära aktierna
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

# Variabler för att spara data i appens minne under körning
if "ultra_köp" not in tf.session_state: tf.session_state.ultra_köp = None
if "ultra_sälj" not in tf.session_state: tf.session_state.ultra_sälj = None
if "alla_aktier" not in tf.session_state: tf.session_state.alla_aktier = None

# Startknapp högst upp
if tf.button("STARTA ANALYS ⚡ (Hämtar data för 100 aktier)", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Analyserar {ticker}...")
        progress_bar.progress((i + 1) / len(AKTIER))
        
        try:
            data = yf.download(ticker, period="60d", interval="1d", progress=False)
            if len(data) < 30: continue
            
            # Beräkningar
            data['RSI'] = ta.momentum.rsi(data['Close'], window=14)
            data['Volym_Snitt'] = data['Volume'].rolling(window=10).mean()
            macd_obj = ta.trend.MACD(data['Close'])
            data['MACD'] = macd_obj.macd()
            data['MACD_Signal'] = macd_obj.macd_signal()
            
            # Senaste värden
            pris = float(data['Close'].iloc[-1])
            rsi = float(data['RSI'].iloc[-1])
            vol = float(data['Volume'].iloc[-1])
            v_snitt = float(data['Volym_Snitt'].iloc[-1])
            m = float(data['MACD'].iloc[-1])
            s = float(data['MACD_Signal'].iloc[-1])
            
            # Kolla MACD-korsning
            m_igår = float(data['MACD'].iloc[-2])
            s_igår = float(data['MACD_Signal'].iloc[-2])
            macd_korsat_upp = m > s and m_igår <= s_igår
            macd_korsat_ner = m < s and m_igår >= s_igår

            # Spara till stora listan
            temp_alla.append({
                "Aktie": ticker,
                "Pris": round(pris, 2),
                "RSI": round(rsi, 1)
            })

            # Kolla Ultra-kriterier
            if rsi <= 35 and vol > v_snitt and macd_korsat_upp:
                temp_köp.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Volym": f"+{((vol/v_snitt)-1)*100:.0f}%"
                })
            elif rsi >= 70 or macd_korsat_ner:
                anledning = "Överköpt" if rsi >= 70 else "Trendbrott (MACD)"
                temp_sälj.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Anledning": anledning
                })
        except:
            continue

    # Spara resultaten till session_state
    tf.session_state.ultra_köp = temp_köp
    tf.session_state.ultra_sälj = temp_sälj
    tf.session_state.alla_aktier = temp_alla

    progress_bar.empty()
    status_text.empty()
    
    # Tvinga appen att ladda om och visa all data direkt
    tf.rerun()

# Skapa flikar EFTER knappen så att datan ritas ut korrekt
tab1, tab2, tab3 = tf.tabs(["🌟 Ultra-Skanner", "📊 Allas RSI", "💼 Trade-Kalkylator"])

# --- FLIK 1: ULTRA SKANNER ---
with tab1:
    tf.subheader("💎 Ultra-signaler (Hög träffsäkerhet)")
    tf.write("Visar aktier där RSI, Volym och MACD samverkar.")
    
    if tf.session_state.ultra_köp is not None:
        tf.success("🌟 FÖRESLAGNA ULTRA-KÖP")
        if tf.session_state.ultra_köp:
            tf.dataframe(pd.DataFrame(tf.session_state.ultra_köp), use_container_width=True)
        else:
            tf.info("Inga aktier uppfyller alla köpkriterier just nu.")
            
        tf.write("---")
        tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
        if tf.session_state.ultra_sälj:
            tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
        else:
            tf.info("Inga starka säljsignaler just nu.")
    else:
        tf.info("Klicka på 'STARTA ANALYS' högst upp för att starta.")

# --- FLIK 2: ALLAS RSI ---
with tab2:
    tf.subheader("📈 Marknadsöversikt")
    tf.write("Alla 100 aktier sorterade efter lägst RSI först.")
    
    if tf.session_state.alla_aktier is not None:
        if tf.session_state.alla_aktier:
            df_alla = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
            tf.dataframe(df_alla, use_container_width=True, height=600)
        else:
            tf.warning("Ingen data hittades efter körning.")
    else:
        tf.info("Klicka på 'STARTA ANALYS' högst upp för att ladda listan.")

# --- FLIK 3: KALKYLATOR ---
with tab3:
    tf.subheader("Räkna på pågående trade")
    kp = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)
    if kp > 0:
        tf.success(f"🎯 Målkurs (+5%): **{kp * 1.05:.2f}**")
        tf.error(f"🛑 Stop Loss (-3%): **{kp * 0.97:.2f}**")
