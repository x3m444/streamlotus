"""
admin_manager/lansare.py
------------------------
Sectiunea "Lansare Productie" din pagina Admin.
Permite trimiterea efectiva a loturilor catre bucatarie:
  - Lot Pranz
  - Lot Cina
  - Comanda Sandwich
  - Comanda Speciala / Eveniment

Primeste `data_plan` (datetime.date) din main.py.
"""

import streamlit as st
import database as db
import utils


def show(data_plan):
    """Randeaza sectiunea de lansare productie pentru data primita."""
    data_afisata = data_plan.strftime('%d/%m/%Y')
    toate = db.get_toate_produsele()

    st.subheader("🏭 Lansare Loturi în Producție")
    st.warning(f"📅 Loturile de mai jos vor fi lansate pentru data: **{data_afisata}**")

    # -------------------------------------------------------
    # PRANZ
    # -------------------------------------------------------
    with st.expander("🍲 LANSARE PRODUCȚIE PRÂNZ"):
        m_p = db.get_meniu_planificat(data_plan, tip_plan="pranz")

        if not m_p:
            st.warning("⚠️ Plan prânz lipsă pentru această zi! Mergi la 'Planificare Săptămânală'.")
        else:
            if 'buffer_pranz' not in st.session_state:
                st.session_state.buffer_pranz = []

            prod_ales = st.selectbox(
                "Alege produsul:",
                m_p,
                format_func=lambda x: x['nume'],
                key="sel_p_final"
            )
            qty_aleasa = st.number_input("Cantitate:", min_value=1, step=1, value=1, key="qty_p_final")

            if st.button("➕ Adaugă în Lot", use_container_width=True, key="btn_add_p"):
                existent = next(
                    (item for item in st.session_state.buffer_pranz if item["id"] == prod_ales['id']),
                    None
                )
                if existent:
                    existent['cantitate'] += qty_aleasa
                else:
                    st.session_state.buffer_pranz.append({
                        "id": prod_ales['id'],
                        "nume": prod_ales['nume'],
                        "cantitate": qty_aleasa,
                        "pret": prod_ales.get('pret_standard', 0)
                    })
                st.rerun()

            if st.session_state.buffer_pranz:
                st.markdown("---")
                for i, item in enumerate(st.session_state.buffer_pranz):
                    c_txt, c_del = st.columns([4, 1])
                    c_txt.write(f"**{item['cantitate']}** x {item['nume']}")
                    if c_del.button("❌", key=f"del_p_f_{i}"):
                        st.session_state.buffer_pranz.pop(i)
                        st.rerun()

                if st.button("🚀 Confirmă și Salvează Lot Prânz", type="primary", use_container_width=True):
                    total_lot = sum(item['cantitate'] * item['pret'] for item in st.session_state.buffer_pranz)
                    db.save_comanda_finala(
                        999, st.session_state.buffer_pranz, total_lot,
                        "INTERN", "12:00", "Lot Producție Prânz", "cantina", "pranz", data_plan
                    )
                    st.session_state.buffer_pranz = []
                    st.success(f"✅ Lotul Prânz a fost lansat! (Valoare: {total_lot} lei)")
                    st.rerun()

    # -------------------------------------------------------
    # CINA
    # -------------------------------------------------------
    with st.expander("🌙 LANSARE PRODUCȚIE CINĂ"):
        m_c = db.get_meniu_planificat(data_plan, tip_plan="cina")

        if not m_c:
            st.warning("⚠️ Plan cină lipsă pentru această zi!")
        else:
            if 'buffer_cina' not in st.session_state:
                st.session_state.buffer_cina = []

            prod_ales_c = st.selectbox(
                "Alege felul (Cină):",
                options=m_c,
                format_func=lambda x: x['nume'],
                key="sel_cina_prod_v3"
            )
            qty_aleasa_c = st.number_input("Nr. porții:", min_value=1, step=1, value=1, key="qty_cina_val_v3")

            if st.button("➕ Adaugă la Lot Cină", key="btn_add_cina_v3", use_container_width=True):
                existent = next(
                    (item for item in st.session_state.buffer_cina if item["id"] == prod_ales_c['id']),
                    None
                )
                if existent:
                    existent['cantitate'] += qty_aleasa_c
                else:
                    st.session_state.buffer_cina.append({
                        "id": prod_ales_c['id'],
                        "nume": prod_ales_c['nume'],
                        "cantitate": qty_aleasa_c,
                        "pret": prod_ales_c.get('pret_standard', 0)
                    })
                st.rerun()

            if st.session_state.buffer_cina:
                st.markdown("---")
                for i, item in enumerate(st.session_state.buffer_cina):
                    c_txt, c_del = st.columns([4, 1])
                    c_txt.write(f"**{item['cantitate']}** x {item['nume']} ({item['pret']} lei/buc)")
                    if c_del.button("❌", key=f"del_cina_item_v3_{i}"):
                        st.session_state.buffer_cina.pop(i)
                        st.rerun()

                col_confirm, col_clear = st.columns(2)
                with col_confirm:
                    if st.button("🚀 Confirmă Producție Cină", type="primary", use_container_width=True):
                        total_cina = sum(item['cantitate'] * item.get('pret', 0) for item in st.session_state.buffer_cina)
                        db.save_comanda_finala(
                            999, st.session_state.buffer_cina, total_cina,
                            "INTERN", "19:00", "Lot Producție Cină", "cantina", "cina", data_plan
                        )
                        st.session_state.buffer_cina = []
                        st.success(f"✅ Cina salvată! (Total: {total_cina:.2f} lei)")
                        st.rerun()
                with col_clear:
                    if st.button("🗑️ Golește lista", key="clear_cina_all_v3", use_container_width=True):
                        st.session_state.buffer_cina = []
                        st.rerun()

    # -------------------------------------------------------
    # SANDWICH
    # -------------------------------------------------------
    with st.expander("🥪 LANSARE COMANDĂ SANDWICH"):
        m_s = db.get_meniu_planificat(data_plan, tip_plan="sandwich")

        if not m_s:
            st.warning("⚠️ Plan sandwich lipsă pentru această zi!")
        else:
            with st.form("form_lansare_sw", clear_on_submit=True):
                sw_selectat = st.selectbox(
                    "Alege tipul de sandwich:",
                    options=m_s,
                    format_func=lambda x: x['nume'],
                    key="sw_type_select"
                )
                col_dest, col_buc = st.columns([2, 1])
                with col_dest:
                    destinatie = st.text_input("Unde merge?", placeholder="Ex: Școala 10 / Intern")
                with col_buc:
                    bucati = st.number_input("Bucăți:", 1, 500, step=1)

                if st.form_submit_button("🚀 Lansează Comanda", use_container_width=True):
                    if destinatie:
                        pret_unitar = sw_selectat.get('pret_standard', 0)
                        total_sw = bucati * pret_unitar
                        db.save_comanda_finala(
                            999,
                            [{"id": sw_selectat['id'], "nume": sw_selectat['nume'],
                              "cantitate": bucati, "pret": pret_unitar}],
                            total_sw, "INTERN", "08:00", destinatie, "cantina", "sandwich", data_plan
                        )
                        st.success(f"✅ Lansat: {bucati}x {sw_selectat['nume']} → {destinatie} ({total_sw} lei)")
                    else:
                        st.error("⚠️ Trebuie să introduci destinația!")

    # -------------------------------------------------------
    # SPECIAL / EVENIMENT
    # -------------------------------------------------------
    with st.expander("✨ LANSARE COMANDĂ SPECIALĂ (PROTOCOL / EVENIMENT)"):
        tip_spec = st.radio("Tip:", ["special", "eveniment"], horizontal=True, key="rad_spec")
        desc_spec = st.text_input("📍 Descriere OBLIGATORIE (ex: Botez Popescu):", key="obs_spec")

        if 'buffer_special' not in st.session_state:
            st.session_state.buffer_special = []

        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            p_sel = st.selectbox("Produs:", toate, format_func=lambda x: x['nume'], key="p_spec")
        with c2:
            q_sel = st.number_input("Cant:", min_value=1, value=1, key="q_spec")
        with c3:
            st.write("##")
            if st.button("➕ Adaugă", key="btn_add_spec"):
                pret_val = p_sel.get('pret_standard') or p_sel.get('pret', 0)
                st.session_state.buffer_special.append({
                    "id": p_sel['id'],
                    "nume": p_sel['nume'],
                    "cantitate": q_sel,
                    "pret": pret_val
                })
                st.rerun()

        if st.session_state.buffer_special:
            st.markdown("---")
            for i, item in enumerate(st.session_state.buffer_special):
                col_t, col_r = st.columns([4, 1])
                col_t.write(f"✅ {item['nume']} x {item['cantitate']} ({item['pret']} lei/buc)")
                if col_r.button("🗑️", key=f"del_spec_{i}"):
                    st.session_state.buffer_special.pop(i)
                    st.rerun()

            if st.button(f"🚀 Lansează {tip_spec.upper()}", use_container_width=True, type="primary"):
                if not desc_spec:
                    st.error("⚠️ Lipsește descrierea!")
                else:
                    total_spec = sum(item['cantitate'] * item.get('pret', 0) for item in st.session_state.buffer_special)
                    db.save_comanda_finala(
                        999, st.session_state.buffer_special, total_spec,
                        "INTERN", "08:00", desc_spec, "cantina", tip_spec, data_plan
                    )
                    st.session_state.buffer_special = []
                    st.success(f"✅ Comanda trimisă! Total: {total_spec:.2f} lei")
                    st.rerun()
