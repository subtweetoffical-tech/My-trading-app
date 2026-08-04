import concurrent.futures
import xml.etree.ElementTree as ET
import urllib.parse
import urllib.request

import nltk
import numpy as np
import pandas as pd
import streamlit as st
import ta
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Förbered NLTK VADER
try:
    nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Swing Trading Skanner", layout="wide")
st.title("📈 Swing Trading - Veckokandidater med Nyhetssensor")
st.caption("Skanner för 2–5 dagars innehav baserad på dagsgrafer, marknadstrend och Google News-sentiment.")

# --- AKTIER OCH NAMN ---
NAMN_MAPPNING = {
    # Svenska aktier (SEK)
    "SINCH.ST": "Sinch", "EMBRAC-B.ST": "Embracer", "ASMDEE-B.ST": "Asmodee",
    "SIVERS.ST": "Sivers Semiconductors", "FORTV.ST": "Fortnox", "EVO.ST": "Evolution", 
    "BETCO.ST": "Betsson", "G5EN.ST": "G5 Entertainment", "MTG-B.ST": "MTG", 
    "BOOZT.ST": "Boozt", "BHG.ST": "BHG Group", "HPOL-B.ST": "Hexatronic", 
    "MYCR.ST": "Mycronic", "SBB-B.ST": "SBB B", "CORE-B.ST": "Corem B", 
    "BOL.ST": "Boliden", "SSAB-B.ST": "SSAB B", "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B", 
    "NIBE-B.ST": "Nibe", "INVE-B.ST": "Investor B", "AVAN.ST": "Avanza", "HM-B.ST": "H&M B",

    # USA (USD)
    "AAPL": "Apple", "MSFT": "Microsoft", "NVDA": "NVIDIA", "AMD": "AMD", 
    "TSLA": "Tesla", "AMZN": "Amazon", "META": "Meta", "GOOGL": "Alphabet", 
    "PLTR": "Palantir", "COIN": "Coinbase", "MARA": "Marathon Digital", "MSTR": "MicroStrategy"
}

AKTIER = list(NAMN_MAPPNING.keys())

