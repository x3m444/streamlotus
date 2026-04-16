import streamlit as st
import pandas as pd
import database as db
import utils  # Importăm fișierul nou creat
from datetime import date


engine = db.get_engine()
def show_menu_editor():
    st.title("👨‍🍳 Administrare Bucătărie")

    tab_plan, tab_nom, tab_comenzi = st.tabs(["📅 Planificare Zilnică", "📋 Gestiune Nomenclator", "📊 Monitorizare Comenzi"])

    # =========================================================
    # --- TAB 1: PLANIFICARE ȘI LANSARE PRODUCȚIE ---
    # =========================================================
    with tab_plan:
        st.subheader("🚀 Configurare Fluxuri Producție")
        
        # 1. Selector Dată și Date de Bază
        data_plan = st.date_input("Selectează data:", date.today(), key="dp")
        nume_zi_ro = utils.format_nume_zi(data_plan)
        st.write(f"Gestionezi fluxurile pentru: **{nume_zi_ro}**")
        
        toate = db.get_toate_produsele()
        if not toate:
            st.warning("Nomenclatorul este gol. Adaugă produse în Tab-ul 2.")
            return

        # ---------------------------------------------------------
        # MODUL A: PLANIFICARE (Salvarea în bază a ceea ce urmează să se gătească)
        # ---------------------------------------------------------
        st.markdown("### 📝 1. Planificare Meniuri")
        
        # A.1. Sub-Modul: Plan Meniu Prânz (F1, F2a, F2b, Salata)
        with st.expander("🥣 PLANIFICĂ PRÂNZ", expanded=True):
            f1_opts = [None] + [p for p in toate if p['categorie'] == 'felul_1']
            f2_opts = [None] + [p for p in toate if p['categorie'] == 'felul_2']
            acc_opts = [None] + [p for p in toate if p['categorie'] == 'salate' or p['pret_standard'] == 0]
            
            def format_p(x): return x['nume'] if x else "-- Alege --"

            c1, c2, c3, c4 = st.columns(4)
            with c1: sel_f1 = st.selectbox("Felul 1:", f1_opts, format_func=format_p, key="plan_f1")
            with c2: sel_f2_1 = st.selectbox("Felul 2 (A):", f2_opts, format_func=format_p, key="plan_f2a")
            with c3: sel_f2_2 = st.selectbox("Felul 2 (B):", f2_opts, format_func=format_p, key="plan_f2b")
            with c4: sel_acc = st.selectbox("Salată/Acc.:", acc_opts, format_func=format_p, key="plan_acc")

            if st.button("💾 Salvează Plan Prânz", use_container_width=True):
                if sel_f1 and sel_f2_1 and sel_f2_2 and sel_acc:
                    id_uri = [sel_f1['id'], sel_f2_1['id'], sel_f2_2['id'], sel_acc['id']]
                    db.salveaza_planificare(data_plan, id_uri, tip_plan="pranz")
                    st.success("Planificat: Prânz ✅")
                    st.rerun()
                else:
                    st.error("Selectează toate componentele prânzului!")

        # A.2. Sub-Modul: Plan Cină
        with st.expander("🌙 PLANIFICĂ CINĂ"):
            # 1. Pregătim listele filtrate special pentru cină
            # Primul picker: doar felul 2
            f2_options_cina = [None] + [p for p in toate if p['categorie'] == 'felul_2']
            # Al doilea picker: doar salate
            salate_options_cina = [None] + [p for p in toate if p['categorie'] == 'salate']
            
            def format_p(x): return x['nume'] if x else "-- Alege --"

            c1, c2 = st.columns(2)
            with c1: 
                sel_f2_c = st.selectbox("🍖 Felul Principal (Cină):", f2_options_cina, format_func=format_p, key="plan_f2_c_only")
            with c2: 
                sel_sal_c = st.selectbox("🥗 Salată (Cină):", salate_options_cina, format_func=format_p, key="plan_sal_c_only")
            
            if st.button("💾 Salvează Plan Cină", use_container_width=True):
                # Validăm să fie ambele selectate
                if sel_f2_c and sel_sal_c:
                    # Salvăm ID-urile în baza de date cu tip_plan="cina"
                    db.salveaza_planificare(data_plan, [sel_f2_c['id'], sel_sal_c['id']], tip_plan="cina")
                    st.success(f"Cina pentru {nume_zi_ro} a fost salvată!")
                    st.toast(f"Cina pentru {nume_zi_ro} a fost salvată!", icon="✅")
                    st.rerun()
                else:
                    st.error("⚠️ Te rugăm să alegi atât felul principal, cât și salata pentru cină!")

        # A.3. Sub-Modul: Plan Sandwich-uri (Programarea celor de 12 lei)
        with st.expander("🥪 PLANIFICĂ SANDWICH-URILE ZILEI"):
            sw_opts = [p for p in toate if p['categorie'] == 'sandwich']
            sel_sw_zi = st.multiselect("Ce sandwich-uri avem azi?", sw_opts, format_func=lambda x: x['nume'], key="plan_sw")
            
            if st.button("💾 Salvează Plan Sandwich", use_container_width=True):
                if sel_sw_zi:
                    db.salveaza_planificare(data_plan, [s['id'] for s in sel_sw_zi], tip_plan="sandwich")
                    st.success("Planificat: Sandwich-uri ✅")
                    st.rerun()

        st.divider()
        st.header("📋 Planificare Săptămânală (Privire de Ansamblu)")

        zile_sapt = utils.get_zile_saptamana(data_plan)
        
        # 1. PRELUARE DATE (O singură dată pentru toată săptămâna)
        plan_saptamanal = db.get_meniu_planificat(zile_sapt[0], zile_sapt[-1])

        # 2. GENERARE ANTET (Header)
        header_html = "".join([
            f"<th style='border: 1px solid #444; padding: 12px; background-color: #262730; color: #FAFAFA; min-width: 150px;'>"
            f"<div style='color: #FF4B4B; font-size: 1.1em;'>{utils.format_nume_zi(z)}</div>"
            f"<div style='font-size: 0.9em; font-weight: normal; opacity: 0.7;'>{z.strftime('%d.%m')}</div></th>" 
            for z in zile_sapt
        ])

        # 3. GENERARE RÂNDURI (Rows)
        rows_html = ""
        tipuri_masa = [
            ("pranz", "🥣 PRÂNZ"),
            ("cina", "🌙 CINĂ"),
            ("sandwich", "🥪 SANDWICH")
        ]

        for cod_tip, nume_afisat in tipuri_masa:
            # Începem rândul cu eticheta mesei (Prânz, Cină etc.)
            row_content = f"""<tr>
                <td style='border: 1px solid #444; padding: 15px; font-weight: bold; background-color: #262730; color: #FAFAFA; text-align: left; border-right: 3px solid #FF4B4B;'>
                    {nume_afisat}
                </td>"""
            
            for zi in zile_sapt:
                # Căutăm în dicționarul rapid în loc de db.get_meniu_planificat
                m = plan_saptamanal.get((str(zi), cod_tip.lower()), [])
                
                if m:
                    p_items = []
                    for p in m:
                        p_label = p['nume']
                        # Verificăm dacă avem preț și îl formatăm
                        if p.get('pret_standard') and p['pret_standard'] > 0:
                            p_label += f" <span style='color: #888; font-size: 0.85em;'>({int(p['pret_standard'])} lei)</span>"
                        p_items.append(f"<div style='margin-bottom: 5px;'>• {p_label}</div>")
                    
                    celula_text = "".join(p_items)
                    row_content += f"<td style='border: 1px solid #444; padding: 12px; vertical-align: top; color: #FAFAFA; font-size: 0.95em;'>{celula_text}</td>"
                else:
                    row_content += "<td style='border: 1px solid #444; padding: 12px; color: #555; font-style: italic; text-align: center; vertical-align: middle;'>---</td>"
            
            row_content += "</tr>"
            rows_html += row_content

        # 4. CONSTRUCȚIE TABEL FINAL
        tabel_html = f"""
        <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #444; margin: 20px 0;">
            <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: #1e1e1e;">
                <thead>
                    <tr>
                        <th style="border: 1px solid #444; padding: 12px; background-color: #262730; color: #888; width: 150px;">FLUX</th>
                        {header_html}
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>"""

        # 5. AFIȘARE
        st.markdown(tabel_html, unsafe_allow_html=True)
