from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from core.db import Database


def main() -> None:
    st.title("Progress Dashboard")
    db = Database()
    today = date.today()
    summary = db.weekly_summary(today)
    if not summary:
        st.info("Log meals to see your progress.")
        return
    df = pd.DataFrame(summary, index=["Weekly Totals"]).T
    st.bar_chart(df)


if __name__ == "__main__":
    main()
