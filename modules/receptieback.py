import streamlit as st
import database as db
from datetime import date
from datetime import datetime
import utils # Importăm fișierul de utilitare

# Variabile globale pentru acest script, calculate la fiecare refresh
acum = utils.get_ro_time()
data_azi = acum.date()
ora_acum = acum.strftime("%H:%M")

# Acum folosești data_azi peste tot:
st.write(f"Data curentă sistem: {data_azi}")

# În Rezumat, selectorul se va deschide mereu pe data corectă:
data_filtrare = st.date_input("Alege data:", value=data_azi)

def main_receptie_page():
    # Creăm cele două tab-uri la nivel înalt
    tab1, tab2 = st.tabs(["🆕 Introducere Comenzi", "📊 Rezumat Livrări"])

    with tab1:
        # Apelăm funcția ta existentă. 
        # Tot ce ai scris tu până acum și funcționează rămâne aici.
        show_receptie() 

    with tab2:
        # Aici punem codul nou, separat, care nu va deranja show_receptie
        render_rezumat_zi()
####receptiecomenzi####
def show_receptie():

    
    st.title("📞 Recepție Comenzi")
    if 'buffer_comanda' not in st.session_state:
        st.session_state.buffer_comanda = []
    # --- 1. SELECTARE DATĂ COMANDĂ ---
    st.subheader("📅 Programare Comandă")
    data_selectata = st.date_input(
        "Pentru ce dată este comanda?", 
        value=utils.get_ro_time().date(), # Implicit este azi
        min_value=utils.get_ro_time().date(), # Nu putem pune comenzi în trecut
        key="data_comanda_selector"
    )

    # Acum, restul codului va depinde de 'data_selectata', nu de 'data_azi'
    plan_zi = db.get_meniu_planificat(data_selectata)
    # 1. Inițializăm variabilele (exact ca în tabela SQL)
    client_id = None
    nume_client = ""
    telefon = ""
    adresa_principala = ""

    # 2. Preluăm TOȚI clienții din bază pentru selectbox (ordonat alfabetic)
    # Presupunem că db.get_all_clienti() returnează lista ordonată
    toti_clientii = db.get_all_clienti() 

    # 3. CASETA UNICĂ: Selectează sau caută prin tastare
    opțiuni_clienti = {f"{c['nume_client']} | {c['telefon']}": c for c in toti_clientii}
    lista_nume = sorted(list(opțiuni_clienti.keys())) # Ordonare alfabetică

    selectie = st.selectbox(
        "👤 Selectează Clientul (sau caută după nume/telefon):",
        ["-- Client Nou / Adaugă Persoană --"] + lista_nume
    )

    # Dacă am ales un client existent, îi încărcăm datele
    if selectie != "-- Client Nou / Adaugă Persoană --":
        c = opțiuni_clienti[selectie]
        client_id = c['id']
        nume_client = c['nume_client']
        telefon = c['telefon']
        adresa_principala = c['adresa_principala']

    # 4. EXPANDERUL (Închis implicit)
    # Se deschide manual doar dacă vrem să creăm un client nou sau să edităm adresa celui selectat
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

