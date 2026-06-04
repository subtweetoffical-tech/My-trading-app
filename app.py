import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner")

# --- INFORMATIONSFLIK (UTFÄLLBAR) ---
with tf.expander("ℹ️ SÅ HÄR FUNGERAR APPEN (Klicka för att öppna)"):
    tf.markdown("""
    ### Skillnaden på Köpsignalerna:
    
    * **🌟 ULTRA-KÖP:** Den säkraste signalen. Kräver att RSI är lågt (<35), Volymen är hög (RVOL >= 1.5) OCH että MACD precis har vänt uppåt.
    * **👍 REKOMMENDERADE KÖP:** En klassisk "köp dippen"-signal. Aktier som har fallit extremt hårt på kort tid där RSI har pressats under 30. Perfekt för att fånga snabba studsar.
    """)

# UTÖKAD LISTA: 120 handplockade daytrading-aktier (Sverige + USA)
AKTIER = [
    # --- SVERIGE (OMX - 60 st högvolatila & likvida) ---
    "VOLV-B.ST", "AZN.ST", "EVO.ST", "INVE-B.ST", "SEB-A.ST", "SHB-A.ST", "SWED-A.ST", "ERIC-B.ST", "TELIA.ST",
    "SAND.ST", "ATCO-A.ST", "SKF-B.ST", "BOL.ST", "HEXA-B.ST", "ASSA-B.ST", "NIBE-B.ST", "SBB-B.ST", "SINCH.ST",
    "SAAB-B.ST", "GETI-B.ST", "HM-B.ST", "KINV-B.ST", "ELUX-B.ST", "BALD-B.ST", "CAST.ST", "SSAB-B.ST", "SCA-B.ST",
    "ALIV-SDB.ST", "JM.ST", "NCC-B.ST", "PEAB-B.ST", "BILI.ST", "FABG.ST", "WIHL.ST", "WALL-B.ST", "MYCR.ST",
    "AAK.ST", "BIOT.ST", "LUND-B.ST", "BETCO.ST", "ANOT.ST", "STE-R.ST", "STOR-B.ST", "SKAF-B.ST", "LOOM.ST",
    "TIGO-SDB.ST", "KLED.ST", "SRECO.ST", "HPOL-B.ST", "LIFCO-B.ST", "INDT.ST", "ADDTECH-B.ST", "LAGR-B.ST", 
    "AXFO.ST", "ICA.ST", "ALFA.ST", "DOM.ST", "FING-B.ST", "VITR.ST", "SCA-A.ST",
    # --- USA (NASDAQ / S&P 500 - 60 st teknik, AI, krypto & momentum) ---
    "AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "META", "TSLA", "BRK-B", "LLY", "V",
    "UNH", "JPM", "MA", "AVGO", "HD", "XOM", "PG", "COST", "AMD", "NFLX",
    "ADBE", "CRM", "INTC", "CSCO", "TXN", "AMAT", "QCOM", "MU", "PANW", "SNOW",
    "PLTR", "COIN", "MARA", "RIOT", "SOFI", "NIO", "XPEV", "LI", "BABA", "PDD",
    "PYPL", "SQ", "DIS", "BA", "CAT", "GE", "F", "GM", "UBER", "ABNB",
    "SMCI", "MSTR", "HOOD", "AFRM", "UPST", "RIVN", "LCID", "DKNG", "PINS", "ROKU"
]

# Initiera minne i sessionen
if "ultra_köp" not in tf.session_state: tf.session_state.ultra_köp = []
if "rek_köp" not in tf.session_state: tf.session_state.rek_köp = []
if "ultra_sälj" not in tf.session_state: tf.session_state.ultra_sälj = []
if "alla_aktier" not in tf.session_state: tf.session_state.alla_aktier = []
if "har_skannat" not in tf.session_state: tf.session_state.har_skannat = False

