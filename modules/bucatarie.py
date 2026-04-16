"""
modules/bucatarie.py
---------------------
Ecranul bucatariei — doua tab-uri cu roluri distincte:

  TAB 1 — GATIRE
    Bucatarul vede CE are de gatit:
      - Loturile lansate de admin (pranz, cina, sandwich, eveniment intern)
        → afisate agregat pe produs: "100x Ciorba de vacuta — 0 gata"
      - Comenzi speciale de la receptie (tip_comanda: special / eveniment)
        → afisate individual, pe comanda
    Poate marca fiecare produs ca "GATIT" (batch update pe toata ziua).
    Marcarea unui produs ca "gatit" actualizeaza si liniile din comenzile
    clientilor — impachetarea devine deblocata automat.

  TAB 2 — IMPACHETARE
    Echipa de ambalare vede comenzile REALE de la clienti (receptie).
    O comanda poate fi ambalata DOAR cand toate produsele ei sunt "gatit".
    Dupa ambalare, comanda primeste status "pregatit" si dispare din flux.
"""

import streamlit as st
import database as db
from datetime import date


engine = db.get_engine()


def show_bucatarie():
    st.header("👨‍🍳 Monitor Producție și Expediție")

    data_selectata = st.date_input("Comenzi pentru data:", value=date.today(), key="buc_data")

    tab_gatire, tab_impachetare = st.tabs([
        "🔥 Gatire (Loturi Producție)",
        "📦 Impachetare (Comenzi Clienți)"
    ])

    # =========================================================
    # TAB 1 — GATIRE
    # Ce are de gatit bucatarul azi
    # =========================================================
    with tab_gatire:
        _render_gatire(data_selectata)

    # =========================================================
    # TAB 2 — IMPACHETARE
    # Comenzile clientilor, gata de ambalat
    # =========================================================
    with tab_impachetare:
        _render_impachetare(data_selectata)


# ---------------------------------------------------------
# SECTIUNEA: GATIRE
# ---------------------------------------------------------
def _render_gatire(data_selectata):
    """
    Afiseaza ce are de gatit bucatarul:
      1. Loturile lansate de admin — agregate pe produs
      2. Comenzile speciale de la receptie — individuale
    """
    st.subheader("🔥 Ce gătim azi")

    loturi = db.get_loturi_productie(data_selectata)

    # -------------------------------------------------------
    # 1. LOTURI ADMIN — agregate pe produs
    # -------------------------------------------------------
    if not loturi:
        st.info("Adminul nu a lansat niciun lot pentru această zi.")
    else:
        # Agregam toate produsele din toate loturile zilei
        # { "Ciorba de vacuta": {"nou": 80, "gatit": 20, "total": 100} }
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
                        st.write("")  # spatiu vertical
                        if not toate_gata:
                            if st.button(
                                f"✅ Gata {nume}",
                                key=f"btn_gatit_{nume}",
                                use_container_width=True,
                            ):
                                # Batch update: marcheaza TOATE liniile cu acest produs
                                # din TOATE comenzile zilei (loturi + comenzi clienti)
                                db.update_status_batch(engine, data_selectata, nume, "gatit")
                                st.rerun()
                        else:
                            if st.button(
                                f"🔄 Reset {nume}",
                                key=f"btn_reset_{nume}",
                                use_container_width=True
                            ):
                                db.update_status_batch(engine, data_selectata, nume, "nou")
                                st.rerun()

    # -------------------------------------------------------
    # 2. COMENZI SPECIALE DE LA RECEPTIE
    # Apar automat fara ca adminul sa lanseze manual.
    # tip_comanda: 'special' sau 'eveniment', client real (nu 999)
    # -------------------------------------------------------
    st.divider()
    st.subheader("✨ Comenzi Speciale (direct de la Recepție)")
    st.caption("Produse care nu sunt in meniul zilei — apar automat fara sa fie lansate de admin.")

    # get_produse_speciale_zi returneaza doar liniile cu tip_linie='special'
    # din comenzile clientilor reali — agregat pe produs
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
                            use_container_width=True,
                        ):
                            db.update_status_batch(engine, data_selectata, nume, "gatit")
                            st.rerun()
                    else:
                        if st.button(
                            f"🔄 Reset {nume}",
                            key=f"btn_spec_reset_{nume}",
                            use_container_width=True
                        ):
                            db.update_status_batch(engine, data_selectata, nume, "nou")
                            st.rerun()


