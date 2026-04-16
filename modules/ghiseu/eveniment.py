"""
ghiseu/eveniment.py
--------------------
TAB Eveniment — servire din loturi speciale lansate de admin.
Selectezi lotul, numeri portiile servite.
"""

import streamlit as st
import database as db


def show(data_azi):
    st.subheader("🎉 Servire Eveniment")

    loturi = db.get_loturi_eveniment(data_azi)
    if not loturi:
        st.info("Nu există loturi de eveniment lansate pentru astăzi. Adminul trebuie să lanseze o comandă specială.")
        return

    lot_sel = st.selectbox(
        "Selectează evenimentul:",
        loturi,
        format_func=lambda x: f"{x['tip_comanda'].upper()} — {x['descriere']}",
        key="eveniment_selectat"
    )

    if not lot_sel:
        return

    st.markdown(f"**Produse în lot:** {lot_sel['produse']}")

    serviri_existente = db.get_serviri_eveniment_azi(lot_sel['id'], data_azi)

    if serviri_existente:
        st.markdown("**Servit până acum:**")
        for nume, total in serviri_existente.items():
            st.write(f"• {nume}: {total} porții")

    st.divider()
    st.markdown("**Înregistrează servire:**")

    produse_lot = []
    for parte in (lot_sel['produse'] or '').split(', '):
        try:
            qty_str, nume = parte.split('x ', 1)
            produse_lot.append({'nume': nume.strip(), 'qty_lot': int(qty_str.strip())})
        except Exception:
            continue

    if not produse_lot:
        st.warning("Lotul nu are produse valide.")
        return

    with st.form(f"form_ev_{lot_sel['id']}"):
        serviri_form = []
        for p in produse_lot:
            deja_servit = serviri_existente.get(p['nume'], 0)
            ramas = p['qty_lot'] - deja_servit
            qty = st.number_input(
                f"{p['nume']} (rămas: {ramas})",
                min_value=0,
                max_value=max(ramas, 0),
                value=0,
                step=1,
                key=f"ev_qty_{p['nume']}"
            )
            serviri_form.append({'nume_produs': p['nume'], 'cantitate': qty, 'din_nevandut': False})

        if st.form_submit_button("✅ Confirmă Servire Eveniment", use_container_width=True, type="primary"):
            produse_de_salvat = [p for p in serviri_form if p['cantitate'] > 0]
            if produse_de_salvat:
                db.save_servire(data_azi, 'eveniment', produse_de_salvat, comanda_ref_id=lot_sel['id'])
                st.success("Servire înregistrată!")
                st.rerun()
            else:
                st.warning("Introduceți cel puțin o cantitate.")