# 1. STARTKNAPP HÖGST UPP
if tf.button("STARTA ULTRA-ANALYS ⚡ (Skanna 120 aktier)", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Skannar ({i+1}/120): {ticker}...")
        progress_bar.progress((i + 1) / len(AKTIER))
        
        try:
            # Hämtar 15m-data (Begränsat till 20 dagar för max hastighet med 120 aktier)
            df = yf.download(ticker, period="20d", interval="15m", progress=False)
            
            if df.empty or len(df) < 30:
                continue
                
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            close_series = pd.Series(df['Close'].dropna().values.flatten())
            volume_series = pd.Series(df['Volume'].dropna().values.flatten())
            open_series = pd.Series(df['Open'].dropna().values.flatten())
            
            if len(close_series) < 15:
                continue
                
            # Beräkningar
            df_rsi = ta.momentum.rsi(close_series, window=14)
            df_vol_snitt = volume_series.rolling(window=10).mean()
            macd_obj = ta.trend.MACD(close_series)
            df_macd = macd_obj.macd()
            df_macd_sig = macd_obj.macd_signal()
            
            # Senaste värden
            pris = float(close_series.iloc[-1])
            öppning = float(open_series.iloc[-1])
            rsi = float(df_rsi.iloc[-1])
            vol = float(volume_series.iloc[-1])
            v_snitt = float(df_vol_snitt.iloc[-1])
            m = float(df_macd.iloc[-1])
            s = float(df_macd_sig.iloc[-1])
            
            # RVOL & Dagsrörelse
            rvol = vol / v_snitt if v_snitt > 0 else 1.0
            dags_utveckling = ((pris - öppning) / öppning) * 100
            
            # MACD korsningar
            m_igår = float(df_macd.iloc[-2])
            s_igår = float(df_macd_sig.iloc[-2])
            macd_korsat_upp = m > s and m_igår <= s_igår
            macd_korsat_ner = m < s and m_igår >= s_igår
            
            macd_status = "Avvakta 🟡"
            if m > s:
                macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
            elif m < s:
                macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

            # Spara till stora listan
            temp_alla.append({
                "Aktie": ticker,
                "Pris": round(pris, 2),
                "Idag %": f"{dags_utveckling:+.2f}%",
                "RSI (15m)": round(rsi, 1),
                "RVOL": f"{rvol:.2f}x",
                "Trend (MACD)": macd_status
            })

            # Sortering till de olika köptabellerna
            if rsi <= 35 and rvol >= 1.5 and macd_korsat_upp:
                temp_ultra_köp.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Idag %": f"{dags_utveckling:+.2f}%"
                })
            elif rsi <= 30:
                temp_rek_köp.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Idag %": f"{dags_utveckling:+.2f}%"
                })
                
            # Säljsignaler
            if rsi >= 70 or macd_korsat_ner:
                anledning = "Överköpt ⚠️" if rsi >= 70 else "Trendbrott 🚨"
                temp_sälj.append({
                    "Aktie": ticker, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Anledning": anledning, "Idag %": f"{dags_utveckling:+.2f}%"
                })
        except:
            continue

    tf.session_state.ultra_köp = temp_ultra_köp
    tf.session_state.rek_köp = temp_rek_köp
    tf.session_state.ultra_sälj = temp_sälj
    tf.session_state.alla_aktier = temp_alla
    tf.session_state.har_skannat = True

    progress_bar.empty()
    status_text.empty()

# --- PRESENTATION PÅ SKÄRMEN ---

if tf.session_state.har_skannat:
    
    # 1. ULTRA-KÖP
    tf.success("🌟 FÖRESLAGNA ULTRA-KÖP (RSI + RVOL + MACD)")
    if tf.session_state.ultra_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_köp), use_container_width=True)
    else:
        tf.info("Inga aktier uppfyller alla tre kriterier just nu.")
        
    # 2. VANLIGA REKOMMENDERADE KÖP
    tf.write("---")
    tf.info("👍 REKOMMENDERADE KÖP (Kraftigt översålda, RSI < 30)")
    if tf.session_state.rek_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.rek_köp), use_container_width=True)
    else:
        tf.info("Inga översålda aktier just nu.")
        
    # 3. SÄLJ
    tf.write("---")
    tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
    if tf.session_state.ultra_sälj:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
    else:
        tf.info("Inga säljsignaler just nu.")
        
    # 4. MARKNADSÖVERSIKT
    tf.write("---")
    tf.subheader("📊 Komplett Marknadsöversikt (120 aktier)")
    if tf.session_state.alla_aktier:
        df_visa = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI (15m)", ascending=True)
        tf.dataframe(df_visa, use_container_width=True, height=500)

else:
    tf.info("Klicka på knappen ovan för att starta skanningen.")

# 5. TRADE-KALKYLATOR
tf.write("---")
tf.subheader("💼 Trade-Kalkylator")
kp = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)
if kp > 0:
    tf.success(f"🎯 Målkurs (+5%): **{kp * 1.05:.2f}**")
    tf.error(f"🛑 Stop Loss (-3%): **{kp * 0.97:.2f}**")
