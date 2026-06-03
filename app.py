import streamlit as st
import yfinance as yf
import pandas as pd
import ta
import json

# Sätt layout och titel på appen
st.set_page_config(page_title="Global Cloud Trader", layout="wide", initial_sidebar_state="expanded")
st.title("🚀 Global Cloud Trader – Top 100 Utan ETF (Sorterad på Signal)")

# --- MOLNHANTERING: PORTFÖLJ UTAN LOKALA FILER ---
if "portfolio" not in st.session_state:
    st.session_state.portfolio = []

# --- TOP 100 VOLATILA TRADING-AKTIER (HELT UTAN ETF:er) ---
# Sorterade och rensade: 70 st USA-aktier och 30 st Svenska aktier
ALL_TICKERS = sorted([
    # --- 🇺🇸 USA: Tech, AI, Krypto-aktier, Elbilar & Aggressiv tillväxt (70 st) ---
    "AAPL", "ABNB", "AMD", "AMZN", "ARM", "ASML", "AVGO", "BABA", "BKNG", "CMG", 
    "COIN", "DIS", "GOOGL", "HOOD", "ISRG", "JPM", "LLY", "MARA", "MELI", "META", 
    "MSFT", "NFLX", "NKE", "NVDA", "NVO", "PLTR", "RIVN", "SHOP", "SMCI", "SPOT", 
    "TSLA", "UBER", "V", "XOM", "AFRM", "ALCC", "ASTS", "BILI", "BYND", "CELH", 
    "CLSK", "CRWD", "DDOG", "DKNG", "ENPH", "FSLR", "GME", "LCID", "LI", "MSTR", 
    "NET", "OKTA", "OPEN", "PATH", "PDD", "PINS", "PLUG", "QS", "ROKU", "SE", 
    "SNOW", "SOFI", "SOUN", "SQ", "TEAM", "TTD", "TWLO", "U", "UPST", "WBD",
    # --- 🇸🇪 SVERIGE: Mycket volatila tillväxtbolag & tradingfavoriter (30 st) ---
    "EVO.ST", "SINCH.ST", "SECB.ST", "VOLV-B.ST", "SAND.ST", "SKF-B.ST", 
    "ALIV-SDB.ST", "HM-B.ST", "SBB-B.ST", "GETI-B.ST", "KINV-B.ST", "BETCO.ST", 
    "BOI.ST", "CALTX.ST", "CAMX.ST", "CTEK.ST", "DOM.ST", "FING-B.ST", "ORX.ST", 
    "OX2.ST", "READ.ST", "SVIK.ST", "TH7G.ST", "VNV.ST", "YUBICO.ST", "FORTNO.ST", 
    "EMBRAC-B.ST", "MTRS.ST", "NIBE-B.ST", "AAK.ST"
])

# --- SIDEBAR: RISK, KAPITAL & VALUTA ---
st.sidebar.header("💰 Aggressiv Riskhantering")
total_capital_sek = st.sidebar.number_input("Ditt totala tradingkapital (SEK):", value=100000.0, step=5000.0)

@st.cache_data(ttl=3600)
def get_usd_sek_rate():
    try:
        usd_sek = yf.Ticker("SEK=X")
        return usd_sek.history(period="1d")['Close'].iloc[-1]
    except:
        return 10.50

usd_rate = get_usd_sek_rate()
st.sidebar.write(f"💵 Aktuell Dollarkurs: **{round(usd_rate, 2)} SEK**")

st.sidebar.subheader("Aktiv Strategi")
profit_target = st.sidebar.slider("Vinstmål / Take Profit (%)", 0.5, 15.0, 4.0)
stop_loss = st.sidebar.slider("Förlustgräns / Stop Loss (%)", -10.0, -0.5, -3.0)

tab1, tab2, tab3 = st.tabs(["🔎 Rankad Skanner", "💼 Mitt Innehav", "📊 Marginal & Totalbalans"])

