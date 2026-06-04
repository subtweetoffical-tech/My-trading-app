import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Ultra Trading Bot", layout="centered")

tf.title("🚀 Ultra Trading Scanner Pro")

# --- INFORMATIONSFLIK (UTFÄLLBAR) ---
with tf.expander("ℹ️ SÅ HÄR FUNGERAR DE OPTIMERADE SIGNALERNA"):
    tf.markdown("""
    ### Förbättrad logik för högre lönsamhet:
    
    * **🌟 ULTRA-KÖP:** Säkraste signalen. Kräver översåld nivå (<35), hög volym (RVOL >= 1.5) OCH ett bekräftat prisskifte (MACD korsar upp precis nu).
    * **👍 REKOMMENDERADE KÖP (Stabiliserad dipp):** Kräver RSI < 30, men nu även att säljet har avtagit (priset stänger högre än föregående 15-minutersbars stängning). Detta förhindrar att du köper en fallande kniv.
    * **🚨 FÖRESLAGNA SÄLJ:** Signalerar nu endast när trenden faktiskt bryts (MACD korsar ner på översålda nivåer), vilket låter vinnare löpa längre.
    """)

NAMN_MAPPNING = {
    # --- SVERIGE ---
    "VOLV-B.ST": "Volvo, AB ser. B", "AZN.ST": "AstraZeneca", "EVO.ST": "Evolution", "INVE-B.ST": "Investor B", 
    "SEB-A.ST": "SEB A", "SHB-A.ST": "Handelsbanken A", "SWED-A.ST": "Swedbank A", "ERIC-B.ST": "Ericsson B", 
    "TELIA.ST": "Telia Company", "SAND.ST": "Sandvik", "ATCO-A.ST": "Atlas Copco A", "SKF-B.ST": "SKF B", 
    "BOL.ST": "Boliden", "HEXA-B.ST": "Hexagon B", "ASSA-B.ST": "Assa Abloy B", "NIBE-B.ST": "Nibe Industrier B", 
    "SBB-B.ST": "Samhällsbyggnadsbolaget B", "SINCH.ST": "Sinch", "SAAB-B.ST": "Saab B", "GETI-B.ST": "Getinge B", 
    "HM-B.ST": "Hennes & Mauritz B", "KINV-B.ST": "Kinnevik B", "ELUX-B.ST": "Electrolux B", "BALD-B.ST": "Balder B", 
    "CAST.ST": "Castellum", "SSAB-B.ST": "SSAB B", "SCA-B.ST": "SCA B", "ALIV-SDB.ST": "Autoliv SDB", 
    "JM.ST": "JM", "NCC-B.ST": "NCC B", "PEAB-B.ST": "Peab B", "BILI.ST": "Bilia A", 
    "FABG.ST": "Fabege", "WIHL.ST": "Wihlborgs Fastigheter", "WALL-B.ST": "Wallenstam B", "MYCR.ST": "Mycronic",
    "AAK.ST": "AAK", "BIOT.ST": "Biotage", "LUND-B.ST": "Lundbergföretagen B", "BETCO.ST": "Betsson B", 
    "ANOT.ST": "Anoto Group", "STE-R.ST": "Stora Enso R", "STOR-B.ST": "Stora Enso B", "SKAF-B.ST": "SkiStar B", 
    "LOOM.ST": "Loomis", "TIGO-SDB.ST": "Millicom Int. Cellular SDB", "KLED.ST": "Kallebäck Property Invest", 
    "SRECO.ST": "Swedish Orphan Biovitrum", "HPOL-B.ST": "Hexatronic Group", "LIFCO-B.ST": "Lifco B", 
    "INDT.ST": "Indutrade", "ADDTECH-B.ST": "Addtech B", "LAGR-B.ST": "Lagercrantz Group B", "AXFO.ST": "Axfood", 
    "ALFA.ST": "Alfa Laval", "DOM.ST": "Dometic Group", "FING-B.ST": "Fingerprint Cards B", "VITR.ST": "Vitrolife", "SCA-A.ST": "SCA A",
    # --- USA ---
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "GOOGL": "Alphabet Inc. Class A", "AMZN": "Amazon.com Inc.", 
    "NVDA": "NVIDIA Corp.", "META": "Meta Platforms Inc.", "TSLA": "Tesla Inc.", "BRK-B": "Berkshire Hathaway B", 
    "LLY": "Eli Lilly & Co.", "V": "Visa Inc.", "UNH": "UnitedHealth Group", "JPM": "JPMorgan Chase & Co.", 
    "MA": "Mastercard Inc.", "AVGO": "Broadcom Inc.", "HD": "Home Depot Inc.", "XOM": "Exxon Mobil Corp.", 
    "PG": "Procter & Gamble Co.", "COST": "Costco Wholesale", "AMD": "Advanced Micro Devices", "NFLX": "Netflix Inc.",
    "ADBE": "Adobe Inc.", "CRM": "Salesforce Inc.", "INTC": "Intel Corp.", "CSCO": "Cisco Systems", 
    "TXN": "Texas Instruments", "AMAT": "Applied Materials", "QCOM": "Qualcomm Inc.", "MU": "Micron Technology", 
    "PANW": "Palo Alto Networks", "SNOW": "Snowflake Inc.", "PLTR": "Palantir Technologies", "COIN": "Coinbase Global", 
    "MARA": "MARA Holdings", "RIOT": "Riot Platforms", "SOFI": "SoFi Technologies", "BABA": "Alibaba Group", 
    "PDD": "PDD Holdings (Pinduoduo)", "NIO": "Nio Inc. ADR", "XPEV": "Xpeng Inc. ADR", "LI": "Li Auto Inc. ADR", 
    "PYPL": "PayPal Holdings", "SQ": "Block Inc. (Square)", "DIS": "Walt Disney Co.", "BA": "Boeing Co.", 
    "CAT": "Caterpillar Inc.", "GE": "General Electric", "F": "Ford Motor Co.", "GM": "General Motors", 
    "ABNB": "Airbnb Inc.", "SMCI": "Super Micro Computer", "MSTR": "MicroStrategy Inc.", "HOOD": "Robinhood Markets", 
    "AFRM": "Affirm Holdings", "UPST": "Upstart Holdings", "RIVN": "Rivian Automotive", "LCID": "Lucid Group", 
    "DKNG": "DraftKings Inc.", "PINS": "Pinterest Inc.", "ROKU": "Roku Inc."
}

