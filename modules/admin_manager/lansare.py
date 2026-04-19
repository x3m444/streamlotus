"""
admin_manager/lansare.py
------------------------
Sectiunea "Lansare Productie" din pagina Admin.
  - Lot Prânz
  - Lot Cină
  - Comandă Specială / Eveniment

Sandwich-urile se lansează din tab-ul Firme → Lansare Zilnică.
Primeste `data_plan` (datetime.date) din main.py.
"""

import streamlit as st
import database as db


def _card_lot(lot, key_prefix, label="Lot"):
    """Card consistent cu cel din Lansare Firme. Returneaza True dacă s-a cerut editare."""
    comanda_id = lot["comanda_id"]
    with st.container(border=True):
        c_n, c_info, c_ed, c_del = st.columns([2.5, 5, 1.2, 1.2])
        c_n.markdown(f"**{label}**")
        c_n.markdown(":green[✅ Lansat]")
        detalii_str = f"  |  {lot['detalii']}" if lot.get("detalii") else ""
        c_info.caption(
            f"🕐 {lot['ora']}  |  💰 {lot['total']:.0f} lei  |  "
            f"{lot['status'].upper()}{detalii_str}"
        )
        edit   = c_ed.button("✏️ Edit", key=f"edit_{key_prefix}_{comanda_id}",
                              use_container_width=True)
        if c_del.button("🗑️ Șterge", key=f"del_{key_prefix}_{comanda_id}",
                        use_container_width=True):
            db.delete_comanda(comanda_id)
            st.rerun()
        return edit


