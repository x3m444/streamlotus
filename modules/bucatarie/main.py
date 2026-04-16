"""
bucatarie/main.py
------------------
Punct de intrare pentru ecranul bucatariei.
Orchestreaza cele 3 taburi: Gatire, Impachetare, Nevandut.
"""

import streamlit as st
import database as db
from datetime import date

from modules.bucatarie import gatire, impachetare, nevandut, buffer as buffer_tab


engine = db.get_engine()


def show_bucatarie():
    st.header("👨‍🍳 Monitor Producție și Expediție")

    data_selectata = st.date_input("Comenzi pentru data:", value=date.today(), key="buc_data")

    tab_gatire, tab_impachetare, tab_buffer, tab_nevandut = st.tabs([
        "🔥 Gătire (Loturi Producție)",
        "📦 Împachetare (Comenzi Clienți)",
        "🗃️ Buffer Pre-ambalare",
        "🍽️ Declară Nevândut"
    ])

    with tab_gatire:
        gatire.show(data_selectata, engine)

    with tab_impachetare:
        impachetare.show(data_selectata, engine)

    with tab_buffer:
        buffer_tab.show(data_selectata)

    with tab_nevandut:
        nevandut.show(data_selectata)
