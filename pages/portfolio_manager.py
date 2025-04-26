import streamlit as st
import math
from models import SessionLocal, ClientPortfolio, Holding
from currency_converter import CurrencyConverter
import yfinance as yf
import pandas as pd
c = CurrencyConverter()
st.set_page_config(page_title="Portfolio Manager", layout="wide")
st.title("📁 Portfolio Manager")

session = SessionLocal()

# --- ADD NEW PORTFOLIO FORM ---
with st.form("add_portfolio_form", border=True):
    new_name = st.text_input("Add New Portfolio")
    submitted = st.form_submit_button("Create")
    if submitted and new_name:
        existing = session.query(ClientPortfolio).filter_by(name=new_name).first()
        if existing:
            st.warning("A portfolio with this name already exists.")
        else:
            session.add(ClientPortfolio(name=new_name))
            session.commit()
            st.success(f"Portfolio '{new_name}' added!")
            st.rerun()

# --- PORTFOLIO LIST ---
portfolios = session.query(ClientPortfolio).all()
if not portfolios:
    st.info("No portfolios found.")
    st.stop()

st.subheader("📋 All Portfolios")

df = pd.DataFrame([{"Name": p.name, "id": p.id} for p in portfolios])

# Display portfolio list
selection = st.dataframe(
    df.drop(columns="id"),
    column_config={"Name": st.column_config.TextColumn("Portfolio Name")},
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row",
).selection

# If a row is selected
if selection["rows"]:
    selected_id = df.iloc[selection["rows"][0]]["id"]
    selected_portfolio = next(p for p in portfolios if p.id == selected_id)

    st.markdown("---")
    st.subheader(f"📂 Portfolio: {selected_portfolio.name}")

    # DELETE BUTTON

    # Holdings expander
    with st.expander("View Holdings", expanded=True):
        holdings = session.query(Holding).filter_by(portfolio_id=selected_portfolio.id).all()

        if not holdings:
            st.info("No holdings in this portfolio.")
        else:
            rows = []
            total_market_value = 0
            
            for h in holdings:
                try:
                    ticker = h.ticker.upper()
                    yf_ticker = yf.Ticker(ticker)
                    data = yf_ticker.history(period="1d")
                    closing_price = data["Close"].iloc[-1] if not data.empty else None
                    if h.currency == "GBP":
                        closing_price = closing_price / 100
                except Exception as e:
                    closing_price = None
            
                avg_price = h.total_cost / h.quantity if h.quantity else 0
                market_value = closing_price * h.quantity if closing_price else h.total_cost
                unrealized = market_value - h.total_cost if closing_price else 0
            
                usd_market_value = c.convert(market_value, h.currency, "USD")
            
                rows.append({
                    "Security Name": h.name,
                    "Currency": h.currency,
                    "Type": h.datatype,
                    "Security Ticker": h.ticker,
                    "Total Quantity": h.quantity,
                    "Total Cost": h.total_cost,
                    "Average Price": round(avg_price, 2),
                    "Closing Price": round(closing_price, 2) if closing_price else math.nan,
                    "Market Value": round(market_value, 2),
                    "Unrealized Gain/(Loss)": round(unrealized, 2),
                    "USD Market Value": round(usd_market_value, 2),
                })
            
            df = pd.DataFrame(rows)
            
            # Add weighting
            df["Weighting"] = df["USD Market Value"] / df["USD Market Value"].sum() * 100
            df = df.sort_values(["Type", "Currency", "Security Name"])
            
            # Display
            st.dataframe(df.set_index("Security Name"))
                
    if st.button("🗑️ Delete This Portfolio", type="primary"):
        session.delete(selected_portfolio)
        session.commit()
        st.success(f"Portfolio '{selected_portfolio.name}' deleted.")
        st.rerun()
