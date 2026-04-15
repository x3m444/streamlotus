import streamlit as st
import pandas as pd
from datetime import date
import database as db

def show(db, utils, toate):
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
        with st.expander("💰 REZUMAT FINANCIAR ȘI PE SECȚII", expanded=True):
            sectii = {}
            
            for c in toate_comenzile:
                # Identificăm tipul (PRANZ, CINA, LIVRARE etc.)
                tip = str(c.get('tip_comanda', 'ALTELE')).upper()
                
                if tip not in sectii:
                    sectii[tip] = {"produse": {}, "bani": 0}
                
                # Acum c.get('total_plata') va aduce valoarea reală din SQL, nu 0
                valoare_comanda = c.get('total_plata', 0)
                sectii[tip]["bani"] += valoare_comanda
                
                detalii_raw = c.get('detalii')
                # Protecție pentru comenzi fără produse
                if not detalii_raw:
                    continue
                
                parti = detalii_raw.split(', ')
                for p in parti:
                    try:
                        if 'x ' in p:
                            qty_str, nume_p = p.split('x ', 1)
                            qty = int(qty_str)
                            sectii[tip]["produse"][nume_p] = sectii[tip]["produse"].get(nume_p, 0) + qty
                    except: 
                        continue

            if not sectii:
                st.info("Nicio comandă procesabilă pentru această dată.")
            else:
                total_general_zi = 0
                
                for nume_sectie, date_sectie in sectii.items():
                    st.markdown(f"#### 📍 SECȚIA: {nume_sectie}")
                    
                    # Afișăm tabelul de produse dacă există
                    if date_sectie["produse"]:
                        df_sectie = pd.DataFrame([
                            {"Produs": k, "Cantitate": v} 
                            for k, v in date_sectie["produse"].items()
                        ])
                        st.table(df_sectie)
                    
                    valoare_sectie = date_sectie["bani"]
                    total_general_zi += valoare_sectie
                    
                    # Afișăm subtotalul valoric pe secție
                    st.metric(label=f"Subtotal {nume_sectie}", value=f"{valoare_sectie} lei")
                    st.divider()
                
                # Totalul mare la finalul expanderului
                st.subheader(f"💵 TOTAL GENERAL ZI: {total_general_zi} lei")
        # ---------------------------------------------------------
        # 3. LISTA DETALIATĂ (Codul tău original)
        # ---------------------------------------------------------
        st.markdown("### 📝 Detalii Comenzi")
        for cz in toate_comenzile:
            icon = "🚚" if cz['tip_comanda'] == 'livrare' else "🏢"
            
            with st.container():
                # Am ajustat puțin proporțiile coloanelor pentru a face loc prețului
                c1, c2, c3, c4 = st.columns([1, 2.5, 4, 1.5])
                
                c1.write(f"🕒 {str(cz['ora_livrare_estimata'])[:5]}")
                
                with c2:
                    st.markdown(f"**{icon} {cz['client']}**")
                    st.caption(f"Tip: {cz.get('tip_comanda', 'N/A').upper()}")
                    # Afișăm metoda de plată să știm dacă e cash sau intern
                    st.caption(f"💳 {cz.get('metoda_plata', 'N/A').upper()}")

                with c3:
                    txt_detalii = cz['detalii'].replace(', ', '\n\n') if cz['detalii'] else "Fără produse"
                    st.info(txt_detalii)

                with c4:
                    # Afișăm prețul total al comenzii
                    suma = cz.get('total_plata', 0)
                    st.markdown(f"### {suma:.2f} lei")
                    
                    # Butonul de ștergere mai jos
                    if st.button("🗑️", key=f"admin_del_{cz['id']}", use_container_width=True):
                        if db.delete_comanda(cz['id']):
                            st.rerun()
            
            st.divider()

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