"""
auth.py
-------
Autentificare cu cookie persistent + sesiune în DB.
Token UUID stocat în cookie (30 zile) și în tabela sesiuni.
"""

import streamlit as st
import bcrypt
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
import database as db

ROL_LABEL = {
    "admin":     "⚙️ Admin",
    "receptie":  "📝 Recepție",
    "bucatarie": "👨‍🍳 Bucătărie",
    "ghiseu":    "🏪 Ghișeu",
    "livrator":  "🚚 Livrator",
}

SESSION_DAYS   = 30
COOKIE_NAME    = "sl_session"
COOKIE_MAX_AGE = SESSION_DAYS * 24 * 3600


# ── helpers DB ────────────────────────────────────────────────

def _engine():
    return db.get_engine()


def _hash(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def _verify(password: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode(), hashed.encode())
    except Exception:
        return False


def get_user_by_username(username: str):
    with _engine().connect() as conn:
        r = conn.execute(text("""
            SELECT u.id, u.username, u.password_hash, u.rol, u.activ,
                   u.livrator_id, l.nume AS livrator_nume
            FROM utilizatori u
            LEFT JOIN livratori l ON l.id = u.livrator_id
            WHERE u.username = :u
        """), {"u": username}).fetchone()
        return dict(r._mapping) if r else None


def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)
    with _engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO sesiuni (token, user_id, expires_at)
            VALUES (:t, :uid, :exp)
        """), {"t": token, "uid": user_id, "exp": expires})
    return token


def get_user_by_token(token: str):
    with _engine().connect() as conn:
        r = conn.execute(text("""
            SELECT u.id, u.username, u.rol, u.activ,
                   u.livrator_id, l.nume AS livrator_nume
            FROM sesiuni s
            JOIN utilizatori u ON u.id = s.user_id
            LEFT JOIN livratori l ON l.id = u.livrator_id
            WHERE s.token = :t
              AND s.expires_at > NOW()
              AND u.activ = TRUE
        """), {"t": token}).fetchone()
        return dict(r._mapping) if r else None


def delete_session(token: str):
    with _engine().begin() as conn:
        conn.execute(text("DELETE FROM sesiuni WHERE token = :t"), {"t": token})


def cleanup_expired_sessions():
    with _engine().begin() as conn:
        conn.execute(text("DELETE FROM sesiuni WHERE expires_at < NOW()"))


# ── UI ────────────────────────────────────────────────────────

def _get_cookie_manager():
    import extra_streamlit_components as stx
    return stx.CookieManager(key="auth_cookie_mgr")


def login_page():
    """Pagina de login — afișată când nu există sesiune validă."""
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("## 🍽️ Cantina Lotus")
        st.markdown("### Autentificare")
        st.divider()

        username = st.text_input("Utilizator:", key="login_user")
        password = st.text_input("Parolă:", type="password", key="login_pass")

        if st.button("🔐 Intră", use_container_width=True, type="primary"):
            if not username or not password:
                st.error("Completează utilizatorul și parola.")
                return

            user = get_user_by_username(username)
            if not user:
                st.error("Utilizator inexistent.")
                return
            if not user["activ"]:
                st.error("Contul este dezactivat. Contactează adminul.")
                return
            if not _verify(password, user["password_hash"]):
                st.error("Parolă incorectă.")
                return

            token = create_session(user["id"])
            st.session_state["auth_user"]  = user
            st.session_state["auth_token"] = token
            st.session_state["_set_cookie"] = token
            st.rerun()


def check_auth() -> dict | None:
    """
    Verifică sesiunea activă.
    Returnează user dict dacă autentificat, None altfel.
    Gestionează cookie-ul pentru persistență.
    """
    # 1. Deja în session_state (același tab, fără refresh)
    if st.session_state.get("auth_user"):
        return st.session_state["auth_user"]

    cookie_mgr = _get_cookie_manager()

    # 2. Setează cookie după login (rerun imediat după autentificare)
    if st.session_state.get("_set_cookie"):
        token = st.session_state.pop("_set_cookie")
        cookie_mgr.set(COOKIE_NAME, token, max_age=COOKIE_MAX_AGE)
        return st.session_state.get("auth_user")

    # 3. Restaurare din cookie după refresh
    token = cookie_mgr.get(COOKIE_NAME)
    if token:
        user = get_user_by_token(token)
        if user:
            st.session_state["auth_user"]  = user
            st.session_state["auth_token"] = token
            return user
        else:
            cookie_mgr.delete(COOKIE_NAME)

    return None


def logout():
    """Șterge sesiunea din DB + cookie + session_state."""
    cookie_mgr = _get_cookie_manager()
    token = st.session_state.pop("auth_token", None)
    if token:
        delete_session(token)
    st.session_state.pop("auth_user", None)
    try:
        cookie_mgr.delete(COOKIE_NAME)
    except Exception:
        pass
    st.rerun()


def require_role(*roluri):
    """Decorator / guard — oprește dacă userul nu are rolul cerut."""
    user = st.session_state.get("auth_user")
    if not user or user["rol"] not in roluri:
        st.error("⛔ Nu ai permisiunea să accesezi această secțiune.")
        st.stop()
    return user
