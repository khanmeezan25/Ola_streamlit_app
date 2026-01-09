import pandas as pd
import sqlite3

DATA_PATH = "data/ola_clean.csv"

def run_query(sql):
    df = pd.read_csv(DATA_PATH)

    conn = sqlite3.connect(":memory:")
    df.to_sql("ola_cleaned", conn, index=False, if_exists="replace")

    result = pd.read_sql_query(sql, conn)
    conn.close()
    return result

