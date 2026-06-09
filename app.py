import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration
st.set_page_config(page_title="Högvolatil 200 Scanner", layout="centered")

st.title("⚡ Högvolatila Scannern (Optimera Data)")

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ STRATEGI FÖR HÖG VOLATILITET & FLERA AFFÄRER/VECKA"):
    st.markdown("""
    ### Din specialanpassade strategi (Buggtestad):
    * **1-Timmarsdata (1h):** Perfekt för svängningar som varar i några dagar.
    * **Säker datahantering:** Fixat MultiIndex-buggen från Yahoo Finance så att inga aktier missas i skanningen.
    """)

# Uppdaterad och rensad lista (Ingen SAS, ICA, etc.)
NAMN_MAPPNING = {
    "SINCH.ST": "Sinch (Tech)", "EMBRAC-B.ST": "Embracer (Gaming)", "FORTV.ST": "Fortnox (Mjukvara)",
    "EVO.ST": "Evolution (iGaming)", "BETCO.ST": "Betsson (Gaming)", "G5EN.ST": "G5 Entertainment",
    "MTG-B.ST": "MTG (Gaming)", "BOOZT.ST": "Boozt (E-handel)", "BHG.ST": "BHG Group (E-handel)", 
    "HPOL-B.ST": "Hexatronic (Fiber)", "MYCR.ST": "Mycronic (Tech)", "SBB-B.ST": "SBB B (Fastigheter)", 
    "CORE-B.ST": "Corem B (Fastigheter)", "BICO.ST": "BICO Group (Biotech)", "FING-B.ST": "Fingerprint Cards", 
    "PCELL.ST": "PowerCell (Vätgas)", "VITR.ST": "Vitrolife (Biotech)", "BIOT.ST": "Biotage (Biotech)", 
    "TIGO-SDB.ST": "Millicom SDB", "SRECO.ST": "SOBI (Biotech)", "BOL.ST": "Boliden (Gruvor)", 
    "SSAB-B.ST": "SSAB B (Stål)", "ORRON.ST": "Orron Energy", "AOI.ST": "Africa Oil (Olja)", 
    "SCA-B.ST": "SCA B (Skog)", "STE-R.ST": "Stora Enso", "SKF-B.ST": "SKF B", "SAND.ST": "Sandvik", 
    "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B (Försvar)", "NIBE-B.ST": "Nibe (Grön Energi)", 
    "DOM.ST": "Dometic", "HEXA-B.ST": "Hexagon", "AFRY.ST": "AFRY", "JM.ST": "JM (Bygg)",
    "PEAB-B.ST": "Peab", "NCC-B.ST": "NCC B", "AVAN.ST": "Avanza", "NORD.ST": "Nordnet",
    "HM-B.ST": "H&M B", "BILI.ST": "Bilia", "DUST.ST": "Dustin Group", "ALIV-SDB.ST": "Autoliv SDB",
    "FABG.ST": "Fabege", "WIHL.ST": "Wihlborgs", "WALL-B.ST": "Wallenstam", "NYF.ST": "Nyfosa",
    "CAST.ST": "Castellum", "BALD-B.ST": "Balder", "SECUM-B.ST": "Securitas", "TELE2-B.ST": "Tele2", 
    "TELIA.ST": "Telia Company", "ERIC-B.ST": "Ericsson B", "AXFO.ST": "Axfood", "RVRC.ST": "RevolutionRace", 
    "GETI-B.ST": "Getinge", "ELUX-B.ST": "Electrolux", "BONEX.ST": "BoneSupport", "MIPS.ST": "MIPS",
    "NOTE.ST": "NOTE (Elektronik)", "TOBII.ST": "Tobii (Eyetracking)", "VNV.ST": "VNV Global"
}

AKTIER = list(NAMN_MAPPNING.keys())

if "ultra_köp" not in st.session_state: st.session_state.ultra_köp = []
if "rek_köp" not in st.session_state: st.session_state.rek_köp = []
if "ultra_sälj" not in st.session_state: st.session_state.ultra_sälj = []
if "alla_aktier" not in st.session_state: st.session_state.alla_aktier = []
if "har_skannat" not in st.session_state: st.session_state.har_skannat = False

MAX_AKTIEPRIS = 250.0

