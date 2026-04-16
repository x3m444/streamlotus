"""
admin_manager/firme.py
-----------------------
Gestiunea firmelor cu contract (adaugare, editare, activare/dezactivare).
Include confirmarea prezentei zilnice (rezervari) per firma.
Angajatii sunt gestionati direct de vanzator din ecranul Ghiseu.
"""

import streamlit as st
import database as db
import utils


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

    active   = [f for f in firme if f['activ']]
    inactive = [f for f in firme if not f['activ']]

    # ----------------------------------------------------------
    # CONFIRMARE PREZENȚĂ AZI
    # ----------------------------------------------------------
    data_azi   = utils.get_ro_time().date()
    rezervari  = db.get_rezervari_firme_azi(data_azi)
    total_rez  = sum(v['cantitate'] for v in rezervari.values())

    with st.expander(
        f"📋 Confirmare Prezență Azi — {data_azi.strftime('%d.%m.%Y')}"
        f"{'  ✅ ' + str(total_rez) + ' porții rezervate' if total_rez else '  (nicio confirmare)'}",
        expanded=True
    ):
        if not active:
            st.info("Nu există firme active.")
        else:
            st.caption("Confirmă câți angajați vin azi. Cantitatea scade din stocul zilei.")

            col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1.5, 1, 1])
            col_h1.caption("**Firmă**")
            col_h2.caption("**Contract**")
            col_h3.caption("**Angajați activi**")
            col_h4.caption("**Rezervat azi**")
            st.divider()

            for firma in active:
                fid         = firma['id']
                nr_activi   = len(db.get_angajati_firma(fid, doar_activi=True))
                rez_curenta = rezervari.get(fid, {}).get('cantitate', 0)

                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1, 1, 1])
                c1.write(f"🏢 **{firma['nume_firma']}**")
                c2.caption(TIPURI_CONTRACT.get(firma['tip_contract'], ''))
                c3.write(str(nr_activi))

                qty = c4.number_input(
                    "qty", min_value=0, max_value=200,
                    value=rez_curenta if rez_curenta else nr_activi,
                    step=1, key=f"rez_{fid}",
                    label_visibility="collapsed"
                )

                if rez_curenta:
                    if c5.button("✅ Update", key=f"btn_rez_{fid}", use_container_width=True):
                        db.save_rezervare_firma(fid, data_azi, qty)
                        st.rerun()
                else:
                    if c5.button("Confirmă", key=f"btn_rez_{fid}",
                                 use_container_width=True, type="primary"):
                        db.save_rezervare_firma(fid, data_azi, qty)
                        st.rerun()

            st.divider()
            if total_rez:
                st.success(f"**Total rezervat pentru firme azi: {total_rez} porții**")
            else:
                st.info("Nicio firmă confirmată pentru azi.")

    st.divider()

    # ----------------------------------------------------------
    # GESTIUNE FIRME (angajati, activare/dezactivare)
    # ----------------------------------------------------------
    st.markdown(f"**Firme active ({len(active)}):**")

    for firma in active:
        fid         = firma['id']
        toti        = db.get_angajati_firma(fid, doar_activi=False)
        activi_ang  = [a for a in toti if a['activ']]
        inactivi_ang= [a for a in toti if not a['activ']]

        with st.expander(f"🏢 {firma['nume_firma']} — {TIPURI_CONTRACT.get(firma['tip_contract'], '')}"):
            col_info, col_dezact_f = st.columns([4, 1])
            col_info.caption(f"Angajați activi: {len(activi_ang)} | Inactivi: {len(inactivi_ang)}")
            if col_dezact_f.button("🔴 Dezactivează firma", key=f"dezact_firma_{fid}", use_container_width=True):
                db.update_firma(fid, firma['nume_firma'], firma['tip_contract'], False)
                st.rerun()

            st.divider()

            col_inp, col_btn = st.columns([4, 1])
            nou = col_inp.text_input("Adaugă angajat:", key=f"new_ang_{fid}",
                                     placeholder="Nume și prenume", label_visibility="collapsed")
            with col_btn:
                if st.button("➕ Adaugă", key=f"btn_add_ang_{fid}", use_container_width=True):
                    if nou.strip():
                        db.add_angajat(fid, nou.strip())
                        st.success(f"Adăugat: {nou.strip()}")
                        st.rerun()

            if activi_ang:
                for ang in activi_ang:
                    ca, cb = st.columns([5, 1])
                    ca.write(f"👤 {ang['nume_angajat']}")
                    if cb.button("Concediu", key=f"adm_dezact_{ang['id']}", use_container_width=True):
                        db.toggle_angajat(ang['id'], False)
                        st.rerun()
            else:
                st.info("Niciun angajat activ.")

            if inactivi_ang:
                st.caption(f"Inactivi ({len(inactivi_ang)}):")
                for ang in inactivi_ang:
                    ca, cb = st.columns([5, 1])
                    ca.write(f"💤 {ang['nume_angajat']}")
                    if cb.button("Reactivează", key=f"adm_act_{ang['id']}", use_container_width=True):
                        db.toggle_angajat(ang['id'], True)
                        st.rerun()

    if inactive:
        with st.expander(f"Firme inactive ({len(inactive)})"):
            for firma in inactive:
                col_n, col_act = st.columns([4, 1])
                col_n.write(f"💤 {firma['nume_firma']} — {TIPURI_CONTRACT.get(firma['tip_contract'], '')}")
                if col_act.button("🟢 Reactivează", key=f"act_firma_{firma['id']}", use_container_width=True):
                    db.update_firma(firma['id'], firma['nume_firma'], firma['tip_contract'], True)
                    st.rerun()
