"""
receptie/comenzi.py
--------------------
TAB Introducere Comenzi — receptia preia comenzi de la clienti.
Selectie client, produse din meniu/special/custom, logistica livrare.
"""

import streamlit as st
import database as db
import utils


@st.fragment
def show(data_selectata=None):
    st.title("📞 Recepție Comenzi")

    if 'buffer_comanda' not in st.session_state:
        st.session_state.buffer_comanda = []

    # --- 1. SELECTARE DATĂ COMANDĂ ---
    st.subheader("📅 Programare Comandă")
    if data_selectata is None:
        data_selectata = st.date_input(
            "Pentru ce dată este comanda?",
            value=utils.get_ro_time().date(),
            min_value=utils.get_ro_time().date(),
            key="data_comanda_selector"
        )

    plan_zi = db.get_meniu_planificat(data_selectata)

    client_id = None
    nume_client = ""
    telefon = ""
    adresa_principala = ""

    toti_clientii = db.get_all_clienti()
    optiuni_clienti = {f"{c['nume_client']} | {c['telefon']}": c for c in toti_clientii}
    lista_nume = sorted(list(optiuni_clienti.keys()))

    selectie = st.selectbox(
        "👤 Selectează Clientul (sau caută după nume/telefon):",
        ["-- Client Nou / Adaugă Persoană --"] + lista_nume
    )

    if selectie != "-- Client Nou / Adaugă Persoană --":
        c = optiuni_clienti[selectie]
        client_id = c['id']
        nume_client = c['nume_client']
        telefon = c['telefon']
        adresa_principala = c['adresa_principala']

    with st.expander("🛠️ Gestionare Date Client (Nou / Editare)", expanded=False):
        nume_client = st.text_input("Nume Client", value=nume_client)
        telefon = st.text_input("Telefon", value=telefon)
        adresa_principala = st.text_input("Adresa Principala", value=adresa_principala)

        col1, col2 = st.columns(2)

        if client_id is None:
            if col1.button("💾 Salvează Client Nou", type="primary"):
                db.add_client(nume_client, telefon, adresa_principala)
                st.success("Client adăugat!")
                st.rerun()
        else:
            if col1.button("🆙 Actualizează Date"):
                db.update_client(client_id, nume_client, telefon, adresa_principala)
                st.success("Modificări salvate!")
                st.rerun()

            if col2.button("🗑️ Șterge Client"):
                if db.delete_client(client_id):
                    st.success("Client eliminat!")
                    st.rerun()

    # --- 2. SELECȚIE PRODUSE ---
    st.divider()
    plan_zi = db.get_meniu_planificat(data_selectata)
    nomenclator_complet = db.get_toate_produsele()

    lista_f1_plan = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2_plan = [p for p in plan_zi if p['categorie'] == 'felul_2']
    lista_salate_plan = [p for p in plan_zi if p['categorie'] == 'salate']

    lista_toate_specialele = [p for p in nomenclator_complet if p['categorie'] == 'special']
    toate_f1 = [p for p in nomenclator_complet if p['categorie'] == 'felul_1']
    toate_f2 = [p for p in nomenclator_complet if p['categorie'] == 'felul_2']

    nume_f1    = lista_f1_plan[0]['nume'] if lista_f1_plan else "Felul 1"
    pret_f1    = lista_f1_plan[0].get('pret_standard', 0) if lista_f1_plan else 0

    nume_f2_v1 = lista_f2_plan[0]['nume'] if len(lista_f2_plan) >= 1 else "Felul 2 V1"
    pret_f2_v1 = lista_f2_plan[0].get('pret_standard', 0) if len(lista_f2_plan) >= 1 else 0

    nume_f2_v2 = lista_f2_plan[1]['nume'] if len(lista_f2_plan) >= 2 else "Felul 2 V2"
    pret_f2_v2 = lista_f2_plan[1].get('pret_standard', 0) if len(lista_f2_plan) >= 2 else 0

    nume_salata = lista_salate_plan[0]['nume'] if lista_salate_plan else "Salată"
    pret_salata = lista_salate_plan[0].get('pret_standard', 0) if lista_salate_plan else 0

    def adauga_in_buffer(nume, cantitate, pret, tip):
        tip_linie = 'special' if tip in ('Special', 'Custom') else 'standard'
        for item in st.session_state.buffer_comanda:
            if item['nume'] == nume and item['tip_linie'] == tip_linie:
                item['cantitate'] += cantitate
                return
        st.session_state.buffer_comanda.append({
            "nume": nume,
            "cantitate": cantitate,
            "pret": pret,
            "tip": tip,
            "tip_linie": tip_linie
        })

    # --- ZONA A: MENIURI RAPIDE ---
    st.markdown(f"#### 🍱 Meniuri și Porții Rapide - {data_selectata.strftime('%d/%m/%Y')}")

    if not lista_f1_plan or not lista_f2_plan:
        st.info("⏳ Nu există meniu planificat pentru această dată. Folosește secțiunea de mai jos pentru produse speciale.")
        st.divider()
        # salt direct la zona B
    else:
        # Rând 1: Meniuri complete
        st.caption("🍱 Meniu complet")
        col_v1, col_v2 = st.columns(2)

        with col_v1:
            with st.container(border=True):
                st.markdown(f"**V1** — {nume_f1} + {nume_f2_v1}" + (f" + {nume_salata}" if lista_salate_plan else ""))
                m_v1 = st.number_input("Porții:", min_value=0, step=1, key="rapid_v1", label_visibility="collapsed")
                if st.button("➕ Adaugă Meniu V1", key="btn_m_v1_rapide", width="stretch", type="primary"):
                    if m_v1 > 0:
                        adauga_in_buffer(nume_f1, m_v1, pret_f1, "Meniu V1")
                        adauga_in_buffer(nume_f2_v1, m_v1, pret_f2_v1, "Meniu V1")
                        if lista_salate_plan:
                            adauga_in_buffer(nume_salata, m_v1, pret_salata, "Meniu V1")

        with col_v2:
            with st.container(border=True):
                st.markdown(f"**V2** — {nume_f1} + {nume_f2_v2}" + (f" + {nume_salata}" if lista_salate_plan else ""))
                m_v2 = st.number_input("Porții:", min_value=0, step=1, key="rapid_v2", label_visibility="collapsed")
                if st.button("➕ Adaugă Meniu V2", key="btn_m_v2_rapide", width="stretch", type="primary"):
                    if m_v2 > 0:
                        adauga_in_buffer(nume_f1, m_v2, pret_f1, "Meniu V2")
                        adauga_in_buffer(nume_f2_v2, m_v2, pret_f2_v2, "Meniu V2")
                        if lista_salate_plan:
                            adauga_in_buffer(nume_salata, m_v2, pret_salata, "Meniu V2")

        # Rând 2: Porții solo
        st.caption("🍽️ Porție solo")
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            with st.container(border=True):
                st.markdown(f"**Solo** — {nume_f1}")
                f1_s = st.number_input("Porții:", min_value=0, step=1, key="rapid_f1", label_visibility="collapsed")
                if st.button("➕ Adaugă", key="btn_s_f1_rapide", width="stretch"):
                    if f1_s > 0:
                        adauga_in_buffer(nume_f1, f1_s, pret_f1, "Solo")

        with col_s2:
            with st.container(border=True):
                st.markdown(f"**Solo** — {nume_f2_v1}" + (f" + {nume_salata}" if lista_salate_plan else ""))
                f2_v1 = st.number_input("Porții:", min_value=0, step=1, key="rapid_f2v1", label_visibility="collapsed")
                if st.button("➕ Adaugă", key="btn_s_f2v1_rapide", width="stretch"):
                    if f2_v1 > 0:
                        adauga_in_buffer(nume_f2_v1, f2_v1, pret_f2_v1, "Solo")
                        if lista_salate_plan:
                            adauga_in_buffer(nume_salata, f2_v1, pret_salata, "Solo")

        with col_s3:
            with st.container(border=True):
                st.markdown(f"**Solo** — {nume_f2_v2}" + (f" + {nume_salata}" if lista_salate_plan else ""))
                f2_v2 = st.number_input("Porții:", min_value=0, step=1, key="rapid_f2v2", label_visibility="collapsed")
                if st.button("➕ Adaugă", key="btn_s_f2v2_rapide", width="stretch"):
                    if f2_v2 > 0:
                        adauga_in_buffer(nume_f2_v2, f2_v2, pret_f2_v2, "Solo")
                        if lista_salate_plan:
                            adauga_in_buffer(nume_salata, f2_v2, pret_salata, "Solo")

    st.divider()
    # --- ZONA B: PRODUSE SPECIALE & MENIU COMPUS ---
    st.markdown("#### 🛠️ Produse Speciale & Meniu Special")
    tab_spec, tab_custom = st.tabs(["✨ Produse Speciale", "🍱 Meniu Special"])

    with tab_spec:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            sel_s = st.selectbox(
                "✨ Nomenclator Speciale:",
                options=lista_toate_specialele,
                format_func=lambda x: f"{x['nume']} - {x.get('pret_standard', 0)} lei",
                index=None, placeholder="Caută produs...", key="sb_spec_liber"
            )
        with c2:
            qty_s = st.number_input("Bucăți", min_value=1, step=1, key="q_spec_liber")
        with c3:
            st.write("")
            if st.button("➕ Adaugă Special", key="btn_spec_liber"):
                if sel_s:
                    adauga_in_buffer(sel_s['nume'], qty_s, sel_s.get('pret_standard', 0), "Special")

    with tab_custom:
        st.markdown("##### 🧩 Adaugă produse individuale")
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])

        with c1:
            f1_sel = st.selectbox(
                "🥣 Felul 1:",
                options=toate_f1,
                format_func=lambda x: f"{x['nume']} ({x.get('pret_standard', 0)} lei)",
                index=None, key="c_f1", placeholder="-- Ciorbă --"
            )
        with c2:
            f2_sel = st.selectbox(
                "🍖 Felul 2:",
                options=toate_f2,
                format_func=lambda x: f"{x['nume']} ({x.get('pret_standard', 0)} lei)",
                index=None, key="c_f2", placeholder="-- Fel 2 --"
            )
        with c3:
            toate_salatele = [p for p in nomenclator_complet if p['categorie'] == 'salate']
            s_sel = st.selectbox(
                "🥗 Salată:",
                options=toate_salatele,
                format_func=lambda x: f"{x['nume']} ({x.get('pret_standard', 0)} lei)",
                index=None, key="c_s", placeholder="-- Salată --"
            )
        with c4:
            qty_custom = st.number_input("Unități:", min_value=1, step=1, key="q_free_val")

        st.divider()
        if st.button("➕ Adaugă selecția în coș", width="stretch"):
            if not (f1_sel or f2_sel or s_sel):
                st.warning("⚠️ Selectează cel puțin un produs!")
            else:
                if f1_sel:
                    adauga_in_buffer(f1_sel['nume'], qty_custom, f1_sel.get('pret_standard', 0), "Custom")
                if f2_sel:
                    adauga_in_buffer(f2_sel['nume'], qty_custom, f2_sel.get('pret_standard', 0), "Custom")
                if s_sel:
                    adauga_in_buffer(s_sel['nume'], qty_custom, s_sel.get('pret_standard', 0), "Custom")
                st.success("✅ Adăugat!")

    # --- ZONA C: REZUMAT COMANDĂ ---
    st.divider()
    total_p = 0

    if st.session_state.buffer_comanda:
        st.subheader("📋 Rezumat Comandă")
        for i, item in enumerate(st.session_state.buffer_comanda):
            subtotal_item = item['pret'] * item['cantitate']
            total_p += subtotal_item

            col_n, col_q, col_p, col_x = st.columns([4, 1, 1, 1])
            col_n.write(f"**{item['nume']}**")
            col_q.write(f"{item['cantitate']} buc")
            col_p.write(f"{subtotal_item} lei")
            if col_x.button("❌", key=f"del_prod_{i}"):
                st.session_state.buffer_comanda.pop(i)

        st.markdown(f"### 💰 Total de plată: {total_p} lei")
    else:
        st.info("Coșul este gol. Adaugă produse din secțiunile de mai sus.")

    # --- ZONA D: LOGISTICĂ ȘI LIVRARE ---
    st.divider()
    lista_livratori_reali = db.get_lista_livratori()

    st.warning(f"🗓️ Comanda va fi programată pentru data de: **{data_selectata.strftime('%d/%m/%Y')}**")

    col_ora, col_sofer = st.columns(2)

    with col_ora:
        st.subheader("🕒 Programare")
        intervale = ["11:00-11:30", "11:30-12:00", "12:00-12:30", "12:30-13:00", "13:00-13:30", "13:30-14:00", "URGENT"]
        ora_livrare = st.select_slider("Selectează ora:", options=intervale, value="12:00-12:30", key="ora_v9")

    with col_sofer:
        st.subheader("🚚 Livrator")
        sofer = st.selectbox("Cine preia comanda?", options=lista_livratori_reali, key="sofer_v9")

    metoda_plata = st.selectbox("Metoda de Plată:", ["cash", "card", "factura"])

    if metoda_plata == "cash":
        st.info(f"💰 Suma de încasat de șofer: {total_p} lei")
    else:
        st.warning(f"💳 Plată prin {metoda_plata}. Șoferul NU încasează numerar.")

    obs_comanda = st.text_input("📝 Observații (Adresă, detalii):", value="", key="obs_final")

    st.divider()

    if st.button("💾 SALVEAZĂ COMANDA FINALĂ", type="primary", width="stretch"):
        if not st.session_state.buffer_comanda:
            st.warning("⚠️ Comanda nu are produse!")
        else:
            succes = db.save_comanda_finala(
                client_id=client_id,
                produse=st.session_state.buffer_comanda,
                total=total_p,
                sofer=sofer,
                ora=ora_livrare,
                obs=obs_comanda,
                plata=metoda_plata,
                tip_comanda='livrare',
                data_comanda=data_selectata
            )
            if succes:
                st.success(f"✅ Comandă salvată pentru {data_selectata.strftime('%d/%m/%Y')}! Livrator: {sofer}")
                st.session_state.buffer_comanda = []
                st.rerun()
