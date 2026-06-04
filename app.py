import streamlit as tf
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration för mobilvänlighet
tf.set_page_config(page_title="Global 150 Trading Bot", layout="centered")

tf.title("🚀 Global Trading Scanner - 150 Aktier")

# --- INFORMATIONSFLIK (UTFÄLLBAR) ---
with tf.expander("ℹ️ SÅ HÄR FUNGERAR DET GLOBALA URVALET"):
    tf.markdown("""
    ### Marknadsfokus utan krångliga avtal:
    * **Sverige (SEK):** 80 mest omsatta aktierna på Stockholmsbörsen. Bra för förmiddagstrading (09:00 - 17:30).
    * **USA & Asien (USD):** 70 extremt likvida amerikanska techjättar samt asiatiska giganter (via vanliga ADR-aktier på USA-börsen). Perfekt för eftermiddagstrading (15:30 - 22:00).
    * **Stabiliserade dippar:** Köpsignaler kräver att priset stängt högre än föregående 15-minutersperiod för att undvika "fallande knivar".
    """)

# Ordbok med exakt 150 handplockade day trading-aktier (80 Sve, 70 USA/Asien)
NAMN_MAPPNING = {
    # --- SVERIGE (80 st - Handlas i SEK) ---
    "VOLV-B.ST": "Volvo B", "AZN.ST": "AstraZeneca", "EVO.ST": "Evolution", "INVE-B.ST": "Investor B", 
    "SEB-A.ST": "SEB A", "SHB-A.ST": "Handelsbanken A", "SWED-A.ST": "Swedbank A", "ERIC-B.ST": "Ericsson B", 
    "TELIA.ST": "Telia Company", "SAND.ST": "Sandvik", "ATCO-A.ST": "Atlas Copco A", "SKF-B.ST": "SKF B", 
    "BOL.ST": "Boliden", "HEXA-B.ST": "Hexagon B", "ASSA-B.ST": "Assa Abloy B", "NIBE-B.ST": "Nibe Industrier B", 
    "SBB-B.ST": "SBB B", "SINCH.ST": "Sinch", "SAAB-B.ST": "Saab B", "GETI-B.ST": "Getinge B", 
    "HM-B.ST": "H&M B", "KINV-B.ST": "Kinnevik B", "ELUX-B.ST": "Electrolux B", "BALD-B.ST": "Balder B", 
    "CAST.ST": "Castellum", "SSAB-B.ST": "SSAB B", "SCA-B.ST": "SCA B", "ALIV-SDB.ST": "Autoliv", 
    "JM.ST": "JM", "NCC-B.ST": "NCC B", "PEAB-B.ST": "Peab B", "BILI.ST": "Bilia", "FABG.ST": "Fabege", 
    "WIHL.ST": "Wihlborgs", "WALL-B.ST": "Wallenstam B", "MYCR.ST": "Mycronic", "AAK.ST": "AAK", 
    "BIOT.ST": "Biotage", "LUND-B.ST": "Lundbergföretagen", "BETCO.ST": "Betsson B", "STE-R.ST": "Stora Enso", 
    "SKAF-B.ST": "SkiStar B", "LOOM.ST": "Loomis", "TIGO-SDB.ST": "Millicom", "SRECO.ST": "SOBI", 
    "HPOL-B.ST": "Hexatronic", "LIFCO-B.ST": "Lifco B", "INDT.ST": "Indutrade", "ADDTECH-B.ST": "Addtech B", 
    "LAGR-B.ST": "Lagercrantz B", "AXFO.ST": "Axfood", "ALFA.ST": "Alfa Laval", "DOM.ST": "Dometic", 
    "FING-B.ST": "Fingerprint B", "VITR.ST": "Vitrolife", "SECUM-B.ST": "Securitas B", "TELE2-B.ST": "Tele2 B",
    "AFRY.ST": "AFRY", "AVAN.ST": "Avanza", "BEI-B.ST": "Beijer Ref B", "BELE.ST": "Bravida", "BHG.ST": "BHG Group", 
    "BILL.ST": "Billerud", "BOOZT.ST": "Boozt", "BURE.ST": "Bure Equity", "CORE-B.ST": "Corem B", 
    "COOR.ST": "Coor", "CREDES-A.ST": "Creades A", "DIOS.ST": "Diös", "DUST.ST": "Dustin", 
    "EMBRAC-B.ST": "Embracer B", "EQT.ST": "EQT", "ESSITY-B.ST": "Essity B", "FORTV.ST": "Fortnox", 
    "G5EN.ST": "G5 Entertainment", "GRNG.ST": "Gränges", "HMS.ST": "HMS Networks", "INSTAL.ST": "Instalco", 
    "INTRUM.ST": "Intrum", "NORD.ST": "Nordnet", "NYF.ST": "Nyfosa", "RVRC.ST": "RevolutionRace",
    # --- USA & ASIATISKA ADR (70 st - Handlas i USD) ---
    "AAPL": "Apple (US)", "MSFT": "Microsoft (US)", "GOOGL": "Alphabet (US)", "AMZN": "Amazon (US)", 
    "NVDA": "NVIDIA (US)", "META": "Meta (US)", "TSLA": "Tesla (US)", "AMD": "AMD (US)", "NFLX": "Netflix (US)",
    "PLTR": "Palantir (US)", "COIN": "Coinbase (US)", "PYPL": "PayPal (US)", "SQ": "Block / Square (US)",
    "TSM": "TSMC (Taiwan ADR)", "BABA": "Alibaba (Kina ADR)", "PDD": "PDD Holdings / Temu (Kina ADR)",
    "NIO": "Nio (Kina ADR)", "LI": "Li Auto (Kina ADR)", "XPEV": "Xpeng (Kina ADR)", "JD": "JD.com (Kina ADR)",
    "BIDU": "Baidu (Kina ADR)", "NTES": "NetEase (Kina ADR)", "TCEHY": "Tencent (Kina ADR)", "SONY": "Sony (Japan ADR)",
    "HMC": "Honda (Japan ADR)", "TM": "Toyota (Japan ADR)", "MUFG": "Mitsubishi Financial (Japan ADR)",
    "INFY": "Infosys (Indien ADR)", "WIT": "Wipro (Indien ADR)", "RELIANCE.NS": "Reliance (Indien)",
    "ASML": "ASML (Nederländerna)", "SMCI": "Super Micro (US)", "MSTR": "MicroStrategy (US)",
    "CRM": "Salesforce (US)", "INTC": "Intel (US)", "QCOM": "Qualcomm (US)", "MU": "Micron (US)",
    "AMAT": "Applied Materials (US)", "PANW": "Palo Alto (US)", "SNOW": "Snowflake (US)", 
    "MARA": "MARA Holdings (US)", "RIOT": "Riot Platforms (US)", "HOOD": "Robinhood (US)",
    "AFRM": "Affirm (US)", "RIVN": "Rivian (US)", "DKNG": "DraftKings (US)", "PINS": "Pinterest (US)",
    "ROKU": "Roku (US)", "DIS": "Disney (US)", "BA": "Boeing (US)", "CAT": "Caterpillar (US)",
    "F": "Ford (US)", "GM": "General Motors (US)", "UBER": "Uber (US)", "ABNB": "Airbnb (US)",
    "NKE": "Nike (US)", "SBUX": "Starbucks (US)", "XOM": "Exxon Mobil (US)", "CVX": "Chevron (US)",
    "JPM": "JPMorgan Chase (US)", "V": "Visa (US)", "MA": "Mastercard (US)", "LLY": "Eli Lilly (US)",
    "WMT": "Walmart (US)", "COST": "Costco (US)", "HD": "Home Depot (US)", "GME": "GameStop (US)",
    "AMC": "AMC Entertainment (US)", "DJT": "Trump Media (US)", "AAL": "American Airlines (US)"
}

