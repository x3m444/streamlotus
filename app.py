import streamlit as st
from modules import frontend, admin, receptie, bucatarie, livrare
import database as db
import utils  # Importăm fișierul nou creat
#from modules import admin_manager as admin

st.set_page_config(page_title="Cantina Lotus", layout="wide", page_icon="🍱")

# Navigare superioară simplă (în locul sidebar-ului pentru un look de site)
st.sidebar.image("https://img.icons8.com/color/96/000000/restaurant.png", width=80)
pagina = st.sidebar.radio("Navigare", ["🏠 Acasă (Public)", "🔒 Zona Staff"])

if pagina == "🏠 Acasă (Public)":
    frontend.show_landing_page()

else:
    # --- LOGICA DE STAFF ---
    if 'rol' not in st.session_state:
        st.session_state['rol'] = "Admin"
    
    rol = st.sidebar.selectbox("Rol (Test):", ["Admin", "Recepție", "Bucătărie", "Livrator"])
    st.session_state['rol'] = rol
    
    if rol == "Admin":
        t1, t2, t3, t4 = st.tabs(["⚙️ Admin", "📝 Recepție", "👨‍🍳 Bucătărie", "🚚 Livrare"])
        with t1: admin.show_menu_editor()  # Trimitem db și toate către funcția show din admin.py
        with t2: receptie.show_receptie()
        with t3: bucatarie.show_bucatarie()
        with t4: livrare.show_livrare()
    
    # ADAUGĂ ACESTE ELIF-URI:
    elif rol == "Recepție":
        receptie.main_receptie_page()

    elif rol == "Bucătărie":
        # bucatarie.show_bucatarie()
        bucatarie.show_bucatarie()

    elif rol == "Livrator":
        # livrare.show_livrare()
        st.info("Ecran Livrare în curs de implementare...")