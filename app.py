import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from db import run_query

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="OLA Ride Insights",
    page_icon="🚖",
    layout="wide"
)

# ---------------- SIDEBAR ----------------
page = st.sidebar.radio(
    "MENU",
    ["SQL Analysis", "Dashboard"],
    index=0
)

# ---------------- UI STYLING ----------------
st.markdown("""
<style>
.stApp { background-color: #f3f4f6; }
.block-container {
    background-color: #ffffff;
    padding: 2.5rem 3.5rem;
    border-radius: 14px;
    box-shadow: 0px 4px 15px rgba(0,0,0,0.06);
}
h3 { margin-top: 30px; color: #111827; }
[data-testid="metric-container"] {
    background-color: #f9fafb;
    border-radius: 12px;
    padding: 15px;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div style='text-align:center;'>
    <h1 style='color:#dc2626; font-weight:800;'>🚖 OLA Ride Insights</h1>
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# SQLite Date Expression (replacement of STR_TO_DATE)
DATE_EXPR = "DATE(substr(Date,7,4)||'-'||substr(Date,4,2)||'-'||substr(Date,1,2))"

# =====================================================
# ================= SQL ANALYSIS ======================
# =====================================================
if page == "SQL Analysis":

    st.subheader("1. Successful Bookings")
    st.dataframe(run_query(
        "SELECT * FROM ola_cleaned WHERE Booking_Status='Success';"
    ), use_container_width=True)
    st.markdown("---")

    st.subheader("2. Average Ride Distance by Vehicle Type")
    st.dataframe(run_query("""
        SELECT Vehicle_Type, AVG(Ride_Distance) AS avg_distance
        FROM ola_cleaned
        GROUP BY Vehicle_Type;
    """), use_container_width=True)
    st.markdown("---")

    st.subheader("3. Cancelled Rides by Customer")
    cancelled_customer = run_query("""
        SELECT COUNT(*) AS c
        FROM ola_cleaned
        WHERE Booking_Status='Canceled by Customer';
    """).iloc[0,0]
    st.metric("Total Cancelled by Customer", cancelled_customer)
    st.markdown("---")

    st.subheader("4. Top 5 Customers by Total Rides")
    st.dataframe(run_query("""
        SELECT Customer_ID, COUNT(Booking_ID) AS total_rides
        FROM ola_cleaned
        GROUP BY Customer_ID
        ORDER BY total_rides DESC
        LIMIT 5;
    """), use_container_width=True)
    st.markdown("---")

    st.subheader("5. Driver Cancellations (Personal & Car Issues)")
    driver_cancel = run_query("""
        SELECT COUNT(*) AS c
        FROM ola_cleaned
        WHERE Canceled_Rides_by_Driver='Personal & Car related issue';
    """).iloc[0,0]
    st.metric("Driver Cancellations", driver_cancel)
    st.markdown("---")

    st.subheader("6. Driver Ratings for Prime Sedan")
    df6 = run_query("""
        SELECT MAX(Driver_Ratings) AS max_rating,
               MIN(Driver_Ratings) AS min_rating
        FROM ola_cleaned
        WHERE Vehicle_Type='Prime Sedan';
    """)
    c1, c2 = st.columns(2)
    c1.metric("Max Rating", df6.iloc[0,0])
    c2.metric("Min Rating", df6.iloc[0,1])
    st.markdown("---")

    st.subheader("7. Rides Paid via UPI")
    st.dataframe(
        run_query("SELECT * FROM ola_cleaned WHERE Payment_Method='UPI';"),
        use_container_width=True
    )
    st.markdown("---")

    st.subheader("8. Average Customer Rating by Vehicle Type")
    st.dataframe(run_query("""
        SELECT Vehicle_Type, AVG(Customer_Rating) AS avg_customer_rating
        FROM ola_cleaned
        GROUP BY Vehicle_Type;
    """), use_container_width=True)
    st.markdown("---")

    st.subheader("9. Total Booking Value (Successful Rides)")
    total_value = run_query("""
        SELECT SUM(Booking_Value) AS total_value
        FROM ola_cleaned
        WHERE Booking_Status='Success';
    """).iloc[0,0]
    st.metric("Total Booking Value", f"₹ {total_value}")
    st.markdown("---")

    st.subheader("10. Incomplete Rides & Reasons")
    st.dataframe(run_query("""
        SELECT Booking_ID, Incomplete_Rides_Reason
        FROM ola_cleaned
        WHERE Incomplete_Rides='Yes';
    """), use_container_width=True)

# =====================================================
# ================= DASHBOARD =========================
# =====================================================


# ================= DASHBOARD PAGE ====================
else:

    st.header("📊 Dashboard Overview")

    tab1, tab2, tab3, tab4, tab5 = st.tabs(
        ["Overall", "Vehicle Type", "Revenue", "Cancellation", "Ratings"]
    )

    # ==================================================
    # ================= TAB 1: OVERALL =================
    # ==================================================
    with tab1:
        st.subheader("Overall")

        # ⚠️ NO DATE FILTER (root cause fixed)
        total_bookings = run_query(
            "SELECT COUNT(*) AS c FROM ola_cleaned;"
        ).iloc[0, 0]

        total_value = run_query("""
            SELECT SUM(Booking_Value) AS s
            FROM ola_cleaned
            WHERE Booking_Status='Success';
        """).iloc[0, 0]

        c1, c2 = st.columns(2)
        c1.metric("Total Bookings", total_bookings)
        c2.metric("Total Booking Value", f"₹ {round((total_value or 0)/1_000_000,2)} M")

        status_df = run_query("""
            SELECT Booking_Status, COUNT(*) AS cnt
            FROM ola_cleaned
            GROUP BY Booking_Status;
        """)
        st.subheader("Booking Status Breakdown")
        fig, ax = plt.subplots()
        ax.pie(status_df["cnt"], labels=status_df["Booking_Status"], autopct="%1.1f%%")
        st.pyplot(fig)
        
        st.subheader("Ride Volume over Time")
        trend_df = run_query("""
            SELECT Date AS d, COUNT(*) AS c
            FROM ola_cleaned
            GROUP BY Date
            ORDER BY Date;
        """).set_index("d")

        st.line_chart(trend_df)

    # ==================================================
    # ================= TAB 2: VEHICLE TYPE =============
    # ==================================================
    with tab2:
        st.subheader("Vehicle Type Performance")

        vehicle_df = run_query("""
            SELECT
                Vehicle_Type AS "Vehicle Type",
                ROUND(SUM(Booking_Value)/1000000,2) AS "Total Booking Value (M)",
                ROUND(SUM(
                    CASE WHEN Booking_Status='Success'
                    THEN Booking_Value ELSE 0 END
                )/1000000,2) AS "Success Booking Value (M)",
                ROUND(AVG(Ride_Distance),2) AS "Avg. Distance Travelled",
                ROUND(SUM(Ride_Distance)/1000,0) AS "Total Distance Travelled (K)"
            FROM ola_cleaned
            GROUP BY Vehicle_Type
            ORDER BY "Total Booking Value (M)" DESC;
        """)

        st.dataframe(vehicle_df, use_container_width=True, hide_index=True)

    # ==================================================
    # ================= TAB 3: REVENUE ==================
    # ==================================================
    with tab3:
        st.subheader("Revenue Analysis")

        revenue_payment_df = run_query("""
            SELECT Payment_Method, SUM(Booking_Value) AS revenue
            FROM ola_cleaned
            WHERE Booking_Status='Success'
            GROUP BY Payment_Method;
        """).set_index("Payment_Method")

        st.subheader("Revenue by Payment Method")
        st.bar_chart(revenue_payment_df)

        distance_df = run_query("""
            SELECT Date AS d, SUM(Ride_Distance) AS dist
            FROM ola_cleaned
            WHERE Booking_Status='Success'
            GROUP BY Date
            ORDER BY Date;
        """).set_index("d")

        st.subheader("Ride distance distribution per date")
        st.bar_chart(distance_df)

        top_customers_df = run_query("""
            SELECT Customer_ID, SUM(Booking_Value) AS total_booking_value
            FROM ola_cleaned
            WHERE Booking_Status='Success'
            GROUP BY Customer_ID
            ORDER BY total_booking_value DESC
            LIMIT 5;
        """)

        st.subheader("Top 5 Customers by Total Booking Value")
        st.dataframe(top_customers_df, use_container_width=True, hide_index=True)

    # ==================================================
    # ================= TAB 4: CANCELLATION =============
    # ==================================================
    with tab4:
        st.subheader("Cancellation Analysis")

        total_bookings = run_query(
            "SELECT COUNT(*) FROM ola_cleaned;"
        ).iloc[0, 0]

        success_bookings = run_query(
            "SELECT COUNT(*) FROM ola_cleaned WHERE Booking_Status='Success';"
        ).iloc[0, 0]

        canceled_bookings = run_query(
            "SELECT COUNT(*) FROM ola_cleaned WHERE Booking_Status LIKE 'Canceled%';"
        ).iloc[0, 0]

        cancel_rate = (canceled_bookings / total_bookings) * 100 if total_bookings else 0

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Bookings", total_bookings)
        c2.metric("Succeeded Bookings", success_bookings)
        c3.metric("Canceled Bookings", canceled_bookings)
        c4.metric("Cancellation Rate", f"{round(cancel_rate,2)} %")

        driver_df = run_query("""
            SELECT Canceled_Rides_by_Driver AS reason, COUNT(*) AS cnt
            FROM ola_cleaned
            WHERE Booking_Status='Canceled by Driver'
              AND Canceled_Rides_by_Driver IS NOT NULL
            GROUP BY Canceled_Rides_by_Driver;
        """)

        fig2, ax2 = plt.subplots()
        ax2.pie(driver_df["cnt"], labels=driver_df["reason"], autopct="%1.2f%%")
        ax2.axis("equal")
        st.subheader("Cancelled Rides by Drivers")
        st.pyplot(fig2)

    # ==================================================
    # ================= TAB 5: RATINGS ==================
    # ==================================================
    with tab5:
        st.subheader("Ratings Analysis")
        st.subheader("Driver Ratings")
        driver_rating_df = run_query("""
            SELECT Vehicle_Type, ROUND(AVG(Driver_Ratings),2) AS avg_driver_rating
            FROM ola_cleaned
            WHERE Driver_Ratings IS NOT NULL
            GROUP BY Vehicle_Type;
        """)

        cols = st.columns(len(driver_rating_df))
        for col, row in zip(cols, driver_rating_df.itertuples()):
            col.metric(row.Vehicle_Type, row.avg_driver_rating)

        st.markdown("---")
        st.subheader("Customer Ratings")
        customer_rating_df = run_query("""
            SELECT Vehicle_Type, ROUND(AVG(Customer_Rating),2) AS avg_customer_rating
            FROM ola_cleaned
            WHERE Customer_Rating IS NOT NULL
            GROUP BY Vehicle_Type;
        """)

        cols = st.columns(len(customer_rating_df))
        for col, row in zip(cols, customer_rating_df.itertuples()):
            col.metric(row.Vehicle_Type, row.avg_customer_rating)