AKTIER = list(NAMN_MAPPNING.keys())

if "ultra_köp" not in tf.session_state: tf.session_state.ultra_köp = []
if "rek_köp" not in tf.session_state: tf.session_state.rek_köp = []
if "ultra_sälj" not in tf.session_state: tf.session_state.ultra_sälj = []
if "alla_aktier" not in tf.session_state: tf.session_state.alla_aktier = []
if "har_skannat" not in tf.session_state: tf.session_state.har_skannat = False

if tf.button("STARTA GLOBALSÖKNING ⚡ (Skanna 150 aktier)", use_container_width=True):
    status_text = tf.empty()
    progress_bar = tf.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    for i, ticker in enumerate(AKTIER):
        status_text.write(f"Skannar ({i+1}/150): {NAMN_MAPPNING[ticker]}...")
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
            pris_förra_bar = float(close_series.iloc[-2])
            öppning = float(open_series.iloc[-1])
            rsi = float(df_rsi.iloc[-1])
            vol = float(volume_series.iloc[-1])
            v_snitt = float(df_vol_snitt.iloc[-1])
            m = float(df_macd.iloc[-1])
            s = float(df_macd_sig.iloc[-1])
            
            rvol = vol / v_snitt if v_snitt > 0 else 1.0
            dags_utveckling = ((pris - öppning) / öppning) * 100
            
            valuta = "SEK" if ticker.endswith(".ST") else "USD"
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
                "Aktie (Sök Avanza)": fullt_namn, "Symbol": ticker, "Pris": round(pris, 2), "Valuta": valuta,
                "Idag %": f"{dags_utveckling:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "MACD": macd_status
            })

            # --- KÖPLOGIK ---
            if rsi <= 35 and rvol >= 1.5 and macd_korsat_upp:
                temp_ultra_köp.append({
                    "Aktie (Sök Avanza)": fullt_namn, "Pris": round(pris, 2), "Valuta": valuta, "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Idag %": f"{dags_utveckling:+.2f}%"
                })
            elif rsi <= 30 and pris > pris_förra_bar:
                temp_rek_köp.append({
                    "Aktie (Sök Avanza)": fullt_namn, "Pris": round(pris, 2), "Valuta": valuta, "RSI": round(rsi, 1), "Idag %": f"{dags_utveckling:+.2f}%"
                })
                
            # --- SÄLJLOGIK ---
            if (rsi >= 70 and macd_korsat_ner) or rsi >= 75:
                anledning = "Extremt Överköpt ⚠️" if rsi >= 75 else "Vändning Nedåt 🚨"
                temp_sälj.append({
                    "Aktie (Sök Avanza)": fullt_namn, "Pris": round(pris, 2), "Valuta": valuta, "RSI": round(rsi, 1), "Anledning": anledning
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

# --- PRESENTATION ---
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
        tf.info("Inga översålda aktier just nu.")
        
    tf.write("---")
    tf.error("🚨 FÖRESLAGNA SÄLJ/TA VINST")
    if tf.session_state.ultra_sälj:
        tf.dataframe(pd.DataFrame(tf.session_state.ultra_sälj), use_container_width=True)
    else:
        tf.info("Inga säljsignaler just nu.")
        
    tf.write("---")
    tf.subheader("📊 Komplett Marknadsöversikt (150 globala aktier)")
    if tf.session_state.alla_aktier:
        df_visa = pd.DataFrame(tf.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        tf.dataframe(df_visa, use_container_width=True, height=500)
else:
    tf.info("Klicka på knappen ovan för att starta skanningen.")

# --- DYNAMISK TRADE-KALKYLATOR ---
tf.write("---")
tf.subheader("💼 Flexibel Trade-Kalkylator")

valutaval = tf.radio("Välj valuta för din kalkylator:", ["SEK", "USD"], horizontal=True)
kp = tf.number_input(f"Ditt köppris ({valutaval}):", min_value=0.0, step=0.1)

col1, col2 = tf.columns(2)
with col1:
    vinst_procent = tf.slider("Målvinst (%)", 1.0, 15.0, 5.0, step=0.5)
with col2:
    loss_procent = tf.slider("Stop Loss (%)", 1.0, 10.0, 3.0, step=0.5)

if kp > 0:
    target = kp * (1 + (vinst_procent / 100))
    stop = kp * (1 - (loss_procent / 100))
    tf.success(f"🎯 Målkurs (+{vinst_procent}%): **{target:.2f} {valutaval}**")
    tf.error(f"🛑 Stop Loss (-{loss_procent}%): **{stop:.2f} {valutaval}**")
