"""
admin_manager/utilizatori.py
-----------------------------
Gestiune utilizatori — vizibil doar adminului.
"""

import streamlit as st
from sqlalchemy import text
import database as db
import auth

ROL_LABEL = {
    "admin":     "⚙️ Admin",
    "receptie":  "📝 Recepție",
    "bucatarie": "👨‍🍳 Bucătărie",
    "ghiseu":    "🏪 Ghișeu",
    "livrator":  "🚚 Livrator",
}


def _get_toti_utilizatorii():
    with db.get_engine().connect() as conn:
        r = conn.execute(text("""
            SELECT u.id, u.username, u.rol, u.activ,
                   u.livrator_id, l.nume AS livrator_nume,
                   u.created_at
            FROM utilizatori u
            LEFT JOIN livratori l ON l.id = u.livrator_id
            ORDER BY u.rol, u.username
        """))
        return [dict(x._mapping) for x in r]


def _set_activ(user_id, activ):
    with db.get_engine().begin() as conn:
        conn.execute(text("UPDATE utilizatori SET activ = :a WHERE id = :id"),
                     {"a": activ, "id": user_id})


def _reset_password(user_id, new_pass):
    hashed = auth._hash(new_pass)
    with db.get_engine().begin() as conn:
        conn.execute(text("UPDATE utilizatori SET password_hash = :h WHERE id = :id"),
                     {"h": hashed, "id": user_id})


def _add_user(username, password, rol, livrator_id=None):
    hashed = auth._hash(password)
    with db.get_engine().begin() as conn:
        conn.execute(text("""
            INSERT INTO utilizatori (username, password_hash, rol, livrator_id)
            VALUES (:u, :h, :r, :lid)
        """), {"u": username, "h": hashed, "r": rol, "lid": livrator_id or None})


def show():
    st.subheader("👥 Gestiune Utilizatori")

    livratori = db.get_lista_livratori()

    # ── Adaugă utilizator nou ─────────────────────────────────
    with st.expander("➕ Adaugă Utilizator Nou", expanded=False):
        c1, c2, c3, c4 = st.columns([2, 2, 2, 1])
        nou_user = c1.text_input("Username:", key="nou_username")
        nou_pass = c2.text_input("Parolă:", type="password", key="nou_pass")
        nou_rol  = c3.selectbox("Rol:", list(ROL_LABEL.keys()),
                                format_func=lambda x: ROL_LABEL[x], key="nou_rol")

        liv_id = None
        if nou_rol == "livrator":
            liv_ales = st.selectbox(
                "Leagă de livrator existent:",
                ["— nou livrator —"] + livratori,
                key="nou_liv_link"
            )
            if liv_ales != "— nou livrator —":
                with db.get_engine().connect() as conn:
                    r = conn.execute(text("SELECT id FROM livratori WHERE nume = :n"),
                                     {"n": liv_ales}).fetchone()
                    liv_id = r[0] if r else None

        c4.write("")
        c4.write("")
        if c4.button("Adaugă", key="btn_add_user", type="primary", use_container_width=True):
            if not nou_user.strip() or not nou_pass.strip():
                st.error("Username și parola sunt obligatorii.")
            else:
                try:
                    _add_user(nou_user.strip(), nou_pass.strip(), nou_rol, liv_id)
                    st.success(f"✅ Utilizator creat: **{nou_user}** ({ROL_LABEL[nou_rol]})")
                    st.rerun()
                except Exception as e:
                    if "unique" in str(e).lower():
                        st.error("Username deja există.")
                    else:
                        st.error(f"Eroare: {e}")

    st.divider()

    # ── Lista utilizatori ─────────────────────────────────────
    utilizatori = _get_toti_utilizatorii()

    for rol_key, rol_label in ROL_LABEL.items():
        grup = [u for u in utilizatori if u["rol"] == rol_key]
        if not grup:
            continue

        st.markdown(f"**{rol_label}**")
        for u in grup:
            uid       = u["id"]
            activ     = u["activ"]
            icon      = "🟢" if activ else "💤"
            liv_info  = f" → {u['livrator_nume']}" if u.get("livrator_nume") else ""
            titlu_exp = f"{icon} **{u['username']}**{liv_info}"

            with st.expander(titlu_exp):
                col_pass, col_act, col_liv = st.columns([3, 1, 2])

                # Reset parolă
                new_pass = col_pass.text_input("Parolă nouă:", type="password",
                                               key=f"rp_{uid}", placeholder="lasă gol = neschimbat")
                if col_pass.button("🔑 Resetează parola", key=f"btn_rp_{uid}",
                                   use_container_width=True):
                    if new_pass.strip():
                        _reset_password(uid, new_pass.strip())
                        st.success("Parolă resetată.")
                        st.rerun()
                    else:
                        st.warning("Introdu parola nouă.")

                # Activare / dezactivare
                col_act.write("")
                col_act.write("")
                if activ:
                    if col_act.button("🔴 Dezactivează", key=f"dez_{uid}",
                                      use_container_width=True):
                        _set_activ(uid, False)
                        st.rerun()
                else:
                    if col_act.button("🟢 Activează", key=f"act_{uid}",
                                      use_container_width=True):
                        _set_activ(uid, True)
                        st.rerun()

                # Leagă livrator (doar pentru rol livrator)
                if u["rol"] == "livrator":
                    liv_curent = u.get("livrator_nume") or "— nelegat —"
                    opt_liv = ["— nelegat —"] + livratori
                    idx = opt_liv.index(liv_curent) if liv_curent in opt_liv else 0
                    nou_liv = col_liv.selectbox("Livrator:", opt_liv, index=idx,
                                               key=f"liv_sel_{uid}")
                    if col_liv.button("💾 Salvează", key=f"liv_save_{uid}",
                                      use_container_width=True):
                        if nou_liv == "— nelegat —":
                            new_lid = None
                        else:
                            with db.get_engine().connect() as conn:
                                r = conn.execute(text("SELECT id FROM livratori WHERE nume = :n"),
                                                 {"n": nou_liv}).fetchone()
                                new_lid = r[0] if r else None
                        with db.get_engine().begin() as conn:
                            conn.execute(text("UPDATE utilizatori SET livrator_id = :lid WHERE id = :id"),
                                         {"lid": new_lid, "id": uid})
                        st.rerun()

        st.divider()
