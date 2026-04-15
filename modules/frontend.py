import streamlit as st
import database as db
from datetime import date

def show_landing_page():
    # Titlul principal cu logo-ul tau
    st.title("🍱 CANTINA LOTUS")
    st.subheader("Mâncare gătită zilnic, livrată la ușa ta")
    
    st.divider()

    col_menu, col_info = st.columns([2, 1])

    with col_menu:
        st.markdown("### 📅 Meniul Zilei")
        ziua_azi = date.today()
        meniu_azi = db.get_meniu_planificat(ziua_azi)
        
        if meniu_azi:
            for p in meniu_azi:
                # Folosim formatul nativ Streamlit pentru claritate
                nume = p['nume']
                pret = p['pret_standard']
                if pret > 0:
                    st.write(f"✅ **{nume}** : {pret} LEI")
                else:
                    st.write(f"✅ **{nume}**")

            # Caseta de oferte folosind un element nativ "info"
            st.info(f"""
            **💰 OFERTE SPECIALE:**
            * **FELUL 1 + FEL PRINCIPAL:** 28 LEI
            * **DOAR FELUL 1 (CIORBĂ):** 10 LEI
            """)
        else:
            st.warning("Meniul de astăzi este în curs de actualizare. Reveniți după ora 09:30!")

        # --- SECȚIUNEA: ALTE PREPARATE (FĂRĂ SALATE) ---
        # --- SECȚIUNEA: ALTE PREPARATE & DESERTURI ---
        # --- SECȚIUNEA: SPECIALITĂȚI (TOATE) ---
        st.write("")
        st.markdown("### ✨ Alte preparate & Specialități")
        toate = db.get_toate_produsele()
        
        speciale = [p for p in toate if p['categorie'] == 'special']
        
        if speciale:
            # Folosim coloane pentru a economisi spațiu dacă sunt multe
            col_s1, col_s2 = st.columns(2)
            for i, s in enumerate(speciale):
                p_text = f" — **{s['pret_standard']} lei**" if s['pret_standard'] > 0 else ""
                # Distribuim produsele stânga-dreapta
                if i % 2 == 0:
                    col_s1.write(f"• {s['nume']}{p_text}")
                else:
                    col_s2.write(f"• {s['nume']}{p_text}")
        
        # --- SECȚIUNEA: DESERTURI (TOATE) ---
        deserturi = [p for p in toate if p['categorie'] == 'desert']
        
        if deserturi:
            st.write("")
            st.markdown("#### 🍰 Desert")
            col_d1, col_d2 = st.columns(2)
            for i, d in enumerate(deserturi):
                p_text = f" — **{d['pret_standard']} lei**" if d['pret_standard'] > 0 else ""
                if i % 2 == 0:
                    col_d1.write(f"• {d['nume']}{p_text}")
                else:
                    col_d2.write(f"• {d['nume']}{p_text}")
    with col_info:
        # Folosim un "container" pentru contact care arată bine în orice temă
        with st.container(border=True):
            st.markdown("#### 📞 Contact Comenzi")
            st.write("Cantina noastră vă oferă meniuri în regim de catering pentru:")
            st.caption("Parastase, înmormântări, aniversări sau majorate.")
            
            st.error("📱 0743 090 212\n\n📱 0743 093 618")
            
            st.markdown("---")
            st.markdown("**📍 Adresă:**")
            st.write("Str. Ing. Dumitru Ivanov, nr. 18, Tulcea (intrarea Frigorifer)")
            
            st.markdown("**⏰ Program Livrări:**")
            st.write("Luni - Vineri: 10:00 - 16:00")