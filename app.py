import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import numpy as np

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="Aktierekommendationer Daytrading", layout="wide")
st.title("⚡ Daytrading Köprekommendationer (Intraday)")
st.caption("Optimerad skanner för momentum- och dipp-strategier med automatisk R/R-beräkning.")

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
min_omsattning_5m = st.sidebar.number_input("Min omsättning 5m (SEK/USD)", value=10000, step=5000)
min_rvol = st.sidebar.slider("Min RVOL (Relative Volume)", 1.0, 3.0, 1.5, 0.1)
max_pris = st.sidebar.number_input("Max aktiepris", value=2000, step=100)

st.sidebar.markdown("---")
st.sidebar.subheader("🛡️ Riskhantering (ATR)")
atr_sl_mult = st.sidebar.slider("Stop Loss (ATR-multipel)", 1.0, 3.0, 1.5, 0.1)
atr_tp_mult = st.sidebar.slider("Target (ATR-multipel)", 1.5, 5.0, 2.5, 0.1)

# --- SKANNING ---
if st.button("Hämta Rekommendationer 🚀", use_container_width=True):
    temp_momentum = []
    temp_dipp = []

    alla_tickers_str = " ".join(AKTIER)
    with st.spinner("Hämtar marknadsdata och beräknar indikatorer..."):
        try:
            stort_df = yf.download(alla_tickers_str, period="5d", interval="5m", progress=False, group_by="ticker")
        except Exception as e:
            st.error(f"Fel vid hämtning av data: {e}")
            stort_df = pd.DataFrame()

    if not stort_df.empty:
        for ticker in AKTIER:
            try:
                valuta = "SEK" if ticker.endswith(".ST") else "USD"
                
                # Säker uthämtning av ticker-dataframe
                if isinstance(stort_df.columns, pd.MultiIndex):
                    if ticker not in stort_df.columns.levels[0]:
                        continue
                    df_ticker = stort_df[ticker].copy()
                else:
                    df_ticker = stort_df.copy()

                df_ticker = df_ticker.dropna(subset=['Open', 'High', 'Low', 'Close', 'Volume'])

                if len(df_ticker) < 50:
                    continue

                close_ser = df_ticker['Close'].squeeze()
                high_ser = df_ticker['High'].squeeze()
                low_ser = df_ticker['Low'].squeeze()
                vol_ser = df_ticker['Volume'].squeeze()

                pris = float(close_ser.iloc[-1])
                vol = float(vol_ser.iloc[-1])

                if pris > max_pris or pris <= 0:
                    continue

                # Omsättningsfilter (senaste 5 periodernas snitt)
                if (close_ser * vol_ser).tail(5).mean() < min_omsattning_5m:
                    continue

                # Indikatorer (beräknas på HELA datamängden för exakthet)
                rsi = float(ta.momentum.rsi(close_ser, window=14).iloc[-1])
                v_snitt = float(vol_ser.rolling(window=10).mean().iloc[-1])
                ema_snabb = float(ta.trend.ema_indicator(close_ser, window=20).iloc[-1])
                ema_langsam = float(ta.trend.ema_indicator(close_ser, window=50).iloc[-1])
                atr_varde = float(ta.volatility.average_true_range(high_ser, low_ser, close_ser, window=14).iloc[-1])

                # VWAP (Beräknas korrekt per dag)
                tz_namn = "Europe/Stockholm" if ticker.endswith(".ST") else "America/New_York"
                if df_ticker.index.tz is None:
                    lokalt_index = df_ticker.index.tz_localize("UTC").tz_convert(tz_namn)
                else:
                    lokalt_index = df_ticker.index.tz_convert(tz_namn)

                tp = (high_ser + low_ser + close_ser) / 3
                vwap_varde = float(((tp * vol_ser).groupby(lokalt_index.date).cumsum() / vol_ser.groupby(lokalt_index.date).cumsum()).iloc[-1])

                if pd.isna(rsi) or pd.isna(ema_snabb) or pd.isna(vwap_varde) or np.isinf(vwap_varde):
                    continue

                rvol = (vol / v_snitt) if (pd.notna(v_snitt) and v_snitt > 0) else 1.0

                # Risk / Reward beräkning
                stop_loss = pris - (atr_sl_mult * atr_varde)
                target = pris + (atr_tp_mult * atr_varde)
                risk = pris - stop_loss
                reward = target - pris
                rr_kvot = round(reward / risk, 2) if risk > 0 else 0.0

                fullt_namn = NAMN_MAPPNING[ticker]

                data_punkt = {
                    "Aktie": fullt_namn,
                    "Ticker": ticker,
                    "Pris": f"{pris:.2f} {valuta}",
                    "RSI": round(rsi, 1),
                    "RVOL_num": round(rvol, 2),
                    "RVOL": f"{rvol:.1f}x",
                    "R/R Kvot": f"1:{rr_kvot:.2f}",
                    "Stop Loss": f"{stop_loss:.2f} {valuta}",
                    "Target": f"{target:.2f} {valuta}"
                }

                # 1. Momentum Köp
                if pris > vwap_varde and pris > ema_snabb and ema_snabb > ema_langsam and rvol >= min_rvol and (50 <= rsi <= 70):
                    temp_momentum.append(data_punkt)

                # 2. Dipp Köp
                vol_dämpad = vol < v_snitt
                if ema_snabb > ema_langsam and rsi <= 42 and pris > ema_langsam and vol_dämpad:
                    temp_dipp.append(data_punkt)

            except Exception as e:
                # Skriv ut ev. fel under felsökning om en ticker misslyckas
                continue

    # --- VISNING AV RESULTAT ---
    st.subheader("🚀 Momentum Köp")
    if temp_momentum:
        df_mom = pd.DataFrame(temp_momentum)
        df_mom = df_mom.sort_values(by="RVOL_num", ascending=False).drop(columns=["RVOL_num"])
        st.dataframe(df_mom, use_container_width=True)
    else:
        st.info("Inga momentum-kandidater just nu.")

    st.subheader("📈 Dipp Köp")
    if temp_dipp:
        df_dipp = pd.DataFrame(temp_dipp)
        df_dipp = df_dipp.sort_values(by="RSI", ascending=True).drop(columns=["RVOL_num"])
        st.dataframe(df_dipp, use_container_width=True)
    else:
        st.info("Inga dipp-kandidater just nu.")