@st.fragment
def show(data_plan):
    data_afisata   = data_plan.strftime('%d/%m/%Y')
    toate          = db.get_toate_produsele()
    loturi_lansate = db.get_loturi_lansate(data_plan)

    st.subheader("🏭 Lansare Loturi în Producție")
    st.warning(f"📅 Loturile de mai jos vor fi lansate pentru data: **{data_afisata}**")

    # ── Stoc curent ──────────────────────────────────────────
    stoc           = db.get_stoc_zi(data_plan)
    total_rezervat = db.get_total_rezervat_firme(data_plan)
    if stoc:
        with st.expander("📊 Stoc lansat azi — situație curentă", expanded=False):
            if total_rezervat:
                st.info(f"🏢 **{total_rezervat} porții rezervate** pentru firme cu contract azi")
            cols = st.columns([3, 1, 1, 1, 1])
            cols[0].markdown("**Produs**"); cols[1].markdown("**Lansat**")
            cols[2].markdown("**Firme**");  cols[3].markdown("**Ambalat**")
            cols[4].markdown("**Rămas**")
            for nume, s in stoc.items():
                c0, c1, c2, c3, c4 = st.columns([3, 1, 1, 1, 1])
                c0.write(nume); c1.write(s['lansat'])
                c2.caption(f"~{s.get('rezervat', 0)}"); c3.write(s['ambalat'])
                ramas = s['ramas']
                if ramas <= 0:   c4.markdown(f":red[**{ramas}**]")
                elif ramas < 5:  c4.markdown(f":orange[**{ramas}**]")
                else:            c4.markdown(f":green[**{ramas}**]")

    # ── PRÂNZ ────────────────────────────────────────────────
    loturi_pranz = loturi_lansate.get("pranz", [])
    status_pranz = "  ✅ Lansat" if loturi_pranz else "  ⏳ Nelansat"
    with st.expander(f"🍲 LANSARE PRODUCȚIE PRÂNZ{status_pranz}", expanded=False):
        if loturi_pranz:
            for lot in loturi_pranz:
                if _card_lot(lot, "pranz", label="Lot Prânz"):
                    db.delete_comanda(lot["comanda_id"])
                    st.rerun()
        else:
            m_p = db.get_meniu_planificat(data_plan, tip_plan="pranz")
            if not m_p:
                st.warning("⚠️ Plan prânz lipsă! Mergi la 'Planificare Săptămânală'.")
            else:
                if "buffer_pranz" not in st.session_state:
                    st.session_state.buffer_pranz = []

                prod_ales  = st.selectbox("Alege produsul:", m_p,
                                          format_func=lambda x: x["nume"], key="sel_p_final")
                qty_aleasa = st.number_input("Cantitate:", min_value=1, step=1, value=1, key="qty_p_final")

                if st.button("➕ Adaugă în Lot", use_container_width=True, key="btn_add_p"):
                    ex = next((i for i in st.session_state.buffer_pranz if i["id"] == prod_ales["id"]), None)
                    if ex:
                        ex["cantitate"] += qty_aleasa
                    else:
                        st.session_state.buffer_pranz.append({
                            "id": prod_ales["id"], "nume": prod_ales["nume"],
                            "cantitate": qty_aleasa, "pret": prod_ales.get("pret_standard", 0)
                        })

                if st.session_state.buffer_pranz:
                    st.markdown("---")
                    for i, item in enumerate(st.session_state.buffer_pranz):
                        c_txt, c_del = st.columns([4, 1])
                        c_txt.write(f"**{item['cantitate']}** x {item['nume']}")
                        if c_del.button("❌", key=f"del_p_f_{i}"):
                            st.session_state.buffer_pranz.pop(i)
                    if st.button("🚀 Confirmă și Salvează Lot Prânz", type="primary", use_container_width=True):
                        total_lot = sum(i["cantitate"] * i["pret"] for i in st.session_state.buffer_pranz)
                        db.save_comanda_finala(999, st.session_state.buffer_pranz, total_lot,
                                               "INTERN", "12:00", "Lot Producție Prânz",
                                               "cantina", "pranz", data_plan)
                        st.session_state.buffer_pranz = []
                        st.rerun()

    # ── CINĂ ─────────────────────────────────────────────────
    loturi_cina = loturi_lansate.get("cina", [])
    status_cina = "  ✅ Lansat" if loturi_cina else "  ⏳ Nelansat"
    with st.expander(f"🌙 LANSARE PRODUCȚIE CINĂ{status_cina}", expanded=False):
        if loturi_cina:
            for lot in loturi_cina:
                if _card_lot(lot, "cina", label="Lot Cină"):
                    db.delete_comanda(lot["comanda_id"])
                    st.rerun()
        else:
            m_c = db.get_meniu_planificat(data_plan, tip_plan="cina")
            if not m_c:
                st.warning("⚠️ Plan cină lipsă pentru această zi!")
            else:
                if "buffer_cina" not in st.session_state:
                    st.session_state.buffer_cina = []

                prod_ales_c  = st.selectbox("Alege felul (Cină):", m_c,
                                             format_func=lambda x: x["nume"], key="sel_cina_prod_v3")
                qty_aleasa_c = st.number_input("Nr. porții:", min_value=1, step=1, value=1, key="qty_cina_val_v3")

                if st.button("➕ Adaugă la Lot Cină", key="btn_add_cina_v3", use_container_width=True):
                    ex = next((i for i in st.session_state.buffer_cina if i["id"] == prod_ales_c["id"]), None)
                    if ex:
                        ex["cantitate"] += qty_aleasa_c
                    else:
                        st.session_state.buffer_cina.append({
                            "id": prod_ales_c["id"], "nume": prod_ales_c["nume"],
                            "cantitate": qty_aleasa_c, "pret": prod_ales_c.get("pret_standard", 0)
                        })

                if st.session_state.buffer_cina:
                    st.markdown("---")
                    for i, item in enumerate(st.session_state.buffer_cina):
                        c_txt, c_del = st.columns([4, 1])
                        c_txt.write(f"**{item['cantitate']}** x {item['nume']} ({item['pret']} lei/buc)")
                        if c_del.button("❌", key=f"del_cina_item_v3_{i}"):
                            st.session_state.buffer_cina.pop(i)
                    col_confirm, col_clear = st.columns(2)
                    with col_confirm:
                        if st.button("🚀 Confirmă Producție Cină", type="primary", use_container_width=True):
                            total_cina = sum(i["cantitate"] * i.get("pret", 0) for i in st.session_state.buffer_cina)
                            db.save_comanda_finala(999, st.session_state.buffer_cina, total_cina,
                                                   "INTERN", "19:00", "Lot Producție Cină",
                                                   "cantina", "cina", data_plan)
                            st.session_state.buffer_cina = []
                            st.rerun()
                    with col_clear:
                        if st.button("🗑️ Golește lista", key="clear_cina_all_v3", use_container_width=True):
                            st.session_state.buffer_cina = []

    # ── SPECIAL / EVENIMENT ───────────────────────────────────
    loturi_spec_ev = loturi_lansate.get("special", []) + loturi_lansate.get("eveniment", [])
    status_spec    = f"  ✅ {len(loturi_spec_ev)} lansat(e)" if loturi_spec_ev else ""
    with st.expander(f"✨ LANSARE COMANDĂ SPECIALĂ (PROTOCOL / EVENIMENT){status_spec}", expanded=False):
        if loturi_spec_ev:
            st.markdown("**Comenzi speciale lansate:**")
            for lot in loturi_spec_ev:
                _card_lot(lot, "spec", label=lot.get("detalii") or lot["status"].upper())
            st.divider()

        tip_spec  = st.radio("Tip:", ["special", "eveniment"], horizontal=True, key="rad_spec")
        desc_spec = st.text_input("📍 Descriere OBLIGATORIE (ex: Botez Popescu):", key="obs_spec")

        if "buffer_special" not in st.session_state:
            st.session_state.buffer_special = []

        categorii = sorted({p["categorie"] for p in toate if p.get("categorie")})
        c1, c2, c3, c4 = st.columns([2, 3, 1, 1])
        with c1: cat_sel = st.selectbox("Categorie:", categorii, key="spec_cat")
        with c2:
            produse_cat = [p for p in toate if p.get("categorie") == cat_sel]
            p_sel = st.selectbox("Produs:", produse_cat, format_func=lambda x: x["nume"], key="p_spec")
        with c3: q_sel = st.number_input("Cant:", min_value=1, value=1, key="q_spec")
        with c4:
            st.write("##")
            if st.button("➕ Adaugă", key="btn_add_spec", use_container_width=True):
                if p_sel:
                    st.session_state.buffer_special.append({
                        "id": p_sel["id"], "nume": p_sel["nume"],
                        "cantitate": q_sel, "pret": p_sel.get("pret_standard") or 0
                    })

        if st.session_state.buffer_special:
            st.markdown("---")
            for i, item in enumerate(st.session_state.buffer_special):
                col_t, col_r = st.columns([4, 1])
                col_t.write(f"✅ {item['nume']} x {item['cantitate']} ({item['pret']} lei/buc)")
                if col_r.button("🗑️", key=f"del_spec_{i}"):
                    st.session_state.buffer_special.pop(i)
            if st.button(f"🚀 Lansează {tip_spec.upper()}", use_container_width=True, type="primary"):
                if not desc_spec:
                    st.error("⚠️ Lipsește descrierea!")
                else:
                    total_spec = sum(i["cantitate"] * i.get("pret", 0) for i in st.session_state.buffer_special)
                    db.save_comanda_finala(999, st.session_state.buffer_special, total_spec,
                                           "INTERN", "08:00", desc_spec, "cantina", tip_spec, data_plan)
                    st.session_state.buffer_special = []
                    st.rerun()
