"""
ghiseu/bon_casa.py
-------------------
TAB Bon Casă — clientul anonim a platit la casa.
Ghiseul selecteaza ce a cumparat si confirma servirea.
Consuma din stocul zilei (verifica gatit + stoc disponibil).
"""

import streamlit as st
import database as db


def show(data_azi):
    st.subheader("🧾 Servire cu Bon de Casă")
    st.caption("Clientul a plătit la casă. Selectează ce a cumpărat și confirmă servirea.")

    plan_zi    = db.get_meniu_planificat(data_azi)
    stoc       = db.get_stoc_zi(data_azi)
    gatite     = db.get_produse_gatite_azi(data_azi)
    comp       = db._plan_to_componente(plan_zi)
    buffer_azi = db.get_buffer_ambalare(data_azi)

    lista_f1     = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2     = [p for p in plan_zi if p['categorie'] == 'felul_2']
    lista_salate = [p for p in plan_zi if p['categorie'] == 'salate']

    if not lista_f1 and not lista_f2:
        st.warning("Nu există meniu planificat pentru astăzi.")
        return

    # -------------------------------------------------------
    # SECTIUNEA BUFFER — portii pre-ambalate de bucatarie
    # -------------------------------------------------------
    TIP_ETICHETE_BUF = {
        'v1': 'Meniu V1', 'v2': 'Meniu V2',
        'solo_f1': 'Solo F1', 'solo_f2v1': 'Solo F2 v1',
        'solo_f2v2': 'Solo F2 v2', 'solo_salata': 'Solo Salată',
    }
    tipuri_cu_buffer = [
        t for t in db.TIP_MENIU_KEYS
        if buffer_azi.get(t, {}).get('disponibil', 0) > 0 and comp.get(t)
    ]
    if tipuri_cu_buffer:
        st.markdown("**📦 Meniu pre-ambalat (din buffer):**")
        cols_buf = st.columns(len(tipuri_cu_buffer))
        for col, tip in zip(cols_buf, tipuri_cu_buffer):
            disponibil = buffer_azi[tip]['disponibil']
            label_buf  = " + ".join(p['nume'] for p in comp[tip])
            with col:
                if st.button(
                    f"📦 {label_buf}\n({disponibil} disponibile)",
                    key=f"bon_buf_{tip}", use_container_width=True, type="primary"
                ):
                    ok = db.distribuie_din_buffer(data_azi, tip)
                    if ok:
                        st.success(f"Servit din buffer: {TIP_ETICHETE_BUF.get(tip, tip)}")
                        st.rerun()
                    else:
                        st.error("Buffer epuizat!")
        st.divider()

    if not gatite:
        st.info("⏳ Bucătăria nu a marcat încă niciun produs ca gătit. Reîncarcă pagina când mâncarea e gata.")
        return

    if 'bon_buffer' not in st.session_state:
        st.session_state.bon_buffer = []

    def adauga_bon(nume, qty=1, din_nevandut=False):
        for item in st.session_state.bon_buffer:
            if item['nume_produs'] == nume and item['din_nevandut'] == din_nevandut:
                item['cantitate'] += qty
                return
        st.session_state.bon_buffer.append({
            "nume_produs": nume,
            "cantitate": qty,
            "din_nevandut": din_nevandut
        })

    def buton_produs(produs, key, icon="🍽️"):
        nume = produs['nume']
        este_gatit = nume in gatite
        ramas = stoc.get(nume, {}).get('ramas', 0)
        disponibil = este_gatit and ramas > 0

        label = f"{icon} {nume}\n({'gata' if disponibil else ('⏳ negatit' if not este_gatit else '❌ stoc epuizat')})"
        if st.button(label, key=key, use_container_width=True, disabled=not disponibil):
            adauga_bon(nume)
            st.rerun()

    f1    = lista_f1[0]    if lista_f1           else None
    f2v1  = lista_f2[0]    if len(lista_f2) >= 1 else None
    f2v2  = lista_f2[1]    if len(lista_f2) >= 2 else None
    salata = lista_salate[0] if lista_salate      else None

    def meniu_disponibil(componente):
        return all(p['nume'] in gatite and stoc.get(p['nume'], {}).get('ramas', 0) > 0 for p in componente if p)

    # --- Meniuri complete
    st.markdown("**🍱 Meniu complet:**")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        componente_v1 = [p for p in [f1, f2v1, salata] if p]
        disponibil_v1 = meniu_disponibil(componente_v1)
        if st.button(
            " + ".join(p['nume'] for p in componente_v1),
            key="bon_meniu_v1", use_container_width=True, disabled=not disponibil_v1
        ):
            for p in componente_v1:
                adauga_bon(p['nume'])
            st.rerun()

    with col_v2:
        componente_v2 = [p for p in [f1, f2v2, salata] if p]
        disponibil_v2 = meniu_disponibil(componente_v2)
        if st.button(
            " + ".join(p['nume'] for p in componente_v2),
            key="bon_meniu_v2", use_container_width=True, disabled=not disponibil_v2
        ):
            for p in componente_v2:
                adauga_bon(p['nume'])
            st.rerun()

    # --- Portii solo
    st.markdown("**🍽️ Porție solo:**")
    cols_solo = st.columns(4)
    produse_solo = [
        (f1,    "🥣", "bon_f1"),
        (f2v1,  "🍖", "bon_f2v1"),
        (f2v2,  "🍖", "bon_f2v2"),
        (salata,"🥗", "bon_salata"),
    ]
    for col, (produs, icon, key) in zip(cols_solo, produse_solo):
        with col:
            if produs:
                buton_produs(produs, key=key, icon=icon)

    # --- Bon curent
    if st.session_state.bon_buffer:
        st.divider()
        st.markdown("**Bon curent:**")
        for i, item in enumerate(st.session_state.bon_buffer):
            c1, c2 = st.columns([6, 1])
            prefix = '🔄 ' if item['din_nevandut'] else ''
            c1.markdown(f"{prefix}**{item['nume_produs']}** — x{item['cantitate']}")
            if c2.button("❌", key=f"del_bon_{i}", use_container_width=True):
                st.session_state.bon_buffer.pop(i)
                st.rerun()

        col_conf, col_clear = st.columns(2)
        with col_conf:
            if st.button("✅ Confirmă Servirea", type="primary", use_container_width=True):
                db.save_servire(data_azi, 'bon_casa', st.session_state.bon_buffer)
                st.session_state.bon_buffer = []
                st.success("Servit!")
                st.rerun()
        with col_clear:
            if st.button("🗑️ Golește", use_container_width=True):
                st.session_state.bon_buffer = []
                st.rerun()