#    st.divider()
    # Aici urmează secțiunea de produse...

    # --- 2. SELECȚIE PRODUSE ---
    st.divider()
    # --- 2. PRELUARE DATE (Sursă Dublă: Planificare la data aleasă + Nomenclator) ---
    # FOARTE IMPORTANT: Folosim data_selectata de mai sus
    plan_zi = db.get_meniu_planificat(data_selectata)
    nomenclator_complet = db.get_nomenclator_produse()

    # A. Pentru Meniuri Rapide (Din Planificarea datei alese)
    lista_f1_plan = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2_plan = [p for p in plan_zi if p['categorie'] == 'felul_2']
    lista_salate_plan = [p for p in plan_zi if p['categorie'] == 'salate']
    # ... restul codului rămâne la fel (toate_f1, toate_f2, etc.) ...

    # B. Pentru Speciale și Custom (Din tot Nomenclatorul - Libertate Totală)
    lista_toate_specialele = [p for p in nomenclator_complet if p['categorie'] == 'special']
    toate_f1 = [p for p in nomenclator_complet if p['categorie'] == 'felul_1']
    toate_f2 = [p for p in nomenclator_complet if p['categorie'] == 'felul_2']

    # C. Definire Nume și Prețuri pentru Butoanele Rapide (Zero Hardcoding)
    # Felul 1
    nume_f1 = lista_f1_plan[0]['nume'] if lista_f1_plan else "Felul 1"
    pret_f1 = lista_f1_plan[0].get('pret_standard', 0) if lista_f1_plan else 0

    # Felul 2 - Varianta 1
    nume_f2_v1 = lista_f2_plan[0]['nume'] if len(lista_f2_plan) >= 1 else "Felul 2 V1"
    pret_f2_v1 = lista_f2_plan[0].get('pret_standard', 0) if len(lista_f2_plan) >= 1 else 0

    # Felul 2 - Varianta 2
    nume_f2_v2 = lista_f2_plan[1]['nume'] if len(lista_f2_plan) >= 2 else "Felul 2 V2"
    pret_f2_v2 = lista_f2_plan[1].get('pret_standard', 0) if len(lista_f2_plan) >= 2 else 0
    ##Salata##
    nume_salata = lista_salate_plan[0]['nume'] if lista_salate_plan else "Salată"
    pret_salata = lista_salate_plan[0].get('pret_standard', 0) if lista_salate_plan else 0
 # --- ZONA A: MENIURI RAPIDE (DINAMICĂ ȘI FĂRĂ HARDCODING) ---
    st.markdown(f"#### 🍱 Meniuri și Porții Rapide - {data_azi.strftime('%d/%m/%Y')}")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.info(f"Meniul Zilei ({nume_f1})")
        m_v1 = st.number_input(f"Meniu cu {nume_f2_v1}", min_value=0, step=1, key="rapid_v1")
        m_v2 = st.number_input(f"Meniu cu {nume_f2_v2}", min_value=0, step=1, key="rapid_v2")
        
        if st.button("➕ Adaugă Meniurile", key="btn_m_rapide"):
            # --- LOGICĂ PENTRU VARIANTA 1 ---
            if m_v1 > 0:
                # 1. Adăugăm Felul 1 (Ciorba)
                st.session_state.buffer_comanda.append({
                    "nume": nume_f1, 
                    "cantitate": m_v1, 
                    "pret": pret_f1, 
                    "tip": "Meniu V1 (F1)"
                })
                # 2. Adăugăm Felul 2 (Tocana/Sarmale/etc)
                st.session_state.buffer_comanda.append({
                    "nume": nume_f2_v1, 
                    "cantitate": m_v1, 
                    "pret": pret_f2_v1, 
                    "tip": "Meniu V1 (F2)"
                })
                st.session_state.buffer_comanda.append({
                    "nume": nume_salata, 
                    "cantitate": m_v1, 
                    "pret": pret_salata, 
                    "tip": "Meniu V1 (S)"
                })
            # --- LOGICĂ PENTRU VARIANTA 2 ---
            if m_v2 > 0:
                # 1. Adăugăm Felul 1 (Ciorba)
                st.session_state.buffer_comanda.append({
                    "nume": nume_f1, 
                    "cantitate": m_v2, 
                    "pret": pret_f1, 
                    "tip": "Meniu V2 (F1)"
                })
                # 2. Adăugăm Felul 2 (Varianta 2)
                st.session_state.buffer_comanda.append({
                    "nume": nume_f2_v2, 
                    "cantitate": m_v2, 
                    "pret": pret_f2_v2, 
                    "tip": "Meniu V2 (F2)"
                })
                st.session_state.buffer_comanda.append({
                    "nume": nume_salata, 
                    "cantitate": m_v2, 
                    "pret": pret_salata, 
                    "tip": "Meniu V2 (S)"
                })
            st.rerun()

    with col2:
        st.warning("Componente Solo")
        f1_s = st.number_input(f"Doar {nume_f1}", min_value=0, step=1, key="rapid_f1")
        f2_v1 = st.number_input(f"Doar {nume_f2_v1}", min_value=0, step=1, key="rapid_f2v1")
        
        if st.button("➕ Adaugă Solo V1", key="btn_s1_rapide"):
            if f1_s > 0:
                st.session_state.buffer_comanda.append({
                    "nume": f"{nume_f1} (Solo)", 
                    "cantitate": f1_s, 
                    "pret": pret_f1, 
                    "tip": "Solo"
                })
            if f2_v1 > 0:
                st.session_state.buffer_comanda.append({
                    "nume": f"{nume_f2_v1} (Solo)", 
                    "cantitate": f2_v1, 
                    "pret": pret_f2_v1, 
                    "tip": "Solo"
                })
                st.session_state.buffer_comanda.append({
                    "nume": nume_salata, 
                    "cantitate": f2_v1, 
                    "pret": pret_salata, 
                    "tip": "Solo (S)"
                })
            
            st.rerun()

    with col3:
        st.success("Opțiuni V2")
        f2_v2 = st.number_input(f"Doar {nume_f2_v2}", min_value=0, step=1, key="rapid_f2v2")
        
        if st.button("➕ Adaugă Solo V2", key="btn_s2_rapide"):
            if f2_v2 > 0:
                st.session_state.buffer_comanda.append({
                    "nume": f"{nume_f2_v2} (Solo)", 
                    "cantitate": f2_v2, 
                    "pret": pret_f2_v2, 
                    "tip": "Solo"
                })
                st.session_state.buffer_comanda.append({
                    "nume": nume_salata, 
                    "cantitate": f2_v2, 
                    "pret": pret_salata, 
                    "tip": "Solo (S)"
                })
            st.rerun()

    st.divider()
    # --- ZONA B: PRODUSE SPECIALE ȘI MENIU COMPUS ---
    st.markdown("#### 🛠️ Produse Speciale & Meniu Special")
    tab_spec, tab_custom = st.tabs(["✨ Produse Speciale", "🍱 Meniu Special"])

    with tab_spec:
        c1, c2, c3 = st.columns([3, 1, 1])
        with c1:
            # Folosim lista completă de speciale din nomenclator
            sel_s = st.selectbox(
                "✨ Alege din tot Nomenclatorul Speciale:", 
                options=lista_toate_specialele, 
                format_func=lambda x: f"{x['nume']} - {x.get('pret_standard', 0)} lei", 
                index=None, 
                placeholder="Caută produs (ex: Pepsi, Desert...)",
                key="sb_spec_liber"
            )
        with c2:
            qty_s = st.number_input("Bucăți", min_value=1, step=1, key="q_spec_liber")
        with c3:
            st.write("")
            if st.button("➕ Adaugă Special", key="btn_spec_liber"):
                if sel_s:
                    st.session_state.buffer_comanda.append({
                        "nume": sel_s['nume'], 
                        "cantitate": qty_s, 
                        "pret": sel_s.get('pret_standard', 0), 
                        "tip": "Special"
                    })
                    st.rerun()
                else:
                    st.warning("Selectează un produs mai întâi!")

    with tab_custom:
        cm1, cm2, cm3, cm4 = st.columns([2, 2, 1, 1])
        
        with cm1:
            f1_sel = st.selectbox(
                "Felul 1 (Toate):", 
                options=toate_f1, 
                # AICI am adăugat prețul în paranteză:
                format_func=lambda x: f"{x['nume']} ({x.get('pret_standard', 0)} lei)", 
                index=None, 
                placeholder="Alege ciorbă...",
                key="sb_f1_custom_liber"
            )
            
        with cm2:
            f2_sel = st.selectbox(
                "Felul 2 (Toate):", 
                options=toate_f2, 
                # ȘI AICI am adăugat prețul:
                format_func=lambda x: f"{x['nume']} ({x.get('pret_standard', 0)} lei)", 
                index=None, 
                placeholder="Alege fel 2...",
                key="sb_f2_custom_liber"
            )
            
        with cm3:
            qty_m = st.number_input("Meniuri", min_value=1, step=1, key="q_m_v4_liber")
            
        with cm4:
            st.write("")
            if st.button("➕ Adaugă Meniu", key="btn_m_v4_liber"):
                if f1_sel and f2_sel: 
                    # 1. Extragem prețurile direct din obiectele selectate
                    pret_f1 = f1_sel.get('pret_standard', 0)
                    pret_f2 = f2_sel.get('pret_standard', 0)
                    
                    # 2. Adăugăm Felul 1 în buffer
                    st.session_state.buffer_comanda.append({
                        "nume": f1_sel['nume'], 
                        "cantitate": qty_m, 
                        "pret": pret_f1, 
                        "tip": "Custom F1"
                    })
                    
                    # 3. Adăugăm Felul 2 în buffer
                    st.session_state.buffer_comanda.append({
                        "nume": f2_sel['nume'], 
                        "cantitate": qty_m, 
                        "pret": pret_f2, 
                        "tip": "Custom F2"
                    })
                    
                    # Calculăm totalul adăugat doar pentru notificare
                    total_adaugat = (pret_f1 + pret_f2) * qty_m
                    st.success(f"✅ Adăugat! Total: {total_adaugat} lei")
                    st.rerun()
                else:
                    st.warning("⚠️ Selectează ambele feluri!")