# --- SECȚIUNE EXPORT EXCEL (Fără Sandwich) ---
# --- SECȚIUNE EXPORT EXCEL (FORMAT CONFORM IMAGINE) ---
# --- SECȚIUNE EXPORT EXCEL (CU PREȚURI ȘI FORMAT CORECT) ---
# --- SECȚIUNE EXPORT LANDSCAPE ---
# --- SECȚIUNE EXPORT VERTICAL (CANTINA LOTUS) ---
# --- GENERARE EXPORT LANDSCAPE (RĂSTURNAT) ---
        try:
            rows_landscape = []
            
            for zi in zile_sapt:
                # Eticheta zilei
                data_label = f"{utils.format_nume_zi(zi)}\n{zi.strftime('%d.%m')}"
                
                # Formatare preparate Prânz
                m_pranz = plan_saptamanal.get((str(zi), "pranz"), [])
                txt_pranz = "\n".join([
                    f"• {p['nume']} ({int(p['pret_standard'])} lei)" if p.get('pret_standard') and p['pret_standard'] > 0 else f"• {p['nume']}" 
                    for p in m_pranz
                ])
                
                # Formatare preparate Cină
                m_cina = plan_saptamanal.get((str(zi), "cina"), [])
                txt_cina = "\n".join([
                    f"• {p['nume']} ({int(p['pret_standard'])} lei)" if p.get('pret_standard') and p['pret_standard'] > 0 else f"• {p['nume']}" 
                    for p in m_cina
                ])
                
                rows_landscape.append({
                    "DATA / ZIUA": data_label,
                    "🥣 MENIU PRÂNZ": txt_pranz if txt_pranz else "---",
                    "🌙 MENIU CINĂ": txt_cina if txt_cina else "---"
                })

            df_final = pd.DataFrame(rows_landscape)
            # ATENȚIE: Apelăm funcția de landscape (v2)
            excel_file = utils.export_to_excel_landscape_v2(df_final)

            st.download_button(
                label="🖨️ Descarcă Meniu Landscape Răsturnat (Cantina LOTUS)",
                data=excel_file,
                file_name=f"Meniu_Lotus_Landscape_{zile_sapt[0].strftime('%d_%m')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except Exception as e:
            st.error(f"Eroare la generare: {e}")
        # ---------------------------------------------------------
        # MODUL B: LANSARE PRODUCȚIE (Trimiterea efectivă către bucătărie)
        # ---------------------------------------------------------
# Formatăm data selectată
        data_afisata = data_plan.strftime('%d/%m/%Y')

        # Titlul principal
        st.markdown(f"### 🏭 2. Lansare Loturi în Producție")

        # Mesaj de confirmare a datei și instrucțiune
        st.warning(f"📅 Loturile de mai jos vor fi lansate pentru data: **{data_afisata}**")
        st.caption("💡 *Dacă vrei să lansezi pentru altă zi, schimbă data din calendarul de sus (Secțiunea 1).*")
        
#        col_l1, col_l2, col_l3 = st.columns(3)
        
        # B.1. Lansare Prânz
        # --- B.1. LANSARE PRODUCȚIE PRÂNZ ---
#        with col_l1:
        with st.expander("🍲 LANSARE PRODUCȚIE PRÂNZ"):
            m_p = db.get_meniu_planificat(data_plan, tip_plan="pranz")
            
            if m_p:
                if 'buffer_pranz' not in st.session_state:
                    st.session_state.buffer_pranz = []

                # 1. Selectorul de produse
                prod_ales = st.selectbox("Alege produsul:", m_p, format_func=lambda x: x['nume'], key="sel_p_final")
                qty_aleasa = st.number_input("Cantitate:", min_value=1, step=1, value=1, key="qty_p_final")
                
                if st.button("➕ Adaugă în Lot", use_container_width=True, key="btn_add_p"):
                    existent = next((item for item in st.session_state.buffer_pranz if item["id"] == prod_ales['id']), None)
                    if existent:
                        existent['cantitate'] += qty_aleasa
                    else:
                        # AICI luăm prețul direct din obiectul prod_ales care vine din baza de date
                        st.session_state.buffer_pranz.append({
                            "id": prod_ales['id'], 
                            "nume": prod_ales['nume'], 
                            "cantitate": qty_aleasa,
                            "pret": prod_ales.get('pret_standard', 0) # Încearcă să ia prețul real, pune 0 doar dacă lipsește cu desăvârșire
                        })
                    st.rerun()

                # 2. Previzualizare listă
                if st.session_state.buffer_pranz:
                    st.markdown("---")
                    for i, item in enumerate(st.session_state.buffer_pranz):
                        c_txt, c_del = st.columns([4, 1])
                        c_txt.write(f"**{item['cantitate']}** x {item['nume']}")
                        if c_del.button("❌", key=f"del_p_f_{i}"):
                            st.session_state.buffer_pranz.pop(i)
                            st.rerun()

# ... (partea de selector și buffer rămâne la fel)

# 3. Butonul Final de Lansare
                if st.button("🚀 Confirmă și Salvează Lot", type="primary", use_container_width=True):
                    # CALCULĂM TOTALUL REAL AL LOTULUI
                    total_lot = sum(item['cantitate'] * item['pret'] for item in st.session_state.buffer_pranz)
                    
                    db.save_comanda_finala(
                        999,                                  # ID-ul clientului 'CANTINA'
                        st.session_state.buffer_pranz, 
                        total_lot,                            # <--- Am înlocuit 0 cu total_lot
                        "INTERN", 
                        "12:00", 
                        "Lot Producție Prânz", 
                        "cantina", 
                        "pranz", 
                        data_plan                             # <--- Data corectă pentru viitor
                    )
                    st.session_state.buffer_pranz = []
                    st.success(f"✅ Lotul a fost lansat! (Valoare totală: {total_lot} lei)")
                    st.rerun()
        # B.2. LANSARE PRODUCȚIE CINĂ
#        with col_l2:
        with st.expander("🌙 LANSARE PRODUCȚIE CINĂ"):
            m_c = db.get_meniu_planificat(data_plan, tip_plan="cina")
            
            if m_c:
                if 'buffer_cina' not in st.session_state:
                    st.session_state.buffer_cina = []

                # 1. Selectorul de produse
                prod_ales_c = st.selectbox(
                    "Alege felul (Cină):", 
                    options=m_c, 
                    format_func=lambda x: x['nume'],
                    key="sel_cina_prod_v3"
                )
                
                qty_aleasa_c = st.number_input("Nr. porții:", min_value=1, step=1, value=1, key="qty_cina_val_v3")
                
                if st.button("➕ Adaugă la Lot Cină", key="btn_add_cina_v3", use_container_width=True):
                    existent = next((item for item in st.session_state.buffer_cina if item["id"] == prod_ales_c['id']), None)
                    if existent:
                        existent['cantitate'] += qty_aleasa_c
                    else:
                        # SALVĂM sub cheia 'pret' valoarea din 'pret_standard'
                        st.session_state.buffer_cina.append({
                            "id": prod_ales_c['id'], 
                            "nume": prod_ales_c['nume'], 
                            "cantitate": qty_aleasa_c,
                            "pret": prod_ales_c.get('pret_standard', 0) # <--- Sursa e pret_standard
                        })
                    st.rerun()

                # 2. Afișare Buffer
                if st.session_state.buffer_cina:
                    st.markdown("---")
                    for i, item in enumerate(st.session_state.buffer_cina):
                        c_txt, c_del = st.columns([4, 1])
                        c_txt.write(f"**{item['cantitate']}** x {item['nume']} ({item['pret']} lei/buc)")
                        if c_del.button("❌", key=f"del_cina_item_v3_{i}"):
                            st.session_state.buffer_cina.pop(i)
                            st.rerun()

                    # 3. Salvare Finală
                    if st.button("🚀 Confirmă Producție Cină", type="primary", use_container_width=True):
                        if st.session_state.buffer_cina:
                            # CALCULUL: Acum ambele folosesc 'pret', deci va funcționa!
                            total_cina = sum(item['cantitate'] * item.get('pret', 0) for item in st.session_state.buffer_cina)
                            
                            db.save_comanda_finala(
                                999, 
                                st.session_state.buffer_cina, 
                                total_cina, 
                                "INTERN", 
                                "19:00", 
                                "Lot Producție Cină", 
                                "cantina", 
                                "cina", 
                                data_plan 
                            )
                            st.session_state.buffer_cina = [] 
                            st.success(f"✅ Cina a fost salvată! (Total: {total_cina:.2f} lei)")
                            st.rerun()

                    if st.button("🗑️ Golește lista", key="clear_cina_all_v3", use_container_width=True):
                        st.session_state.buffer_cina = []
                        st.rerun()
            else:
                st.warning("⚠️ Plan cină lipsă pentru această zi!")

        # B.3. Lansare Sandwich-uri
        with st.expander("🥪 LANSARE COMANDĂ SANDWICH"):
            # 1. Preluăm ce am planificat
            m_s = db.get_meniu_planificat(data_plan, tip_plan="sandwich")
            
            if m_s:
                # Folosim un formular pentru a putea reseta totul dintr-o dată
                with st.form("form_lansare_sw", clear_on_submit=True):
                    sw_selectat = st.selectbox(
                        "Alege tipul de sandwich:",
                        options=m_s,
                        format_func=lambda x: x['nume'],
                        key="sw_type_select"
                    )
                    
                    col_dest, col_buc = st.columns([2, 1])
                    with col_dest:
                        destinatie = st.text_input("Unde merge?", placeholder="Ex: Școala 10 / Intern", key="sw_dest")
                    
                    with col_buc:
                        bucati = st.number_input("Bucăți:", 1, 500, step=1, key="sw_qty")

                    submitted = st.form_submit_button("🚀 Lansează Comanda", use_container_width=True)

                                        # ... (restul codului până la submitted)
                    if submitted:
                        if destinatie:
                            # Preluăm prețul (dacă există în obiectul sw_selectat)
                            pret_unitar = sw_selectat.get('pret_standard', 0)
                            total_comanda = bucati * pret_unitar
                            
                            produse_comanda = [{
                                "id": sw_selectat['id'], 
                                "nume": sw_selectat['nume'], 
                                "cantitate": bucati,
                                "pret": pret_unitar
                            }]
                            
                            db.save_comanda_finala(
                                999,               # Clientul CANTINA
                                produse_comanda, 
                                total_comanda,     # <--- Înlocuit 0 cu totalul real (bucăți * preț)
                                "INTERN", 
                                "08:00", 
                                destinatie, 
                                "cantina", 
                                "sandwich",
                                data_plan          # <--- Data selectată în calendarul Admin
                            )
                            
                            st.success(f"✅ Lansat: {bucati}x {sw_selectat['nume']} către {destinatie} (Total: {total_comanda} lei)")
                        else:
                            st.error("⚠️ Trebuie să introduci destinația!")
        # ---------------------------------------------------------
        # MODUL C: SPECIAL / EVENIMENTE (Picker-ul universal)
        # ---------------------------------------------------------
        #st.write("---")
        # --- LANSARE COMANDĂ SPECIALĂ (PROTOCOL / EVENIMENT) ---
        with st.expander("✨ LANSARE COMANDĂ SPECIALĂ (PROTOCOL / EVENIMENT)"):
            tip_spec = st.radio("Tip:", ["special", "eveniment"], horizontal=True, key="rad_spec")
            desc_spec = st.text_input("📍 Descriere OBLIGATORIE (ex: Botez Popescu):", key="obs_spec")
            
            if 'puffer' not in st.session_state: 
                st.session_state.puffer = []
            
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1: 
                p_sel = st.selectbox("Produs:", toate, format_func=lambda x: x['nume'], key="p_spec")
            with c2: 
                q_sel = st.number_input("Cant:", min_value=1, value=1, key="q_spec")
            with c3: 
                st.write("##")
                if st.button("➕ Adaugă"):
                    # Pasul 1: Extragem valoarea indiferent cum se numește în sursă
                    valoare_pret = p_sel.get('pret_standard') if p_sel.get('pret_standard') is not None else p_sel.get('pret', 0)
                    
                    # Pasul 2: SALVĂM în puffer folosind cheia simplă 'pret'
                    st.session_state.puffer.append({
                        "id": p_sel['id'], 
                        "nume": p_sel['nume'], 
                        "cantitate": q_sel,
                        "pret": valoare_pret  # <--- Aici e cheia succesului
                    })
                    st.rerun()
            
            if st.session_state.puffer:
                st.markdown("---")
                for i, item in enumerate(st.session_state.puffer): 
                    col_t, col_r = st.columns([4, 1])
                    # Folosim 'pret' și la afișare
                    col_t.write(f"✅ {item['nume']} x {item['cantitate']} ({item['pret']} lei/buc)")
                    if col_r.button("🗑️", key=f"del_spec_{i}"):
                        st.session_state.puffer.pop(i)
                        st.rerun()
                
                if st.button(f"🚀 Lansează {tip_spec.upper()}", use_container_width=True, type="primary"):
                    if not desc_spec: 
                        st.error("⚠️ Lipsește descrierea!")
                    elif not st.session_state.puffer:
                        st.error("⚠️ Lista de produse este goală!")
                    else:
                        # Pasul 3: CALCULĂM folosind ACEEAȘI CHEIE 'pret'
                        total_spec = sum(item['cantitate'] * item.get('pret', 0) for item in st.session_state.puffer)
                        
                        db.save_comanda_finala(
                            999, 
                            st.session_state.puffer, 
                            total_spec, 
                            "INTERN", 
                            "08:00", 
                            desc_spec, 
                            "cantina", 
                            tip_spec,
                            data_plan 
                        )
                        st.session_state.puffer = []
                        st.success(f"✅ Comanda trimisă! Total: {total_spec:.2f} lei")
                        st.rerun()
    # --- TAB 2: GESTIUNE NOMENCLATOR --- (Păstrăm logica ta originală)
    # =========================================================

    with tab_nom:
        st.subheader("⚙️ Gestiune Produse")
        
        # 1. Formular Adăugare (cu placeholdere text și fără 0.00 la preț)
        with st.expander("➕ Adaugă Produs Nou", expanded=False):
            with st.form("add_produs", clear_on_submit=True):
                col_nume, col_cat, col_pret = st.columns([2, 1, 1])
                with col_nume: 
                    nume_n = st.text_input("Denumire Produs", placeholder="ex: Ciorbă de văduvă...")
                with col_cat: 
                    cat_n = st.selectbox("Categorie", 
                                       options=[None, "felul_1", "felul_2", "salate", "special", "desert"],
                                       format_func=lambda x: "--- Alege ---" if x is None else x)
                with col_pret: 
                    # Folosim value=None pentru a avea placeholder text curat
                    pret_n = st.number_input("Preț (RON)", min_value=0.0, step=0.5, value=None, placeholder="Introduceți prețul...")
                
                submit_add = st.form_submit_button("Salvează în Nomenclator", use_container_width=True)

            if submit_add:
                if nume_n and cat_n and pret_n is not None:
                    db.add_produs(nume_n, cat_n, pret_n)
                    st.success(f"✅ Adăugat cu succes: {nume_n}")
                    st.rerun()
                else:
                    st.error("⚠️ Te rugăm să completezi toate câmpurile!")

        st.divider()

        # 2. Tabel Editabil și Ștergere
        st.subheader("📋 Gestiune Tabelară")
        st.info("💡 Poți edita direct în tabel sau poți bifa 'Șterge' pentru a elimina înregistrări.")
        
        toate_produsele = db.get_toate_produsele()
        
        if toate_produsele:
            df_nom = pd.DataFrame(toate_produsele)
            
            # Adăugăm o coloană temporară pentru ștergere (nu există în DB, e doar pentru UI)
            df_nom["șterge"] = False
            
            # Reordonăm coloanele să fie ID, Nume, Categorie, Preț, Șterge
            df_nom = df_nom[["id", "nume", "categorie", "pret_standard", "șterge"]]

            # Configurăm st.data_editor
            edited_data = st.data_editor(
                df_nom,
                column_config={
                    "id": st.column_config.NumberColumn("ID", disabled=True),
                    "nume": st.column_config.TextColumn("Denumire Produs", required=True),
                    "categorie": st.column_config.SelectboxColumn(
                        "Categorie", 
                        options=["felul_1", "felul_2", "salate", "special", "desert"],
                        required=True
                    ),
                    "pret_standard": st.column_config.NumberColumn("Preț (RON)", min_value=0, format="%.2f"),
                    "șterge": st.column_config.CheckboxColumn("Elimină?", help="Bifează pentru a șterge produsul")
                },
                hide_index=True,
                use_container_width=True,
                key="nomenclator_editor"
            )

            # Buton pentru salvarea tuturor modificărilor (Update + Delete)
            if st.button("💾 Salvează Modificările (Editări și Ștergeri)", use_container_width=True, type="primary"):
                # 1. Identificăm rândurile de șters
                ids_de_sters = edited_data[edited_data["șterge"] == True]["id"].tolist()
                
                # 2. Identificăm rândurile modificate (cele care nu sunt de șters)
                for index, row in edited_data.iterrows():
                    if row['id'] in ids_de_sters:
                        db.delete_produs(row['id'])
                    else:
                        # Verificăm dacă s-a schimbat ceva față de original
                        original_row = df_nom.iloc[index]
                        if not row.equals(original_row):
                            db.update_produs(row['id'], row['nume'], row['categorie'], row['pret_standard'])
                
                st.success("✅ Baza de date a fost actualizată!")
                st.rerun()

            # 3. Export (folosim datele din tabelul afișat)
            st.write("")
            df_export = edited_data[edited_data["șterge"] == False][["nume", "categorie", "pret_standard"]]
            excel_data = utils.export_to_excel(df_export, sheet_name="Nomenclator")
            st.download_button(
                label="📥 Exportă Nomenclatorul (fără cele marcate de șters)",
                data=excel_data,
                file_name=f"Nomenclator_{date.today().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        else:
            st.info("Nomenclatorul este gol.")


    # =========================================================
    # -- TAB 3: MONITORIZARE COMENZI -- (Păstrăm logica ta originală) 
    # =========================================================   
    # =========================================================
    # --- TAB 3: MONITORIZARE ȘI EDITARE COMENZI LANSTATE ---
    # =========================================================
    # Adaugă tab-ul la listă
#    tab_plan, tab_nom, tab_comenzi = st.tabs(["📅 Planificare Zilnică", "📋 Gestiune Nomenclator", "📊 Monitorizare Comenzi"])

    with tab_comenzi:
        st.subheader("📊 Control General Producție & Livrări")
        
        col_d1, col_d2 = st.columns([1, 2])
        with col_d1:
            data_viz = st.date_input("Data:", date.today(), key="admin_view_date")
        
        # Aduce datele din baza de date
        toate_comenzile = db.get_rezumat_zi(data_viz) 

        if not toate_comenzile:
            st.info("Nicio comandă sau lot de producție găsit pentru această dată.")
        else:
            # ---------------------------------------------------------
            # 1. EXPANDERUL VECHI (Reparat împotriva erorii split)
            # ---------------------------------------------------------
            with st.expander("👨‍🍳 REZUMAT TOTAL CANTITĂȚI (Bucătărie)", expanded=False):
                dict_totaluri = {}
                for c in toate_comenzile:
                    detalii_raw = c.get('detalii')
                    
                    ### PROTECȚIE: Dacă detaliile sunt goale, sărim peste această comandă
                    if not detalii_raw or detalii_raw is None:
                        continue
                    
                    parti = detalii_raw.split(', ')
                    for p in parti:
                        try:
                            if 'x ' in p:
                                qty_str, nume_p = p.split('x ', 1)
                                dict_totaluri[nume_p] = dict_totaluri.get(nume_p, 0) + int(qty_str)
                        except: continue
                
                if dict_totaluri:
                    df_summary = pd.DataFrame([{"Produs": k, "Total Porții": v} for k, v in dict_totaluri.items()])
                    st.table(df_summary)
                else:
                    st.write("Nu există produse de centralizat.")

# ---------------------------------------------------------
            # 2. NOUL EXPANDER: REZUMAT FINANCIAR ȘI PE SECȚII
            # ---------------------------------------------------------
# ---------------------------------------------------------
            # SECȚIUNEA 2: REZUMAT FINANCIAR ȘI PE SECȚII (MODIFICATĂ)
            # ---------------------------------------------------------
            # ---------------------------------------------------------
            # 2. REZUMAT FINANCIAR (Grupare automată după MENIURI/TIPURI)
            # ---------------------------------------------------------
            sectii = {}
            total_general = 0
            
            # Pasul 1: Colectăm datele și grupăm totul
            for c in toate_comenzile:
                # 'categoria' va fi PRANZ, CINA, SANDWICH etc., exact cum e definit meniul
                categoria = str(c.get('tip_comanda', 'ALTELE')).upper().strip()
                valoare = c.get('total_plata', 0)
                
                if categoria not in sectii:
                    sectii[categoria] = {"produse": {}, "bani": 0}
                
                sectii[categoria]["bani"] += valoare
                total_general += valoare

                detalii_raw = c.get('detalii')
                if detalii_raw:
                    parti = detalii_raw.split(', ')
                    for p in parti:
                        if 'x ' in p:
                            try:
                                qty_str, rest = p.split('x ', 1)
                                # Tăiem statusul |gatit sau |nou pentru a avea tabel curat
                                nume_p = rest.split('|')[0] 
                                sectii[categoria]["produse"][nume_p] = sectii[categoria]["produse"].get(nume_p, 0) + int(qty_str)
                            except: continue

            # Pasul 2: Construim titlul dinamic pentru expander
            elemente_titlu = [f"{cat}: {date_cat['bani']:.0f} lei" for cat, date_cat in sectii.items()]
            titlu_final = "💰 Rezumat Zi: " + " | ".join(elemente_titlu) + f" —— TOTAL: {total_general:.2f} lei"

            # Pasul 3: Afișăm Expanderul (Închis default)
            with st.expander(titlu_final, expanded=False):
                if not sectii:
                    st.info("Nicio comandă procesabilă pentru această dată.")
                else:
                    # Afișăm sub-tabele pentru fiecare tip de meniu găsit
                    for nume_cat, date_cat in sectii.items():
                        with st.container(border=True):
                            c1, c2 = st.columns([3, 1])
                            # Exemplu: 📍 CATEGORIE: PRANZ
                            c1.markdown(f"#### 📍 {nume_cat}")
                            c2.metric("Vânzări", f"{date_cat['bani']:.2f} lei")
                            
                            if date_cat["produse"]:
                                df_cat = pd.DataFrame([
                                    {"Produs": k, "Cantitate": v} 
                                    for k, v in date_cat["produse"].items()
                                ])
                                # Stilizăm puțin tabelul să fie discret
                                st.table(df_cat)
            # 3. LISTA DETALIATĂ (Codul tău original)
            # ---------------------------------------------------------
            # ---------------------------------------------------------
            st.markdown("### 📝 Detalii Comenzi & Status Real-Time")

            for cz in toate_comenzile:
                # 1. Pregătim datele pentru Titlul Expanderului
                icon_tip = "🚚" if cz['tip_comanda'] == 'livrare' else "🏢"
                ora = str(cz['ora_livrare_estimata'])[:5]
                client = cz['client']
                suma = cz.get('total_plata', 0)
                
                # Mapare Status pentru Titlu
                status_emoji = {
                    'nou': "🔵",
                    'pregatit': "🟢",
                    'livrat': "⚪"
                }.get(cz['status_comanda'], "❓")
                
                status_text = cz['status_comanda'].upper()

                # 2. Construim titlul compact al expanderului
                # Format: [Status] Ora - Client - Suma - Tip
                titlu_compact = f"{status_emoji} {status_text} | {ora} | {client} | {suma:.2f} lei | {icon_tip}"

                # 3. Creăm Expanderul
                with st.expander(titlu_compact):
                    col_stanga, col_dreapta = st.columns([3, 1])
                    
                    with col_stanga:
                        st.write("**Produse și Stadiu Producție:**")
                        if cz['detalii']:
                            linii = cz['detalii'].split(', ')
                            for linie in linii:
                                try:
                                    # Procesăm statusul individual al produsului
                                    produs_full, stare = linie.split('|')
                                    if stare == 'gatit':
                                        st.markdown(f"✅ :green[{produs_full}]")
                                    else:
                                        st.markdown(f"⏳ :orange[{produs_full}]")
                                except:
                                    st.write(f"• {linie}")
                        else:
                            st.caption("Fără produse")

                        st.divider()
                        # Date contact (utile pentru recepție/admin)
                        st.caption(f"📞 {cz.get('telefon', 'N/A')} | 💳 {cz.get('metoda_plata', '').upper()}")
                        if cz['tip_comanda'] == 'livrare':
                            st.caption(f"📍 {cz.get('adresa_principala', 'N/A')}")

                    with col_dreapta:
                        st.write("") # Spațiere
                        # Putem adăuga un buton de vizualizare rapidă sau print dacă e cazul
                        if st.button("Anulează", key=f"admin_cancel_{cz['id']}", use_container_width=True):
                            # Exemplu: dacă vrei să-i pui status 'anulat' în loc să o ștergi direct
                            db.update_status_comanda(engine, cz['id'], 'anulat')
                            st.rerun()
                        
                        if st.button("🗑️ Șterge", key=f"admin_del_{cz['id']}", use_container_width=True):
                            if db.delete_comanda(cz['id']):
                                st.rerun()

        st.divider()
        st.subheader("📊 Raportare Periodică")

        # 1. Selecție Interval
        today = utils.get_ro_time().date()
        first_day = today.replace(day=1) # Prima zi a lunii curente

        interval = st.date_input(
            "Selectează intervalul:",
            value=(first_day, today),
            max_value=today
        )

        # Verificăm dacă utilizatorul a selectat ambele date (start și end)
        if isinstance(interval, tuple) and len(interval) == 2:
            d_start, d_end = interval
            
            if st.button("Generează Raport"):
                date_raport = db.get_raport_interval(d_start, d_end)
                
                if not date_raport:
                    st.info(f"Nicio comandă găsită între {d_start} și {d_end}")
                else:
                    st.write(f"### Rezultat: {d_start} -> {d_end}")
                    
                    # Creăm coloane pentru statistici rapide
                    total_per_perioada = sum(r['total_valoare'] for r in date_raport)
                    nr_total = sum(r['nr_comenzi'] for r in date_raport)
                    
                    c1, c2 = st.columns(2)
                    c1.metric("Total Încasări (brut)", f"{total_per_perioada:.2f} lei")
                    c2.metric("Număr Total Comenzi", nr_total)
                    
                    # Tabel detaliat pe secții
                    df_raport = pd.DataFrame(date_raport)
                    df_raport.columns = ['Secția', 'Total Valoare (lei)', 'Nr. Comenzi']
                    st.table(df_raport)          