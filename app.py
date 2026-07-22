import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np
import plotly.graph_objects as go

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Högvolatil Scanner Pro", layout="wide")

st.title("⚡ Intraday Scanner Pro med VWAP & Visuella Grafer")

# --- INFORMATIONSFLIK ---
with st.expander("ℹ️ SÅ HÄR ANVÄNDS DEN FÖRBÄTTRADE STRATEGIN"):
    st.markdown("""
    ### 🎯 Träffsäkra Intraday-signaler & Beslutsstöd:
    * **MOMENTUM KÖP 🚀:** Priset ligger ovanför **VWAP**, EMA 20 > EMA 50, volymen (RVOL) har exploderat och RSI är i en hälsosam zon (50–70).
    * **DIPP KÖP 📈:** Översåld aktie ($RSI \le 42$) i en stabil upptrend där priset håller sig över den långsamma trenden.
    * **ÖVERKÖPT / SÄLJ 🔥:** Varning för rekyl nedåt ($RSI \ge 75$).
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
                    df_ticker = stort_df[ticker].dropna(subset=['Close']).copy()
                else:
                    df_ticker = stort_df.dropna(subset=['Close']).copy()
                
                if len(df_ticker) < 50: 
                    continue
                
                # --- BERÄKNING AV TEKNISKA INDIKATORER ---
                df_ticker['RSI'] = ta.momentum.rsi(df_ticker['Close'], window=14)
                df_ticker['Vol_Snitt'] = df_ticker['Volume'].rolling(window=20).mean()
                df_ticker['EMA_Snabb'] = ta.trend.ema_indicator(df_ticker['Close'], window=20)
                df_ticker['EMA_Langsam'] = ta.trend.ema_indicator(df_ticker['Close'], window=50)
                df_ticker['ATR'] = ta.volatility.average_true_range(df_ticker['High'], df_ticker['Low'], df_ticker['Close'], window=14)
                
                # Korrekt Intraday VWAP (Återställs varje dag)
                tp = (df_ticker['High'] + df_ticker['Low'] + df_ticker['Close']) / 3
                df_ticker['VWAP'] = (tp * df_ticker['Volume']).groupby(df_ticker.index.date).cumsum() / \
                                    df_ticker['Volume'].groupby(df_ticker.index.date).cumsum()

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

                if pd.isna(rsi) or pd.isna(ema_snabb) or pd.isna(vwap_varde):
                    continue

                if pris > max_pris or pris <= 0: 
                    continue
                
                # Omsättningsfilter
                omsattning = pris * vol
                if omsattning < min_omsattning: 
                    continue
                    
                rvol = vol / v_snitt if v_snitt > 0 else 1.0
                utveckling_bar = ((pris - öppning) / öppning) * 100
                fullt_namn = NAMN_MAPPNING[ticker]

                # Risk/Reward Beräkning
                stop_loss = round(pris - (1.5 * atr_varde), 2)
                target = round(pris + (2.5 * atr_varde), 2)

                # Spara DataFrame för grafer
                sparad_df_dict[ticker] = df_ticker

                # --- STRATEGILOGIK ---
                rekommendation = "Avvakta 🟡"
                
                # Regel 1: VWAP + EMA + RVOL Momentum
                if pris > vwap_varde and pris > ema_snabb and ema_snabb > ema_langsam and rvol >= min_rvol and (50 <= rsi <= 70):
                    rekommendation = "MOMENTUM KÖP 🚀"
                    temp_ultra_köp.append({
                        "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2),
                        "RSI": round(rsi, 1), "RVOL": f"{rvol:.1f}x", "Stop Loss": stop_loss, "Target": target
                    })
                
                # Regel 2: Dipp-köp över EMA50
                elif ema_snabb > ema_langsam and rsi <= 42 and pris > ema_langsam:
                    rekommendation = "DIPP KÖP 📈"
                    temp_rek_köp.append({
                        "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2),
                        "RSI": round(rsi, 1), "Stop Loss": stop_loss, "Target": target
                    })
                
                elif rsi >= 75:
                    rekommendation = "ÖVERKÖPT / SÄLJ 🔥"

                temp_alla.append({
                    "Ticker": ticker, "Aktie": fullt_namn, "Pris": round(pris, 2), "Rekommendation": rekommendation,
                    "Senaste 5m %": f"{utveckling_bar:+.2f}%", "RSI": round(rsi, 1), "RVOL": f"{rvol:.2f}x",
                    "VWAP": round(vwap_varde, 2), "ATR": round(atr_varde, 2)
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
        df_visa['prio'] = df_visa['Rekommendation'].map(sortering)
        df_visa = df_visa.sort_values(by="prio").drop(columns=['prio'])
        st.dataframe(df_visa, use_container_width=True, height=350)

    # --- INTERAKTIV CANDLESTICK-GRAF ---
    st.write("---")
    st.subheader("📈 Visuell Grafanalys")
    
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

            # Candlesticks
            fig.add_trace(go.Candlestick(
                x=chart_df.index,
                open=chart_df['Open'],
                high=chart_df['High'],
                low=chart_df['Low'],
                close=chart_df['Close'],
                name="Pris (5m)"
            ))

            # EMA 20
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['EMA_Snabb'],
                line=dict(color='orange', width=1.5), name="EMA 20"
            ))

            # EMA 50
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['EMA_Langsam'],
                line=dict(color='blue', width=1.5), name="EMA 50"
            ))

            # VWAP
            fig.add_trace(go.Scatter(
                x=chart_df.index, y=chart_df['VWAP'],
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
