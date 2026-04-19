"""
bucatarie/nevandut.py
----------------------
TAB Declară Nevândut — bucatarul declara stocul ramas neservit.
Ghiseul va putea oferi aceste portii angajatilor firmelor cu contract.
"""

import streamlit as st
import database as db


@st.fragment
def show(data_selectata):
    st.subheader("🍽️ Declară Stoc Nevândut")
    st.caption("Declară ce a rămas neservit. Ghișeul va putea oferi aceste porții angajaților firmelor.")

    stoc = db.get_stoc_zi(data_selectata)
    nevandut_curent = db.get_stoc_nevandut(data_selectata)

    if not stoc:
        st.info("Nu există stoc lansat pentru această dată.")
        return

    produse_ramase = {k: v for k, v in stoc.items() if v['ramas'] > 0}

    if not produse_ramase:
        st.success("✅ Tot stocul a fost ambalat/livrat. Nimic de declarat.")
    else:
        st.markdown("#### Stoc rămas disponibil")
        for nume, s in produse_ramase.items():
            deja_declarat = nevandut_curent.get(nume)
            with st.container(border=True):
                col_info, col_input, col_btn = st.columns([3, 1.5, 1.5])

                with col_info:
                    st.write(f"**{nume}**")
                    st.caption(f"Rămas în stoc: {s['ramas']} porții")
                    if deja_declarat:
                        ramas_nev = deja_declarat['ramas']
                        st.caption(
                            f"Declarat nevândut: {deja_declarat['cantitate']} | "
                            f"Servit: {deja_declarat['cantitate_servita']} | "
                            f"Disponibil: {ramas_nev}"
                        )

                with col_input:
                    qty = st.number_input(
                        "Porții nevândute:",
                        min_value=0,
                        max_value=s['ramas'],
                        value=deja_declarat['cantitate'] if deja_declarat else 0,
                        step=1,
                        key=f"nev_{nume}"
                    )

                with col_btn:
                    st.write("")
                    st.write("")
                    if st.button("💾 Salvează", key=f"btn_nev_{nume}", width="stretch"):
                        if qty > 0:
                            db.declara_nevandut(data_selectata, nume, qty)
                            st.success(f"Salvat: {qty} porții {nume}")
                        else:
                            db.sterge_nevandut(data_selectata, nume)
                            st.info(f"Șters: {nume}")
                        st.rerun()

    # Sumar nevandute declarate
    if nevandut_curent:
        st.divider()
        st.markdown("#### 📋 Nevândute declarate azi")
        total_nev = sum(v['cantitate'] for v in nevandut_curent.values())
        total_servit = sum(v['cantitate_servita'] for v in nevandut_curent.values())
        col1, col2, col3 = st.columns(3)
        col1.metric("Total declarat", f"{total_nev} porții")
        col2.metric("Servit din nevândute", f"{total_servit} porții")
        col3.metric("Disponibil ghișeu", f"{total_nev - total_servit} porții")
