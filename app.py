import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import os

# Sätt sidkonfiguration
st.set_page_config(page_title="Högvolatil Scanner & Journal Pro", layout="centered")

st.title("⚡ Trading Scanner med Automatisk Journal Pro")

# --- DATAHANTERING FÖR JOURNAL ---
JOURNAL_FILE = "trading_journal.csv"

def load_journal():
    if os.path.exists(JOURNAL_FILE):
        try:
            return pd.read_csv(JOURNAL_FILE)
        except:
            return pd.DataFrame(columns=["Datum", "Aktie", "Inköpspris", "ATR", "Target", "Stop_Loss", "Status"])
    else:
        return pd.DataFrame(columns=["Datum", "Aktie", "Inköpspris", "ATR", "Target", "Stop_Loss", "Status"])

def save_trade(aktie, pris, atr, target, stop):
    df = load_journal()
    ny_trade = pd.DataFrame([{
        "Datum": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "Aktie": aktie,
        "Inköpspris": round(pris, 2),
        "ATR": round(atr, 2),
        "Target": round(target, 2),
        "Stop_Loss": round(stop, 2),
        "Status": "Öppen ⏳"
    }])
    df = pd.concat([df, ny_trade], ignore_index=True)
    df.to_csv(JOURNAL_FILE, index=False)

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ STRATEGI & AUTOMATISK JOURNAL"):
    st.markdown("""
    ### Så här fungerar din nya Pro-Scanner:
    1. **EMA 200 & RVOL:** Sorterar stenhårt fram aktier i upptrend med institutionell volym.
    2. **ATR-Riskhantering:** Beräknar automatiskt din exakta Stop Loss (1.5x ATR) och Target (3.0x ATR).
    3. **Inbyggd Journal:** När du ser en signal du gillar, fyll i värdena längst ner för att spara affären. Det hjälper dig att spåra ditt kapital och se vilka aktier du tjänar mest pengar på!
    """)

