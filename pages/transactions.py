import streamlit as st
from models import SessionLocal, ClientPortfolio, Transaction, TransactionType, Holding
import pandas as pd

st.set_page_config(page_title="View/Delete Transactions", layout="wide")
st.title("🧾 Transaction Viewer & Editor")

session = SessionLocal()
portfolios = session.query(ClientPortfolio).all()

if not portfolios:
    st.warning("No portfolios found.")
    st.stop()

portfolio_dict = {p.name: p.id for p in portfolios}
selected_name = st.selectbox("Select Portfolio", list(portfolio_dict.keys()))
selected_id = portfolio_dict[selected_name]

transactions = session.query(Transaction).filter_by(portfolio_id=selected_id).order_by(Transaction.date.desc()).all()

if not transactions:
    st.info("No transactions for this portfolio.")
    st.stop()

st.markdown("### 📋 Transactions")

txn_df = pd.DataFrame([{
    "ID": t.id,
    "Date": t.date.date(),
    "Ticker": t.ticker,
    "Quantity": t.quantity,
    "Price": t.price,
    "Type": t.transaction_type.value,
    "Currency": t.currency
} for t in transactions])

selected = st.dataframe(
    txn_df.drop(columns="ID"),
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="single-row"
).selection

if selected["rows"]:
    txn_row = txn_df.iloc[selected["rows"][0]]
    txn_id = txn_df.iloc[selected["rows"][0]]["ID"]
    txn = session.query(Transaction).get(txn_id)

    st.warning(f"⚠️ You are about to delete the {txn.transaction_type.value} transaction for {txn.ticker} on {txn.date.date()}.")

    if st.button("🗑️ Delete Transaction", type="primary"):
        # Find the related holding
        holding = session.query(Holding).filter_by(
            portfolio_id=txn.portfolio_id,
            ticker=txn.ticker,
            currency=txn.currency
        ).first()

        if not holding:
            st.error("Holding not found. Database may be inconsistent.")
            st.stop()

        # Reverse the transaction
        value = txn.quantity * txn.price

        if txn.transaction_type == TransactionType.BUY:
            if holding.quantity < txn.quantity:
                st.error("❌ Cannot reverse BUY: not enough quantity remaining.")
                st.stop()
            holding.quantity -= txn.quantity
            holding.total_cost -= value

        elif txn.transaction_type == TransactionType.SELL:
            holding.quantity += txn.quantity
            holding.total_cost += value  # restore the original value (approximate)

        if holding.quantity == 0:
            session.delete(holding)
        session.delete(txn)
        session.commit()
        st.success("✅ Transaction deleted and holding updated.")
        st.rerun()

