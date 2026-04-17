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
                    st.session_state.bon_buffer.append({
                        "label": f"📦 {label_buf}",
                        "produse": [{"nume_produs": p['nume'], "cantitate": 1,
                                     "din_nevandut": False} for p in comp[tip]],
                        "din_buffer": True,
                        "tip_meniu": tip,
                    })
                    st.rerun()
        st.divider()

    if not gatite:
        st.info("⏳ Bucătăria nu a marcat încă niciun produs ca gătit. Reîncarcă pagina când mâncarea e gata.")
        return

    if 'bon_buffer' not in st.session_state:
        st.session_state.bon_buffer = []

    def adauga_grup(label, componente, din_nevandut=False):
        """Adauga un grup (meniu sau portie solo) ca un singur item in bon."""
        st.session_state.bon_buffer.append({
            "label": label,
            "produse": [{"nume_produs": p['nume'], "cantitate": 1,
                         "din_nevandut": din_nevandut} for p in componente]
        })

    def buton_produs(produs, key, icon="🍽️"):
        nume = produs['nume']
        disponibil = nume in gatite and stoc.get(nume, {}).get('ramas', 0) > 0
        stare = 'gata' if disponibil else ('⏳ negatit' if nume not in gatite else '❌ epuizat')
        if st.button(f"{icon} {nume}\n({stare})", key=key,
                     use_container_width=True, disabled=not disponibil):
            adauga_grup(f"{icon} {nume}", [produs])
            st.rerun()

    f1    = lista_f1[0]    if lista_f1           else None
    f2v1  = lista_f2[0]    if len(lista_f2) >= 1 else None
    f2v2  = lista_f2[1]    if len(lista_f2) >= 2 else None
    salata = lista_salate[0] if lista_salate      else None

    def meniu_disponibil(componente):
        return all(p['nume'] in gatite and stoc.get(p['nume'], {}).get('ramas', 0) > 0
                   for p in componente if p)

    # --- Meniuri complete
    st.markdown("**🍱 Meniu complet:**")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        componente_v1 = [p for p in [f1, f2v1, salata] if p]
        disponibil_v1 = meniu_disponibil(componente_v1)
        label_v1 = " + ".join(p['nume'] for p in componente_v1)
        if st.button(label_v1, key="bon_meniu_v1",
                     use_container_width=True, disabled=not disponibil_v1):
            adauga_grup(f"🍱 {label_v1}", componente_v1)
            st.rerun()

    with col_v2:
        componente_v2 = [p for p in [f1, f2v2, salata] if p]
        disponibil_v2 = meniu_disponibil(componente_v2)
        label_v2 = " + ".join(p['nume'] for p in componente_v2)
        if st.button(label_v2, key="bon_meniu_v2",
                     use_container_width=True, disabled=not disponibil_v2):
            adauga_grup(f"🍱 {label_v2}", componente_v2)
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

    # --- Bon curent — un buton per grup, apesi ca sa stergi
    if st.session_state.bon_buffer:
        st.divider()
        st.markdown("**Bon curent:**")
        for i, grup in enumerate(st.session_state.bon_buffer):
            if st.button(f"🗑️ {grup['label']}", key=f"del_bon_{i}",
                         use_container_width=True):
                st.session_state.bon_buffer.pop(i)
                st.rerun()

        col_conf, col_clear = st.columns(2)
        with col_conf:
            if st.button("✅ Confirmă Servirea", type="primary", use_container_width=True):
                grupuri_buffer  = [g for g in st.session_state.bon_buffer if g.get('din_buffer')]
                grupuri_normale = [g for g in st.session_state.bon_buffer if not g.get('din_buffer')]

                if grupuri_normale:
                    produse_normale = [p for g in grupuri_normale for p in g['produse']]
                    db.save_servire(data_azi, 'bon_casa', produse_normale)

                for g in grupuri_buffer:
                    db.distribuie_din_buffer(data_azi, g['tip_meniu'])

                st.session_state.bon_buffer = []
                st.success("Servit!")
                st.rerun()
        with col_clear:
            if st.button("🗑️ Golește", use_container_width=True):
                st.session_state.bon_buffer = []
                st.rerun()
