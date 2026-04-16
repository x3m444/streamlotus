"""
admin_manager/firme.py
-----------------------
Gestiunea firmelor cu contract (adaugare, editare, activare/dezactivare).
Angajatii sunt gestionati direct de vanzator din ecranul Ghiseu.
"""

import streamlit as st
import database as db


TIPURI_CONTRACT = {
    "pranz_cina": "Prânz + Cină",
    "pranz":      "Doar Prânz",
    "cina":       "Doar Cină",
}


def show():
    st.subheader("🏢 Gestiune Firme cu Contract")

    firme = db.get_all_firme(doar_active=False)

    # Formular adaugare firma noua
    with st.expander("➕ Adaugă Firmă Nouă", expanded=(len(firme) == 0)):
        col_n, col_t, col_btn = st.columns([3, 2, 1])
        with col_n:
            nou_nume = st.text_input("Nume firmă:", key="firma_noua_nume")
        with col_t:
            nou_tip = st.selectbox("Contract:", list(TIPURI_CONTRACT.keys()),
                                   format_func=lambda x: TIPURI_CONTRACT[x],
                                   key="firma_noua_tip")
        with col_btn:
            st.write("")
            st.write("")
            if st.button("Adaugă", key="btn_add_firma", use_container_width=True, type="primary"):
                if nou_nume.strip():
                    db.add_firma(nou_nume.strip(), nou_tip)
                    st.success(f"Firmă adăugată: {nou_nume.strip()}")
                    st.rerun()
                else:
                    st.error("Introdu numele firmei.")

    if not firme:
        st.info("Nu există firme înregistrate.")
        return

    # Lista firme
    active = [f for f in firme if f['activ']]
    inactive = [f for f in firme if not f['activ']]

    st.markdown(f"**Firme active ({len(active)}):**")

    for firma in active:
        with st.container(border=True):
            col_n, col_t, col_ang, col_dezact = st.columns([3, 2, 1, 1])

            col_n.write(f"**{firma['nume_firma']}**")
            col_t.write(TIPURI_CONTRACT.get(firma['tip_contract'], firma['tip_contract']))

            angajati = db.get_angajati_firma(firma['id'], doar_activi=True)
            col_ang.metric("Angajați activi", len(angajati))

            if col_dezact.button("🔴 Dezactivează", key=f"dezact_firma_{firma['id']}", use_container_width=True):
                db.update_firma(firma['id'], firma['nume_firma'], firma['tip_contract'], False)
                st.rerun()

    if inactive:
        with st.expander(f"Firme inactive ({len(inactive)})"):
            for firma in inactive:
                col_n, col_act = st.columns([4, 1])
                col_n.write(f"💤 {firma['nume_firma']} — {TIPURI_CONTRACT.get(firma['tip_contract'], '')}")
                if col_act.button("🟢 Reactivează", key=f"act_firma_{firma['id']}", use_container_width=True):
                    db.update_firma(firma['id'], firma['nume_firma'], firma['tip_contract'], True)
                    st.rerun()
