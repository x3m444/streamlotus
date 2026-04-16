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
    gatite = db.get_produse_gatite_azi(data_azi)

    lista_f1     = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2     = [p for p in plan_zi if p['categorie'] == 'felul_2']
    lista_salate = [p for p in plan_zi if p['categorie'] == 'salate']

    if not lista_f1 and not lista_f2:
        st.warning("Nu există meniu planificat pentru astăzi.")
        return

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
        """Randeaza un buton pentru un produs — dezactivat daca nu e gatit sau stoc 0."""
        nume = produs['nume']
        este_gatit = nume in gatite
        ramas = stoc.get(nume, {}).get('ramas', 0)
        disponibil = este_gatit and ramas > 0

        label = f"{icon} {nume}\n({'gata' if disponibil else ('⏳ negatit' if not este_gatit else '❌ stoc epuizat')})"
        if st.button(label, key=key, use_container_width=True, disabled=not disponibil):
            adauga_bon(nume)
            st.rerun()

    # --- Meniuri complete (butoane compuse)
    st.markdown("**🍱 Meniu complet:**")
    col_v1, col_v2 = st.columns(2)

    f1    = lista_f1[0]    if lista_f1           else None
    f2v1  = lista_f2[0]    if len(lista_f2) >= 1 else None
    f2v2  = lista_f2[1]    if len(lista_f2) >= 2 else None
    salata = lista_salate[0] if lista_salate       else None

    def meniu_disponibil(componente):
        return all(p['nume'] in gatite and stoc.get(p['nume'], {}).get('ramas', 0) > 0 for p in componente if p)

    with col_v1:
        componente_v1 = [p for p in [f1, f2v1, salata] if p]
        disponibil_v1 = meniu_disponibil(componente_v1)
        if st.button(
            f"Meniu V1\n{' + '.join(p['nume'] for p in componente_v1)}",
            key="bon_meniu_v1", use_container_width=True, disabled=not disponibil_v1
        ):
            for p in componente_v1:
                adauga_bon(p['nume'])
            st.rerun()

    with col_v2:
        componente_v2 = [p for p in [f1, f2v2, salata] if p]
        disponibil_v2 = meniu_disponibil(componente_v2)
        if st.button(
            f"Meniu V2\n{' + '.join(p['nume'] for p in componente_v2)}",
            key="bon_meniu_v2", use_container_width=True, disabled=not disponibil_v2
        ):
            for p in componente_v2:
                adauga_bon(p['nume'])
            st.rerun()

    # --- Porții solo
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
            c1, c2, c3 = st.columns([4, 1, 1])
            c1.write(f"{'🔄 ' if item['din_nevandut'] else ''}{item['nume_produs']}")
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

    gatite = db.get_produse_gatite_azi(data_azi)
    if not gatite:
        st.info("⏳ Bucătăria nu a marcat încă niciun produs ca gătit. Reîncarcă pagina când mâncarea e gata.")
        return

    # Meniu zilei
    plan_zi      = db.get_meniu_planificat(data_azi)
    stoc         = db.get_stoc_zi(data_azi)
    nevandut     = db.get_stoc_nevandut(data_azi)
    lista_f1     = [p for p in plan_zi if p["categorie"] == "felul_1"]
    lista_f2     = [p for p in plan_zi if p["categorie"] == "felul_2"]
    lista_salate = [p for p in plan_zi if p["categorie"] == "salate"]

    f1     = lista_f1[0]     if lista_f1           else None
    f2v1   = lista_f2[0]     if len(lista_f2) >= 1 else None
    f2v2   = lista_f2[1]     if len(lista_f2) >= 2 else None
    salata = lista_salate[0] if lista_salate        else None

    def componente_disponibile(componente):
        return all(
            p and p["nume"] in gatite and stoc.get(p["nume"], {}).get("ramas", 0) > 0
            for p in componente
        )

    # Optiunile de meniu disponibile
    optiuni_meniu = {}
    if f1 and f2v1:
        comps_v1 = [p for p in [f1, f2v1, salata] if p]
        if componente_disponibile(comps_v1):
            optiuni_meniu["Meniu Complet V1"] = comps_v1
    if f1 and f2v2:
        comps_v2 = [p for p in [f1, f2v2, salata] if p]
        if componente_disponibile(comps_v2):
            optiuni_meniu["Meniu Complet V2"] = comps_v2
    if f1 and f1["nume"] in gatite and stoc.get(f1["nume"], {}).get("ramas", 0) > 0:
        optiuni_meniu[f"Solo {f1["nume"]}"] = [f1]
    if f2v1 and f2v1["nume"] in gatite and stoc.get(f2v1["nume"], {}).get("ramas", 0) > 0:
        optiuni_meniu[f"Solo {f2v1["nume"]}"] = [f2v1]
    if f2v2 and f2v2["nume"] in gatite and stoc.get(f2v2["nume"], {}).get("ramas", 0) > 0:
        optiuni_meniu[f"Solo {f2v2["nume"]}"] = [f2v2]

    optiuni_nevandut = {k: v for k, v in nevandut.items() if v["ramas"] > 0}

    if not optiuni_meniu and not optiuni_nevandut:
        st.warning("Nu există meniu disponibil pentru servire (stoc epuizat sau negatit).")
        return

    # Fiecare firma = un expander
    for firma in firme:
        firma_id     = firma["id"]
        toti         = db.get_angajati_firma(firma_id, doar_activi=False)
        activi       = [a for a in toti if a["activ"]]
        inactivi     = [a for a in toti if not a["activ"]]
        serviti_azi  = db.get_angajati_serviti_azi(firma_id, data_azi)
        nr_serviti   = len(serviti_azi)

        titlu = f"🏢 {firma["nume_firma"]}  —  {nr_serviti}/{len(activi)} serviți"

        with st.expander(titlu, expanded=(nr_serviti < len(activi))):

            # Adauga angajat nou direct din ghiseu
            col_inp, col_btn = st.columns([4, 1])
            nou = col_inp.text_input(
                "Angajat nou:", key=f"new_ang_gh_{firma_id}",
                placeholder="Nume și prenume", label_visibility="collapsed"
            )
            if col_btn.button("➕", key=f"add_ang_gh_{firma_id}", use_container_width=True):
                if nou.strip():
                    db.add_angajat(firma_id, nou.strip())
                    st.rerun()

            st.divider()

            pachete_ang = db.get_pachete_angajat_azi(firma_id, data_azi)

            for ang in activi:
                aid         = ang["id"]
                la_masa     = serviti_azi.get(aid)
                pachet_info = pachete_ang.get(aid)

                # Complet rezolvat
                if la_masa:
                    c1, c2 = st.columns([3, 4])
                    c1.markdown(f"🍽️ ~~{ang['nume_angajat']}~~")
                    c2.caption(la_masa)
                    continue

                if pachet_info and pachet_info["status_pachet"] == "ridicat":
                    c1, c2 = st.columns([3, 4])
                    c1.markdown(f"📦 ~~{ang['nume_angajat']}~~")
                    c2.caption(f"Ridicat — {pachet_info['produse']}")
                    continue

                with st.container(border=True):
                    col_n, col_meniu, col_nev, col_btn1, col_btn2, col_conc = st.columns([2, 2, 2, 1, 1, 0.7])

                    col_n.write(f"👤 **{ang['nume_angajat']}**")

                    # Pachet existent (astept sau ambalat)
                    if pachet_info:
                        status = pachet_info["status_pachet"]
                        col_meniu.caption(pachet_info["produse"])
                        if status == "astept":
                            col_btn1.caption("⏳ Bucătărie")
                        elif status == "ambalat":
                            col_nev.markdown(":green[📦 Gata!]")
                            if col_btn1.button("🚀 Ridicat", key=f"ridicat_{aid}",
                                               use_container_width=True, type="primary"):
                                db.update_status_pachet(pachet_info["servire_id"], "ridicat")
                                st.rerun()
                    else:
                        # Neservit — alege meniu + la masa sau pachet
                        with col_meniu:
                            optiuni_lista = list(optiuni_meniu.keys())
                            meniu_ales = st.selectbox(
                                "Meniu:", optiuni_lista if optiuni_lista else ["— indisponibil —"],
                                key=f"meniu_{aid}", label_visibility="collapsed"
                            )
                        with col_nev:
                            if optiuni_nevandut:
                                nev_ales = st.selectbox(
                                    "+ Nevândut:", ["— fără —"] + list(optiuni_nevandut.keys()),
                                    key=f"nev_{aid}", label_visibility="collapsed"
                                )
                            else:
                                nev_ales = "— fără —"
                                st.caption("-")

                        def _produse(meniu, nev, _optiuni_meniu=optiuni_meniu, _opt_nev=optiuni_nevandut):
                            p = [{"nume_produs": x["nume"], "cantitate": 1, "din_nevandut": False}
                                 for x in _optiuni_meniu.get(meniu, [])]
                            if nev != "— fără —" and nev in _opt_nev:
                                p.append({"nume_produs": nev, "cantitate": 1, "din_nevandut": True})
                            return p

                        if optiuni_lista:
                            if col_btn1.button("🍽️ La masă", key=f"masa_{aid}",
                                               use_container_width=True, type="primary"):
                                db.save_servire(data_azi, "firma", _produse(meniu_ales, nev_ales),
                                                firma_id=firma_id, angajat_id=aid, tip_ridicare="la_masa")
                                st.rerun()
                            if col_btn2.button("📦 Pachet", key=f"pachet_{aid}",
                                               use_container_width=True):
                                db.save_servire(data_azi, "firma", _produse(meniu_ales, nev_ales),
                                                firma_id=firma_id, angajat_id=aid, tip_ridicare="pachet")
                                st.rerun()

                    if col_conc.button("🔴", key=f"conc_{aid}",
                                       use_container_width=True, help="Concediu"):
                        db.toggle_angajat(aid, False)
                        st.rerun()

            # Inactivi
            if inactivi:
                with st.expander(f"💤 Inactivi / Concediu ({len(inactivi)})"):
                    for ang in inactivi:
                        ca, cb = st.columns([5, 1])
                        ca.write(f"💤 {ang["nume_angajat"]}")
                        if cb.button("🟢", key=f"act_{ang["id"]}", use_container_width=True, help="Reactivează"):
                            db.toggle_angajat(ang["id"], True)
                            st.rerun()


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
