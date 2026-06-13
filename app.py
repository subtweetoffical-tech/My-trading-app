import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np

# Sätt sidkonfiguration
st.set_page_config(page_title="Högvolatil 200 Scanner", layout="centered")

st.title("⚡ Global Trading Scanner - Med Köprekommendation")

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ VARFÖR ÄR DET BRA ATT HANDLA DESSA AKTIER?"):
    st.markdown("""
    ### Tre anledningar till varför det här urvalet passar din portfölj:
    1. **Anpassat för 1 000 kr:** Alla aktier kostar under 250 kr, vilket gör att du faktiskt kan köpa ett antal aktier och bygga en portfölj, istället för att hela kassan låses i en enda dyr aktie.
    2. **0 kr i courtage:** Genom att hålla oss till svenska aktier i SEK slipper du valutaväxlingsavgifter. Har du Avanza Start handlar du helt gratis!
    3. **Rörelse & Volatilitet:** Listan fokuserar på tech, gaming och råvaror – sektorer som svänger tillräckligt mycket under en dag för att ge snabba vinstmöjligheter.
    """)

# Urval av rörliga aktier under 250 kr (Nasdaq Stockholm & First North)
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
    "NOTE.ST": "NOTE (Elektronik)", "TOBII.ST": "Tobii (Eyetracking)", "VNV.ST": "VNV Global",
    "DIOS.ST": "Diös Fastigheter", "HEBA-B.ST": "Heba B", "PLAT-B.ST": "Platzer", "CAT-B.ST": "Catena",
    "TRIAN-B.ST": "Trianon B", "PNDX-B.ST": "Pandox", "SLP-B.ST": "Swedish Logistic Properties", "EAST.ST": "Eastnine",
    "KFAST-B.ST": "K-Fastigheter", "LOGIST.ST": "Logistea", "INV.ST": "Invisio", "FAG.ST": "Fagerhult",
    "KNOW.ST": "Knowit", "B3.ST": "B3 Consulting", "ITS.ST": "I.A.R Systems", "FORX.ST": "Formpipe Software",
    "ADD-B.ST": "AddNode Group", "TIETO.ST": "Tietoevry", "HMS.ST": "HMS Networks",
    "PREV.ST": "Prevas B", "SOFT-B.ST": "Softronic", "EXP-B.ST": "Exsitec", "CINT.ST": "Cint Group",
    "SVR-B.ST": "Svedbergs B", "TAG.ST": "TagMaster", "SENS.ST": "Sustainable Energy",
    "STU-B.ST": "Starbreeze B", "MAG.ST": "Mag Interactive", "ANOD.ST": "Anora Group", "LYKO.ST": "Lyko Group",
    "NELLY.ST": "Nelly Group", "CDON.ST": "CDON", "QNLI.ST": "Qliro", "SPLAY.ST": "Storytel",
    "READ.ST": "Readly International", "PION-B.ST": "PION Group", "CATE.ST": "Catena Media", "ANGI.ST": "Angler Gaming",
    "EVIL.ST": "Enea", "GIG.ST": "Gaming Innovation Group", "KRE.ST": "Kambi Group", "RAK.ST": "Raketech",
    "INVE-B.ST": "Investor B", "KINV-B.ST": "Kinnevik B", "LATO-B.ST": "Latour B", "RATO-B.ST": "Ratos B",
    "CREA-B.ST": "Creades B", "BURE.ST": "Bure Equity", "SVOL-B.ST": "Svolder B", "TRAC-B.ST": "Traction B", 
    "AMBEV.ST": "Ambea", "ATT.ST": "Attendo", "HUM.ST": "Humana", "XBRANE.ST": "Xbrane Biopharma", 
    "MUNTE.ST": "Munters Group", "BEGR.ST": "Beijer Alma", "BELE.ST": "Beijer Ref", "BUFAB.ST": "Bufab",
    "MEKO.ST": "Mekonomen", "SYSTEM.ST": "Systemair", "RESURS.ST": "Resurs Holding", 
    "TF_BANK.ST": "TF Bank", "VOLO.ST": "Volo", "REJL-B.ST": "Rejlers B", 
    "PINS.ST": "Pricer B", "SITRA.ST": "SinterCast", "MALMK.ST": "Gränges", "BEGroup.ST": "BE Group", 
    "RUG.ST": "RugVista", "NOLA-B.ST": "Nolato B", "CLIME.ST": "Climeon", "OX2.ST": "OX2", 
    "MINESTO.ST": "Minesto", "SALT.ST": "SaltX Technology", "METV.ST": "Metacon",
    "ECCO.ST": "Eolus Vind", "ARISE.ST": "Arise", "CIBUS.ST": "Cibus Nordic Real Estate",
    "MID-B.ST": "Midsona B", "CLAS-B.ST": "Clas Ohlson", "NEWW-B.ST": "New Wave Group", "ITAB.ST": "ITAB Shop Concept", 
    "GREEN.ST": "Green Landscaping", "COOR.ST": "Coor Service Mgmt", "TEQN.ST": "Teqnion", 
    "PROF-B.ST": "Profoto B", "FERRO.ST": "Ferroamp", "GARO.ST": "Garo", "EPIW-B.ST": "Epiroc B", 
    "LIFCO-B.ST": "Lifco B", "INDT.ST": "Indutrade", "ADDV.ST": "AddLife", "BALCO.ST": "Balco Group",
    "TEQN.ST": "Teqnion", "SBB-D.ST": "SBB D"
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

