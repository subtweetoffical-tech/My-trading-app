import streamlit as st
import yfinance as yf
import pandas as pd
import ta

# Sätt sidkonfiguration
st.set_page_config(page_title="Högvolatil 200 Scanner", layout="centered")

st.title("⚡ Högvolatila Scannern (200 Aktier under 250 kr)")

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ STRATEGI FÖR HÖG VOLATILITET & FLERA AFFÄRER/VECKA"):
    st.markdown("""
    ### Din specialanpassade strategi:
    * **Hög svängning (Volatilitet):** Listan är fylld med gaming, tillväxt, tech och råvaror som rör sig snabbt.
    * **Prisspärr (Max 250 kr):** Alla aktier är billiga nog för att du ska kunna köpa flera stycken med dina 1 000 kr.
    * **Internationell mix i SEK:** Innehåller utländska bolag och råvarurelaterade aktier som handlas direkt på Stockholmsbörsen för att slippa dyra växlingsavgifter.
    * **1-Timmarsdata (1h):** Perfekt tidsupplösning för att hitta köp- och säljlägen som varar i 1–3 dagar.
    """)

# Ordbok med exakt 200 rörliga aktier (mestadels tillväxt, tech, gaming, råvaror och SDBs)
NAMN_MAPPNING = {
    # --- TECH, GAMING & TILLVÄXT (Sverige) ---
    "SINCH.ST": "Sinch (Tech)", "EMBRAC-B.ST": "Embracer (Gaming)", "FORTV.ST": "Fortnox (Mjukvara)",
    "EVO.ST": "Evolution (iGaming)", "BETCO.ST": "Betsson (Gaming)", "G5EN.ST": "G5 Entertainment",
    "MTG-B.ST": "MTG (Gaming)", "PAR.ST": "Paradox Interactive", "BOOZT.ST": "Boozt (E-handel)",
    "BHG.ST": "BHG Group (E-handel)", "HPOL-B.ST": "Hexatronic (Fiber)", "MYCR.ST": "Mycronic (Tech)",
    "HMS.ST": "HMS Networks (IoT)", "SBB-B.ST": "SBB B (Fastigheter)", "CORE-B.ST": "Corem B (Fastigheter)",
    "OASM.ST": "Oasmia Pharmaceutical", "BICO.ST": "BICO Group (Biotech)", "CANT.ST": "Cantargia (Biotech)",
    "ANOT.ST": "Anoto Group (Tech)", "FING-B.ST": "Fingerprint Cards", "SVIK.ST": "Studsvik (Energi)",
    "PCELL.ST": "PowerCell (Vätgas)", "SEDG.ST": "Sedana Medical", "XVIVO.ST": "Xvivo Perfusion",
    "VITR.ST": "Vitrolife (Biotech)", "BIOT.ST": "Biotage (Biotech)", "IMMUN.ST": "Immunovia",
    "STNK.ST": "Stenkulla", "TIGO-SDB.ST": "Millicom (Latinamerika SDB)", "SRECO.ST": "SOBI (Biotech)",
    
    # --- RÅVAROR, ENERGI & INDUSTRI (Hög svängning) ---
    "BOL.ST": "Boliden (Gruvor)", "SSAB-B.ST": "SSAB B (Stål)", "LUMI.ST": "Lundin Mining",
    "ORRON.ST": "Orron Energy", "AOI.ST": "Africa Oil (Olja)", "MAHA-A.ST": "Maha Energy (Olja)",
    "IPC.ST": "International Petroleum", "SCA-B.ST": "SCA B (Skog)", "STE-R.ST": "Stora Enso",
    "SKF-B.ST": "SKF B", "SAND.ST": "Sandvik", "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B (Försvar)",
    "ALFA.ST": "Alfa Laval", "NIBE-B.ST": "Nibe (Grön Energi)", "DOM.ST": "Dometic",
    "MUNTE.ST": "Munters", "HEXA-B.ST": "Hexagon", "AFRY.ST": "AFRY", "JM.ST": "JM (Bygg)",
    "PEAB-B.ST": "Peab", "NCC-B.ST": "NCC B", "BEI-B.ST": "Beijer Ref", "LAGR-B.ST": "Lagercrantz",
    "ADDTECH-B.ST": "Addtech", "INDT.ST": "Indutrade", "LIFCO-B.ST": "Lifco", "NORD.ST": "Nordnet",
    "AVAN.ST": "Avanza", "RESURS.ST": "Resurs Holding", "HOFI.ST": "Hoist Finance",
    
    # --- KONSUMENT, FASTIGHET & ÖVRIGT SVERIGE ---
    "HM-B.ST": "H&M B", "BILI.ST": "Bilia", "MEKO.ST": "Mekonomen", "CLAS-B.ST": "Clas Ohlson",
    "WNDR.ST": "Wonderland", "DUST.ST": "Dustin Group", "ALIV-SDB.ST": "Autoliv SDB",
    "FABG.ST": "Fabege", "WIHL.ST": "Wihlborgs", "WALL-B.ST": "Wallenstam", "NYF.ST": "Nyfosa",
    "DIOS.ST": "Diös", "CAST.ST": "Castellum", "BALD-B.ST": "Balder", "CAT-B.ST": "Catena",
    "PLAZ-B.ST": "Platzer", "COOR.ST": "Coor", "LOOM.ST": "Loomis", "SECUM-B.ST": "Securitas",
    "TELE2-B.ST": "Tele2", "TELIA.ST": "Telia Company", "ERIC-B.ST": "Ericsson B",
    "AXFO.ST": "Axfood", "ICA.ST": "ICA (Om noterad)", "AALB.ST": "Aalborg", "RVRC.ST": "RevolutionRace",
    "ESSity-B.ST": "Essity B", "GETI-B.ST": "Getinge", "ELUX-B.ST": "Electrolux", "BRAV.ST": "Bravida",
    
    # --- UTVALDA NORDISKA / INTERNATIONELLA PÅ STO (SEK) ---
    "STEF.ST": "Stefanel", "SAS.ST": "SAS (Hög risk)", "SOTK.ST": "Sotkamo Silver",
    "GIG.ST": "Gaming Innovation Group", "KRE.ST": "Kambi Group", "BETCO-B.ST": "Betsson",
    "LEO.ST": "LeoVegas", "EVO-SE.ST": "Evolution SEK", "ASAP.ST": "Asapion",
    "NEVI.ST": "Nevici", "MGI.ST": "Media and Games Inv.", "ENQ.ST": "EnQuest (Olja)",
    "SEMCON.ST": "Semcon", "COREG.ST": "Corem", "EPI-B.ST": "Epiroc B",
    
    # --- FLER SVENSKA VOLATILA SMÅ- OCH MIDCAPS ---
    "ACTI.ST": "Actic Group", "AMAST.ST": "Amasten", "ANOD.ST": "Anod",
    "ARO.ST": "Aros Bostad", "BASE.ST": "Baseload Energy", "BEGR.ST": "Bergs Timber",
    "BONEX.ST": "BoneSupport", "BOULE.ST": "Boule Diagnostics", "BUFF.ST": "Buffalo",
    "CALL.ST": "Calliditas Therapeutics", "CAMP.ST": "Camurus", "CAT-A.ST": "Catella A",
    "CELL.ST": "Cellink", "CIBUS.ST": "Cibus Nordic", "CLIME.ST": "Climeon",
    "CONRIC.ST": "Conric", "DDIAG.ST": "Devicell", "EAST.ST": "Eastnine",
    "EDGA.ST": "Edgeware", "EEL.ST": "Eolus Vind", "ELAN.ST": "Eltel",
    "ENEA.ST": "Enea", "ENRO.ST": "Eniro", "ETX.ST": "Etrion",
    "FAG.ST": "Fagerhult", "GARO.ST": "Garo", "GIGSE.ST": "GIG",
    "GREEN.ST": "Green Landscaping", "GTI.ST": "GTI", "HANZA.ST": "Hanza Holding",
    "HEBA-B.ST": "Heba B", "HEXS.ST": "Hexatronic S", "HISTO.ST": "Histolab",
    "HUM.ST": "Humana", "IAR.ST": "I.A.R Systems", "IMCH.ST": "Implantica",
    "IRRAS.ST": "Irras", "ISOF.ST": "Isofol Medical", "ITAB.ST": "ITAB Shop Concept",
    "IVSO.ST": "Invisio", "KARO.ST": "Karo Healthcare", "KAV.ST": "Kavli",
    "KDEV.ST": "Karolinska Development", "KLED.ST": "Kallebäck", "MIDW-B.ST": "Midway B",
    "MIPS.ST": "MIPS (Hjälmtech)", "MQ.ST": "MQ Marqet", "NCAB.ST": "NCAB Group",
    "NMAN.ST": "Nederman", "NIVIKA-B.ST": "Nivika B", "NOLATO-B.ST": "Nolato B",
    "NOTE.ST": "NOTE (Elektronik)", "NPPER.ST": "Nepa", "OBL.ST": "Obligator",
    "OEM-B.ST": "OEM International", "OPUS.ST": "Opus Group", "ORTI-B.ST": "Ortivus B",
    "PION-B.ST": "Pion Group B", "PREB.ST": "Prevas B", "PRIC-B.ST": "Pricer B",
    "PROB.ST": "Probi", "PROEF.ST": "Proffice", "PROV.ST": "Probi",
    "QUIA.ST": "Q-Clean", "QLINEA.ST": "Qlinea", "RAY-B.ST": "RaySearch Laboratories",
    "RECI-B.ST": "Recipharm B", "RHOV.ST": "Rhovac", "SANDB.ST": "Sandberg",
    "SCST.ST": "Scandic Hotels", "SECT-B.ST": "Sectra B", "SEMA.ST": "Semcon",
    "SENS.ST": "Sustainable Energy", "SERNE-B.ST": "Serneke B", "SILI.ST": "Silicon",
    "SINT.ST": "SinterCast", "SIRI.ST": "Sirius", "SKAF-B.ST": "Skistar B",
    "SMID.ST": "Smidmek", "SOFT-B.ST": "Softronic B", "SOLV.ST": "Soltech Energy",
    "SPAG.ST": "Spago Nanomedicine", "STAL.ST": "Stallarholmen", "STG.ST": "Stille",
    "SVCR.ST": "Svenska Stand.", "SWECO-B.ST": "Sweco B", "SWMA.ST": "Swedish Match",
    "SYSTEM.ST": "Systemair", "TAGM-B.ST": "TagMaster B", "TETH.ST": "Tethys Oil",
    "TFBNK.ST": "TF Bank", "TIED.ST": "Tiedemann", "TOBII.ST": "Tobii (Eyetracking)",
    "TRACK.ST": "Tracklib", "TRAC-B.ST": "Traction B", "TROAX.ST": "Troax Group",
    "VBG-B.ST": "VBG Group B", "VNV.ST": "VNV Global", "VOLATI.ST": "Volati",
    "XANO-B.ST": "XANO Industri B", "ZUG.ST": "Zug"
}

