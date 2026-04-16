"""
modules/ghiseu.py
------------------
Ecranul ghișeului — 3 scenarii de servire:

  TAB 1 — BON CASĂ
    Clientul anonim vine cu bon plătit.
    Ghișeul selectează ce a cumpărat → consumă din stoc.

  TAB 2 — FIRME
    Firma selectată → lista angajaților activi.
    Bifă rapidă "Servit". Posibilitate de a oferi nevândute.
    Vânzătorul poate adăuga angajați noi sau dezactiva (concediu etc.)

  TAB 3 — EVENIMENT
    Selectezi lotul special lansat de admin.
    Numeri ce servești din acel lot.
"""

import streamlit as st
import database as db
import utils


def show_ghiseu():
    st.title("🏪 Ghișeu Servire")
    data_azi = utils.get_ro_time().date()
    st.caption(f"Data: {data_azi.strftime('%d.%m.%Y')}")

    tab_bon, tab_firme, tab_eveniment = st.tabs([
        "🧾 Bon Casă",
        "🏢 Firme",
        "🎉 Eveniment"
    ])

    with tab_bon:
        _render_bon_casa(data_azi)

    with tab_firme:
        _render_firme(data_azi)

    with tab_eveniment:
        _render_eveniment(data_azi)


# ----------------------------------------------------------
# TAB 1: BON CASĂ
# ----------------------------------------------------------
def _render_bon_casa(data_azi):
    st.subheader("🧾 Servire cu Bon de Casă")
    st.caption("Clientul a plătit la casă. Selectează ce a cumpărat și confirmă servirea.")

    plan_zi = db.get_meniu_planificat(data_azi)
    stoc = db.get_stoc_zi(data_azi)

    lista_f1 = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2 = [p for p in plan_zi if p['categorie'] == 'felul_2']

    if not lista_f1 and not lista_f2:
        st.warning("Nu există meniu planificat pentru astăzi.")
        return

    if 'bon_buffer' not in st.session_state:
        st.session_state.bon_buffer = []

    # Butoane rapide meniu
    st.markdown("**Adaugă în bon:**")
    col1, col2, col3 = st.columns(3)

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

    with col1:
        if lista_f1:
            f1 = lista_f1[0]
            stoc_f1 = stoc.get(f1['nume'], {}).get('ramas', 0)
            if st.button(f"🥣 {f1['nume']}\n({stoc_f1} porții)", use_container_width=True, key="bon_f1"):
                adauga_bon(f1['nume'])
                st.rerun()

    with col2:
        if lista_f2:
            f2 = lista_f2[0]
            stoc_f2 = stoc.get(f2['nume'], {}).get('ramas', 0)
            if st.button(f"🍖 {f2['nume']}\n({stoc_f2} porții)", use_container_width=True, key="bon_f2v1"):
                adauga_bon(f2['nume'])
                st.rerun()

    with col3:
        if len(lista_f2) >= 2:
            f2v2 = lista_f2[1]
            stoc_f2v2 = stoc.get(f2v2['nume'], {}).get('ramas', 0)
            if st.button(f"🍖 {f2v2['nume']}\n({stoc_f2v2} porții)", use_container_width=True, key="bon_f2v2"):
                adauga_bon(f2v2['nume'])
                st.rerun()

    # Bon curent
    if st.session_state.bon_buffer:
        st.divider()
        st.markdown("**Bon curent:**")
        for i, item in enumerate(st.session_state.bon_buffer):
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"{'🔄' if item['din_nevandut'] else ''} {item['nume_produs']}")
            c2.write(f"x{item['cantitate']}")
            if c3.button("❌", key=f"del_bon_{i}"):
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


