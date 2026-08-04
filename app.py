import concurrent.futures
import datetime
import random
import time
import urllib.parse
import urllib.request

import feedparser
import nltk
import numpy as np
import pandas as pd
import streamlit as st
import ta
import yfinance as yf
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# --- FÖRBERED NLTK VADER (CACHAD) ---
@st.cache_resource
def init_nltk():
    try:
        nltk.data.find('sentiment/vader_lexicon.zip')
    except LookupError:
        nltk.download('vader_lexicon', quiet=True)

init_nltk()

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Swing Trading Skanner Pro", layout="wide")
st.title("📈 Swing Trading - Veckokandidater Pro")
st.caption("Avancerad skanner med nyhets- & rapportfilter, veckotrend samt positionsberäkning.")

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
st.sidebar.subheader("🌍 Smart Filtrering & Trend")
krav_marknadstrend = st.sidebar.checkbox("Kräv positiv S&P 500 trend (Dags-SMA50)", value=True)
krav_veckotrend = st.sidebar.checkbox("Kräv positiv Veckotrend (Vecko-EMA20)", value=True)
krav_nyheter = st.sidebar.checkbox("Filtrera bort negativa nyheter", value=True)
krav_rapport = st.sidebar.checkbox("Filtrera bort rapport inom 7 dagar", value=True)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Risk, Target & Positionsstorlek")
atr_sl_mult = st.sidebar.slider("Stop Loss (ATR-multipel)", 1.0, 3.0, 1.5, 0.1)
atr_tp_mult = st.sidebar.slider("Target (ATR-multipel)", 1.5, 5.0, 2.5, 0.1)

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Portföljinställningar")
portfolj_kapital = st.sidebar.number_input("Totalt kapital i portföljen (SEK)", value=100000, step=10000)
risk_procent = st.sidebar.slider("Max risk per trade (%)", 0.5, 3.0, 1.0, 0.25) / 100

# --- HJÄLPFUNKTIONER ---

def get_series(df, col_name):
    """Säker funktion för att plocka ut en pd.Series ur en MultiIndex DataFrame."""
    if col_name in df.columns:
        res = df[col_name]
        if isinstance(res, pd.DataFrame):
            return res.iloc[:, 0]
        return res
    return pd.Series(dtype=float)

@st.cache_data(ttl=3600)
def hamta_usd_sek_kurs():
    """Hämtar den aktuella USD/SEK-valutakursen live från Yahoo Finance."""
    try:
        usd_sek = yf.Ticker("USDSEK=X").history(period="5d")
        if not usd_sek.empty:
            close = get_series(usd_sek, 'Close').dropna()
            if not close.empty:
                return float(close.iloc[-1])
    except Exception:
        pass
    return 10.5  # Fallback om hämtningen misslyckas

@st.cache_data(ttl=3600)
def hamta_dagsdata(tickers_list):
    alla_tickers_str = " ".join(tickers_list)
    return yf.download(alla_tickers_str, period="2y", interval="1d", progress=False, group_by="ticker", auto_adjust=True)

@st.cache_data(ttl=1800)
def ar_marknaden_positiv():
    try:
        sp500 = yf.Ticker("^GSPC").history(period="60d")
        if len(sp500) < 50:
            return True
        close = get_series(sp500, 'Close').dropna()
        sma_50 = close.rolling(50).mean().iloc[-1]
        senaste_pris = close.iloc[-1]
        return senaste_pris >= sma_50
    except Exception:
        return True

@st.cache_data(ttl=1800)
def ar_nyhetssentiment_ok(bolagsnamn):
    """Hämtar engelskspråkiga nyheter via Google RSS och beräknar sentiment med VADER."""
    try:
        time.sleep(random.uniform(0.1, 0.4))
        
        query = urllib.parse.quote(f'"{bolagsnamn}" stock market analysis news')
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
        
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        )
        with urllib.request.urlopen(req, timeout=4) as response:
            xml_data = response.read()
        
        feed = feedparser.parse(xml_data)
        titlar = [entry.title for entry in feed.entries[:5] if hasattr(entry, 'title')]
        
        if not titlar:
            return True
        
        sia = SentimentIntensityAnalyzer()
        scores = [sia.polarity_scores(t)['compound'] for t in titlar]
        snitt_score = sum(scores) / len(scores)
        
        return snitt_score >= -0.05
    except Exception:
        return True

