import streamlit as st
from models import SessionLocal, ClientPortfolio, Transaction, TransactionType, Holding
from datetime import datetime
import pandas as pd

st.set_page_config(page_title="Buy/Sell", layout="centered")
st.title("💸 Buy / Sell Transaction")

session = SessionLocal()
portfolios = session.query(ClientPortfolio).all()
if not portfolios:
    st.warning("No portfolios available.")
    st.stop()

portfolio_df = pd.DataFrame([{"id": p.id, "name": p.name} for p in portfolios])
portfolio_ids = {p.name: p.id for p in portfolios}

allocation_mode = st.radio("Apply transaction to:", ["One Portfolio", "Multiple Portfolios"])

if allocation_mode == "One Portfolio":
    selected_name = st.selectbox("Select Portfolio", list(portfolio_ids.keys()))
    allocations = {portfolio_ids[selected_name]: 1.0}  # 100% allocation
else:
    st.markdown("### 🧮 Set Proportions")
    default = 1 / len(portfolios)
    weights = {p.name: st.slider(p.name, 0.0, 1.0, default, 0.01) for p in portfolios}
    total_weight = sum(weights.values())
    if total_weight == 0:
        st.error("⚠️ Total weight must be greater than 0.")
        st.stop()
    allocations = {
        portfolio_ids[name]: weight / total_weight
        for name, weight in weights.items() if weight > 0
    }

st.markdown("---")

with st.form("transaction_form"):
    ticker = st.text_input("Ticker (e.g., AAPL)").upper()
    total_quantity = st.number_input("Total Quantity", min_value=0.0, step=1.0)
    price = st.number_input("Price per Share", min_value=0.0)
    currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])
    date = st.date_input("Transaction Date", value=datetime.today())
    transaction_type = st.radio("Transaction Type", ["BUY", "SELL"])
    submitted = st.form_submit_button("Submit Transaction")

    if submitted:
        for pid, proportion in allocations.items():
            qty = total_quantity * proportion
            total_value = qty * price

            txn = Transaction(
                portfolio_id=pid,
                ticker=ticker,
                quantity=qty,
                price=price,
                date=datetime.combine(date, datetime.min.time()),
                transaction_type=TransactionType[transaction_type],
                currency=currency
            )
            session.add(txn)

            holding = session.query(Holding).filter_by(
                portfolio_id=pid, ticker=ticker, currency=currency
            ).first()

            if transaction_type == "BUY":
                if holding:
                    holding.quantity += qty
                    holding.total_cost += total_value
                else:
                    holding = Holding(
                        name=ticker,
                        ticker=ticker,
                        currency=currency,
                        quantity=qty,
                        total_cost=total_value,
                        portfolio_id=pid,
                        datatype="equity"
                    )
                    session.add(holding)

            elif transaction_type == "SELL":
                if not holding:
                    st.error(f"❌ Portfolio {pid} has no {ticker} to sell.")
                    session.rollback()
                    continue
                if holding.quantity < qty:
                    st.error(f"❌ Portfolio {pid} can't sell more than it holds.")
                    session.rollback()
                    continue
                proportion_sold = qty / holding.quantity if holding.quantity != 0 else 0
                cost_reduction = holding.total_cost * proportion_sold
                holding.quantity -= qty
                holding.total_cost -= cost_reduction
                if holding.quantity == 0:
                    session.delete(holding)

        session.commit()
        st.success(f"{transaction_type} transaction(s) for {ticker} processed.")


