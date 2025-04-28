import streamlit as st
from models import SessionLocal, ClientPortfolio, Holding
import pandas as pd

st.set_page_config(page_title="Edit Portfolio", layout="wide")
st.title("🛠️ Edit Portfolio Holdings")

session = SessionLocal()

# --- SELECT PORTFOLIO ---
portfolios = session.query(ClientPortfolio).all()
portfolio_options = {p.name: p.id for p in portfolios}

if not portfolios:
    st.warning("No portfolios available.")
    st.stop()

selected_name = st.selectbox("Choose a portfolio to edit:", list(portfolio_options.keys()))
selected_id = portfolio_options[selected_name]

selected_portfolio = session.query(ClientPortfolio).get(selected_id)
holdings = session.query(Holding).filter_by(portfolio_id=selected_id).all()

# --- EXISTING HOLDINGS ---
if holdings:
    st.subheader(f"✏️ Edit Holdings for '{selected_portfolio.name}'")

    holdings_df = pd.DataFrame([{
        "id": h.id,
        "Security Name": h.name,
        "Ticker": h.ticker,
        "Currency": h.currency,
        "Quantity": h.quantity,
        "Total Cost": h.total_cost,
        "Type": h.datatype 
    } for h in holdings])

    holdings_df = holdings_df.sort_values(["Type", "Currency", "Security Name"])

    edited_df = st.data_editor(
        holdings_df.drop(columns="id"),
        use_container_width=True,
        num_rows="dynamic",
        key="edited_holdings"
    )

    if st.button("💾 Save Changes"):
        for i, row in edited_df.iterrows():
            holding = holdings[i]
            holding.name = row["Security Name"]
            holding.ticker = row["Ticker"]
            holding.currency = row["Currency"]
            holding.quantity = row["Quantity"]
            holding.total_cost = row["Total Cost"]
            holding.datatype = row.get("Type", "0")
        session.commit()
        st.success("Holdings updated successfully!")

else:
    st.info("This portfolio currently has no holdings.")
