import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go
from textblob import TextBlob

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Högvolatil Scanner Pro", layout="wide")

st.title("⚡ Intraday Scanner Pro med VWAP, Nyhets-AI & Visuella Grafer")

# --- CACHAD FUNKTION FÖR NYHETER ---
@st.cache_data(ttl=900)
def hamta_nyheter_cachad(ticker_symbol):
    try:
        return yf.Ticker(ticker_symbol).news
    except Exception:
        return []

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ SÅ HÄR ANVÄNDS DEN FÖRBÄTTRADE STRATEGIN"):
    st.markdown("""
    ### 🎯 Träffsäkra Intraday-signaler & Beslutsstöd:
    * **MOMENTUM KÖP 🚀:** Priset ligger ovanför **VWAP**, EMA 20 > EMA 50, volymen (RVOL) har exploderat och RSI är i en hälsosam zon (50–70).
    * **DIPP KÖP 📈:** Översåld aktie (RSI ≤ 42) i en stabil upptrend där priset håller sig över den långsamma trenden.
    * **ÖVERKÖPT / SÄLJ 🔥:** Varning för rekyl nedåt (RSI ≥ 75).
    * **Nyhets-AI 📰:** Läser de senaste engelska nyhetsrubrikerna och gör en sentimentanalys (Positivt 🟢 / Negativt 🔴).
    * **Riskhantering:** Varje signal beräknar automatiskt en föreslagen **Stop Loss** (1.5x ATR) och **Target** (2.5x ATR).
    """)

# --- SIDEBAR: INTERAKTIVA FILTER ---
st.sidebar.header("⚙️ Inställningar & Filter")
min_omsattning = st.sidebar.number_input("Minsta 5m Omsättning (SEK/USD)", value=10000, step=5000)
min_rvol = st.sidebar.slider("Minsta Volymutbrott (RVOL)", 1.0, 3.0, 1.5, 0.1)
max_pris = st.sidebar.number_input("Max Aktiepris", value=2000, step=100)

# MAPPNING AV AKTIER
NAMN_MAPPNING = {
    # --- Svenska aktier ---
    "SINCH.ST": "Sinch (Tech)", "EMBRAC-B.ST": "Embracer (Gaming)", "ASMDEE-B.ST": "Asmodee (Gaming)",
    "SIVERS.ST": "Sivers Semiconductors", "FORTV.ST": "Fortnox (Mjukvara)", "EVO.ST": "Evolution (iGaming)", 
    "BETCO.ST": "Betsson (Gaming)", "G5EN.ST": "G5 Entertainment", "MTG-B.ST": "MTG (Gaming)", 
    "BOOZT.ST": "Boozt (E-handel)", "BHG.ST": "BHG Group (E-handel)", "HPOL-B.ST": "Hexatronic (Fiber)", 
    "MYCR.ST": "Mycronic (Tech)", "SBB-B.ST": "SBB B (Fastigheter)", "CORE-B.ST": "Corem B (Fastigheter)", 
    "BOL.ST": "Boliden (Gruvor)", "SSAB-B.ST": "SSAB B (Stål)", "VOLV-B.ST": "Volvo B", "SAAB-B.ST": "Saab B (Försvar)", 
    "NIBE-B.ST": "Nibe (Grön Energi)", "INVE-B.ST": "Investor B", "AVAN.ST": "Avanza", "HM-B.ST": "H&M B",

    # --- USA: Tech & Growth ---
    "AAPL": "Apple (Tech)", "MSFT": "Microsoft (Tech)", "NVDA": "NVIDIA (AI)",
    "AMD": "AMD (Semiconductors)", "TSLA": "Tesla (Elbilar)", "AMZN": "Amazon (E-handel)",
    "META": "Meta (Tech)", "GOOGL": "Alphabet (Tech)", "PLTR": "Palantir (AI)", 
    "COIN": "Coinbase (Krypto)", "MARA": "Marathon Digital (Krypto)", "MSTR": "MicroStrategy (Bitcoin)"
}

AKTIER = list(NAMN_MAPPNING.keys())

# Initiera session state
if "skannings_resultat" not in st.session_state:
    st.session_state.skannings_resultat = None
if "sparad_data" not in st.session_state:
    st.session_state.sparad_data = {}

