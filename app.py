import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np

# Sätt sidkonfiguration
st.set_page_config(page_title="Högvolatil 200 Scanner Pro", layout="centered")

st.title("⚡ Global Trading Scanner - Professionell Version")

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ SMARTA TRADING-FILTRENDRINGAR (UPPDATERAD)"):
    st.markdown("""
    ### Hur den här versionen hjälper dig att tjäna mer:
    1. **EMA 200 (Trendfilter):** Vi köper *aldrig* en aktie som rasar långsiktigt. Vi handlar bara i sunda upptrender.
    2. **Volymbekräftelse (RVOL) & Omsättningsfilter:** Köpsignaler kräver hög aktivitet. Dessutom sorterar koden automatiskt bort aktier med för låg omsättning för att undvika dött brus.
    3. **ATR-Riskhantering:** Kalkylatorn i botten använder *Average True Range* för att sätta en perfekt Stop Loss anpassad efter just den aktiens unika svängningar.
    """)

# Optimerat urval av högvolatila och likvida aktier under 250 kr (Nasdaq Stockholm & First North)
NAMN_MAPPNING = {
    # --- Rörliga favoriter & Tech/Gaming ---
    "SINCH.ST": "Sinch (Tech)", "EMBRAC-B.ST": "Embracer (Gaming)", "ASMDEE-B.ST": "Asmodee (Gaming)",
    "SIVERS.ST": "Sivers Semiconductors", "FORTV.ST": "Fortnox (Mjukvara)", "EVO.ST": "Evolution (iGaming)", 
    "BETCO.ST": "Betsson (Gaming)", "G5EN.ST": "G5 Entertainment", "MTG-B.ST": "MTG (Gaming)", 
    "BOOZT.ST": "Boozt (E-handel)", "BHG.ST": "BHG Group (E-handel)", "HPOL-B.ST": "Hexatronic (Fiber)", 
    "MYCR.ST": "Mycronic (Tech)", "SBB-B.ST": "SBB B (Fastigheter)", "CORE-B.ST": "Corem B (Fastigheter)", 
    "BICO.ST": "BICO Group (Biotech)", "FING-B.ST": "Fingerprint Cards", "PCELL.ST": "PowerCell (Vätgas)", 
    
    # --- BioTech, Medicinteknik & Hälsa ---
    "VITR.ST": "Vitrolife (Biotech)", "BIOT.ST": "Biotage (Biotech)", "SRECO.ST": "SOBI (Biotech)", 
    "ADDV.ST": "AddLife (Medtech)", "CANT.ST": "Cantargia (Biotech)", "CAMX.ST": "Camurus (Biotech)",
    "AMBEV.ST": "Ambea", "ATT.ST": "Attendo", "HUM.ST": "Humana", "XBRANE.ST": "Xbrane Biopharma", 
    "BIOV-B.ST": "BioInvent", "STVK.ST": "Sedana Medical", "MVIC.ST": "Moberg Pharma",
    
    # --- Industri, Råvaror & Energi ---
    "BOL.ST": "Boliden (Gruvor)", "SSAB-B.ST": "SSAB B (Stål)", "ORR.ST": "Orron Energy", 
    "AOI.ST": "Africa Oil (Olja)", "SCA-B.ST": "SCA B (Skog)", "STE-R.ST": "Stora Enso", 
    "SKF-B.ST": "SKF B", "SAND.ST": "Sandvik", "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B (Försvar)", 
    "NIBE-B.ST": "Nibe (Grön Energi)", "DOM.ST": "Dometic", "HEXA-B.ST": "Hexagon", "AFRY.ST": "AFRY", 
    "JM.ST": "JM (Bygg)", "PEAB-B.ST": "Peab", "NCC-B.ST": "NCC B", "MUNTE.ST": "Munters Group", 
    "BEGR.ST": "Beijer Alma", "BELE.ST": "Beijer Ref", "BUFAB.ST": "Bufab", "MEKO.ST": "Mekonomen", 
    "SYSTEM.ST": "Systemair", "MALMK.ST": "Gränges", "BEGroup.ST": "BE Group", "NOLA-B.ST": "Nolato B",
    
    # --- Investmentbolag & Finans ---
    "INVE-B.ST": "Investor B", "KINV-B.ST": "Kinnevik B", "LATO-B.ST": "Latour B", "RATO-B.ST": "Ratos B",
    "CREA-B.ST": "Creades B", "BURE.ST": "Bure Equity", "SVOL-B.ST": "Svolder B", "TRAC-B.ST": "Traction B", 
    "AVAN.ST": "Avanza", "NORD.ST": "Nordnet", "TF_BANK.ST": "TF Bank",
    
    # --- Fastigheter ---
    "DIOS.ST": "Diös Fastigheter", "HEBA-B.ST": "Heba B", "PLAT-B.ST": "Platzer", "CAT-B.ST": "Catena",
    "TRIAN-B.ST": "Trianon B", "PNDX-B.ST": "Pandox", "SLP-B.ST": "Swedish Logistic Properties", "EAST.ST": "Eastnine",
    "KFAST-B.ST": "K-Fastigheter", "LOGIST.ST": "Logistea", "FABG.ST": "Fabege", "WIHL.ST": "Wihlborgs", 
    "WALL-B.ST": "Wallenstam", "NYF.ST": "Nyfosa", "CAST.ST": "Castellum", "BALD-B.ST": "Balder",
    
    # --- Techkonsulter & Kommunikation ---
    "KNOW.ST": "Knowit", "B3.ST": "B3 Consulting", "ITS.ST": "I.A.R Systems", "FORX.ST": "Formpipe Software",
    "ADD-B.ST": "AddNode Group", "TIETO.ST": "Tietoevry", "HMS.ST": "HMS Networks", "PREV.ST": "Prevas B", 
    "SOFT-B.ST": "Softronic", "EXP-B.ST": "Exsitec", "CINT.ST": "Cint Group", "TIGO-SDB.ST": "Millicom SDB",
    "TELE2-B.ST": "Tele2", "TELIA.ST": "Telia Company", "ERIC-B.ST": "Ericsson B",
    
    # --- Gaming, Underhållning & Konsument ---
    "STU-B.ST": "Starbreeze B", "MAG.ST": "Mag Interactive", "LYKO.ST": "Lyko Group", "NELLY.ST": "Nelly Group", 
    "CDON.ST": "CDON", "QNLI.ST": "Qliro", "SPLAY.ST": "Storytel", "READ.ST": "Readly International", 
    "CATE.ST": "Catena Media", "ANGI.ST": "Angler Gaming", "KRE.ST": "Kambi Group", "RAK.ST": "Raketech",
    "HM-B.ST": "H&M B", "BILI.ST": "Bilia", "DUST.ST": "Dustin Group", "ALIV-SDB.ST": "Autoliv SDB",
    "RVRC.ST": "RevolutionRace", "ELUX-B.ST": "Electrolux", "MIPS.ST": "MIPS", "RUG.ST": "RugVista",
    "CLAS-B.ST": "Clas Ohlson", "NEWW-B.ST": "New Wave Group", "ITAB.ST": "ITAB Shop Concept",
    
    # --- Cleantech & Förnybart ---
    "CLIME.ST": "Climeon", "MINESTO.ST": "Minesto", "NIL-B.ST": "Nilörngruppen", "METV.ST": "Metacon",
    "ECCO.ST": "Eolus Vind", "ARISE.ST": "Arise", "CIBUS.ST": "Cibus Nordic Real Estate",
    
    # --- Blandade rörliga tillväxtbolag ---
    "TEQN.ST": "Teqnion", "PROF-B.ST": "Profoto B", "NORD-B.ST": "Nordic Waterproofing", "FERRO.ST": "Ferroamp", 
    "GARO.ST": "Garo", "EPIW-B.ST": "Epiroc B", "LIFCO-B.ST": "Lifco B", "INDT.ST": "Indutrade", 
    "VIK-B.ST": "Viking Supply", "BALCO.ST": "Balco Group", "BOULE.ST": "Boule Diagnostics",
    "SBB-D.ST": "SBB D"
}