if st.button("STARTA VOLATILITETSSÖKNING ⚡", use_container_width=True):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    alla_tickers_str = " ".join(AKTIER)
    try:
        # HÄMTA UTAN GROUP_BY FÖR ATT UNDVIKA MULTIINDEX-KRASCH
        stort_df = yf.download(alla_tickers_str, period="30d", interval="1h", progress=False)
    except Exception as e:
        st.error(f"Kunde inte hämta data: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{len(AKTIER)}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            try:
                # SÄKER EXTRAHERING AV COLUMNS FRÅN YFINANCE MultiIndex
                if ('Close', ticker) in stort_df.columns:
                    df_ticker = pd.DataFrame({
                        'Open': stort_df['Open'][ticker],
                        'Close': stort_df['Close'][ticker],
                        'Volume': stort_df['Volume'][ticker]
                    }).dropna() # Dropna på hela strukturen samtidigt, inte kolumn för kolumn!
                else:
                    continue
                
                if len(df_ticker) < 25: continue
                
                pris = float(df_ticker['Close'].iloc[-1])
                
                if pris > MAX_AKTIEPRIS or pris <= 0:
                    continue
                    
                # Beräkna indikatorer på den tvättade dataramen
                df_rsi = ta.momentum.rsi(df_ticker['Close'], window=14)
                df_vol_snitt = df_ticker['Volume'].rolling(window=10).mean()
                macd_obj = ta.trend.MACD(df_ticker['Close'])
                df_macd = macd_obj.macd()
                df_macd_sig = macd_obj.macd_signal()
                
                pris_förra_bar = float(df_ticker['Close'].iloc[-2])
                öppning = float(df_ticker['Open'].iloc[-1])
                rsi = float(df_rsi.iloc[-1])
                vol = float(df_ticker['Volume'].iloc[-1])
                v_snitt = float(df_vol_snitt.iloc[-1])
                m = float(df_macd.iloc[-1])
                s = float(df_macd_sig.iloc[-1])
                
                rvol = vol / v_snitt if v_snitt > 0 else 1.0
                utveckling_bar = ((pris - öppning) / öppning) * 100
                fullt_namn = NAMN_MAPPNING[ticker]
                
                m_igår = float(df_macd.iloc[-2])
                s_igår = float(df_macd_sig.iloc[-2])
                macd_korsat_upp = m > s and m_igår <= s_igår
                macd_korsat_ner = m < s and m_igår >= s_igår
                
                macd_status = "Avvakta 🟡"
                if m > s:
                    macd_status = "Köp 🟢" if macd_korsat_upp else "Stark 📈"
                elif m < s:
                    macd_status = "Sälj 🔴" if macd_korsat_ner else "Svag 📉"

                max_antal = int(1000 // pris)

                if max_antal > 0:
                    temp_alla.append({
                        "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal för 1000kr": max_antal,
                        "Senaste timmen %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "MACD": macd_status
                    })

                    if rsi <= 35 and macd_korsat_upp:
                        temp_ultra_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal": max_antal, "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x"
                        })
                    elif rsi <= 28 and pris > pris_förra_bar:
                        temp_rek_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal": max_antal, "RSI": round(rsi, 1)
                        })
                        
                    if (rsi >= 72 and macd_korsat_ner) or rsi >= 78:
                        anledning = "Extremt Överköpt 🔥" if rsi >= 78 else "Vändning Nedåt 🚨"
                        temp_sälj.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "Anledning": anledning
                        })
            except:
                continue

    st.session_state.ultra_köp = temp_ultra_köp
    st.session_state.rek_köp = temp_rek_köp
    st.session_state.ultra_sälj = temp_sälj
    st.session_state.alla_aktier = temp_alla
    st.session_state.har_skannat = True

    progress_bar.empty()
    status_text.empty()

# --- PRESENTATION ---
if st.session_state.har_skannat:
    st.success("🌟 ULTRA-KÖP (Snabb RSI-dipp + MACD-vändning)")
    if st.session_state.ultra_köp:
        st.dataframe(pd.DataFrame(st.session_state.ultra_köp), use_container_width=True)
    else:
        st.info("Inga aktier har supersignaler just den här timmen.")
        
    st.write("---")
    st.info("👍 REKOMMENDERADE DIPP-KÖP (Översålda på kort sikt)")
    if st.session_state.rek_köp:
        st.dataframe(pd.DataFrame(st.session_state.rek_köp), use_container_width=True)
    else:
        st.info("Inga kraftiga dippar just nu.")
        
    st.write("---")
    st.error("🚨 FÖRESLAGNA SÄLJ (Snabba vinsthemtagningar)")
    if st.session_state.ultra_sälj:
        st.dataframe(pd.DataFrame(st.session_state.ultra_sälj), use_container_width=True)
    else:
        st.info("Inga aktier är överhettade just nu.")
        
    st.write("---")
    st.subheader("📊 Komplett Översikt")
    if st.session_state.alla_aktier:
        df_visa = pd.DataFrame(st.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        st.dataframe(df_visa, use_container_width=True, height=400)

# --- DYNAMISK TRADE-KALKYLATOR ---
st.write("---")
st.subheader("💼 Kalkylator för Snabba Affärer")
kp = st.number_input("Ditt inköpspris (SEK):", min_value=0.0, step=1.0)

col1, col2 = st.columns(2)
with col1:
    vinst_procent = st.slider("Målvinst per trade (%)", 1.5, 12.0, 4.0, step=0.5)
with col2:
    loss_procent = st.slider("Stop Loss (%)", 1.5, 6.0, 2.5, step=0.5)

if kp > 0:
    target = kp * (1 + (vinst_procent / 100))
    stop = kp * (1 - (loss_procent / 100))
    st.success(f"🎯 Ta vinst vid: **{target:.2f} SEK** (+{vinst_procent}%)")
    st.error(f"🛑 Gå ur (Stop Loss) vid: **{stop:.2f} SEK** (-{loss_procent}%)")