# ---------------------------------------------------------
# SECTIUNEA: IMPACHETARE
# ---------------------------------------------------------
def _render_impachetare(data_selectata):
    """
    Afiseaza comenzile reale ale clientilor (de la receptie).
    O comanda poate fi ambalata DOAR cand toate produsele sunt 'gatit'.
    Dupa ambalare → status = 'pregatit' → dispare din flux.
    """
    st.subheader("📦 Comenzi de Ambalat")

    # Luam comenzile cu status 'nou' de la clienti reali
    comenzi = db.get_comenzi_receptie(data_selectata, status_filtru='nou')

    if not comenzi:
        st.success("✅ Nicio comandă în așteptare. Toate au fost ambalate!")
        return

    # Contor rapid: cate sunt gata vs cate asteapta
    gata_count = sum(
        1 for c in comenzi
        if c.get('detalii') and all('|gatit' in l for l in c['detalii'].split(', '))
    )
    st.caption(f"Total comenzi: {len(comenzi)} | Gata de ambalat: {gata_count} | În așteptare: {len(comenzi) - gata_count}")

    for cmd in comenzi:
        detalii_str = cmd.get('detalii') or ""
        linii = detalii_str.split(', ') if detalii_str else []

        nr_total = len(linii)
        nr_gatite = sum(1 for l in linii if '|gatit' in l)
        toate_gata = (nr_total > 0 and nr_total == nr_gatite)

        # Titlul expanderului arata statusul rapid
        icon = "🟢" if toate_gata else "🟡"
        status_txt = "GATA DE AMBALAT" if toate_gata else f"ASTEAPTA ({nr_gatite}/{nr_total} gatite)"
        ora = str(cmd.get('ora_livrare_estimata', ''))[:5]
        titlu = f"{icon} {status_txt} | #{cmd['id']} — {cmd['client']} | ora {ora}"

        # Comenzile gata se deschid automat
        with st.expander(titlu, expanded=toate_gata):
            col_produse, col_actiuni = st.columns([3, 1])

            with col_produse:
                st.write("**Produse:**")
                for linie in linii:
                    try:
                        produs_txt, stare = linie.split('|')
                        if stare == 'gatit':
                            st.markdown(f"✅ {produs_txt}")
                        else:
                            st.markdown(f"⏳ :red[{produs_txt}] — în bucătărie")
                    except Exception:
                        st.write(f"• {linie}")

                st.caption(
                    f"📞 {cmd.get('telefon', 'N/A')} | "
                    f"📍 {cmd.get('adresa_principala', 'N/A')} | "
                    f"💳 {cmd.get('metoda_plata', '').upper()}"
                )

            with col_actiuni:
                st.write("")  # spatiu vertical
                if toate_gata:
                    if st.button(
                        "📦 Ambalat!",
                        key=f"pack_{cmd['id']}",
                        use_container_width=True,
                    ):
                        db.update_status_comanda(engine, cmd['id'], 'pregatit')
                        st.success(f"Comanda #{cmd['id']} marcată ca PREGĂTITĂ!")
                        st.rerun()
                else:
                    st.button(
                        "⏳ Așteaptă",
                        key=f"wait_{cmd['id']}",
                        disabled=True,
                        use_container_width=True,
                        help="Asteapta ca bucatarul sa marcheze toate produsele ca gatite"
                    )