AKTIER = list(NAMN_MAPPNING.keys())

# Initiera session state
if "ultra_köp" not in st.session_state: st.session_state.ultra_köp = []
if "rek_köp" not in st.session_state: st.session_state.rek_köp = []
if "ultra_sälj" not in st.session_state: st.session_state.ultra_sälj = []
if "alla_aktier" not in st.session_state: st.session_state.alla_aktier = []
if "har_skannat" not in st.session_state: st.session_state.har_skannat = False

MAX_AKTIEPRIS = 250.0
KASSA = 1000.0  
MAX_RISK_PER_TRADE = 250.0  

if st.button("STARTA AVANCERAD VOLATILITETSSÖKNING ⚡", use_container_width=True):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    alla_tickers_str = " ".join(AKTIER)
    try:
        # Laddar ner 60d data för stabila indikatorberäkningar
        stort_df = yf.download(alla_tickers_str, period="60d", interval="1h", progress=False, group_by="ticker")
    except Exception as e:
        st.error(f"Kunde inte hämta data från Yahoo Finance: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        tillgangliga_tickers = stort_df.columns.levels[0] if isinstance(stort_df.columns, pd.MultiIndex) else []

        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{len(AKTIER)}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            if ticker not in tillgangliga_tickers:
                continue
                
            try:
                df_ticker = stort_df[ticker].copy()
                df_ticker = df_ticker.dropna(subset=['Close'])
                
                if len(df_ticker) < 50: 
                    continue
                
                pris = float(df_ticker['Close'].iloc[-1])
                vol = float(df_ticker['Volume'].iloc[-1])
                
                if pris > MAX_AKTIEPRIS or pris <= 0 or np.isnan(pris):
                    continue
                
                # --- OMSÄTTNINGSFILTER ---
                # Sorterar bort timmar med extremt låg handel för att undvika falska tekniska signaler
                timomsattning = pris * vol
                if timomsattning < 40000: # Minst 40 000 kr omsatt senaste timmen
                    continue
                    
                # --- TEKNISK ANALYS ---
                df_rsi = ta.momentum.rsi(df_ticker['Close'], window=14)
                df_vol_snitt = df_ticker['Volume'].rolling(window=10).mean()
                
                # Trendfilter: EMA 200 (eller fallbacks till EMA 50)
                window_ema = 200 if len(df_ticker) >= 200 else 50
                df_ema = ta.trend.ema_indicator(df_ticker['Close'], window=window_ema)
                
                # Volatilitet: ATR (Average True Range)
                df_atr = ta.volatility.average_true_range(df_ticker['High'], df_ticker['Low'], df_ticker['Close'], window=14)
                
                macd_obj = ta.trend.MACD(df_ticker['Close'])
                df_macd = macd_obj.macd()
                df_macd_sig = macd_obj.macd_signal()
                
                if df_rsi.isna().iloc[-1] or df_macd.isna().iloc[-1] or df_ema.isna().iloc[-1]:
                    continue

                pris_förra_bar = float(df_ticker['Close'].iloc[-2])
                öppning = float(df_ticker['Open'].iloc[-1])
                rsi = float(df_rsi.iloc[-1])
                v_snitt = float(df_vol_snitt.iloc[-1])
                m = float(df_macd.iloc[-1])
                s = float(df_macd_sig.iloc[-1])
                ema_filter = float(df_ema.iloc[-1])
                atr_varde = float(df_atr.iloc[-1])
                
                rvol = vol / v_snitt if v_snitt > 0 else 1.0
                utveckling_bar = ((pris - öppning) / öppning) * 100
                fullt_namn = NAMN_MAPPNING[ticker]
                
                # Långsiktig trendstatus
                i_upptrend = pris > ema_filter
                
                # MACD-korsningar
                macd_korsat_upp = (m > s) and (df_macd.iloc[-4:-1] < df_macd_sig.iloc[-4:-1]).any()
                macd_korsat_ner = (m < s) and (df_macd.iloc[-4:-1] > df_macd_sig.iloc[-4:-1]).any()
                
                macd_status = "Avvakta 🟡"
                if m > s:
                    macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
                elif m < s:
                    macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

                rek_antal = int(MAX_RISK_PER_TRADE // pris)
                if rek_antal == 0 and pris <= KASSA:
                    rek_antal = 1  
                
                max_absolut_antal = int(KASSA // pris)

                if rek_antal > 0:
                    temp_alla.append({
                        "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal": rek_antal, "Max Antal": max_absolut_antal,
                        "Senaste timmen %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "MACD": macd_status,
                        "Trend": "Upp 📈" if i_upptrend else "Ner 📉", "ATR": round(atr_varde, 2)
                    })

                    # STRATEGI 1: ULTRA-KÖP (Strikta institutionella filter: Trend + Volym + Vändning)
                    if rsi <= 38 and m > s and i_upptrend and rvol >= 1.6:  
                        temp_ultra_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal köp": rek_antal, "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "ATR": round(atr_varde, 2)
                        })
                    
                    # STRATEGI 2: REKOMMENDERADE DIPP-KÖP (Klassisk rekyl i en långsiktig upptrend)
                    elif rsi <= 30 and pris > pris_förra_bar and i_upptrend:
                        temp_rek_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal köp": rek_antal, "RSI": round(rsi, 1), "ATR": round(atr_varde, 2)
                        })
                        
                    # STRATEGI 3: SÄLJ / VINSTHEMTAGNING
                    if (rsi >= 72 and macd_korsat_ner) or rsi >= 78:
                        temp_sälj.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "Anledning": "Extremt Överköpt 🔥" if rsi >= 78 else "Vändning Nedåt 🚨"
                        })
            except Exception as e:
                print(f"Fel vid analys av {ticker}: {e}")
                continue

    st.session_state.ultra_köp = temp_ultra_köp
    st.session_state.rek_köp = temp_rek_köp
    st.session_state.ultra_sälj = temp_sälj
    st.session_state.alla_aktier = temp_alla
    st.session_state.har_skannat = True

    progress_bar.empty()
    status_text.empty()