# ==================== FLIK 1: RANKAD SKANNER ====================
with tab1:
    st.subheader("Börsens bästa lägen just nu (Rankat efter rekommendation)")
    st.write(f"Skannern analyserar {len(ALL_TICKERS)} rena aktier. Det tar ca 25-35 sekunder.")
    
    if st.button("🚀 Starta fullständig skanning & sortering"):
        with st.spinner("Hämtar data och beräknar köpsignaler..."):
            scan_results = []
            for ticker in ALL_TICKERS:
                try:
                    stock = yf.Ticker(ticker)
                    df = stock.history(period="3mo", interval="1d")
                    if len(df) < 20: continue
                    
                    long_name = stock.info.get('longName', ticker)
                    df['RSI_14'] = ta.momentum.rsi(df['Close'], window=14)
                    latest = df.iloc[-1]
                    rsi_val = latest['RSI_14']
                    
                    price_5_days_ago = df.iloc[-6]['Close']
                    current_price = latest['Close']
                    movement_5d = ((current_price - price_5_days_ago) / price_5_days_ago) * 100
                    
                    if ticker.endswith(".ST"):
                        currency = "SEK"
                        price_sek = current_price
                        price_local = current_price
                    else:
                        currency = "USD"
                        price_sek = current_price * usd_rate
                        price_local = current_price
                    
                    if rsi_val <= 25:
                        signal = "⭐ STARKTS KÖPLÄGE"
                        rank = 1
                        motivation = f"RSI är extremt lågt ({round(rsi_val, 1)}). Kraftigt översåld aktie."
                    elif 25 < rsi_val <= 35:
                        signal = "🟢 OK KÖP"
                        rank = 2
                        motivation = f"RSI i köpzonen ({round(rsi_val, 1)}). Bra läge för swingtrade."
                    elif rsi_val >= 75:
                        signal = "🚨 STARKT SÄLJ"
                        rank = 5
                        motivation = f"RSI är extremt högt ({round(rsi_val, 1)}). Överköpt."
                    elif 65 <= rsi_val < 75:
                        signal = "🟠 OK SÄLJ / AVVAKTA"
                        rank = 4
                        motivation = f"RSI närmar sig taket ({round(rsi_val, 1)})."
                    else:
                        signal = "Neutral"
                        rank = 3
                        motivation = f"RSI ligger på {round(rsi_val, 1)}."
                        
                    scan_results.append({
                        "Rank": rank, "Kortnamn": ticker, "Företagsnamn": long_name,
                        "Pris (Lokal valuta)": f"{round(price_local, 2)} {currency}",
                        "Pris (SEK)": round(price_sek, 2),
                        "Rörelse (5 dgr)": f"{'+' if movement_5d >= 0 else ''}{round(movement_5d, 2)}%",
                        "RSI (14)": round(rsi_val, 1) if not pd.isna(rsi_val) else "N/A",
                        "Signal": signal, "AI Motivation": motivation
                    })
                except:
                    continue
                    
            if scan_results:
                df_scan = pd.DataFrame(scan_results).sort_values(by="Rank").drop(columns=["Rank"])
                def color_signals(val):
                    if '⭐' in str(val): return 'background-color: #006622; color: white; font-weight: bold;'
                    if '🟢' in str(val): return 'background-color: #ccffcc; color: black;'
                    if '🚨' in str(val): return 'background-color: #cc0000; color: white; font-weight: bold;'
                    if '🟠' in str(val): return 'background-color: #ffe6cc; color: black;'
                    return ''
                st.dataframe(df_scan.style.map(color_signals, subset=['Signal']), use_container_width=True)

    st.write("---")
    st.subheader("📈 Granska historik innan köp")
    selected_graph_ticker = st.selectbox("Välj en aktie för 1-årsgraf:", ALL_TICKERS)
    if selected_graph_ticker:
        g_stock = yf.Ticker(selected_graph_ticker)
        st.line_chart(g_stock.history(period="1y")['Close'])

# ==================== FLIK 2: INNEHAV ====================
with tab2:
    st.subheader("Hantera dina aktiva positioner")
    
    with st.form("add_stock_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1: ticker_input = st.selectbox("Välj aktie:", ALL_TICKERS)
        with col2: quantity_input = st.number_input("Antal:", min_value=1, value=5)
        is_se = ticker_input.endswith(".ST")
        with col3: price_input = st.number_input(f"Inköpspris ({'SEK' if is_se else '$'}):", min_value=0.1, value=150.0)
        
        if st.form_submit_button("➕ Spara i portföljen"):
            st.session_state.portfolio.append({
                "ticker": ticker_input, "antal": quantity_input, "inkopspris": price_input, "valuta": "SEK" if is_se else "USD"
            })
            st.success("Position sparad i molnsessionen!")
            st.rerun()

    if st.session_state.portfolio:
        for idx, pos in enumerate(st.session_state.portfolio):
            try:
                stock = yf.Ticker(pos["ticker"])
                current_price = stock.history(period="1d")['Close'].iloc[-1]
                pnl_pct = ((current_price - pos["inkopspris"]) / pos["inkopspris"]) * 100
                
                c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
                c1.write(f"**{pos['ticker']}** ({pos['antal']} st)")
                c2.write(f"Köpt: {pos['inkopspris']} -> Nu: {round(current_price, 2)}")
                c3.write(f"P&L: {round(pnl_pct, 2)}%")
                if c4.button("❌", key=f"del_{idx}"):
                    st.session_state.portfolio.pop(idx)
                    st.rerun()
            except:
                continue

# ==================== FLIK 3: MARGINAL ====================
with tab3:
    st.subheader("Totalbalans (SEK)")
    st.write(f"Total kassa inställd på: {total_capital_sek} kr")