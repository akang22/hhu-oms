import streamlit as st
import pandas as pd
from models import SessionLocal, ClientPortfolio, Holding

st.title("Portfolio Creation/Import")

session = SessionLocal()

with st.form("add_portfolio_form", border=True):
    st.subheader("Add New Portfolio")
    new_portfolio_name = st.text_input("Portfolio Name")
    submitted = st.form_submit_button("Add Portfolio")

    if submitted and new_portfolio_name:
        existing = session.query(ClientPortfolio).filter_by(name=new_portfolio_name).first()
        if existing:
            st.warning("Portfolio with this name already exists.")
        else:
            session.add(ClientPortfolio(name=new_portfolio_name))
            session.commit()
            st.success(f"Added new portfolio: {new_portfolio_name}")
            st.rerun()

# Select a target portfolio
portfolios = session.query(ClientPortfolio).all()
if not portfolios:
    st.warning("No portfolios found. Please add one first.")
    st.stop()

portfolio_names = [p.name for p in portfolios]
selected_name = st.selectbox("Select Portfolio to Import Into", portfolio_names)
selected_portfolio = next(p for p in portfolios if p.name == selected_name)

# Upload Excel file
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:
    try:
        # Load sheet names
        xls = pd.ExcelFile(uploaded_file)
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox("Choose Sheet", sheet_names)

        # Read selected sheet
        base_df = pd.read_excel(xls, sheet_name=selected_sheet, skiprows=5, header=0)

        # Ensure required columns
        required_cols = [
            "Security Name", "Currency", "Security Ticker",
            "Total Quantity", "Total Cost"
        ]
        missing_cols = [col for col in required_cols if col not in base_df.columns]
        if missing_cols:
            st.error(f"Missing required columns: {', '.join(missing_cols)}")
            st.stop()

        df = base_df[required_cols]
        df.loc[:, ["Type"]] = "0"

        df.loc[df["Total Cost"].isna(), ["Type"]] = "1" 
        df.loc[df["Total Cost"].isna(), ["Total Cost"]] =  base_df[df["Total Cost"].isna()]["Market Value"]
        df = df[df["Security Name"].notna()]

        st.subheader("📋 Review and Edit Holdings Before Import")
        edited_df = st.data_editor(
            df,
            use_container_width=True,
            num_rows="dynamic",
            key="editable_holdings_table"
        )

        if st.button("✅ Submit to Portfolio"):
            inserted = 0
            for _, row in edited_df.iterrows():
                optionals = { }
                print(row)
                if isinstance(row["Security Ticker"], str):
                    optionals["ticker"] = row["Security Ticker"].upper()

                if row["Total Quantity"]:
                    optionals["quantity"] = row["Total Quantity"]

                holding = Holding(
                    name=row["Security Name"],
                    currency=row["Currency"],
                    datatype=1 if row["Type"] == "1" else 0,
                    total_cost=row["Total Cost"],
                    portfolio_id=selected_portfolio.id,
                    **optionals,
                )
                session.add(holding)
                inserted += 1

            session.commit()
            st.success(f"Successfully imported {inserted} holdings into '{selected_name}'.")

    except Exception as e:
        st.error(f"Something went wrong: {e}")

