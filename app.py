import streamlit as st
import database as db
from modules import frontend, receptie, bucatarie, livrare
from modules.admin_manager import main as admin_main

st.set_page_config(page_title="Cantina Lotus", layout="wide", page_icon="🍱")

st.sidebar.image("https://img.icons8.com/color/96/000000/restaurant.png", width=80)
pagina = st.sidebar.radio("Navigare", ["🏠 Acasă (Public)", "🔒 Zona Staff"])

if pagina == "🏠 Acasă (Public)":
    frontend.show_landing_page()

else:
    if 'rol' not in st.session_state:
        st.session_state['rol'] = "Admin"

    rol = st.sidebar.selectbox("Rol (Test):", ["Admin", "Recepție", "Bucătărie", "Livrator"])
    st.session_state['rol'] = rol

    if rol == "Admin":
        t1, t2, t3, t4 = st.tabs(["⚙️ Admin", "📝 Recepție", "👨‍🍳 Bucătărie", "🚚 Livrare"])
        with t1: admin_main.show_admin()
        with t2: receptie.show_receptie()
        with t3: bucatarie.show_bucatarie()
        with t4:

            livratori = db.get_lista_livratori()
            if livratori:
                sofer_admin = st.selectbox("Vizualizează ruta livratorului:", livratori, key="sofer_admin_view")
                livrare.show_livrare(sofer_admin)
            else:
                st.warning("Nu există livratori configurați în baza de date.")

    elif rol == "Recepție":
        receptie.main_receptie_page()

    elif rol == "Bucătărie":
        bucatarie.show_bucatarie()

    elif rol == "Livrator":
        livratori = db.get_lista_livratori()
        if livratori:
            sofer = st.sidebar.selectbox("Selectează livratorul:", livratori, key="sofer_selectat")
            livrare.show_livrare(sofer)
        else:
            st.warning("Nu există livratori configurați în baza de date.")
