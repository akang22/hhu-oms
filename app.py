import streamlit as st
from models import SessionLocal, ClientPortfolio, Holding
from currency_converter import CurrencyConverter
import yfinance as yf
import pandas as pd
c = CurrencyConverter()

st.set_page_config(page_title="Portfolio Overview", layout="wide")
st.title("📊 Portfolio Overview")

session = SessionLocal()
portfolios = session.query(ClientPortfolio).all()

if not portfolios:
    st.warning("No portfolios found.")
    st.stop()

# --- SUMMARY TABLE ---
summary_data = []

for portfolio in portfolios:
    holdings = session.query(Holding).filter_by(portfolio_id=portfolio.id).all()

    total_cost = sum(h.total_cost for h in holdings)
    total_market_value = 0

    for h in holdings:
        market_value = 0
        if h.datatype == 1:
            market_value = h.total_cost
        else:
            try:
                data = yf.Ticker(h.ticker.upper())
                price = data.history(period="1d")["Close"].iloc[-1]
                if h.currency == "GBP":
                    price = price / 100
                market_value = price * h.quantity
            except Exception as e:
                st.error(e)
                st.warning(f"Couldn't fetch price for {h.ticker}")
        usd_market_value = c.convert(market_value, h.currency, "USD")

        total_market_value += market_value

    gain_loss = total_market_value - total_cost
    gain_loss_pct = (gain_loss / total_cost * 100) if total_cost else 0

    summary_data.append({
        "Portfolio": portfolio.name,
        "Holdings": len(holdings),
        "Total Cost": round(total_cost, 2),
        "Market Value": round(total_market_value, 2),
        "Unrealized Gain/Loss ($)": round(gain_loss, 2),
        "Unrealized Gain/Loss (%)": f"{gain_loss_pct:.2f}%",
    })

summary_df = pd.DataFrame(summary_data)

st.dataframe(summary_df, use_container_width=True)

