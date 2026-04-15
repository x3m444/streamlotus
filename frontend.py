import streamlit as st
import database as db
from datetime import date

def show_landing_page():
    # --- STILIZARE CSS (Pentru a simula cardurile din printscreen) ---
    st.markdown("""
        <style>
        .main { background-color: #fdfaf5; }
        .hero-section {
            background: linear-gradient(135deg, #d35400, #e67e22);
            padding: 40px;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        .menu-card {
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            border-left: 5px solid #d35400;
            box-shadow: 2px 2px 10px rgba(0,0,0,0.1);
            margin-bottom: 15px;
        }
        .price-tag {
            color: #d35400;
            font-weight: bold;
            float: right;
        }
        </style>
    """, unsafe_allow_html=True)

    # --- HEADER / LOGO ---
    st.markdown('<div class="hero-section"><h1>🍱 CANTINA LOTUS</h1><p>Gustul autentic, livrat zilnic</p></div>', unsafe_allow_html=True)

    col1, col2 = st.columns([2, 1])

    with col1:
        # --- SECȚIUNEA: MENIUL ZILEI (EXTRACT AUTOMAT) ---
        st.subheader(f"📅 Meniul Zilei - {date.today().strftime('%d.%m.%Y')}")
        meniu_azi = db.get_meniu_planificat(date.today())
        
        if meniu_azi:
            for p in meniu_azi:
                st.markdown(f"""
                <div class="menu-card">
                    <span class="price-tag">{p['pret_standard']} LEI</span>
                    <b>{p['categorie'].replace('_', ' ').upper()}</b><br>{p['nume']}
                </div>
                """, unsafe_allow_html=True)
            
            st.warning("💡 **OFERTĂ:** Felul 1 (9 LEI) + Fel Principal (19 LEI) = **28 LEI**")
        else:
            st.info("Meniul pentru astăzi urmează să fie actualizat. Reveniți în curând!")

        # --- SECȚIUNEA: MENIURI SPECIALE (EXTRACT DIN NOMENCLATOR) ---
        st.write("---")
        st.subheader("✨ Specialitățile Casei & Desert")
        toate = db.get_toate_produsele()
        speciale = [p for p in toate if p['categorie'] in ['special', 'desert', 'salate']]
        
        for s in speciale:
            st.markdown(f"• **{s['nume']}** — {s['pret_standard']} LEI")

    with col2:
        # --- SECȚIUNEA: CONTACT (DIN PRINTSCREEN 3) ---
        st.markdown("""
            <div style="background-color: #d35400; color: white; padding: 20px; border-radius: 15px;">
                <h3>📞 Comenzi Telefonice</h3>
                <p>Cantina noastră vă oferă meniuri în regim de catering pentru evenimente (pomeni, aniversări, majorate).</p>
                <hr>
                <p style="font-size: 1.2em; font-weight: bold;">
                    0743 090 212<br>
                    0743 093 618
                </p>
            </div>
        """, unsafe_allow_html=True)
        
        st.image("https://img.icons8.com/color/96/000000/delivery--v1.png", width=100)
        st.write("**Program Livrări:**")
        st.write("Luni - Vineri: 10:00 - 16:00")