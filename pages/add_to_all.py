import streamlit as st
from models import SessionLocal, ClientPortfolio, Holding

st.title("📤 Add Holding to All Portfolios")

session = SessionLocal()
portfolios = session.query(ClientPortfolio).all()

if not portfolios:
    st.warning("No portfolios found. Please add at least one portfolio first.")
else:
    with st.form("add_global_holding"):
        st.subheader("Holding Info")
        name = st.text_input("Security Name")
        currency = st.selectbox("Currency", ["USD", "EUR", "GBP", "JPY"])
        ticker = st.text_input("Security Ticker (e.g. AAPL)")
        total_quantity = st.number_input("Total Quantity", min_value=0.0, step=1.0)
        total_cost = st.number_input("Total Cost (in original currency)", min_value=0.0, step=1.0)

        st.subheader("Partition by Portfolio (%)")
        partitions = {}
        total_partition = 0

        for portfolio in portfolios:
            pct = st.number_input(
                f"{portfolio.name} (%)",
                min_value=0.0,
                max_value=100.0,
                step=1.0,
                key=portfolio.id
            )
            partitions[portfolio.id] = pct
            total_partition += pct

        submitted = st.form_submit_button("Distribute Holding")

        if submitted:
            if not all([name, ticker]) or total_quantity <= 0 or total_cost <= 0:
                st.error("Please fill in all required holding info.")
            elif abs(total_partition - 100.0) > 0.01:
                st.error("Total partition must sum to 100%.")
            else:
                for portfolio in portfolios:
                    pct = partitions[portfolio.id] / 100
                    quantity = total_quantity * pct
                    cost = total_cost * pct

                    if quantity > 0:
                        holding = Holding(
                            name=name,
                            currency=currency,
                            ticker=ticker.upper(),
                            quantity=quantity,
                            total_cost=cost,
                            portfolio_id=portfolio.id
                        )
                        session.add(holding)

                session.commit()
                st.success(f"Holding '{name}' distributed across all portfolios.")

