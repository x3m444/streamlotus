"""
bucatarie/gatire.py
--------------------
TAB Gătire — bucatarul vede ce are de gatit:
  - Loturi lansate de admin, agregate pe produs
  - Comenzi speciale de la receptie (tip_linie='special')
Poate marca fiecare produs ca GATIT / Reset.
"""

import streamlit as st
import database as db


@st.fragment
def show(data_selectata, engine):
    st.subheader("🔥 Ce gătim azi")

    loturi = db.get_loturi_productie(data_selectata)

    # -------------------------------------------------------
    # 1. LOTURI ADMIN — agregate pe produs
    # -------------------------------------------------------
    if not loturi:
        st.info("Adminul nu a lansat niciun lot pentru această zi.")
    else:
        produse_totale = {}

        for lot in loturi:
            detalii = lot.get('detalii') or ""
            for parte in detalii.split(', '):
                try:
                    produs_info, status = parte.split('|')
                    qty_str, nume = produs_info.split('x ', 1)
                    nume = nume.strip()
                    qty = int(qty_str.strip())

                    if nume not in produse_totale:
                        produse_totale[nume] = {"nou": 0, "gatit": 0}
                    produse_totale[nume][status] += qty
                except Exception:
                    continue

        if not produse_totale:
            st.warning("Loturile nu conțin produse valide.")
        else:
            st.caption(f"Loturi active: {len(loturi)} | Tipuri de produse: {len(produse_totale)}")

            for nume, info in produse_totale.items():
                total = info['nou'] + info['gatit']
                toate_gata = (info['nou'] == 0)

                with st.container(border=True):
                    col_info, col_btn = st.columns([3, 1])

                    with col_info:
                        if toate_gata:
                            st.markdown(f"### ✅ :green[{nume}]")
                            st.write(f"Toate cele **{info['gatit']}** porții sunt finalizate.")
                        else:
                            st.markdown(f"### 🔥 {nume}")
                            progres = info['gatit'] / total if total > 0 else 0
                            st.progress(progres)
                            st.write(
                                f"De gătit: **{info['nou']}** | "
                                f"Gata: {info['gatit']} | "
                                f"Total: {total}"
                            )

                    with col_btn:
                        st.write("")
                        if not toate_gata:
                            if st.button(
                                f"✅ Gata {nume}",
                                key=f"btn_gatit_{nume}",
                                width="stretch",
                            ):
                                db.update_status_batch(engine, data_selectata, nume, "gatit")
                                st.rerun()
                        else:
                            if st.button(
                                f"🔄 Reset {nume}",
                                key=f"btn_reset_{nume}",
                                width="stretch"
                            ):
                                db.update_status_batch(engine, data_selectata, nume, "nou")
                                st.rerun()

    # -------------------------------------------------------
    # 2. COMENZI SPECIALE DE LA RECEPTIE
    # -------------------------------------------------------
    st.divider()
    st.subheader("✨ Comenzi Speciale (direct de la Recepție)")
    st.caption("Produse care nu sunt in meniul zilei — apar automat fara sa fie lansate de admin.")

    produse_speciale = db.get_produse_speciale_zi(data_selectata)

    if not produse_speciale:
        st.info("Nicio comandă specială de la recepție pentru această dată.")
    else:
        for rand in produse_speciale:
            nume  = rand['nume_produs']
            nou   = rand['nou']
            gatit = rand['gatit']
            total = nou + gatit
            toate_gata = (nou == 0)

            with st.container(border=True):
                col_info, col_btn = st.columns([3, 1])

                with col_info:
                    if toate_gata:
                        st.markdown(f"### ✅ :green[{nume}]")
                        st.write(f"Toate cele **{gatit}** porții sunt finalizate.")
                    else:
                        st.markdown(f"### ✨ {nume}")
                        progres = gatit / total if total > 0 else 0
                        st.progress(progres)
                        st.write(
                            f"De gătit: **{nou}** | "
                            f"Gata: {gatit} | "
                            f"Total: {total} | "
                            f"({rand['nr_comenzi']} comenzi)"
                        )

                with col_btn:
                    st.write("")
                    if not toate_gata:
                        if st.button(
                            f"✅ Gata {nume}",
                            key=f"btn_spec_gatit_{nume}",
                            width="stretch",
                        ):
                            db.update_status_batch(engine, data_selectata, nume, "gatit")
                            st.rerun()
                    else:
                        if st.button(
                            f"🔄 Reset {nume}",
                            key=f"btn_spec_reset_{nume}",
                            width="stretch"
                        ):
                            db.update_status_batch(engine, data_selectata, nume, "nou")
                            st.rerun()