AKTIER = list(NAMN_MAPPNING.keys())

if "ultra_köp" not in st.session_state: st.session_state.ultra_köp = []
if "rek_köp" not in st.session_state: st.session_state.rek_köp = []
if "ultra_sälj" not in st.session_state: st.session_state.ultra_sälj = []
if "alla_aktier" not in st.session_state: st.session_state.alla_aktier = []
if "har_skannat" not in st.session_state: st.session_state.har_skannat = False

MAX_AKTIEPRIS = 250.0

if st.button("STARTA VOLATILITETSSÖKNING ⚡ (200 Aktier)", use_container_width=True):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    temp_ultra_köp = []
    temp_rek_köp = []
    temp_sälj = []
    temp_alla = []
    
    # Batch-hämtning av alla 200 aktier samtidigt för maximal snabbhet
    alla_tickers_str = " ".join(AKTIER)
    try:
        stort_df = yf.download(alla_tickers_str, period="30d", interval="1h", group_by="ticker", progress=False)
    except Exception as e:
        st.error(f"Kunde inte hämta data: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{len(AKTIER)}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            try:
                df_ticker = stort_df[ticker] if isinstance(stort_df.columns, pd.MultiIndex) else stort_df
                close_series = df_ticker['Close'].dropna()
                volume_series = df_ticker['Volume'].dropna()
                open_series = df_ticker['Open'].dropna()
                
                if len(close_series) < 25: continue
                
                pris = float(close_series.iloc[-1])
                
                # PRISFILTER: Sortera bort för dyra aktier direkt
                if pris > MAX_AKTIEPRIS or pris <= 0:
                    continue
                    
                df_rsi = ta.momentum.rsi(close_series, window=14)
                df_vol_snitt = volume_series.rolling(window=10).mean()
                macd_obj = ta.trend.MACD(close_series)
                df_macd = macd_obj.macd()
                df_macd_sig = macd_obj.macd_signal()
                
                pris_förra_bar = float(close_series.iloc[-2])
                öppning = float(open_series.iloc[-1])
                rsi = float(df_rsi.iloc[-1])
                vol = float(volume_series.iloc[-1])
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

                temp_alla.append({
                    "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal för 1000kr": max_antal,
                    "Senaste timmen %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL (Volym)": f"{rvol:.2f}x", "MACD": macd_status
                })

                # --- KÖPLOGIK (Anpassad för snabbare svängningar) ---
                if rsi <= 35 and macd_korsat_upp:
                    temp_ultra_köp.append({
                        "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal": max_antal, "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x"
                    })
                elif rsi <= 28 and pris > pris_förra_bar:
                    temp_rek_köp.append({
                        "Aktie": fullt_namn, "Pris (SEK)": round(pris, 2), "Max antal": max_antal, "RSI": round(rsi, 1)
                    })
                    
                # --- SÄLJLOGIK ---
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
    st.subheader("📊 Komplett Översikt (Sorterat efter lägst RSI)")
    if st.session_state.alla_aktier:
        df_visa = pd.DataFrame(st.session_state.alla_aktier).sort_values(by="RSI", ascending=True)
        st.dataframe(df_visa, use_container_width=True, height=400)
else:
    st.info("Klicka på knappen ovan för att starta skanningen av de 200 högvolatila aktierna.")

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