# --- ZONA C: REZUMAT COMANDĂ ȘI CALCUL TOTAL ---
    st.divider()
    total_p = 0 

    if st.session_state.buffer_comanda:
        st.subheader("📋 Rezumat Comandă")
        
        # Tabel pentru vizualizarea produselor adăugate
        for i, item in enumerate(st.session_state.buffer_comanda):
            subtotal_item = item['pret'] * item['cantitate']
            total_p += subtotal_item
            
            col_n, col_q, col_p, col_x = st.columns([4, 1, 1, 1])
            with col_n:
                st.write(f"**{item['nume']}**")
            with col_q:
                st.write(f"{item['cantitate']} buc")
            with col_p:
                st.write(f"{subtotal_item} lei")
            with col_x:
                if st.button("❌", key=f"del_prod_{i}"):
                    st.session_state.buffer_comanda.pop(i)
                    st.rerun()
        
        st.markdown(f"### 💰 Total de plată: {total_p} lei")
    else:
        st.info("Coșul este gol. Adaugă produse din secțiunile de mai sus.")

    # --- ZONA D: LOGISTICĂ ȘI LIVRARE ---
    st.divider()

    # Preluăm lista oficială
    lista_livratori_reali = db.get_lista_livratori()

    # --- REZUMAT DATĂ ȘI ORA ---
    # Afișăm clar data pentru care se salvează, ca să nu existe dubii la precomenzi
    st.warning(f"🗓️ Comanda va fi programată pentru data de: **{data_selectata.strftime('%d/%m/%Y')}**")

    col_ora, col_sofer = st.columns(2)

    with col_ora:
        st.subheader("🕒 Programare")
        intervale = ["11:00-11:30", "11:30-12:00", "12:00-12:30", "12:30-13:00", "13:00-13:30", "13:30-14:00", "URGENT"]
        ora_livrare = st.select_slider("Selectează ora:", options=intervale, value="12:00-12:30", key="ora_v9")

    with col_sofer:
        st.subheader("🚚 Livrator")
        sofer = st.selectbox(
            "Cine preia comanda?",
            options=lista_livratori_reali,
            key="sofer_v9"
        )

    # 1. Alegerea metodei de plată
    metoda_plata = st.selectbox("Metoda de Plată:", ["cash", "card", "factura"])

    if metoda_plata == "cash":
        st.info(f"💰 Suma de încasat de șofer: {total_p} lei")
    else:
        st.warning(f"💳 Plată prin {metoda_plata}. Șoferul NU încasează numerar.")

    # 2. Câmpul de observații
    # Înlocuiește st.text_area cu st.text_input
    obs_comanda = st.text_input("📝 Observații (Adresă, detalii):", value="", key="obs_final")

    st.divider()

    # 3. BUTONUL FINAL (Unic și Complet)
    if st.button("💾 SALVEAZĂ COMANDA FINALĂ", type="primary", width="stretch"):
        if not st.session_state.buffer_comanda:
            st.warning("⚠️ Comanda nu are produse!")
        else:
            # Trimitem variabila data_selectata către funcția de salvare
            # Am adăugat 'data_comanda=data_selectata' în apelul funcției
            succes = db.save_comanda_finala(
                client_id=client_id,
                produse=st.session_state.buffer_comanda,
                total=total_p,
                sofer=sofer,
                ora=ora_livrare,
                obs=obs_comanda,
                plata=metoda_plata,
                tip_comanda="livrare",
                data_comanda=data_selectata  # <--- ACESTA ESTE PARAMETRUL NOU
            )
            
            if succes:
                st.success(f"✅ Comandă salvată pentru {data_selectata.strftime('%d/%m/%Y')}! Livrator: {sofer}")
                # Curățăm buffer-ul
                st.session_state.buffer_comanda = []
                st.rerun()
