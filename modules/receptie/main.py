"""
receptie/main.py
-----------------
Punct de intrare pentru ecranul receptiei.
Orchestreaza cele 2 taburi: Introducere Comenzi, Rezumat Livrari.
"""

import streamlit as st

from modules.receptie import comenzi, rezumat


def show_receptie():
    tab1, tab2 = st.tabs(["🆕 Introducere Comenzi", "📊 Rezumat Livrări"])

    with tab1:
        comenzi.show()

    with tab2:
        rezumat.show()


# Alias pentru compatibilitate cu app.py (rol Recepție)
def main_receptie_page():
    show_receptie()
