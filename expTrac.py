import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="Expense Tracker Pro",
    page_icon="💰",
    layout="wide"
)

# ---------------- SESSION STATE ----------------
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(
        columns=["Date", "Category", "Amount", "Description"]
    )

# ---------------- SIDEBAR : ADD EXPENSE ----------------
with st.sidebar:
    st.title("➕ Add Expense")

    with st.form("add_form", clear_on_submit=True):
        exp_date = st.date_input("Date", value=date.today())
        category = st.selectbox(
            "Category",
            ["Food", "Transport", "Entertainment", "Utilities",
             "Shopping", "Health", "Education", "Other"]
        )
        amount = st.number_input("Amount (₹)", min_value=0.0, step=10.0)
        desc = st.text_input("Description")

        if st.form_submit_button("Add Expense"):
            new_row = pd.DataFrame({
                "Date": [pd.to_datetime(exp_date)],
                "Category": [category],
                "Amount": [amount],
                "Description": [desc]
            })
            st.session_state.expenses = pd.concat(
                [st.session_state.expenses, new_row],
                ignore_index=True
            )
            st.success("Expense Added")

    st.divider()

    st.subheader("📂 Data")
    uploaded = st.file_uploader("Upload CSV", type="csv")
    if uploaded:
        df = pd.read_csv(uploaded)
        df["Date"] = pd.to_datetime(df["Date"])
        st.session_state.expenses = df
        st.success("CSV Loaded")

    if not st.session_state.expenses.empty:
        if st.button("🗑 Clear All Data"):
            st.session_state.expenses = st.session_state.expenses.iloc[0:0]
            st.rerun()

# ---------------- MAIN DASHBOARD ----------------
st.title("💰 Personal Expense Dashboard")

if st.session_state.expenses.empty:
    st.info("Add expenses from sidebar to start")
    st.stop()

df = st.session_state.expenses.copy()
df["Date"] = pd.to_datetime(df["Date"])

# ---------------- FILTERS ----------------
st.subheader("🔍 Filters")

c1, c2, c3 = st.columns(3)

with c1:
    month = st.selectbox("Month", ["All"] + list(range(1, 13)))

with c2:
    year = st.selectbox(
        "Year",
        ["All"] + sorted(df["Date"].dt.year.unique().tolist())
    )

with c3:
    cat_filter = st.selectbox(
        "Category",
        ["All"] + sorted(df["Category"].unique())
    )

search = st.text_input("Search Description")

if month != "All":
    df = df[df["Date"].dt.month == month]

if year != "All":
    df = df[df["Date"].dt.year == year]

if cat_filter != "All":
    df = df[df["Category"] == cat_filter]

if search:
    df = df[df["Description"].str.contains(search, case=False, na=False)]

# ---------------- METRICS ----------------
total = df["Amount"].sum()
avg = df["Amount"].mean()
count = len(df)

budget = st.number_input("Monthly Budget (₹)", value=10000)

m1, m2, m3, m4 = st.columns(4)
m1.metric("Total Spending", f"₹ {total:,.2f}")
m2.metric("Average Expense", f"₹ {avg:,.2f}")
m3.metric("Transactions", count)
m4.metric("Remaining Budget", f"₹ {budget - total:,.2f}")

if total > budget:
    st.error("🚨 Budget Exceeded!")

st.divider()

# ---------------- CHARTS ----------------
st.subheader("📊 Analysis")

cat_sum = df.groupby("Category")["Amount"].sum().reset_index()

c1, c2 = st.columns(2)

with c1:
    fig1 = px.pie(
        cat_sum,
        names="Category",
        values="Amount",
        hole=0.4,
        title="Category Wise Spending"
    )
    st.plotly_chart(fig1, use_container_width=True)

with c2:
    fig2 = px.bar(
        cat_sum,
        x="Category",
        y="Amount",
        text="Amount",
        title="Category Comparison"
    )
    st.plotly_chart(fig2, use_container_width=True)

# ---------------- EDIT / DELETE (FIXED) ----------------
st.subheader("✏ Edit / Delete Expense")

if df.empty:
    st.info("No transactions available.")
else:
    df_reset = df.reset_index()

    selected = st.selectbox(
        "Select Transaction",
        df_reset.index.tolist(),
        format_func=lambda x: (
            f"{df_reset.loc[x,'Date'].date()} | "
            f"{df_reset.loc[x,'Category']} | "
            f"₹{df_reset.loc[x,'Amount']}"
        )
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        new_date = st.date_input(
            "Edit Date",
            value=df_reset.loc[selected, "Date"].date()
        )

    with col2:
        categories = ["Food", "Transport", "Entertainment", "Utilities",
                      "Shopping", "Health", "Education", "Other"]

        new_cat = st.selectbox(
            "Edit Category",
            categories,
            index=categories.index(df_reset.loc[selected, "Category"])
        )

    with col3:
        new_amt = st.number_input(
            "Edit Amount",
            value=float(df_reset.loc[selected, "Amount"]),
            min_value=0.0
        )

    new_desc = st.text_input(
        "Edit Description",
        value=str(df_reset.loc[selected, "Description"])
    )

    b1, b2 = st.columns(2)

    if b1.button("Update"):
        orig_index = df_reset.loc[selected, "index"]
        st.session_state.expenses.loc[orig_index] = [
            new_date, new_cat, new_amt, new_desc
        ]
        st.success("Expense Updated")
        st.rerun()

    if b2.button("Delete"):
        orig_index = df_reset.loc[selected, "index"]
        st.session_state.expenses = st.session_state.expenses.drop(orig_index)
        st.success("Expense Deleted")
        st.rerun()

# ---------------- DOWNLOAD ----------------
st.divider()
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇ Download CSV Report",
    csv,
    "expenses_report.csv",
    "text/csv"
)