if st.button("STARTA VOLATILITETSSÖKNING ⚡ (200 AKTIER)", use_container_width=True):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    alla_tickers_str = " ".join(AKTIER)
    try:
        # Hämtar data i timintervall (30 dagar ger bra underlag för 14-dagars indikatorer)
        stort_df = yf.download(alla_tickers_str, period="30d", interval="1h", progress=False, group_by="ticker")
    except Exception as e:
        st.error(f"Kunde inte hämta data från Yahoo Finance: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        total_aktier = len(AKTIER)
        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{total_aktier}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / total_aktier)
            
            try:
                # Säkerställ att tickern faktiskt finns i den nedladdade datan
                if ticker in stort_df.columns.levels[0]:
                    df_ticker = stort_df[ticker].dropna(subset=['Close']).copy()
                else:
                    continue
                
                if len(df_ticker) < 25: 
                    continue
                
                pris = float(df_ticker['Close'].iloc[-1])
                
                if pris > MAX_AKTIEPRIS or pris <= 0 or np.isnan(pris):
                    continue
                    
                # Beräkna tekniska indikatorer
                df_rsi = ta.momentum.rsi(df_ticker['Close'], window=14)
                df_vol_snitt = df_ticker['Volume'].rolling(window=10).mean()
                macd_obj = ta.trend.MACD(df_ticker['Close'])
                df_macd = macd_obj.macd()
                df_macd_sig = macd_obj.macd_signal()
                
                if df_rsi.isna().iloc[-1] or df_macd.isna().iloc[-1]:
                    continue

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
                
                # Säker hantering av MACD-korsning (senaste 3 staplarna)
                m_tidigare = df_macd.iloc[-4:-1]
                s_tidigare = df_macd_sig.iloc[-4:-1]
                macd_korsat_upp = (m > s) and (m_tidigare < s_tidigare).any()
                macd_korsat_ner = (m < s) and (m_tidigare > s_tidigare).any()
                
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
                        "Senaste timmen %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "MACD": macd_status
                    })

                    # Filtreringsregler för köp och sälj
                    if rsi <= 35 and m > s:  
                        temp_ultra_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal köp": rek_antal, "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x"
                        })
                    elif rsi <= 28 and pris > pris_förra_bar:
                        temp_rek_köp.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Rek. Antal köp": rek_antal, "RSI": round(rsi, 1)
                        })
                        
                    if (rsi >= 72 and macd_korsat_ner) or rsi >= 78:
                        temp_sälj.append({
                            "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "RSI": round(rsi, 1), "Anledning": "Extremt Överköpt 🔥" if rsi >= 78 else "Vändning Nedåt 🚨"
                        })
            except Exception as e:
                # Loggar fel tyst i bakgrunden så att skannern fortsätter rulla
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
    st.success("🌟 ULTRA-KÖP (Bästa signalerna just nu)")
    if st.session_state.ultra_köp:
        st.dataframe(pd.DataFrame(st.session_state.ultra_köp), use_container_width=True)
    else:
        st.info("Inga aktier har supersignaler just den här timmen.")
        
    st.write("---")
    st.info("👍 REKOMMENDERADE DIPP-KÖP (Översålda)")
    if st.session_state.rek_köp:
        st.dataframe(pd.DataFrame(st.session_state.rek_köp), use_container_width=True)
    else:
        st.info("Inga kraftiga dippar just nu.")
        
    st.write("---")
    st.error("🚨 FÖRESLAGNA SÄLJ (Dags att hämta hem vinst)")
    if st.session_state.ultra_sälj:
        st.dataframe(pd.DataFrame(st.session_state.ultra_sälj), use_container_width=True)
    else:
        st.info("Inga aktier är överhettade just nu.")
        
    st.write("---")
    st.subheader("📊 Komplett Översikt (Sorterat på lägst RSI)")
    if st.session_state.alla_aktier:
        df_visa = pd.DataFrame(st.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        st.dataframe(df_visa, use_container_width=True, height=500)

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