# ----------------------------------------------------------
# TAB 2: FIRME
# ----------------------------------------------------------
def _render_firme(data_azi):
    st.subheader("🏢 Servire Firme cu Contract")

    firme = db.get_all_firme(doar_active=True)
    if not firme:
        st.info("Nu există firme active. Adminul trebuie să adauge firme cu contract.")
        return

    firma_sel = st.selectbox(
        "Selectează firma:",
        firme,
        format_func=lambda x: x['nume_firma'],
        key="firma_selectata"
    )

    if not firma_sel:
        return

    firma_id = firma_sel['id']
    nevandut = db.get_stoc_nevandut(data_azi)
    are_nevandut = any(v['ramas'] > 0 for v in nevandut.values())
    serviti_azi = db.get_angajati_serviti_azi(firma_id, data_azi)

    st.divider()

    # Adaugă angajat nou — inline, fără a ieși din ecran
    with st.expander("➕ Angajat nou"):
        col_n, col_btn = st.columns([3, 1])
        nou_nume = col_n.text_input("Nume angajat:", key="nou_angajat_nume", label_visibility="collapsed", placeholder="Nume și prenume")
        with col_btn:
            st.write("")
            if st.button("Adaugă", key="btn_add_angajat", use_container_width=True):
                if nou_nume.strip():
                    db.add_angajat(firma_id, nou_nume.strip())
                    st.success(f"Adăugat: {nou_nume.strip()}")
                    st.rerun()

    # Lista angajaților (toți — activi + inactivi pentru management)
    toti_angajatii = db.get_angajati_firma(firma_id, doar_activi=False)

    if not toti_angajatii:
        st.info("Firma nu are angajați înregistrați. Adaugă mai sus.")
        return

    activi = [a for a in toti_angajatii if a['activ']]
    inactivi = [a for a in toti_angajatii if not a['activ']]

    st.markdown(f"**Angajați activi ({len(activi)})** — bifează cine a mâncat:")

    for ang in activi:
        aid = ang['id']
        deja_servit = aid in serviti_azi

        with st.container(border=True):
            col_nume, col_nev, col_serv, col_dezact = st.columns([3, 2, 1.5, 1.5])

            with col_nume:
                if deja_servit:
                    st.markdown(f"✅ ~~{ang['nume_angajat']}~~")
                    st.caption("Servit azi")
                else:
                    st.write(f"👤 {ang['nume_angajat']}")

            with col_nev:
                if are_nevandut and not deja_servit:
                    optiuni_nev = {
                        f"{k} ({v['ramas']} porții)": k
                        for k, v in nevandut.items() if v['ramas'] > 0
                    }
                    nev_ales = st.selectbox(
                        "Oferă nevândut:",
                        ["— fără —"] + list(optiuni_nev.keys()),
                        key=f"nev_sel_{aid}",
                        label_visibility="collapsed"
                    )
                elif deja_servit:
                    st.write("")
                else:
                    st.caption("Fără nevândute")

            with col_serv:
                if not deja_servit:
                    if st.button("✅ Servit", key=f"serv_{aid}", use_container_width=True, type="primary"):
                        produse = [{"nume_produs": "Meniu firmă", "cantitate": 1, "din_nevandut": False}]
                        # Adauga nevandut daca a fost ales
                        nev_sel_val = st.session_state.get(f"nev_sel_{aid}", "— fără —")
                        if nev_sel_val != "— fără —" and are_nevandut:
                            nume_nev = optiuni_nev.get(nev_sel_val)
                            if nume_nev:
                                produse.append({"nume_produs": nume_nev, "cantitate": 1, "din_nevandut": True})
                        db.save_servire(data_azi, 'firma', produse, firma_id=firma_id, angajat_id=aid)
                        st.rerun()

            with col_dezact:
                if st.button("🔴 Concediu", key=f"dezact_{aid}", use_container_width=True):
                    db.toggle_angajat(aid, False)
                    st.rerun()

    # Angajați inactivi
    if inactivi:
        with st.expander(f"Inactivi / Concediu ({len(inactivi)})"):
            for ang in inactivi:
                col_n, col_act = st.columns([4, 1])
                col_n.write(f"💤 {ang['nume_angajat']}")
                if col_act.button("🟢 Reactivează", key=f"act_{ang['id']}", use_container_width=True):
                    db.toggle_angajat(ang['id'], True)
                    st.rerun()

    # Sumar serviri azi pentru firma
    st.divider()
    st.caption(f"Serviți azi din {firma_sel['nume_firma']}: {len(serviti_azi)} / {len(activi)} angajați activi")


# ----------------------------------------------------------
# TAB 3: EVENIMENT
# ----------------------------------------------------------
def _render_eveniment(data_azi):
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

    # Serviri deja înregistrate din acest lot
    serviri_existente = db.get_serviri_eveniment_azi(lot_sel['id'], data_azi)

    if serviri_existente:
        st.markdown("**Servit până acum:**")
        for nume, total in serviri_existente.items():
            st.write(f"• {nome}: {total} porții")

    st.divider()
    st.markdown("**Înregistrează servire:**")

    # Parsam produsele din lot
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
