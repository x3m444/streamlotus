"""
ghiseu/main.py
---------------
Punct de intrare pentru ecranul ghiseului.
Orchestreaza cele 3 taburi: Bon Casa, Firme, Eveniment.
"""

import streamlit as st
import utils

from modules.ghiseu import bon_casa, firme, eveniment


def show_ghiseu():
    st.title("🏪 Ghișeu Servire")
    data_azi = utils.get_ro_time().date()
    st.caption(f"Data: {data_azi.strftime('%d.%m.%Y')}")

    tab_bon, tab_firme, tab_eveniment = st.tabs([
        "🧾 Bon Casă",
        "🏢 Firme",
        "🎉 Eveniment"
    ])

    with tab_bon:
        bon_casa.show(data_azi)

    with tab_firme:
        firme.show(data_azi)

    with tab_eveniment:
        eveniment.show(data_azi)
