import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner")
tf.write("Felsäker version – RSI + Volym + MACD")

# Komprimerad lista för att garantera snabb och stabil laddning
AKTIER = [
    "VOLV-B.ST", "AZN.ST", "EVO.ST", "INVE-B.ST", "SEB-A.ST", "SHB-A.ST", "SWED-A.ST", "ERIC-B.ST", "TELIA.ST",
    "SAND.ST", "ATCO-A.ST", "SKF-B.ST", "BOL.ST", "HEXA-B.ST", "ASSA-B.ST", "NIBE-B.ST", "SBB-B.ST", "SINCH.ST",
    "SAAB-B.ST", "GETI-B.ST", "HM-B.ST", "BALD-B.ST", "CAST.ST", "SSAB-B.ST",
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "LLY", "V",
    "UNH", "JPM", "MA", "AVGO", "HD", "XOM", "COST", "AMD", "NFLX",
    "ADBE", "CRM", "INTC", "CSCO", "PANW", "PLTR", "COIN", "UBER"
]

# Initiera minne i sessionen
if "ultra_köp" not in tf.session_state: tf.session_state.ultra_köp = []
if "ultra_sälj" not in tf.session_state: tf.session_state.ultra_sälj = []
if "alla_aktier" not in tf.session_state: tf.session_state.alla_aktier = []
if "har_skannat" not in tf.session_state: tf.session_state.har_skannat = False

# 1. STARTKNAPP HÖGST UPP
if tf.button("STARTA ANALYS ⚡", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Hämtar: {ticker}...")
        progress_bar.progress((i + 1) / len(AKTIER))
        
        try:
            # Hämta historik dygnsdata
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            # Kontrollera att vi faktiskt fick data och att den inte är tom
            if df.empty or len(df) < 20:
                continue
                
            # Säkerställ att vi har rätt kolumner och städa bort eventuella MultiIndex-problem
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            # Beräkna indikatorer (Felsäkrat)
            close_series = pd.Series(df['Close'].dropna().values.flatten())
            volume_series = pd.Series(df['Volume'].dropna().values.flatten())
            
            if len(close_series) < 15:
                continue
                
            df_rsi = ta.momentum.rsi(close_series, window=14)
            df_vol_snitt = volume_series.rolling(window=10).mean()
            macd_obj = ta.trend.MACD(close_series)
            df_macd = macd_obj.macd()
            df_macd_sig = macd_obj.macd_signal()
            
            # Plocka ut de senaste värdena
            pris = float(close_series.iloc[-1])
            rsi = float(df_rsi.iloc[-1])
            vol = float(volume_series.iloc[-1])
            v_snitt = float(df_vol_snitt.iloc[-1])
            m = float(df_macd.iloc[-1])
            s = float(df_macd_sig.iloc[-1])
            
            m_igår = float(df_macd.iloc[-2])
            s_igår = float(df_macd_sig.iloc[-2])
            
            macd_korsat_upp = m > s and m_igår <= s_igår
            macd_korsat_ner = m < s and m_igår >= s_igår

            # Spara till stora listan (om allt gick bra)
            temp_alla.append({
                "Aktie": ticker,
                "Pris": round(pris, 2),
                "RSI": round(rsi, 1)
            })

            # Kolla strategier
            if rsi <= 35 and vol > v_snitt and macd_korsat_upp:
                temp_köp.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Volym": f"+{((vol/v_snitt)-1)*100:.0f}%"
                })
            elif rsi >= 70 or macd_korsat_ner:
                anledning = "Överköpt" if rsi >= 70 else "MACD Sälj"
                temp_sälj.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Info": anledning
                })
        except Exception as e:
            # Om en enskild aktie kraschar, ignorera den och fortsätt
            continue

    # Spara till sessionen
    tf.session_state.ultra_köp = temp_köp
    tf.session_state.ultra_sälj = temp_sälj
    tf.session_state.alla_aktier = temp_alla
    tf.session_state.har_skannat = True

    progress_bar.empty()
    status_text.empty()

# --- UTMATNING (PRESENTATION AV DATA) ---

if tf.session_state.har_skannat:
    
    # KÖP-SEKTION
    tf.success("🌟 FÖRESLAGNA ULTRA-KÖP")
    if tf.session_state.ultra_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_köp), use_container_width=True)
    else:
        tf.info("Inga aktier uppfyller alla tre köpkriterier just nu.")
        
    # SÄLJ-SEKTION
    tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
    if tf.session_state.ultra_sälj:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
    else:
        tf.info("Inga säljsignaler just nu.")
        
    # STORA LISTAN (Här tvingar vi fram rådata för att se att det laddar)
    tf.subheader("📊 Marknadsöversikt (Sorterad på lägst RSI)")
    if tf.session_state.alla_aktier:
        df_visa = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        tf.dataframe(df_visa, use_container_width=True)
    else:
        tf.warning("Listan kunde inte skapas. Kontrollera internetuppkopplingen mot Yahoo Finance.")

else:
    tf.info("Klicka på knappen ovan för att starta skanningen.")

# KALKYLATOR LÄNGST NER
tf.write("---")
tf.subheader("💼 Trade-Kalkylator")
kp = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)
if kp > 0:
    tf.success(f"🎯 Målkurs (+5%): **{kp * 1.05:.2f}**")
    tf.error(f"🛑 Stop Loss (-3%): **{kp * 0.97:.2f}**")
