import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Aktierekommendationer", layout="centered")
st.title("⚡ Köprekommendationer (Intraday)")

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
st.sidebar.header("Filter")
min_omsattning_5m = st.sidebar.number_input("Min omsättning 5m", value=10000, step=5000)
min_rvol = st.sidebar.slider("Min RVOL", 1.0, 3.0, 1.5, 0.1)
max_pris = st.sidebar.number_input("Max pris", value=2000, step=100)

# --- SKANNING ---
if st.button("Hämta Rekommendationer 🚀", use_container_width=True):
    temp_momentum = []
    temp_dipp = []

    alla_tickers_str = " ".join(AKTIER)
    try:
        stort_df = yf.download(alla_tickers_str, period="5d", interval="5m", progress=False, group_by="ticker")
    except Exception as e:
        st.error(f"Fel vid hämtning: {e}")
        stort_df = pd.DataFrame()

    if not stort_df.empty:
        for ticker in AKTIER:
            try:
                valuta = "SEK" if ticker.endswith(".ST") else "USD"
                df_ticker = stort_df[ticker].dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume']) if isinstance(stort_df.columns, pd.MultiIndex) else stort_df.dropna()

                if len(df_ticker) < 50:
                    continue

                close_ser = df_ticker['Close'].squeeze()
                high_ser = df_ticker['High'].squeeze()
                low_ser = df_ticker['Low'].squeeze()
                open_ser = df_ticker['Open'].squeeze()
                vol_ser = df_ticker['Volume'].squeeze()

                # Indikatorer
                rsi = float(ta.momentum.rsi(close_ser, window=14).iloc[-1])
                v_snitt = float(vol_ser.rolling(window=20).mean().iloc[-1])
                ema_snabb = float(ta.trend.ema_indicator(close_ser, window=20).iloc[-1])
                ema_langsam = float(ta.trend.ema_indicator(close_ser, window=50).iloc[-1])
                atr_varde = float(ta.volatility.average_true_range(high_ser, low_ser, close_ser, window=14).iloc[-1])

                # VWAP
                tz_namn = "Europe/Stockholm" if ticker.endswith(".ST") else "America/New_York"
                lokalt_index = df_ticker.index.tz_localize("UTC").tz_convert(tz_namn) if df_ticker.index.tz is None else df_ticker.index.tz_convert(tz_namn)
                tp = (high_ser + low_ser + close_ser) / 3
                vwap_varde = float(((tp * vol_ser).groupby(lokalt_index.date).cumsum() / vol_ser.groupby(lokalt_index.date).cumsum()).iloc[-1])

                senaste = df_ticker.iloc[-1]
                pris = float(senaste['Close'])
                vol = float(senaste['Volume'])

                if pd.isna(rsi) or pd.isna(ema_snabb) or pd.isna(vwap_varde) or np.isinf(vwap_varde) or pris > max_pris or pris <= 0:
                    continue

                # Omsättningsfilter
                if (close_ser * vol_ser).tail(5).mean() < min_omsattning_5m:
                    continue

                rvol = (vol / v_snitt) if (pd.notna(v_snitt) and v_snitt > 0) else 1.0
                stop_loss = round(pris - (1.5 * atr_varde), 2)
                target = round(pris + (2.5 * atr_varde), 2)
                fullt_namn = NAMN_MAPPNING[ticker]

                # Matchning utifrån preferenser
                data_punkt = {
                    "Aktie": fullt_namn,
                    "Ticker": ticker,
                    "Pris": f"{pris:.2f} {valuta}",
                    "RSI": round(rsi, 1),
                    "Stop Loss": f"{stop_loss:.2f} {valuta}",
                    "Target": f"{target:.2f} {valuta}"
                }

                if pris > vwap_varde and pris > ema_snabb and ema_snabb > ema_langsam and rvol >= min_rvol and (50 <= rsi <= 70):
                    data_punkt["RVOL"] = f"{rvol:.1f}x"
                    temp_momentum.append(data_punkt)

                elif ema_snabb > ema_langsam and rsi <= 42 and pris > ema_langsam:
                    temp_dipp.append(data_punkt)

            except Exception:
                continue

    # --- VISNING AV RESULTAT ---
    st.subheader("🚀 Momentum Köp")
    if temp_momentum:
        st.dataframe(pd.DataFrame(temp_momentum), use_container_width=True)
    else:
        st.info("Inga momentum-kandidater just nu.")

    st.subheader("📈 Dipp Köp")
    if temp_dipp:
        st.dataframe(pd.DataFrame(temp_dipp), use_container_width=True)
    else:
        st.info("Inga dipp-kandidater just nu.")
