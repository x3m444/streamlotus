"""
admin_manager/firme.py
-----------------------
Gestiunea firmelor cu contract — doua categorii distincte:

  Ghișeu        — servire nominală per angajat la ghișeu (existent)
  Ghișeu+Livrare— prânz livrat, cină la ghișeu, tabel nominal
  Livrare       — cantitate fixă livrată (școli, sandwich)
  Special       — meniu construit manual, independent de planificare

Taburi:
  1. Lansare Zilnică  — comenzi pentru firmele cu livrare
  2. Gestiune Firme   — adaugă/editează/dezactivează
  3. Confirmare Prezență — rezervări ghișeu (doar ghișeu/ghișeu+livrare)
  4. Raport Serviri   — export Excel per firmă
"""

import streamlit as st
from collections import Counter
from itertools import groupby
import database as db
import utils

TIPURI_CONTRACT = {
    "pranz_cina": "Prânz + Cină",
    "pranz":      "Doar Prânz",
    "cina":       "Doar Cină",
}

TIP_FIRMA_LABEL = {
    "ghiseu":          "🏪 Ghișeu (nominal)",
    "ghiseu_livrare":  "🚚+🏪 Ghișeu + Livrare prânz",
    "livrare":         "🚚 Livrare fixă (școli/sandwich)",
    "special":         "⭐ Meniu Special",
}

TIP_FIRMA_DESC = {
    "ghiseu":         "Angajații vin la ghișeu. Servire nominală per persoană.",
    "ghiseu_livrare": "Prânzul se livrează. Cina se ridică la ghișeu. Tabel nominal.",
    "livrare":        "Cantitate fixă livrată zilnic (sandwich, meniu fix). Fără tabel nominal.",
    "special":        "Meniu construit manual de admin. Nu depinde de planificarea zilei.",
}