@st.cache_data(ttl=7200)
def har_rapport_snart(ticker_symbol):
    """Robust kontroll om bolaget har rapport de närmsta 7 dagarna."""
    try:
        time.sleep(random.uniform(0.2, 0.5))
        t = yf.Ticker(ticker_symbol)
        cal = None
        
        try:
            cal = t.get_calendar()
        except Exception:
            cal = getattr(t, 'calendar', None)
            
        idag = datetime.date.today()
        datum_lista = []

        if cal is not None:
            if isinstance(cal, pd.DataFrame) and not cal.empty:
                datum_lista = cal.values.flatten()
            elif isinstance(cal, pd.Series):
                datum_lista = cal.values
            elif isinstance(cal, dict):
                for v in cal.values():
                    if isinstance(v, (list, tuple, np.ndarray)):
                        datum_lista.extend(v)
                    else:
                        datum_lista.append(v)

        for val in datum_lista:
            try:
                d = pd.to_datetime(val).tz_localize(None).date()
                if 0 <= (d - idag).days <= 7:
                    return True
            except Exception:
                continue
        return False
    except Exception:
        return False

# --- SESSION STATE ---
if "skannat" not in st.session_state:
    st.session_state.skannat = False
    st.session_state.temp_trend = []
    st.session_state.temp_dipp = []