# --- PRESENTATION PÅ SKÄRMEN ---
if st.session_state.har_skannat:
    st.success("🌟 ULTRA-KÖP (Bäst statistik – Trend + Institutionell Volym + RSI + MACD)")
    if st.session_state.ultra_köp:
        st.dataframe(pd.DataFrame(st.session_state.ultra_köp), use_container_width=True)
    else:
        st.info("Inga aktier har tillräckligt starka köpsignaler just den här timmen.")
        
    st.write("---")
    st.info("👍 REKOMMENDERADE DIPP-KÖP (Översålda aktier i en sund upptrend)")
    if st.session_state.rek_köp:
        st.dataframe(pd.DataFrame(st.session_state.rek_köp), use_container_width=True)
    else:
        st.info("Inga säkra dippar i upptrender just nu.")
        
    st.write("---")
    st.error("🚨 FÖRESLAGNA SÄLJ (Dags att säkra vinster)")
    if st.session_state.ultra_sälj:
        st.dataframe(pd.DataFrame(st.session_state.ultra_sälj), use_container_width=True)
    else:
        st.info("Inga aktier är överhettade för stunden.")
        
    st.write("---")
    st.subheader("📊 Komplett Översikt (Sorterat på lägst RSI)")
    if st.session_state.alla_aktier:
        df_visa = pd.DataFrame(st.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        st.dataframe(df_visa, use_container_width=True, height=500)

# --- DYNAMISK VOLATILITETSKALKYLATOR (ATR) ---
st.write("---")
st.subheader("💼 Smart Riskkalkylator (ATR-baserad)")
st.markdown("_Denna kalkylator anpassar dina targets efter hur mycket aktien faktiskt brukar röra sig i genomsnitt för att undvika att bli utstoppad på brus._")

kp = st.number_input("Ditt inköpspris (SEK):", min_value=0.0, step=1.0)
valda_atr = st.number_input("Aktiens ATR-värde (se tabellen ovan):", min_value=0.0, step=0.1)

if kp > 0 and valda_atr > 0:
    # Sätter Stop Loss på 1.5x ATR och Target på 3x ATR (Risk/Reward 1:2)
    stop_loss_pris = kp - (1.5 * valda_atr)
    target_pris = kp + (3.0 * valda_atr)
    
    vinst_procent = ((target_pris - kp) / kp) * 100
    risk_procent = ((kp - stop_loss_pris) / kp) * 100
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(f"🎯 Ta vinst vid: **{target_pris:.2f} SEK** (+{vinst_procent:.1f}%)")
    with col2:
        st.error(f"🛑 Stop Loss vid: **{stop_loss_pris:.2f} SEK** (-{risk_procent:.1f}%)")