@st.fragment
def show():
    st.subheader("🏢 Gestiune Firme cu Contract")

    data_azi = utils.get_ro_time().date()

    tab_lansare, tab_gestiune, tab_prezenta, tab_raport = st.tabs([
        "🚀 Lansare Zilnică", "⚙️ Gestiune Firme",
        "📋 Confirmare Prezență", "📊 Raport Serviri",
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1 — LANSARE ZILNICĂ
    # ══════════════════════════════════════════════════════════════
    with tab_lansare:
        st.markdown("#### 🚀 Comenzi zilnice pentru firmele cu livrare")
        st.caption("Fiecare firmă poate fi lansată o singură dată pe zi. Folosește Editează pentru modificări.")

        data_lansare = st.date_input("Data livrare:", data_azi, key="lansare_firma_data")
        livratori    = db.get_lista_livratori()

        if not livratori:
            st.warning("Nu există livratori configurați.")
            return

        firme_liv = db.get_firme_livrare(doar_active=True)
        if not firme_liv:
            st.info("Nu există firme cu livrare configurate. Adaugă din tab-ul Gestiune Firme.")
        else:
            plan_zi   = db.get_meniu_planificat(data_lansare)
            lista_f1  = [p for p in plan_zi if p["categorie"] == "felul_1"]
            lista_f2  = [p for p in plan_zi if p["categorie"] == "felul_2"]
            lista_sal = [p for p in plan_zi if p["categorie"] == "salate"]
            lista_sw  = db.get_meniu_planificat(data_lansare, tip_plan="sandwich")

            f1     = lista_f1[0]  if lista_f1           else None
            f2v1   = lista_f2[0]  if len(lista_f2) >= 1 else None
            f2v2   = lista_f2[1]  if len(lista_f2) >= 2 else None
            salata = lista_sal[0] if lista_sal           else None

            lansate = db.get_comenzi_lansate_firme(data_lansare)
            # set de firma_id-uri in modul edit (stergere + relansare)
            if "edit_lansare" not in st.session_state:
                st.session_state["edit_lansare"] = set()

            def _card_lansata(firma, info):
                """Afișează cardul pentru o firmă deja lansată."""
                fid = firma["id"]
                with st.container(border=True):
                    c_n, c_info, c_ed, c_del = st.columns([2.5, 5, 1.2, 1.2])
                    c_n.markdown(f"**{firma['nume_firma']}**")
                    c_n.markdown(":green[✅ Lansată]")
                    c_info.caption(
                        f"🚗 {info['sofer']}  |  🕐 {info['ora']}  |  "
                        f"💰 {info['total']:.0f} lei  |  {info['detalii'] or ''}"
                    )
                    if c_ed.button("✏️ Edit", key=f"edit_btn_{fid}", use_container_width=True):
                        st.session_state["edit_lansare"].add(fid)
                        st.rerun()
                    if c_del.button("🗑️", key=f"del_btn_{fid}", use_container_width=True,
                                    help="Șterge lansarea"):
                        db.delete_comanda(info["comanda_id"])
                        st.session_state["edit_lansare"].discard(fid)
                        st.rerun()

            # ── Firme Ghișeu+Livrare ─────────────────────────────
            firme_gl = [f for f in firme_liv if f["tip_firma"] == "ghiseu_livrare"]
            if firme_gl:
                st.markdown("**🚚+🏪 Ghișeu + Livrare prânz**")
                for firma in firme_gl:
                    fid      = firma["id"]
                    info_lan = lansate.get(fid)
                    in_edit  = fid in st.session_state["edit_lansare"]

                    if info_lan and not in_edit:
                        _card_lansata(firma, info_lan)
                        continue

                    # dacă e în edit, ștergem comanda existentă și resetăm flag-ul
                    if info_lan and in_edit:
                        db.delete_comanda(info_lan["comanda_id"])
                        st.session_state["edit_lansare"].discard(fid)
                        lansate.pop(fid, None)

                    angajati = db.get_angajati_firma(fid, doar_activi=True)
                    nr_def   = len(angajati)

                    with st.container(border=True):
                        c_n, c_qty, c_menu, c_liv, c_ora, c_btn = st.columns([2.5, 1, 2, 2, 1.5, 1.5])
                        c_n.markdown(f"**{firma['nume_firma']}**")
                        c_n.caption(TIP_FIRMA_DESC["ghiseu_livrare"])

                        qty = c_qty.number_input("Porții:", min_value=1, value=nr_def,
                                                 key=f"gl_qty_{fid}", label_visibility="collapsed")

                        optiuni_meniu = []
                        if f1 and f2v1:
                            optiuni_meniu.append("V1")
                        if f1 and f2v2:
                            optiuni_meniu.append("V2")
                        if not optiuni_meniu:
                            optiuni_meniu = ["— fără plan —"]

                        meniu_ales = c_menu.selectbox("Meniu:", optiuni_meniu,
                                                      key=f"gl_menu_{fid}", label_visibility="collapsed")
                        livrator   = c_liv.selectbox("Livrator:", livratori,
                                                     key=f"gl_liv_{fid}", label_visibility="collapsed")
                        ora        = c_ora.text_input("Ora:", value="12:00",
                                                      key=f"gl_ora_{fid}", label_visibility="collapsed")

                        if c_btn.button("🚀 Lansează", key=f"gl_btn_{fid}",
                                        use_container_width=True, type="primary"):
                            if meniu_ales not in ("V1", "V2"):
                                st.error("Nu există plan de meniu pentru această dată.")
                            else:
                                produse = [p for p in ([f1, f2v1, salata] if meniu_ales == "V1"
                                                       else [f1, f2v2, salata]) if p]
                                produse_fmt = [{"id": p["id"], "nume": p["nume"],
                                                "cantitate": qty, "pret": p.get("pret_standard", 0)}
                                               for p in produse]
                                db.save_comanda_firma_livrare(fid, firma["nume_firma"],
                                                             produse_fmt, livrator, ora,
                                                             data_lansare, tip_comanda="livrare")
                                st.rerun()

                st.divider()

            # ── Firme Livrare Fixă ────────────────────────────────
            firme_lf = [f for f in firme_liv if f["tip_firma"] == "livrare"]
            if firme_lf:
                st.markdown("**🚚 Livrare fixă** — școli, sandwich")
                for firma in firme_lf:
                    fid      = firma["id"]
                    info_lan = lansate.get(fid)
                    in_edit  = fid in st.session_state["edit_lansare"]

                    if info_lan and not in_edit:
                        _card_lansata(firma, info_lan)
                        continue

                    if info_lan and in_edit:
                        db.delete_comanda(info_lan["comanda_id"])
                        st.session_state["edit_lansare"].discard(fid)
                        lansate.pop(fid, None)

                    qty_def = firma["cantitate_default"] or 1

                    with st.container(border=True):
                        c_n, c_qty, c_sw, c_liv, c_ora, c_btn = st.columns([2.5, 1, 2, 2, 1.5, 1.5])
                        c_n.markdown(f"**{firma['nume_firma']}**")
                        c_n.caption(TIP_FIRMA_DESC["livrare"])

                        qty = c_qty.number_input("Buc:", min_value=1, value=qty_def,
                                                 key=f"lf_qty_{fid}", label_visibility="collapsed")

                        if lista_sw:
                            produs_ales = c_sw.selectbox(
                                "Produs:", lista_sw,
                                format_func=lambda p: p["nume"],
                                key=f"lf_prod_{fid}", label_visibility="collapsed"
                            )
                        else:
                            c_sw.warning("⚠️ Niciun sandwich planificat")
                            produs_ales = None

                        livrator = c_liv.selectbox("Livrator:", livratori,
                                                   key=f"lf_liv_{fid}", label_visibility="collapsed")
                        ora      = c_ora.text_input("Ora:", value="11:30",
                                                    key=f"lf_ora_{fid}", label_visibility="collapsed")

                        if c_btn.button("🚀 Lansează", key=f"lf_btn_{fid}",
                                        use_container_width=True, type="primary"):
                            if not produs_ales:
                                st.error("Niciun produs sandwich planificat pentru această dată.")
                            else:
                                db.save_comanda_firma_livrare(
                                    fid, firma["nume_firma"],
                                    [{"id": produs_ales["id"], "nume": produs_ales["nume"],
                                      "cantitate": qty, "pret": produs_ales.get("pret_standard", 0)}],
                                    livrator, ora, data_lansare, tip_comanda="livrare"
                                )
                                st.rerun()

                st.divider()

            # ── Firme Special ─────────────────────────────────────
            firme_sp = [f for f in firme_liv if f["tip_firma"] == "special"]
            if firme_sp:
                st.markdown("**⭐ Meniu Special** — independent de planificare")
                for firma in firme_sp:
                    fid      = firma["id"]
                    info_lan = lansate.get(fid)
                    in_edit  = fid in st.session_state["edit_lansare"]

                    if info_lan and not in_edit:
                        _card_lansata(firma, info_lan)
                        continue

                    if info_lan and in_edit:
                        db.delete_comanda(info_lan["comanda_id"])
                        st.session_state["edit_lansare"].discard(fid)
                        lansate.pop(fid, None)

                    qty_def   = firma["cantitate_default"] or 1
                    toate_prod = db.get_toate_produsele()

                    with st.expander(f"⭐ {firma['nume_firma']} — construiește meniu"):
                        st.caption(TIP_FIRMA_DESC["special"])

                        col_qty, col_liv, col_ora = st.columns([1, 2, 1.5])
                        qty      = col_qty.number_input("Porții:", min_value=1, value=qty_def,
                                                        key=f"sp_qty_{fid}")
                        livrator = col_liv.selectbox("Livrator:", livratori, key=f"sp_liv_{fid}")
                        ora      = col_ora.text_input("Ora:", value="12:00", key=f"sp_ora_{fid}")

                        st.markdown("**Componente meniu special:**")

                        def sel_prod(categorie, label, key_suf):
                            opts = [None] + [p for p in toate_prod if p["categorie"] == categorie]
                            return st.selectbox(
                                label, opts,
                                format_func=lambda x: "— fără —" if x is None else x["nume"],
                                key=f"sp_{key_suf}_{fid}"
                            )

                        c1, c2, c3 = st.columns(3)
                        with c1: f1_sp  = sel_prod("felul_1", "Felul 1:", "f1")
                        with c2: f2_sp  = sel_prod("felul_2", "Felul 2:", "f2")
                        with c3: sal_sp = sel_prod("salate",  "Salată:",  "sal")

                        componente = [p for p in [f1_sp, f2_sp, sal_sp] if p]

                        if st.button("🚀 Lansează Meniu Special", key=f"sp_btn_{fid}",
                                     use_container_width=True, type="primary"):
                            if not componente:
                                st.error("Selectează cel puțin un produs.")
                            else:
                                produse_fmt = [{"id": p["id"], "nume": p["nume"],
                                                "cantitate": qty, "pret": p.get("pret_standard", 0)}
                                               for p in componente]
                                db.save_comanda_firma_livrare(
                                    fid, firma["nume_firma"], produse_fmt,
                                    livrator, ora, data_lansare, tip_comanda="special"
                                )
                                st.rerun()

    # ══════════════════════════════════════════════════════════════
    # TAB 2 — GESTIUNE FIRME
    # ══════════════════════════════════════════════════════════════
    with tab_gestiune:
        st.markdown("#### ⚙️ Adaugă și gestionează firmele cu contract")

        with st.expander("➕ Adaugă Firmă Nouă", expanded=False):
            c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 1, 1])
            nou_nume    = c1.text_input("Nume firmă / instituție:", key="firma_noua_nume")
            nou_tip_f   = c2.selectbox("Tip firmă:", list(TIP_FIRMA_LABEL.keys()),
                                        format_func=lambda x: TIP_FIRMA_LABEL[x],
                                        key="firma_noua_tip_firma")
            nou_contract= c3.selectbox("Contract:", list(TIPURI_CONTRACT.keys()),
                                        format_func=lambda x: TIPURI_CONTRACT[x],
                                        key="firma_noua_contract")
            are_nominal = nou_tip_f in ("ghiseu", "ghiseu_livrare")
            if are_nominal:
                c4.caption("Cant. = nr. angajați activi")
                nou_cant = 0
            else:
                nou_cant = c4.number_input("Cant. default:", min_value=1, value=1,
                                           key="firma_noua_cant",
                                           help="Cantitate implicită zilnică")
            c5.write("")
            c5.write("")
            if c5.button("Adaugă", key="btn_add_firma", use_container_width=True, type="primary"):
                if nou_nume.strip():
                    db.add_firma(nou_nume.strip(), nou_contract, nou_tip_f, nou_cant)
                    st.success(f"Firmă adăugată: {nou_nume.strip()}")
                    st.rerun()
                else:
                    st.error("Introdu numele firmei.")

        st.divider()
        toate_firme = db.get_all_firme(doar_active=False)

        for tip_f, label_f in TIP_FIRMA_LABEL.items():
            firme_tip = [f for f in toate_firme if f.get("tip_firma", "ghiseu") == tip_f]
            if not firme_tip:
                continue

            st.markdown(f"**{label_f}**")
            st.caption(TIP_FIRMA_DESC[tip_f])

            for firma in firme_tip:
                fid  = firma["id"]
                activ_icon = "🟢" if firma["activ"] else "💤"
                toti = db.get_angajati_firma(fid, doar_activi=False) if tip_f in ("ghiseu", "ghiseu_livrare") else []
                activi_ang   = [a for a in toti if a["activ"]]
                inactivi_ang = [a for a in toti if not a["activ"]]

                nr_activi_str = f"{len(activi_ang)} angajați activi" if tip_f in ("ghiseu", "ghiseu_livrare") else ""
                contact_str = firma.get("telefon") or ""
                titlu_exp = f"{activ_icon} {firma['nume_firma']} — {TIPURI_CONTRACT.get(firma['tip_contract'], '')}"
                if nr_activi_str:
                    titlu_exp += f"  |  👥 {nr_activi_str}"
                if contact_str and not contact_str.startswith("firma_"):
                    titlu_exp += f"  |  📞 {contact_str}"

                with st.expander(titlu_exp):
                    ce1, ce2, ce3, ce4, ce5 = st.columns([2, 2, 2, 1, 1])
                    nou_n  = ce1.text_input("Nume:", value=firma["nume_firma"], key=f"edit_n_{fid}")
                    nou_tc = ce2.selectbox("Contract:", list(TIPURI_CONTRACT.keys()),
                                           index=list(TIPURI_CONTRACT.keys()).index(firma["tip_contract"])
                                                 if firma["tip_contract"] in TIPURI_CONTRACT else 0,
                                           format_func=lambda x: TIPURI_CONTRACT[x],
                                           key=f"edit_tc_{fid}")
                    nou_tip_f = ce3.selectbox("Tip firmă:", list(TIP_FIRMA_LABEL.keys()),
                                              index=list(TIP_FIRMA_LABEL.keys()).index(tip_f)
                                                    if tip_f in TIP_FIRMA_LABEL else 0,
                                              format_func=lambda x: TIP_FIRMA_LABEL[x],
                                              key=f"edit_tf_{fid}")
                    if nou_tip_f in ("ghiseu", "ghiseu_livrare"):
                        ce4.metric("Cant.:", len(activi_ang), help="Din nr. angajați activi")
                        nou_cd = 0
                    else:
                        nou_cd = ce4.number_input("Cant. def.:", min_value=1,
                                                  value=int(firma.get("cantitate_default", 0) or 1),
                                                  key=f"edit_cd_{fid}")
                    ct1, ct2 = st.columns(2)
                    nou_tel = ct1.text_input(
                        "📞 Telefon / persoană contact:",
                        value=firma.get("telefon", "") or "",
                        key=f"edit_tel_{fid}",
                        placeholder="ex: 0740 123 456 — Ion Popescu"
                    )
                    nou_adr = ct2.text_input(
                        "📍 Adresa de livrare:",
                        value=firma.get("adresa", "") or "",
                        key=f"edit_adr_{fid}",
                        placeholder="ex: Str. Școlii nr. 5, Mahmudia"
                    )

                    if st.button("💾 Salvează", key=f"save_f_{fid}", use_container_width=True, type="primary"):
                        db.update_firma(fid, nou_n, nou_tc, firma["activ"], nou_tip_f, nou_cd)
                        db.update_client_firma(fid, nou_tel, nou_adr)
                        st.success("Salvat!")
                        st.rerun()

                    col_act, col_dez = st.columns(2)
                    if firma["activ"]:
                        if col_dez.button("🔴 Dezactivează", key=f"dez_f_{fid}", use_container_width=True):
                            db.update_firma(fid, firma["nume_firma"], firma["tip_contract"],
                                            False, tip_f, firma.get("cantitate_default", 0))
                            st.rerun()
                    else:
                        if col_act.button("🟢 Reactivează", key=f"act_f_{fid}", use_container_width=True):
                            db.update_firma(fid, firma["nume_firma"], firma["tip_contract"],
                                            True, tip_f, firma.get("cantitate_default", 0))
                            st.rerun()

                    if tip_f in ("ghiseu", "ghiseu_livrare"):
                        st.divider()
                        col_inp, col_btn = st.columns([4, 1])
                        nou_ang = col_inp.text_input("Adaugă angajat:", key=f"new_ang_{fid}",
                                                     placeholder="Nume și prenume",
                                                     label_visibility="collapsed")
                        if col_btn.button("➕", key=f"btn_ang_{fid}", use_container_width=True):
                            if nou_ang.strip():
                                db.add_angajat(fid, nou_ang.strip())
                                st.rerun()

                        for ang in activi_ang:
                            ca, cb = st.columns([5, 1])
                            ca.write(f"👤 {ang['nume_angajat']}")
                            if cb.button("Concediu", key=f"conc_{ang['id']}", use_container_width=True):
                                db.toggle_angajat(ang["id"], False)
                                st.rerun()

                        if inactivi_ang:
                            st.caption(f"💤 Inactivi ({len(inactivi_ang)}):")
                            for ang in inactivi_ang:
                                ca, cb = st.columns([5, 1])
                                ca.write(f"💤 {ang['nume_angajat']}")
                                if cb.button("Reactivează", key=f"react_{ang['id']}", use_container_width=True):
                                    db.toggle_angajat(ang["id"], True)
                                    st.rerun()

            st.divider()

    # ══════════════════════════════════════════════════════════════
    # TAB 3 — CONFIRMARE PREZENȚĂ (doar ghișeu / ghișeu+livrare)
    # ══════════════════════════════════════════════════════════════
    with tab_prezenta:
        firme_gh = [f for f in db.get_all_firme(doar_active=True)
                    if f.get("tip_firma", "ghiseu") in ("ghiseu", "ghiseu_livrare")]

        rezervari = db.get_rezervari_firme_azi(data_azi)
        total_rez = sum(v["cantitate"] for v in rezervari.values())

        st.markdown(
            f"#### 📋 Confirmare Prezență — {data_azi.strftime('%d.%m.%Y')}"
            + (f"  ✅ {total_rez} porții rezervate" if total_rez else "  (nicio confirmare)")
        )

        if not firme_gh:
            st.info("Nu există firme active cu servire la ghișeu.")
        else:
            st.caption("Confirmă câți angajați vin azi. Cantitatea scade din stocul zilei.")
            col_h1, col_h2, col_h3, col_h4 = st.columns([3, 1.5, 1, 1])
            col_h1.caption("**Firmă**")
            col_h2.caption("**Contract**")
            col_h3.caption("**Angajați activi**")
            col_h4.caption("**Rezervat azi**")
            st.divider()

            for firma in firme_gh:
                fid        = firma["id"]
                nr_activi  = len(db.get_angajati_firma(fid, doar_activi=True))
                rez_curenta= rezervari.get(fid, {}).get("cantitate", 0)

                c1, c2, c3, c4, c5 = st.columns([3, 1.5, 1, 1, 1])
                tip_icon = "🚚+🏪" if firma.get("tip_firma") == "ghiseu_livrare" else "🏪"
                c1.write(f"{tip_icon} **{firma['nume_firma']}**")
                c2.caption(TIPURI_CONTRACT.get(firma["tip_contract"], ""))
                c3.write(str(nr_activi))

                qty = c4.number_input("qty", min_value=0, max_value=200,
                                      value=rez_curenta if rez_curenta else nr_activi,
                                      step=1, key=f"rez_{fid}",
                                      label_visibility="collapsed")
                label_btn = "✅ Update" if rez_curenta else "Confirmă"
                btn_type  = "secondary" if rez_curenta else "primary"
                if c5.button(label_btn, key=f"btn_rez_{fid}",
                             use_container_width=True, type=btn_type):
                    db.save_rezervare_firma(fid, data_azi, qty)
                    st.rerun()

            st.divider()
            if total_rez:
                st.success(f"**Total rezervat pentru firme azi: {total_rez} porții**")

    # ══════════════════════════════════════════════════════════════
    # TAB 4 — RAPORT SERVIRI
    # ══════════════════════════════════════════════════════════════
    with tab_raport:
        st.markdown("#### 📊 Raport Serviri Firme")
        data_raport = st.date_input("Data raport:", data_azi, key="firme_raport_data")
        serviri     = db.get_raport_serviri_firme(data_raport)

        if not serviri:
            st.info(f"Nu există serviri înregistrate pentru {data_raport.strftime('%d.%m.%Y')}.")
        else:
            firme_servite = Counter(s["nume_firma"] for s in serviri)
            col_m1, col_m2, col_m3 = st.columns(3)
            col_m1.metric("Firme servite", len(firme_servite))
            col_m2.metric("Total angajați", len(serviri))
            col_m3.metric("Pachete", sum(1 for s in serviri if s["tip_ridicare"] == "pachet"))

            for nume_firma, grup in groupby(serviri, key=lambda x: x["nume_firma"]):
                randuri = list(grup)
                la_masa = sum(1 for r in randuri if r["tip_ridicare"] == "la_masa")
                pachete = len(randuri) - la_masa
                with st.expander(f"🏢 {nume_firma} — {len(randuri)} serviți  ({la_masa} masă / {pachete} pachete)"):
                    for r in randuri:
                        tip_icon = "🍽️" if r["tip_ridicare"] == "la_masa" else "📦"
                        ora = str(r["ora_servire"])[:5] if r["ora_servire"] else "—"
                        st.markdown(f"{tip_icon} **{r['nume_angajat']}** — {r['produse']}  `{ora}`")

            st.divider()
            excel_firme = utils.export_raport_firme(serviri, data_raport)
            st.download_button(
                "📥 Export Raport Firme (Excel — un sheet per firmă)",
                data=excel_firme,
                file_name=f"Raport_Firme_{data_raport.strftime('%d%m%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary",
            )