# --- SKANNINGSKNAPP ---
if st.button("STARTA SCANNER (5M INTERVALL) ⚡", use_container_width=True):
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    st.session_state.skannings_resultat = None
    st.session_state.sparad_data = {}

    temp_ultra_köp = []
    temp_rek_köp = []
    temp_alla = []
    sparad_df_dict = {}
    
    alla_tickers_str = " ".join(AKTIER)
    try:
        stort_df = yf.download(alla_tickers_str, period="7d", interval="5m", progress=False, group_by="ticker")
    except Exception as e:
        st.error(f"Kunde inte hämta data från Yahoo Finance: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        om_multiindex = isinstance(stort_df.columns, pd.MultiIndex)

        for i, ticker in enumerate(AKTIER):
            status_text.write(f"Skannar ({i+1}/{len(AKTIER)}): {NAMN_MAPPNING[ticker]}...")
            progress_bar.progress((i + 1) / len(AKTIER))
            
            try:
                if om_multiindex:
                    if ticker not in stort_df.columns.get_level_values(0):
                        continue
                    df_ticker = stort_df[ticker].copy()
                    if isinstance(df_ticker.columns, pd.MultiIndex):
                        df_ticker.columns = df_ticker.columns.get_level_values(0)
                else:
                    df_ticker = stort_df.copy()

                df_ticker = df_ticker.dropna(subset=['Close'])
                
                if len(df_ticker) < 50: 
                    continue
                
                close_ser = df_ticker['Close'].squeeze()
                high_ser = df_ticker['High'].squeeze()
                low_ser = df_ticker['Low'].squeeze()
                open_ser = df_ticker['Open'].squeeze()
                vol_ser = df_ticker['Volume'].squeeze()

                # --- TEKNISKA INDIKATORER ---
                df_ticker['RSI'] = ta.momentum.rsi(close_ser, window=14)
                df_ticker['Vol_Snitt'] = vol_ser.rolling(window=20).mean()
                df_ticker['EMA_Snabb'] = ta.trend.ema_indicator(close_ser, window=20)
                df_ticker['EMA_Langsam'] = ta.trend.ema_indicator(close_ser, window=50)
                df_ticker['ATR'] = ta.volatility.average_true_range(high_ser, low_ser, close_ser, window=14)
                
                # SÄKER VWAP-BERÄKNING PER HANDELSDAG
                tz_namn = "Europe/Stockholm" if ticker.endswith(".ST") else "America/New_York"
                if getattr(df_ticker.index, 'tz', None) is not None:
                    lokalt_index = df_ticker.index.tz_convert(tz_namn)
                else:
                    lokalt_index = df_ticker.index.tz_localize("UTC").tz_convert(tz_namn)

                tp = (high_ser + low_ser + close_ser) / 3
                df_ticker['VWAP'] = (tp * vol_ser).groupby(lokalt_index.date).cumsum() / \
                                    vol_ser.groupby(lokalt_index.date).cumsum()

                senaste = df_ticker.iloc[-1]
                
                pris = float(senaste['Close'])
                vol = float(senaste['Volume'])
                öppning = float(senaste['Open'])
                rsi = float(senaste['RSI'])
                v_snitt = float(senaste['Vol_Snitt'])
                ema_snabb = float(senaste['EMA_Snabb'])
                ema_langsam = float(senaste['EMA_Langsam'])
                atr_varde = float(senaste['ATR'])
                vwap_varde = float(senaste['VWAP'])

                if pd.isna(rsi) or pd.isna(ema_snabb) or pd.isna(vwap_varde) or np.isinf(vwap_varde):
                    continue

                if pris > max_pris or pris <= 0: 
                    continue
                
                omsattning = pris * vol
                if omsattning < min_omsattning: 
                    continue
                    
                rvol = (vol / v_snitt) if (pd.notna(v_snitt) and v_snitt > 0) else 1.0
                utveckling_bar = ((pris - öppning) / öppning * 100) if öppning > 0 else 0.0
                fullt_namn = NAMN_MAPPNING[ticker]

                stop_loss = round(pris - (1.5 * atr_varde), 2)
                target = round(pris + (2.5 * atr_varde), 2)

                sparad_df_dict[ticker] = df_ticker

                # --- STRATEGILOGIK ---
                rekommendation = "Avvakta 🟡"
                
                if pris > vwap_varde and pris > ema_snabb and ema_snabb > ema_langsam and rvol >= min_rvol and (50 <= rsi <= 70):
                    rekommendation = "MOMENTUM KÖP 🚀"
                    temp_ultra_köp.append({
                        "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2),
                        "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", 
                        "Stop Loss": stop_loss, "Target": target
                    })
                
                elif ema_snabb > ema_langsam and rsi <= 42 and pris > ema_langsam:
                    rekommendation = "DIPP KÖP 📈"
                    temp_rek_köp.append({
                        "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2),
                        "RSI": round(rsi, 1), 
                        "Stop Loss": stop_loss, "Target": target
                    })
                
                elif rsi >= 75:
                    rekommendation = "ÖVERKÖPT / SÄLJ 🔥"

                temp_alla.append({
                    "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2), "Rekommendation": rekommendation,
                    "Senaste 5m %": f"{utveckling_bar:+.2f}%", 
                    "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x", "VWAP": round(vwap_varde, 2), "ATR": round(atr_varde, 2)
                })
            except Exception:
                continue

        st.session_state.skannings_resultat = {
            "ultra": temp_ultra_köp,
            "dipp": temp_rek_köp,
            "alla": temp_alla
        }
        st.session_state.sparad_data = sparad_df_dict
        
    progress_bar.empty()
    status_text.empty()

# --- PRESENTATION OCH GRAFER ---
if st.session_state.skannings_resultat:
    res = st.session_state.skannings_resultat
    
    st.subheader("🚀 MOMENTUM KÖP (Utbrott bekräftade av VWAP & Volym)")
    if res["ultra"]: 
        st.dataframe(pd.DataFrame(res["ultra"]), use_container_width=True)
    else: 
        st.info("Inga starka momentum-utbrott hittades just nu.")
        
    st.write("---")
    st.subheader("📈 INTRADAY DIPP-KÖP (Översålda i upptrend)")
    if res["dipp"]: 
        st.dataframe(pd.DataFrame(res["dipp"]), use_container_width=True)
    else: 
        st.info("Inga dipp-köpsignaler hittades för tillfället.")
        
    st.write("---")
    st.subheader("📊 Översikt Alla Aktier")
    if res["alla"]:
        df_visa = pd.DataFrame(res["alla"])
        sortering = {"MOMENTUM KÖP 🚀": 0, "DIPP KÖP 📈": 1, "Avvakta 🟡": 2, "ÖVERKÖPT / SÄLJ 🔥": 3}
        df_visa['prio'] = df_visa['Rekommendation'].map(sortering).fillna(99)
        df_visa = df_visa.sort_values(by="prio").drop(columns=['prio'])
        st.dataframe(df_visa, use_container_width=True, height=350)

    # --- INTERAKTIV CANDLESTICK-GRAF OCH NYHETER ---
    st.write("---")
    st.subheader("📈 Visuell Grafanalys & Nyhetsgranskning")
    
    valda_tickers = list(st.session_state.sparad_data.keys())
    if valda_tickers:
        val_ticker = st.selectbox(
            "Välj en aktie att granska i detalj:",
            options=valda_tickers,
            format_func=lambda x: f"{x} - {NAMN_MAPPNING.get(x, x)}"
        )
        
        if val_ticker in st.session_state.sparad_data:
            chart_df = st.session_state.sparad_data[val_ticker].tail(80)

            fig = go.Figure()

            fig.add_trace(go.Candlestick(
                x=chart_df.index,
                open=chart_df['Open'].squeeze(),
                high=chart_df['High'].squeeze(),
                low=chart_df['Low'].squeeze(),
                close=chart_df['Close'].squeeze(),
                name="Pris (5m)"
            ))

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['EMA_Snabb'].squeeze(),
                line=dict(color='orange', width=1.5), name="EMA 20"
            ))

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['EMA_Langsam'].squeeze(),
                line=dict(color='blue', width=1.5), name="EMA 50"
            ))

            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['VWAP'].squeeze(),
                line=dict(color='purple', width=2, dash='dash'), name="VWAP"
            ))

            fig.update_layout(
                title=f"Intraday 5m-diagram för {NAMN_MAPPNING.get(val_ticker, val_ticker)} ({val_ticker})",
                yaxis_title="Pris",
                xaxis_rangeslider_visible=False,
                template="plotly_dark",
                height=500
            )

            st.plotly_chart(fig, use_container_width=True)

            # --- NYHETSFÖRDJUPNING ---
            st.markdown(f"#### 📰 Senaste rubrikerna & AI-sentiment för {NAMN_MAPPNING.get(val_ticker, val_ticker)}")
            try:
                nyheter_val = hamta_nyheter_cachad(val_ticker)
                if nyheter_val:
                    for artikel in nyheter_val[:4]:
                        innehall = artikel.get('content', artikel) if isinstance(artikel, dict) else {}
                        if not isinstance(innehall, dict):
                            innehall = {}

                        titel = innehall.get('title') or 'Ingen titel'
                        
                        canonical = innehall.get('canonicalUrl') if isinstance(innehall.get('canonicalUrl'), dict) else {}
                        lank = canonical.get('url') or innehall.get('link') or '#'
                        
                        provider = innehall.get('provider') if isinstance(innehall.get('provider'), dict) else {}
                        utgivare = provider.get('displayName') or innehall.get('publisher') or 'Okänd källa'
                        
                        analys = TextBlob(str(titel))
                        score = analys.sentiment.polarity
                        emoji = "🟢" if score > 0.05 else ("🔴" if score < -0.05 else "⚪")
                        
                        st.markdown(f"{emoji} **[{titel}]({lank})** — *{utgivare}*")
                else:
                    st.info("Inga färska nyheter hittades för den valda aktien.")
            except Exception as e:
                st.warning(f"Kunde inte ladda nyhetslänkar: {e}")