# --- SKANNING ---
if st.button("Hämta Veckokandidater 🚀", use_container_width=True):
    temp_trend = []
    temp_dipp = []

    marknadstrend_ok = ar_marknaden_positiv() if krav_marknadstrend else True
    
    if krav_marknadstrend and not marknadstrend_ok:
        st.warning("⚠️ Breda marknaden (S&P 500) ligger under sitt 50-dagars medelvärde. Skanningen är mer restriktiv.")

    with st.spinner("Hämtar marknadsdata och utför indikatoranalys..."):
        stort_df = hamta_dagsdata(AKTIER)
        usd_sek_kurs = hamta_usd_sek_kurs()

    kandidater_for_extra_koll = []

    if not stort_df.empty:
        for ticker in AKTIER:
            try:
                fullt_namn = NAMN_MAPPNING[ticker]
                ar_sek = ticker.endswith(".ST")
                valuta = "SEK" if ar_sek else "USD"
                
                # Säker utdragning ur MultiIndex DataFrame
                if isinstance(stort_df.columns, pd.MultiIndex):
                    if ticker not in stort_df.columns.levels[0]:
                        continue
                    df_ticker = stort_df[ticker].copy()
                else:
                    df_ticker = stort_df.copy()

                df_ticker.index = pd.to_datetime(df_ticker.index)

                close_ser = get_series(df_ticker, 'Close')
                high_ser = get_series(df_ticker, 'High')
                low_ser = get_series(df_ticker, 'Low')
                vol_ser = get_series(df_ticker, 'Volume')

                combined = pd.concat([close_ser, high_ser, low_ser, vol_ser], axis=1).dropna()
                combined.columns = ['Close', 'High', 'Low', 'Volume']

                if len(combined) < 120:
                    continue

                close_ser = combined['Close']
                high_ser = combined['High']
                low_ser = combined['Low']
                vol_ser = combined['Volume']

                pris = float(close_ser.iloc[-1])
                vol = float(vol_ser.iloc[-1])

                # 1. VECKOTREND (KONTROLLERA VECKOSTÄNGNING)
                if krav_veckotrend:
                    df_weekly = close_ser.resample('W-FRI').last().dropna()
                    
                    # Om sista dagen i datan är fredag eller senare, ta bort sista pågående veckan
                    idag_weekday = datetime.date.today().weekday()
                    if idag_weekday < 4 and len(df_weekly) > 1:
                        df_weekly_closed = df_weekly.iloc[:-1]
                    else:
                        df_weekly_closed = df_weekly

                    if len(df_weekly_closed) > 20:
                        vecko_ema_20 = float(ta.trend.ema_indicator(df_weekly_closed, window=20).iloc[-1])
                        if pd.isna(vecko_ema_20) or pris < vecko_ema_20:
                            continue

                # 2. OMSÄTTNINGSFILTER
                snitt_dagsomsattning = (close_ser * vol_ser).tail(10).mean()
                snitt_omsattning_sek = snitt_dagsomsattning * (1.0 if ar_sek else usd_sek_kurs)
                if snitt_omsattning_sek < min_omsattning_sek:
                    continue

                # 3. TEKNISKA INDIKATORER (DAGSGRAF)
                rsi = float(ta.momentum.rsi(close_ser, window=14).iloc[-1])
                vol_snitt_20 = float(vol_ser.rolling(window=20).mean().iloc[-1])
                ema_20 = float(ta.trend.ema_indicator(close_ser, window=20).iloc[-1])
                sma_50 = float(ta.trend.sma_indicator(close_ser, window=50).iloc[-1])
                atr_varde = float(ta.volatility.average_true_range(high_ser, low_ser, close_ser, window=14).iloc[-1])

                if pd.isna(rsi) or pd.isna(ema_20) or pd.isna(sma_50) or pd.isna(atr_varde):
                    continue

                rvol = (vol / vol_snitt_20) if (pd.notna(vol_snitt_20) and vol_snitt_20 > 0) else 1.0

                # RISK & TARGET BERÄKNING
                stop_loss = pris - (atr_sl_mult * atr_varde)
                target = pris + (atr_tp_mult * atr_varde)
                risk_per_aktie = pris - stop_loss
                reward_per_aktie = target - pris
                rr_kvot = round(reward_per_aktie / risk_per_aktie, 2) if risk_per_aktie > 0 else 0.0

                # MOTSTÅNDSKONTROLL (52-WEEKS HIGH)
                hogsta_52w = float(high_ser.tail(252).max())
                nara_motstand = "⚠️ Ja" if target > hogsta_52w else "Nej"

                # POSITIONSSIZERING
                max_kronor_risk = portfolj_kapital * risk_procent
                risk_per_aktie_sek = risk_per_aktie * (1.0 if ar_sek else usd_sek_kurs)
                
                antal_aktier = int(max_kronor_risk / risk_per_aktie_sek) if risk_per_aktie_sek > 0 else 0
                totalt_kopbelopp_lokal = antal_aktier * pris
                totalt_kopbelopp_sek = totalt_kopbelopp_lokal * (1.0 if ar_sek else usd_sek_kurs)

                pos_str = f"{totalt_kopbelopp_lokal:.0f} {valuta}" if ar_sek else f"{totalt_kopbelopp_lokal:.0f} USD (~{totalt_kopbelopp_sek:.0f} SEK)"

                # KÖPSIGNALER
                is_momentum = (pris > ema_20 and ema_20 > sma_50 and (50 <= rsi <= 68) and rvol >= min_rvol)
                is_dipp = (pris > sma_50 and rsi <= 45 and pris <= ema_20)

                if not (is_momentum or is_dipp):
                    continue

                if marknadstrend_ok:
                    data_punkt = {
                        "Aktie": fullt_namn,
                        "Ticker": ticker,
                        "Pris": f"{pris:.2f} {valuta}",
                        "Antal aktier": f"{antal_aktier} st",
                        "Positionsstorlek": pos_str,
                        "RSI (14)": round(rsi, 1),
                        "RVOL": f"{rvol:.1f}x",
                        "R/R Kvot": f"1:{rr_kvot:.2f}",
                        "Stop Loss": f"{stop_loss:.2f} {valuta}",
                        "Target": f"{target:.2f} {valuta}",
                        "Motstånd (52w)": nara_motstand,
                        "RVOL_num": round(rvol, 2),
                        "typ": "momentum" if is_momentum else "dipp"
                    }
                    kandidater_for_extra_koll.append(data_punkt)

            except Exception:
                continue

        # PARALLELL EXEKVERING AV RAPPORT- OCH NYHETSFILTER
        stora_kandidater = []
        if kandidater_for_extra_koll:
            with st.spinner("Analyserar rapportkalendrar och nyhetssentiment i parallella trådar..."):
                def utfor_extra_kontroller(cand):
                    t_symbol = cand["Ticker"]
                    b_namn = cand["Aktie"]
                    
                    if krav_rapport and har_rapport_snart(t_symbol):
                        return None
                    if krav_nyheter and not ar_nyhetssentiment_ok(b_namn):
                        return None
                    return cand

                # Reducerat max_workers till 2 för att minska risken för Yahoo-rate limits
                with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                    resultat = list(executor.map(utfor_extra_kontroller, kandidater_for_extra_koll))
                    stora_kandidater = [c for c in resultat if c is not None]

        # SORTERA KOORDINERAT
        for cand in stora_kandidater:
            typ = cand.pop("typ")
            if typ == "momentum":
                temp_trend.append(cand)
            else:
                temp_dipp.append(cand)

    # Spara till Session State
    st.session_state.temp_trend = temp_trend
    st.session_state.temp_dipp = temp_dipp
    st.session_state.skannat = True

# --- VISNING AV RESULTAT ---
if st.session_state.skannat:
    st.subheader("🚀 Trend-Momentum (Köp i stark upptrend)")
    if st.session_state.temp_trend:
        df_mom = pd.DataFrame(st.session_state.temp_trend)
        df_mom = df_mom.sort_values(by="RVOL_num", ascending=False).drop(columns=["RVOL_num"])
        st.dataframe(df_mom, use_container_width=True)
    else:
        st.info("Inga momentum-kandidater just nu som klarade de tekniska och nyhetsbaserade filtren.")

    st.subheader("📉 Rekyl i Upptrend (Dipp-köp)")
    if st.session_state.temp_dipp:
        df_dipp = pd.DataFrame(st.session_state.temp_dipp)
        df_dipp = df_dipp.sort_values(by="RSI (14)", ascending=True).drop(columns=["RVOL_num"])
        st.dataframe(df_dipp, use_container_width=True)
    else:
        st.info("Inga dipp-kandidater just nu som klarade de tekniska och nyhetsbaserade filtren.")
