import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner")

# --- NYHET: INFORMATIONSFLIK (UTFÄLLBAR) ---
with tf.expander("ℹ️ SÅ HÄR FUNGERAR APPEN (Klicka för att öppna)"):
    tf.markdown("""
    ### Hur strategin fungerar:
    Denna skanner letar efter **rebound-lägen** (när en aktie har fallit för mycket och är redo att vända uppåt). För att undvika falska signaler krävs det att tre indikatorer samverkar:
    
    1. **RSI (14):** Mäter om aktien är överköpt eller översåld. Ett värde under 35 betyder att aktien är billig (översåld).
    2. **Volym (10):** Vi jämför dagens volym med ett 10-dagars snitt. Hög volym visar att de stora grabbarna (institutionerna) har börjat köpa.
    3. **MACD:** En trendindikator. Vi kollar om MACD-linjen har korsat sin signal-linje uppåt, vilket bekräftar att säljtrycket är över och trenden är uppåt.
    
    *Tips: De bästa affärerna görs ofta när alla tre ger grön bock samtidigt!*
    """)

# Komprimerad och stabil aktielista
AKTIER = [
    # --- SVERIGE (OMX) ---
    "VOLV-B.ST", "AZN.ST", "EVO.ST", "INVE-B.ST", "SEB-A.ST", "SHB-A.ST", "SWED-A.ST", "ERIC-B.ST", "TELIA.ST",
    "SAND.ST", "ATCO-A.ST", "SKF-B.ST", "BOL.ST", "HEXA-B.ST", "ASSA-B.ST", "NIBE-B.ST", "SBB-B.ST", "SINCH.ST",
    "SAAB-B.ST", "GETI-B.ST", "HM-B.ST", "BALD-B.ST", "CAST.ST", "SSAB-B.ST",
    # --- USA (S&P 500 / NASDAQ) ---
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
if tf.button("STARTA ULTRA-ANALYS ⚡", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Hämtar: {ticker}...")
        progress_bar.progress((i + 1) / len(AKTIER))
        
        try:
            df = yf.download(ticker, period="60d", interval="1d", progress=False)
            
            if df.empty or len(df) < 20:
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
            
            # Beräkna dagsrörelse i procent
            dags_utveckling = ((pris - öppning) / öppning) * 100
            
            # Skapa text för Volym och MACD-status
            volym_text = "Hög 🚀" if vol > v_snitt else "Normal ⚪"
            
            m_igår = float(df_macd.iloc[-2])
            s_igår = float(df_macd_sig.iloc[-2])
            macd_korsat_upp = m > s and m_igår <= s_igår
            macd_korsat_ner = m < s and m_igår >= s_igår
            
            macd_status = "Avvakta 定"
            if m > s:
                macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
            elif m < s:
                macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

            # Spara till stora listan med ALLA nya kolumner
            temp_alla.append({
                "Aktie": ticker,
                "Pris": round(pris, 2),
                "Idag %": f"{dags_utveckling:+.2f}%",
                "RSI": round(rsi, 1),
                "Volym": volym_text,
                "Trend (MACD)": macd_status
            })

            # Kolla guld-kriterier för Ultra-köp
            if rsi <= 35 and vol > v_snitt and macd_korsat_upp:
                temp_köp.append({
                    "Aktie": ticker, 
                    "Pris": round(pris, 2), 
                    "RSI": round(rsi, 1), 
                    "Volym-Ökning": f"+{((vol/v_snitt)-1)*100:.0f}%",
                    "Idag %": f"{dags_utveckling:+.2f}%"
                })
            elif rsi >= 70 or macd_korsat_ner:
                anledning = "Överköpt ⚠️" if rsi >= 70 else "Trendbrott (MACD) 🚨"
                temp_sälj.append({
                    "Aktie": ticker, 
                    "Pris": round(pris, 2), 
                    "RSI": round(rsi, 1), 
                    "Anledning": anledning,
                    "Idag %": f"{dags_utveckling:+.2f}%"
                })
        except:
            continue

    tf.session_state.ultra_köp = temp_köp
    tf.session_state.ultra_sälj = temp_sälj
    tf.session_state.alla_aktier = temp_alla
    tf.session_state.har_skannat = True

    progress_bar.empty()
    status_text.empty()

# --- PRESENTATION PÅ SKÄRMEN ---

if tf.session_state.har_skannat:
    
    # 2. SEKTION: ULTRA-KÖP
    tf.success("🌟 FÖRESLAGNA ULTRA-KÖP")
    if tf.session_state.ultra_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_köp), use_container_width=True)
    else:
        tf.info("Inga aktier uppfyller alla tre köpkriterier just nu.")
        
    # 3. SEKTION: ULTRA-SÄLJ
    tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
    if tf.session_state.ultra_sälj:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
    else:
        tf.info("Inga säljsignaler just nu.")
        
    # 4. SEKTION: DETALJERAD MARKNADSÖVERSIKT
    tf.subheader("📊 Komplett Marknadsöversikt")
    tf.write("Sorterad efter lägst RSI (mest översåld) först.")
    if tf.session_state.alla_aktier:
        df_visa = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        tf.dataframe(df_visa, use_container_width=True, height=500)

else:
    tf.info("Klicka på knappen ovan för att starta skanningen.")

# 5. SEKTION: TRADE-KALKYLATOR
tf.write("---")
tf.subheader("💼 Trade-Kalkylator")
kp = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)
if kp > 0:
    tf.success(f"🎯 Målkurs (+5%): **{kp * 1.05:.2f}**")
    tf.error(f"🛑 Stop Loss (-3%): **{kp * 0.97:.2f}**")