# Optimerat urval av högvolatila och likvida aktier under 250 kr
NAMN_MAPPNING = {
    "SINCH.ST": "Sinch (Tech)", "EMBRAC-B.ST": "Embracer (Gaming)", "ASMDEE-B.ST": "Asmodee (Gaming)",
    "SIVERS.ST": "Sivers Semiconductors", "FORTV.ST": "Fortnox (Mjukvara)", "EVO.ST": "Evolution (iGaming)", 
    "BETCO.ST": "Betsson (Gaming)", "G5EN.ST": "G5 Entertainment", "MTG-B.ST": "MTG (Gaming)", 
    "BOOZT.ST": "Boozt (E-handel)", "BHG.ST": "BHG Group (E-handel)", "HPOL-B.ST": "Hexatronic (Fiber)", 
    "MYCR.ST": "Mycronic (Tech)", "SBB-B.ST": "SBB B (Fastigheter)", "CORE-B.ST": "Corem B (Fastigheter)", 
    "BICO.ST": "BICO Group (Biotech)", "FING-B.ST": "Fingerprint Cards", "PCELL.ST": "PowerCell (Vätgas)", 
    "VITR.ST": "Vitrolife (Biotech)", "BIOT.ST": "Biotage (Biotech)", "SRECO.ST": "SOBI (Biotech)", 
    "ADDV.ST": "AddLife (Medtech)", "CANT.ST": "Cantargia (Biotech)", "CAMX.ST": "Camurus (Biotech)",
    "AMBEV.ST": "Ambea", "ATT.ST": "Attendo", "HUM.ST": "Humana", "XBRANE.ST": "Xbrane Biopharma", 
    "BIOV-B.ST": "BioInvent", "STVK.ST": "Sedana Medical", "MVIC.ST": "Moberg Pharma",
    "BOL.ST": "Boliden (Gruvor)", "SSAB-B.ST": "SSAB B (Stål)", "ORR.ST": "Orron Energy", 
    "AOI.ST": "Africa Oil (Olja)", "SCA-B.ST": "SCA B (Skog)", "STE-R.ST": "Stora Enso", 
    "SKF-B.ST": "SKF B", "SAND.ST": "Sandvik", "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B (Försvar)", 
    "NIBE-B.ST": "Nibe (Grön Energi)", "DOM.ST": "Dometic", "HEXA-B.ST": "Hexagon", "AFRY.ST": "AFRY", 
    "JM.ST": "JM (Bygg)", "PEAB-B.ST": "Peab", "NCC-B.ST": "NCC B", "MUNTE.ST": "Munters Group", 
    "BEGR.ST": "Beijer Alma", "BELE.ST": "Beijer Ref", "BUFAB.ST": "Bufab", "MEKO.ST": "Mekonomen", 
    "SYSTEM.ST": "Systemair", "MALMK.ST": "Gränges", "BEGroup.ST": "BE Group", "NOLA-B.ST": "Nolato B",
    "INVE-B.ST": "Investor B", "KINV-B.ST": "Kinnevik B", "LATO-B.ST": "Latour B", "RATO-B.ST": "Ratos B",
    "CREA-B.ST": "Creades B", "BURE.ST": "Bure Equity", "SVOL-B.ST": "Svolder B", "TRAC-B.ST": "Traction B", 
    "AVAN.ST": "Avanza", "NORD.ST": "Nordnet", "TF_BANK.ST": "TF Bank", "DIOS.ST": "Diös Fastigheter", 
    "HEBA-B.ST": "Heba B", "PLAT-B.ST": "Platzer", "CAT-B.ST": "Catena", "TRIAN-B.ST": "Trianon B", 
    "PNDX-B.ST": "Pandox", "SLP-B.ST": "Swedish Logistic Properties", "EAST.ST": "Eastnine", 
    "KFAST-B.ST": "K-Fastigheter", "LOGIST.ST": "Logistea", "FABG.ST": "Fabege", "WIHL.ST": "Wihlborgs", 
    "WALL-B.ST": "Wallenstam", "NYF.ST": "Nyfosa", "CAST.ST": "Castellum", "BALD-B.ST": "Balder",
    "KNOW.ST": "Knowit", "B3.ST": "B3 Consulting", "ITS.ST": "I.A.R Systems", "FORX.ST": "Formpipe Software",
    "ADD-B.ST": "AddNode Group", "TIETO.ST": "Tietoevry", "HMS.ST": "HMS Networks", "PREV.ST": "Prevas B", 
    "SOFT-B.ST": "Softronic", "EXP-B.ST": "Exsitec", "CINT.ST": "Cint Group", "TIGO-SDB.ST": "Millicom SDB",
    "TELE2-B.ST": "Tele2", "TELIA.ST": "Telia Company", "ERIC-B.ST": "Ericsson B", "STU-B.ST": "Starbreeze B", 
    "MAG.ST": "Mag Interactive", "LYKO.ST": "Lyko Group", "NELLY.ST": "Nelly Group", "CDON.ST": "CDON", 
    "QNLI.ST": "Qliro", "SPLAY.ST": "Storytel", "READ.ST": "Readly International", "CATE.ST": "Catena Media", 
    "ANGI.ST": "Angler Gaming", "KRE.ST": "Kambi Group", "RAK.ST": "Raketech", "HM-B.ST": "H&M B", 
    "BILI.ST": "Bilia", "DUST.ST": "Dustin Group", "ALIV-SDB.ST": "Autoliv SDB", "RVRC.ST": "RevolutionRace", 
    "ELUX-B.ST": "Electrolux", "MIPS.ST": "MIPS", "RUG.ST": "RugVista", "CLAS-B.ST": "Clas Ohlson", 
    "NEWW-B.ST": "New Wave Group", "ITAB.ST": "ITAB Shop Concept", "CLIME.ST": "Climeon", "MINESTO.ST": "Minesto", 
    "NIL-B.ST": "Nilörngruppen", "METV.ST": "Metacon", "ECCO.ST": "Eolus Vind", "ARISE.ST": "Arise", 
    "CIBUS.ST": "Cibus Nordic Real Estate", "TEQN.ST": "Teqnion", "PROF-B.ST": "Profoto B", 
    "NORD-B.ST": "Nordic Waterproofing", "FERRO.ST": "Ferroamp", "GARO.ST": "Garo", "EPIW-B.ST": "Epiroc B", 
    "LIFCO-B.ST": "Lifco B", "INDT.ST": "Indutrade", "VIK-B.ST": "Viking Supply", "BALCO.ST": "Balco Group", 
    "BOULE.ST": "Boule Diagnostics", "SBB-D.ST": "SBB D"
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
        stort_df = yf.download(alla_tickers_str, period="60d", interval="1h", progress=False, group_by="ticker")
    except Exception as e:
        st.error(f"Kunde inte hämta data från Yahoo Finance: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        # Säkerställ MultiIndex för robust ticker-validering
        if isinstance(stort_df.columns, pd.MultiIndex):
            tillgangliga_tickers = stort_df.columns.levels[0]
        else:
            tillgangliga_tickers = []

        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{len(AKTIER)}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            if ticker not in tillgangliga_tickers:
                continue
                
            try:
                df_ticker = stort_df[ticker].copy().dropna(subset=['Close'])
                if len(df_ticker) < 50: 
                    continue
                
                pris = float(df_ticker['Close'].iloc[-1])
                vol = float(df_ticker['Volume'].iloc[-1])
                if pris > MAX_AKTIEPRIS or pris <= 0 or np.isnan(pris): 
                    continue
                
                # Omsättningsfilter (Min 40k kr senaste timmen)
                if (pris * vol) < 40000: 
                    continue
                    
                df_rsi = ta.momentum.rsi(df_ticker['Close'], window=14)
                df_vol_snitt = df_ticker['Volume'].rolling(window=10).mean()
                
                window_ema = 200 if len(df_ticker) >= 200 else 50
                df_ema = ta.trend.ema_indicator(df_ticker['Close'], window=window_ema)
                df_atr = ta.volatility.average_true_range(df_ticker['High'], df_ticker['Low'], df_ticker['Close'], window=14)
                
                macd_obj = ta.trend.MACD(df_ticker['Close'])
                df_macd = macd_obj.macd()
                df_macd_sig = macd_obj.macd_signal()
                
                # Säker kontroll mot tomma värden och NaN innan iloc[-1]
                if df_rsi.empty or df_macd.empty or df_ema.empty: 
                    continue
                if pd.isna(df_rsi.iloc[-1]) or pd.isna(df_macd.iloc[-1]) or pd.isna(df_ema.iloc[-1]): 
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
                i_upptrend = pris > ema_filter
                
                macd_korsat_upp = (m > s) and (df_macd.iloc[-4:-1] < df_macd_sig.iloc[-4:-1]).any()
                macd_korsat_ner = (m < s) and (df_macd.iloc[-4:-1] > df_macd_sig.iloc[-4:-1]).any()
                
                macd_status = "Avvakta 🟡"
                if m > s: macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
                elif m < s: macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

                rek_antal = int(MAX_RISK_PER_TRADE // pris) or 1
                max_absolut_antal = int(KASSA // pris)

                if rek_antal > 0:
                    temp_alla.append({
                        "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal": rek_antal, "Max Antal": max_absolut_antal,
                        "Senaste timmen %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "MACD": macd_status,
                        "Trend": "Upp 📈" if i_upptrend else "Ner 📉", "ATR": round(atr_varde, 2)
                    })

                    if rsi <= 38 and m > s and i_upptrend and rvol >= 1.6:  
                        temp_ultra_köp.append({"Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "ATR": round(atr_varde, 2)})
                    elif rsi <= 30 and pris > pris_förra_bar and i_upptrend:
                        temp_rek_köp.append({"Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "ATR": round(atr_varde, 2)})
                        
                    if (rsi >= 72 and macd_korsat_ner) or rsi >= 78:
                        temp_sälj.append({"Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "Anledning": "Extremt Överköpt 🔥" if rsi >= 78 else "Vändning Nedåt 🚨"})
            except Exception as e:
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
    st.success("🌟 ULTRA-KÖP (Trend + Volym + RSI + MACD)")
    if st.session_state.ultra_köp: 
        st.dataframe(pd.DataFrame(st.session_state.ultra_köp), use_container_width=True)
    else: 
        st.info("Inga aktier har tillräckligt starka köpsignaler just nu.")
        
    st.write("---")
    st.info("👍 REKOMMENDERADE DIPP-KÖP (Översålda i upptrend)")
    if st.session_state.rek_köp: 
        st.dataframe(pd.DataFrame(st.session_state.rek_köp), use_container_width=True)
    else: 
        st.info("Inga säkra dippar i upptrender just nu.")
        
    st.write("---")
    st.subheader("📊 Komplett Översikt")
    if st.session_state.alla_aktier:
        df_visa = pd.DataFrame(st.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        st.dataframe(df_visa, use_container_width=True, height=300)

# --- DYNAMISK RISK-KALKYLATOR & JOURNAL-LOGGNING ---
st.write("---")
st.subheader("💼 Smart Riskkalkylator & Journal")

col_a, col_b = st.columns(2)
with col_a:
    valda_namn = st.text_input("Aktiens namn (t.ex. Sinch):")
    # Ändrat step=0.01 för att tillåta exakta ören på svenska aktier
    kp = st.number_input("Ditt inköpspris (SEK):", min_value=0.0, step=0.01)
with col_b:
    valda_atr = st.number_input("Aktiens ATR-värde:", min_value=0.0, step=0.01)

if kp > 0 and valda_atr > 0:
    stop_loss_pris = kp - (1.5 * valda_atr)
    target_pris = kp + (3.0 * valda_atr)
    
    st.write(f"🎯 **Target:** {target_pris:.2f} SEK | 🛑 **Stop Loss:** {stop_loss_pris:.2f} SEK")
    
    if st.button("Logga denna affär i Journalen 📝", use_container_width=True):
        save_trade(valda_namn, kp, valda_atr, target_pris, stop_loss_pris)
        st.success(f"Affären i {valda_namn} har sparats till din lokala journal!")

# --- VISA AKTUELL JOURNAL ---
st.write("---")
st.subheader("🗂️ Sparade Affärer (Din Trading-journal)")
journal_df = load_journal()
if not journal_df.empty:
    st.dataframe(journal_df, use_container_width=True)
    if st.button("Rensa journalhistorik 🗑️"):
        if os.path.exists(JOURNAL_FILE): 
            os.remove(JOURNAL_FILE)
        st.rerun()
else:
    st.info("Din journal är tom. Logga en affär ovan för att börja samla statistik!")