AKTIER = list(NAMN_MAPPNING.keys())

if "ultra_köp" not in tf.session_state: tf.session_state.ultra_köp = []
if "rek_köp" not in tf.session_state: tf.session_state.rek_köp = []
if "ultra_sälj" not in tf.session_state: tf.session_state.ultra_sälj = []
if "alla_aktier" not in tf.session_state: tf.session_state.alla_aktier = []
if "har_skannat" not in tf.session_state: tf.session_state.har_skannat = False

if tf.button("STARTA ULTRA-ANALYS ⚡ (Skanna 120 aktier)", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Skannar ({i+1}/120): {NAMN_MAPPNING[ticker]}...")
        progress_bar.progress((i + 1) / len(AKTIER))
        
        try:
            df = yf.download(ticker, period="20d", interval="15m", progress=False)
            if df.empty or len(df) < 30: continue
                
            df.columns = [col[0] if isinstance(col, tuple) else col for col in df.columns]
            
            close_series = pd.Series(df['Close'].dropna().values.flatten())
            volume_series = pd.Series(df['Volume'].dropna().values.flatten())
            open_series = pd.Series(df['Open'].dropna().values.flatten())
            
            if len(close_series) < 15: continue
                
            df_rsi = ta.momentum.rsi(close_series, window=14)
            df_vol_snitt = volume_series.rolling(window=10).mean()
            macd_obj = ta.trend.MACD(close_series)
            df_macd = macd_obj.macd()
            df_macd_sig = macd_obj.macd_signal()
            
            pris = float(close_series.iloc[-1])
            pris_förra_bar = float(close_series.iloc[-2]) # Nytt: Kolla förra 15m-stängningen
            öppning = float(open_series.iloc[-1])
            rsi = float(df_rsi.iloc[-1])
            vol = float(volume_series.iloc[-1])
            v_snitt = float(df_vol_snitt.iloc[-1])
            m = float(df_macd.iloc[-1])
            s = float(df_macd_sig.iloc[-1])
            
            rvol = vol / v_snitt if v_snitt > 0 else 1.0
            dags_utveckling = ((pris - öppning) / öppning) * 100
            
            fullt_namn = NAMN_MAPPNING.get(ticker, ticker)
            
            m_igår = float(df_macd.iloc[-2])
            s_igår = float(df_macd_sig.iloc[-2])
            macd_korsat_upp = m > s and m_igår <= s_igår
            macd_korsat_ner = m < s and m_igår >= s_igår
            
            macd_status = "Avvakta 🟡"
            if m > s:
                macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
            elif m < s:
                macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

            temp_alla.append({
                "Aktie (Sök på Avanza)": fullt_namn, "Symbol": ticker, "Pris": round(pris, 2),
                "Idag %": f"{dags_utveckling:+.2f}%", "RSI (15m)": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "Trend (MACD)": macd_status
            })

            # --- OPTIMERAD KÖPLOGIK ---
            if rsi <= 35 and rvol >= 1.5 and macd_korsat_upp:
                temp_ultra_köp.append({
                    "Aktie (Sök på Avanza)": fullt_namn, "Pris": round(pris, 2), "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Idag %": f"{dags_utveckling:+.2f}%"
                })
            # NYTT FILTER: Priset måste stänga HÖGRE än förra baren (Trendvändning påbörjad, ingen fallande kniv)
            elif rsi <= 30 and pris > pris_förra_bar:
                temp_rek_köp.append({
                    "Aktie (Sök på Avanza)": fullt_namn, "Pris": round(pris, 2), "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Idag %": f"{dags_utveckling:+.2f}%"
                })
                
            # --- OPTIMERAD SÄLJLOGIK ---
            # Kräver att det faktiskt är ett trendbrott (MACD korsar ner) när den är överköpt, 
            # eller att RSI blir extremt överhettad (>75)
            if (rsi >= 70 and macd_korsat_ner) or rsi >= 75:
                anledning = "Extremt Överköpt ⚠️" if rsi >= 75 else "Vändning Nedåt 🚨"
                temp_sälj.append({
                    "Aktie (Sök på Avanza)": fullt_namn, "Pris": round(pris, 2), "RSI": round(rsi, 1), "Anledning": anledning, "Idag %": f"{dags_utveckling:+.2f}%"
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
    tf.success("🌟 FÖRESLAGNA ULTRA-KÖP (RSI + RVOL + MACD)")
    if tf.session_state.ultra_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_köp), use_container_width=True)
    else:
        tf.info("Inga aktier uppfyller alla tre kriterier just nu.")
        
    tf.write("---")
    tf.info("👍 REKOMMENDERADE KÖP (Stabiliserade Dippar, RSI < 30)")
    if tf.session_state.rek_köp:
        tf.dataframe(pd.DataFrame(tf.session_state.rek_köp), use_container_width=True)
    else:
        tf.info("Inga översålda aktier som stabiliserats just nu.")
        
    tf.write("---")
    tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
    if tf.session_state.ultra_sälj:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
    else:
        tf.info("Inga säljsignaler just nu.")
        
    tf.write("---")
    tf.subheader("📊 Komplett Marknadsöversikt (120 aktier)")
    if tf.session_state.alla_aktier:
        df_visa = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI (15m)", ascending=True)
        tf.dataframe(df_visa, use_container_width=True, height=500)
else:
    tf.info("Klicka på knappen ovan för att starta skanningen.")

# --- DYNAMISK TRADE-KALKYLATOR ---
tf.write("---")
tf.subheader("💼 Flexibel Trade-Kalkylator")
kp = tf.number_input("Ditt köppris:", min_value=0.0, step=0.1)

# Låter användaren välja egen vinst och stop loss baserat på marknadens humör
col1, col2 = tf.columns(2)
with col1:
    vinst_procent = tf.slider("Målvinst (%)", 1.0, 15.0, 5.0, step=0.5)
with col2:
    loss_procent = tf.slider("Stop Loss (%)", 1.0, 10.0, 3.0, step=0.5)

if kp > 0:
    target = kp * (1 + (vinst_procent / 100))
    stop = kp * (1 - (loss_procent / 100))
    tf.success(f"🎯 Målkurs (+{vinst_procent}%): **{target:.2f}**")
    tf.error(f"🛑 Stop Loss (-{loss_procent}%): **{stop:.2f}**")
