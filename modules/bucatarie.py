import streamlit as st
import pandas as pd
import database as db
import utils  # Importăm fișierul nou creat
from datetime import date


engine = db.get_engine()
def show_bucatarie():
    st.header("👨‍🍳 Monitor Producție și Expediție")
    
    # Selecția datei - la fel ca în restul aplicației
    data_selectata = st.date_input("Comenzi pentru data:", value=date.today())
    
    tab_productie, tab_expeditie = st.tabs(["🔥 1. Totaluri Producție", "📦 2. Pregătire Comenzi"])

    # --- TAB 1: TOTALURI (Ce are de gătit bucătarul) ---
    with tab_productie:
        # 1. Luăm toate comenzile zilei (fără să filtrăm după status_comanda, 
        # deoarece vrem să vedem statusul individual al produselor din interior)
        comenzi_relevante = db.get_rezumat_zi(data_filtrare=data_selectata)

        if not comenzi_relevante:
            st.info("Nu sunt comenzi înregistrate pentru această dată.")
        else:
            # 2. Reconstruim situația pe produse (Ciorbă, Pizza, etc.)
            situatie_produse = {}
            
            for cmd in comenzi_relevante:
                # Luăm șirul de detalii: "1x Ciorba|nou, 2x Pizza|gatit"
                detalii_string = cmd.get('detalii', '')
                if not detalii_string:
                    continue
                    
                linii = detalii_string.split(', ')
                for linie in linii:
                    try:
                        # Separăm produsul de statusul lui folosind separatorul "|"
                        parti = linie.split('|')
                        text_produs = parti[0]  # "1x Ciorba"
                        status_produs = parti[1] # "nou" sau "gatit"
                        
                        # Extragem cantitatea și numele
                        cant_text, nume_produs = text_produs.split('x ', 1)
                        cantitate = int(cant_text)
                        
                        # Dacă produsul nu e în dicționar, îl inițializăm
                        if nume_produs not in situatie_produse:
                            situatie_produse[nume_produs] = {"nou": 0, "gatit": 0}
                        
                        # Adunăm cantitatea la statusul corespunzător
                        situatie_produse[nume_produs][status_produs] += cantitate
                    except Exception as e:
                        # Dacă o linie e formatată greșit, o sărim
                        continue

            # 3. Afișăm interfața pentru bucătar
            if not situatie_produse:
                st.warning("Comenzile nu conțin produse valide.")
            else:
                for nume, info in situatie_produse.items():
                    total_portii = info['nou'] + info['gatit']
                    este_gata_tot = (info['nou'] == 0)
                    
                    # Container vizual pentru fiecare categorie (Ciorbe, Paste, etc.)
                    with st.container(border=True):
                        col1, col2 = st.columns([2.5, 1.5])
                        
                        with col1:
                            if este_gata_tot:
                                st.markdown(f"### :green[✅ {nume}]")
                                st.write(f"Toate cele **{info['gatit']}** porții sunt finalizate.")
                            else:
                                st.markdown(f"### 🔥 {nume}")
                                st.write(f"Mai ai de făcut: **{info['nou']}** / {total_portii} porții")
                        
                        with col2:
                            # Adăugăm un pic de spațiu pentru aliniere
                            st.write("---") 
                            
                            if not este_gata_tot:
                                # Butonul principal pentru bucătar
                                if st.button(f"Gata {nume}", key=f"btn_done_{nume}", use_container_width=True):
                                    db.update_status_batch(engine, data_selectata, nume, "gatit")
                                    st.rerun()
                            else:
                                # Butonul de RESET (dacă s-a greșit ceva sau s-a vărsat porția)
                                if st.button(f"🔄 Reset {nume}", key=f"btn_reset_{nume}", use_container_width=True):
                                    db.update_status_batch(engine, data_selectata, nume, "nou")
                                    st.rerun()
                                st.caption("Produs marcat ca GATIT")
            # --- TAB 2: EXPEDIȚIE (Ambalarea pe bonuri) ---
    with tab_expeditie:
        # Luăm comenzile cu status 'nou'
        comenzi_ambalare = db.get_rezumat_zi(data_filtrare=data_selectata, status_filtru='nou')

        if not comenzi_ambalare:
            st.info("Nu sunt comenzi de ambalat.")
        else:
            for cmd in comenzi_ambalare:
                # Analizăm produsele
                linii = cmd['detalii'].split(', ')
                nr_total = len(linii)
                nr_gatite = sum(1 for l in linii if '|gatit' in l)
                toate_gata = (nr_total == nr_gatite)
                
                # Etichetă și Culoare Titlu
                icon = "🟢" if toate_gata else "🟡"
                status_txt = "GATA" if toate_gata else f"INCOMPLET ({nr_gatite}/{nr_total})"
                titlu = f"{icon} {status_txt} | Comanda #{cmd['id']} - {cmd['client']}"
                
                # Expander - se deschide automat doar dacă e GATA
                with st.expander(titlu, expanded=toate_gata):
                    c1, c2 = st.columns([3, 1])
                    
                    with c1:
                        st.write("**Produse:**")
                        for linie in linii:
                            p_nume, p_stare = linie.split('|')
                            if p_stare == 'gatit':
                                st.markdown(f"✅ {p_nume}")
                            else:
                                st.markdown(f"⏳ :red[{p_nume}]")
                        
                        st.caption(f"📞 {cmd['telefon']} | 📍 {cmd['adresa_principala']}")

                    with c2:
                        st.write("") # Spațiu vertical
                        if toate_gata:
                            # Aici folosim funcția de ID specific
                            if st.button("📦 LIVRARE", key=f"ship_{cmd['id']}", use_container_width=True):
                                db.update_status_comanda(engine, cmd['id'], 'pregatit')
                                st.success("Trimis la șofer!")
                                st.rerun()
                        else:
                            st.button("📦 Așteaptă", key=f"wait_{cmd['id']}", disabled=True, use_container_width=True)