# --- INSTÄLLNINGAR (SIDEBAR) ---
st.sidebar.header("⚙️ Filter & Inställningar")
min_omsattning_sek = st.sidebar.number_input("Min dagsomsättning (SEK)", value=1000000, step=500000)
min_rvol = st.sidebar.slider("Min RVOL (Relativ Volym 20d)", 1.0, 3.0, 1.2, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("🌍 Smart Filtrering")
krav_marknadstrend = st.sidebar.checkbox("Kräv att S&P 500 har positiv trend", value=True)
krav_nyheter = st.sidebar.checkbox("Filtrera bort aktier med negativa nyheter", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Risk & Target (Dags-ATR)")
atr_sl_mult = st.sidebar.slider("Stop Loss (ATR-multipel)", 1.0, 3.0, 1.5, 0.1)
atr_tp_mult = st.sidebar.slider("Target (ATR-multipel)", 1.5, 5.0, 2.5, 0.1)

# --- HJÄLPFUNKTIONER ---

@st.cache_data(ttl=3600)
def hamta_dagsdata(tickers_list):
    alla_tickers_str = " ".join(tickers_list)
    return yf.download(alla_tickers_str, period="1y", interval="1d", progress=False, group_by="ticker")

@st.cache_data(ttl=1800)
def ar_marknaden_positiv():
    try:
        sp500 = yf.Ticker("^GSPC").history(period="60d")
        if len(sp500) < 50:
            return True
        sma_50 = sp500['Close'].rolling(50).mean().iloc[-1]
        senaste_pris = sp500['Close'].iloc[-1]
        return senaste_pris >= sma_50
    except Exception:
        return True

@st.cache_data(ttl=1800)
def ar_nyhetssentiment_ok(bolagsnamn):
    try:
        # Sök efter engelska nyheter för stabilare VADER-analys
        query = urllib.parse.quote(f"{bolagsnamn} stock news analysis")
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            xml_data = response.read()
        
        root = ET.fromstring(xml_data)
        titlar = [item.find('title').text for item in root.findall('.//item')[:5]]
        
        if not titlar:
            return True
        
        sia = SentimentIntensityAnalyzer()
        scores = [sia.polarity_scores(t)['compound'] for t in titlar]
        snitt_score = sum(scores) / len(scores)
        
        return snitt_score >= -0.05
    except Exception:
        return True

# --- SKANNING ---
if st.button("Hämta Veckokandidater 🚀", use_container_width=True):
    temp_trend = []
    temp_dipp = []

    marknadstrend_ok = ar_marknaden_positiv() if krav_marknadstrend else True
    
    if krav_marknadstrend and not marknadstrend_ok:
        st.warning("⚠️ Breda marknaden (S&P 500) ligger under sitt 50-dagars medelvärde. Skanningen är mer restriktiv.")

    with st.spinner("Hämtar marknadsdata och beräknar indikatorer..."):
        stort_df = hamta_dagsdata(AKTIER)

    kandidater_for_nyheter = []

    if not stort_df.empty:
        USD_SEK_KURS = 10.5  # Ungefärlig växelkurs för korrekta omsättningsfilter
        
        for ticker in AKTIER:
            try:
                fullt_namn = NAMN_MAPPNING[ticker]
                ar_sek = ticker.endswith(".ST")
                valuta = "SEK" if ar_sek else "USD"
                
                if isinstance(stort_df.columns, pd.MultiIndex):
                    if ticker not in stort_df.columns.levels[0]:
                        continue
                    df_ticker = stort_df[ticker].copy()
                else:
                    df_ticker = stort_df.copy()

                df_ticker = df_ticker.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

                if len(df_ticker) < 60:
                    continue

                close_ser = df_ticker['Close'].squeeze()
                high_ser = df_ticker['High'].squeeze()
                low_ser = df_ticker['Low'].squeeze()
                vol_ser = df_ticker['Volume'].squeeze()

                pris = float(close_ser.iloc[-1])
                vol = float(vol_ser.iloc[-1])

                # Omsättningsfilter (Justera USD till SEK)
                snitt_dagsomsattning = (close_ser * vol_ser).tail(10).mean()
                snitt_omsattning_sek = snitt_dagsomsattning * (1.0 if ar_sek else USD_SEK_KURS)
                
                if snitt_omsattning_sek < min_omsattning_sek:
                    continue

                # Indikatorer
                rsi = float(ta.momentum.rsi(close_ser, window=14).iloc[-1])
                vol_snitt_20 = float(vol_ser.rolling(window=20).mean().iloc[-1])
                ema_20 = float(ta.trend.ema_indicator(close_ser, window=20).iloc[-1])
                sma_50 = float(ta.trend.sma_indicator(close_ser, window=50).iloc[-1])
                atr_varde = float(ta.volatility.average_true_range(high_ser, low_ser, close_ser, window=14).iloc[-1])

                if pd.isna(rsi) or pd.isna(ema_20) or pd.isna(sma_50) or pd.isna(atr_varde):
                    continue

                rvol = (vol / vol_snitt_20) if (pd.notna(vol_snitt_20) and vol_snitt_20 > 0) else 1.0

                stop_loss = pris - (atr_sl_mult * atr_varde)
                target = pris + (atr_tp_mult * atr_varde)
                risk = pris - stop_loss
                reward = target - pris
                rr_kvot = round(reward / risk, 2) if risk > 0 else 0.0

                is_momentum = (pris > ema_20 and ema_20 > sma_50 and (50 <= rsi <= 68) and rvol >= min_rvol)
                is_dipp = (pris > sma_50 and rsi <= 45 and pris <= ema_20)

                if not (is_momentum or is_dipp):
                    continue

                if marknadstrend_ok:
                    data_punkt = {
                        "Aktie": fullt_namn,
                        "Ticker": ticker,
                        "Pris": f"{pris:.2f} {valuta}",
                        "RSI (14)": round(rsi, 1),
                        "RVOL": f"{rvol:.1f}x",
                        "R/R Kvot": f"1:{rr_kvot:.2f}",
                        "Stop Loss": f"{stop_loss:.2f} {valuta}",
                        "Target": f"{target:.2f} {valuta}",
                        "Förv. Vinst/aktie": f"{(target - pris):.2f} {valuta}",
                        "RVOL_num": round(rvol, 2),
                        "typ": "momentum" if is_momentum else "dipp"
                    }
                    kandidater_for_nyheter.append(data_punkt)

            except Exception:
                continue

        # Parallell nyhetskontroll för snabbare körning
        stora_kandidater = []
        if krav_nyheter and kandidater_for_nyheter:
            with st.spinner("Analyserar nyhetssentiment..."):
                with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                    future_to_cand = {
                        executor.submit(ar_nyhetssentiment_ok, c["Aktie"]): c 
                        for c in kandidater_for_nyheter
                    }
                    for future in concurrent.futures.as_completed(future_to_cand):
                        cand = future_to_cand[future]
                        try:
                            if future.result():
                                stora_kandidater.append(cand)
                        except Exception:
                            stora_kandidater.append(cand)
        else:
            stora_kandidater = kandidater_for_nyheter

        # Sortera upp i respektive lista
        for cand in stora_kandidater:
            typ = cand.pop("typ")
            if typ == "momentum":
                temp_trend.append(cand)
            else:
                temp_dipp.append(cand)

    # --- VISNING AV RESULTAT ---
    st.subheader("🚀 Trend-Momentum (Köp i stark upptrend)")
    if temp_trend:
        df_mom = pd.DataFrame(temp_trend)
        df_mom = df_mom.sort_values(by="RVOL_num", ascending=False).drop(columns=["RVOL_num"])
        st.dataframe(df_mom, use_container_width=True)
    else:
        st.info("Inga momentum-kandidater just nu som klarade de tekniska och nyhetsbaserade filtren.")

    st.subheader("📉 Rekyl i Upptrend (Dipp-köp)")
    if temp_dipp:
        df_dipp = pd.DataFrame(temp_dipp)
        df_dipp = df_dipp.sort_values(by="RSI (14)", ascending=True).drop(columns=["RVOL_num"])
        st.dataframe(df_dipp, use_container_width=True)
    else:
        st.info("Inga dipp-kandidater just nu som klarade de tekniska och nyhetsbaserade filtren.")