####receptiecomenziend#####                
def render_rezumat_zi():
    data_azi_ro = utils.get_ro_time().date()
    st.header(f"📋 Situație Livrări - {data_azi_ro.strftime('%d-%m-%Y')}")
    
    data_pt_rezumat = st.date_input("Selectează data pentru rezumat:", data_azi_ro)
    comenzi = db.get_rezumat_zi(data_pt_rezumat) 
    
    if not comenzi:
        st.info(f"Fără comenzi în data de {data_pt_rezumat.strftime('%d-%m-%Y')}.")
        return

    total_incasat = sum(c.get('total_plata', 0) for c in comenzi)
    st.metric("Total CASH de încasat", f"{total_incasat} lei")

    livratori = db.get_lista_livratori()
    
    for l in livratori:
        comenzi_sofer = [c for c in comenzi if c['sofer'] == l]
        
        if comenzi_sofer:
            suma_l = sum(s.get('total_plata', 0) for s in comenzi_sofer)
            with st.expander(f"🚚 {l.upper()} — Total Cash: {suma_l} lei"):
                
                # Reorganizăm coloanele: Ora, Client/Tel, Produse, Sumă, Acțiuni
                h1, h2, h3, h4, h5 = st.columns([0.8, 3, 4, 1.2, 0.8])
                h1.write("**Ora**")
                h2.write("**Client & Adresă**")
                h3.write("**Produse (Listă)**")
                h4.write("**Suma Cash**")
                h5.write("**Șterge**")
                st.divider()

                for cz in comenzi_sofer:
                    c1, c2, c3, c4, c5 = st.columns([0.8, 3, 4, 1.2, 0.8])
                    
                    with c1:
                        st.write(f"🕒 {str(cz['ora_livrare_estimata'])[:5]}")
                    
                    with c2:
                        st.write(f"👤 **{cz['client']}**")
                        if cz.get('telefon'):
                            st.write(f"📞 **{cz['telefon']}**") # Bold pe număr pentru vizibilitate
                        st.caption(f"📍 {cz['adresa_principala']}")
                    
                    with c3:
                        # Transformăm virgulele în rânduri noi pentru a avea produsele unul sub altul
                        produse_formatate = cz['detalii'].replace(', ', '\n\n')
                        st.info(produse_formatate)
                    
                    with c4:
                        # Suma apare distinct și mare
                        st.subheader(f"{cz['total_plata']} lei")
                        st.caption(f"Metoda: {cz['metoda_plata']}")
                    
                    with c5:
                        if st.button("🗑️", key=f"del_{cz['id']}", help="Șterge comanda"):
                            if db.delete_comanda(cz['id']):
                                st.rerun()
                    
                    st.divider()