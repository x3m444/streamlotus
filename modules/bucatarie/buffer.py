"""
bucatarie/buffer.py
--------------------
TAB Buffer Ambalare — bucataria pre-ambaleaza portii generice.
Ghiseul serveste din aceste portii pre-ambalate fara a mai astepta status 'gatit' individual.
"""

import streamlit as st
import database as db


TIP_ETICHETE = {
    'v1':          'Meniu V1',
    'v2':          'Meniu V2',
    'solo_f1':     'Solo Felul 1',
    'solo_f2v1':   'Solo Felul 2 (var.1)',
    'solo_f2v2':   'Solo Felul 2 (var.2)',
    'solo_salata': 'Solo Salată',
}


@st.fragment
def show(data_selectata):
    st.subheader("📦 Buffer Ambalare — Porții Pre-ambalate")
    st.caption(
        "Declarați câte porții din fiecare tip ați pre-ambalat. "
        "Ghișeul le va putea servi direct din acest buffer."
    )

    plan_zi    = db.get_meniu_planificat(data_selectata)
    comp       = db._plan_to_componente(plan_zi)
    buffer_azi = db.get_buffer_ambalare(data_selectata)

    if not plan_zi:
        st.warning("Nu există meniu planificat pentru această zi.")
        return

    # Afisam fiecare tip de meniu care are componente in planul zilei
    for tip in db.TIP_MENIU_KEYS:
        produse = comp.get(tip, [])
        if not produse:
            continue

        label = " + ".join(p['nume'] for p in produse)
        buf   = buffer_azi.get(tip, {'cantitate': 0, 'distribuit': 0, 'disponibil': 0})

        with st.container(border=True):
            col_label, col_cant, col_dist, col_dispon, col_input, col_btn = st.columns([3, 1, 1, 1, 1.5, 1.2])

            col_label.markdown(f"**{TIP_ETICHETE.get(tip, tip)}**")
            col_label.caption(label)

            col_cant.metric("Ambalate",   buf['cantitate'])
            col_dist.metric("Distribuite", buf['distribuit'])

            if buf['disponibil'] > 0:
                col_dispon.metric("Disponibile", buf['disponibil'])
            else:
                col_dispon.markdown(":orange[**0 disponibile**]")

            with col_input:
                qty = st.number_input(
                    "Qty", min_value=0, max_value=500, value=0,
                    step=1, key=f"buf_qty_{tip}",
                    label_visibility="collapsed"
                )

            with col_btn:
                st.write("")
                if st.button("➕ Adaugă", key=f"buf_add_{tip}", width="stretch",
                             disabled=(qty == 0)):
                    db.add_to_buffer(data_selectata, tip, qty)
                    st.success(f"+{qty} porții {TIP_ETICHETE.get(tip, tip)}")
                    st.rerun()

    st.divider()

    # Resetare / corectie — seteaza cantitate exacta
    with st.expander("✏️ Corecție — Setează cantitate exactă"):
        st.caption("Folosit pentru corectii (ex: unele portii s-au stricat).")
        tip_sel = st.selectbox(
            "Tip meniu:",
            [t for t in db.TIP_MENIU_KEYS if comp.get(t)],
            format_func=lambda t: TIP_ETICHETE.get(t, t),
            key="buf_corectie_tip"
        )
        qty_set = st.number_input(
            "Cantitate corectă:", min_value=0, max_value=500, step=1,
            key="buf_corectie_qty"
        )
        if st.button("💾 Setează", key="buf_corectie_btn", type="primary"):
            db.set_buffer(data_selectata, tip_sel, qty_set)
            st.success(f"Buffer setat: {TIP_ETICHETE.get(tip_sel, tip_sel)} = {qty_set}")
            st.rerun()
