import streamlit as st
import pandas as pd
import database as db
import utils  # Importăm fișierul nou creat
from datetime import date

def show(db, data_plan, toate):
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