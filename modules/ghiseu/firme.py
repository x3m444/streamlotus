"""
ghiseu/firme.py
----------------
TAB Firme — servire angajati cu contract.
Per angajat: selectie meniu + nevandut, buton La masa / Pachet.
Urmarire status pachet: astept → ambalat → ridicat.
Vanzatorul poate adauga angajati noi sau trimite pe concediu.
"""

import streamlit as st
import database as db


def show(data_azi):
    st.subheader("🏢 Servire Firme cu Contract")

    firme = db.get_all_firme(doar_active=True)
    if not firme:
        st.info("Nu există firme active. Adminul trebuie să adauge firme cu contract.")
        return

    gatite = db.get_produse_gatite_azi(data_azi)
    if not gatite:
        st.info("⏳ Bucătăria nu a marcat încă niciun produs ca gătit. Reîncarcă pagina când mâncarea e gata.")
        return

    plan_zi      = db.get_meniu_planificat(data_azi)
    stoc         = db.get_stoc_zi(data_azi)
    nevandut     = db.get_stoc_nevandut(data_azi)
    comp         = db._plan_to_componente(plan_zi)
    buffer_azi   = db.get_buffer_ambalare(data_azi)
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

    # optiuni_meniu: label → { 'componente': [...], 'tip_meniu': str }
    optiuni_meniu = {}
    if f1 and f2v1:
        comps_v1 = [p for p in [f1, f2v1, salata] if p]
        if componente_disponibile(comps_v1):
            label_v1 = " + ".join(p["nume"] for p in comps_v1)
            optiuni_meniu[label_v1] = {"componente": comps_v1, "tip_meniu": "v1"}
    if f1 and f2v2:
        comps_v2 = [p for p in [f1, f2v2, salata] if p]
        if componente_disponibile(comps_v2):
            label_v2 = " + ".join(p["nume"] for p in comps_v2)
            optiuni_meniu[label_v2] = {"componente": comps_v2, "tip_meniu": "v2"}
    if f1 and f1["nume"] in gatite and stoc.get(f1["nume"], {}).get("ramas", 0) > 0:
        optiuni_meniu[f"Solo {f1['nume']}"] = {"componente": [f1], "tip_meniu": "solo_f1"}
    if f2v1 and f2v1["nume"] in gatite and stoc.get(f2v1["nume"], {}).get("ramas", 0) > 0:
        comps_solo_f2v1 = [p for p in [f2v1, salata] if p]
        label_solo_f2v1 = " + ".join(p["nume"] for p in comps_solo_f2v1)
        optiuni_meniu[label_solo_f2v1] = {"componente": comps_solo_f2v1, "tip_meniu": "solo_f2v1"}
    if f2v2 and f2v2["nume"] in gatite and stoc.get(f2v2["nume"], {}).get("ramas", 0) > 0:
        comps_solo_f2v2 = [p for p in [f2v2, salata] if p]
        label_solo_f2v2 = " + ".join(p["nume"] for p in comps_solo_f2v2)
        optiuni_meniu[label_solo_f2v2] = {"componente": comps_solo_f2v2, "tip_meniu": "solo_f2v2"}

    optiuni_nevandut = {k: v for k, v in nevandut.items() if v["ramas"] > 0}

    if not optiuni_meniu and not optiuni_nevandut:
        st.warning("Nu există meniu disponibil pentru servire (stoc epuizat sau negatit).")
        return

    for firma in firme:
        firma_id     = firma["id"]
        toti         = db.get_angajati_firma(firma_id, doar_activi=False)
        activi       = [a for a in toti if a["activ"]]
        inactivi     = [a for a in toti if not a["activ"]]
        serviti_azi  = db.get_angajati_serviti_azi(firma_id, data_azi)
        nr_serviti   = len(serviti_azi)

        titlu = f"🏢 {firma['nume_firma']}  —  {nr_serviti}/{len(activi)} serviți"

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

                # Complet rezolvat — la masa
                if la_masa:
                    c1, c2 = st.columns([3, 4])
                    c1.markdown(f"🍽️ ~~{ang['nume_angajat']}~~")
                    c2.caption(la_masa)
                    continue

                # Complet rezolvat — pachet ridicat
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

                        def _produse(meniu, nev, _om=optiuni_meniu, _opt_nev=optiuni_nevandut):
                            entry = _om.get(meniu, {})
                            p = [{"nume_produs": x["nume"], "cantitate": 1, "din_nevandut": False}
                                 for x in entry.get("componente", [])]
                            if nev != "— fără —" and nev in _opt_nev:
                                p.append({"nume_produs": nev, "cantitate": 1, "din_nevandut": True})
                            return p

                        if optiuni_lista:
                            if col_btn1.button("🍽️ La masă", key=f"masa_{aid}",
                                               use_container_width=True, type="primary"):
                                db.save_servire(data_azi, "firma", _produse(meniu_ales, nev_ales),
                                                firma_id=firma_id, angajat_id=aid, tip_ridicare="la_masa")
                                st.rerun()
                            # Pachet: din buffer daca disponibil, altfel standard
                            tip_meniu_sel = optiuni_meniu.get(meniu_ales, {}).get("tip_meniu")
                            buf_dispon    = buffer_azi.get(tip_meniu_sel, {}).get("disponibil", 0) if tip_meniu_sel else 0
                            pachet_label  = f"📦 Pachet {'(buf)' if buf_dispon > 0 else ''}"
                            if col_btn2.button(pachet_label, key=f"pachet_{aid}", use_container_width=True):
                                if buf_dispon > 0:
                                    ok = db.distribuie_din_buffer(data_azi, tip_meniu_sel,
                                                                  firma_id=firma_id, angajat_id=aid)
                                    if not ok:
                                        db.save_servire(data_azi, "firma", _produse(meniu_ales, nev_ales),
                                                        firma_id=firma_id, angajat_id=aid, tip_ridicare="pachet")
                                else:
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
                        ca.write(f"💤 {ang['nume_angajat']}")
                        if cb.button("🟢", key=f"act_{ang['id']}", use_container_width=True, help="Reactivează"):
                            db.toggle_angajat(ang["id"], True)
                            st.rerun()
