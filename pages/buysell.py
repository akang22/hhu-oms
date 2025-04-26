import streamlit as st
from models import SessionLocal, ClientPortfolio, Transaction, TransactionType, Holding
from datetime import datetime

st.set_page_config(page_title="Buy/Sell", layout="centered")
st.title("💸 Buy / Sell Transaction")

session = SessionLocal()
portfolios = session.query(ClientPortfolio).all()

if not portfolios:
    st.warning("No portfolios available.")
    st.stop()

portfolio_options = {p.name: p.id for p in portfolios}
selected_name = st.selectbox("Select Portfolio", list(portfolio_options.keys()))
selected_id = portfolio_options[selected_name]

st.markdown("---")

with st.form("transaction_form"):
    ticker = st.text_input("Ticker (e.g., AAPL)").upper()
    quantity = st.number_input("Quantity", min_value=0.0, step=1.0)
    price = st.number_input("Price per Share",  min_value=0.0)
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])
    date = st.date_input("Transaction Date", value=datetime.today())
    transaction_type = st.radio("Transaction Type", ["BUY", "SELL"])

    submitted = st.form_submit_button("Submit Transaction")

    if submitted:
        total_value = quantity * price

        # Save transaction
        txn = Transaction(
            portfolio_id=selected_id,
            ticker=ticker,
            quantity=quantity,
            price=price,
            date=datetime.combine(date, datetime.min.time()),
            transaction_type=TransactionType[transaction_type],
            currency=currency
        )
        session.add(txn)

        # Update or create the holding
        holding = session.query(Holding).filter_by(
            portfolio_id=selected_id,
            ticker=ticker,
            currency=currency
        ).first()

        if transaction_type == "BUY":
            if holding:
                holding.quantity += quantity
                holding.total_cost += total_value
            else:
                holding = Holding(
                    name=ticker,
                    ticker=ticker,
                    currency=currency,
                    quantity=quantity,
                    total_cost=total_value,
                    portfolio_id=selected_id,
                    datatype="equity"
                )
                session.add(holding)

        elif transaction_type == "SELL":
            if not holding:
                st.error("❌ You can't sell a security that isn't in the portfolio.")
                session.rollback()
                st.stop()
            if holding.quantity < quantity:
                st.error(f"❌ You can't sell more ({quantity}) than you hold ({holding.quantity}).")
                session.rollback()
                st.stop()
            proportion = quantity / holding.quantity if holding.quantity != 0 else 0
            cost_reduction = holding.total_cost * proportion
            holding.quantity -= quantity
            holding.total_cost -= cost_reduction

            if holding.quantity == 0:
                session.delete(holding)  # optionally delete empty holding

        session.commit()
        st.success(f"{transaction_type} transaction for {ticker} recorded and holdings updated.")

