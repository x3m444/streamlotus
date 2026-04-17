import streamlit as st
import database as db
import auth

AUTH_ENABLED = False  # Setează True pentru a activa autentificarea
from modules import frontend, livrare
from modules.admin_manager import main as admin_main
from modules.bucatarie import main as bucatarie_main
from modules.ghiseu import main as ghiseu_main
from modules.receptie import main as receptie_main
from modules import manual

st.set_page_config(page_title="Cantina Lotus", layout="wide", page_icon="🍱")

st.markdown("""
<style>
@media (max-width: 768px) {
    .stButton > button { min-height: 52px !important; font-size: 16px !important; }
    input, select, textarea { font-size: 16px !important; }
    [data-testid="stTabs"] { overflow-x: auto !important; }
}
</style>
""", unsafe_allow_html=True)

st.sidebar.image("https://img.icons8.com/color/96/000000/restaurant.png", width=80)
pagina = st.sidebar.radio("Navigare", ["🏠 Acasă (Public)", "🔒 Zona Staff"])

if pagina == "🏠 Acasă (Public)":
    frontend.show_landing_page()

else:
    # ── Autentificare ─────────────────────────────────────────
    if AUTH_ENABLED:
        user = auth.check_auth()
        if not user:
            auth.login_page()
            st.stop()
    else:
        user = {"username": "admin", "rol": "admin",
                "livrator_id": None, "livrator_nume": None}

    rol = user["rol"]

    # ── Sidebar utilizator autentificat ───────────────────────
    st.sidebar.markdown(f"**{user['username']}** — {auth.ROL_LABEL.get(rol, rol)}")
    if st.sidebar.button("🚪 Deconectare", use_container_width=True):
        auth.logout()

    if st.sidebar.button("📖 Manual", use_container_width=True):
        st.session_state["show_manual"] = not st.session_state.get("show_manual", False)

    if st.session_state.get("show_manual", False):
        manual.show_manual()
        st.stop()

    # ── Routing pe rol ────────────────────────────────────────
    if rol == "admin":
        t1, t2, t3, t4 = st.tabs(["⚙️ Admin", "📝 Recepție", "👨‍🍳 Bucătărie", "🚚 Livrare"])
        with t1: admin_main.show_admin()
        with t2: receptie_main.show_receptie()
        with t3: bucatarie_main.show_bucatarie()
        with t4:
            livratori = db.get_lista_livratori()
            if livratori:
                sofer_admin = st.selectbox("Vizualizează ruta livratorului:", livratori, key="sofer_admin_view")
                livrare.show_livrare(sofer_admin)
            else:
                st.warning("Nu există livratori configurați.")

    elif rol == "receptie":
        receptie_main.main_receptie_page()

    elif rol == "bucatarie":
        bucatarie_main.show_bucatarie()

    elif rol == "ghiseu":
        ghiseu_main.show_ghiseu()

    elif rol == "livrator":
        sofer = user.get("livrator_nume")
        if sofer:
            livrare.show_livrare(sofer)
        else:
            st.warning("Contul tău nu este legat de un livrator. Contactează adminul.")
