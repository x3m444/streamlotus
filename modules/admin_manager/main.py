"""
admin_manager/main.py
---------------------
Punctul de intrare al paginii Admin.
Afiseaza selectorul de data global (deasupra taburilor) si
orchestreaza cele 4 sectiuni: Lansare, Monitorizare, Planificare, Nomenclator.
"""

import streamlit as st
import database as db
import utils
from datetime import date

from modules.admin_manager import lansare, planificare, nomenclator, rapoarte


def show_admin():
    st.title("👨‍🍳 Administrare Bucătărie")

    # --- SELECTOR DATĂ GLOBAL ---
    # Plasat DEASUPRA taburilor — activ indiferent de sectiunea deschisa.
    # Valoarea este transmisa ca parametru fiecarui sub-modul.
    col_data, col_info = st.columns([1, 3])
    with col_data:
        data_selectata = st.date_input(
            "📅 Data de lucru:",
            value=date.today(),
            key="admin_data_globala"
        )
    with col_info:
        st.info(
            f"Lucrezi pentru: **{utils.format_nume_zi(data_selectata)}, "
            f"{data_selectata.strftime('%d.%m.%Y')}**"
        )

    st.divider()

    # --- TABURI PRINCIPALE ---
    tab_lansare, tab_monitor, tab_plan, tab_nom = st.tabs([
        "🚀 Lansare Producție",
        "📊 Monitorizare Comenzi",
        "📅 Planificare Săptămânală",
        "📋 Gestiune Nomenclator",
    ])

    with tab_lansare:
        lansare.show(data_selectata)

    with tab_monitor:
        rapoarte.show(data_selectata)

    with tab_plan:
        planificare.show(data_selectata)

    with tab_nom:
        nomenclator.show()
