"""
app_nicegui.py
--------------
StreamLotus — NiceGUI version.
Rulare: python app_nicegui.py
Acces:  http://localhost:8081
"""

from dotenv import load_dotenv
load_dotenv()  # incarca .env inainte de orice import din database.py

from nicegui import ui, app
from datetime import date, datetime
import database as db
import utils

from ng_modules import receptie  as ng_receptie
from ng_modules import bucatarie as ng_bucatarie
from ng_modules import livrare   as ng_livrare
from ng_modules import ghiseu    as ng_ghiseu
from ng_modules import admin     as ng_admin

# ── Navigare per rol ──────────────────────────────────────────
ROLURI = ["Recepție", "Bucătărie", "Livrare", "Ghișeu", "Admin"]

NAV: dict[str, list[tuple[str, str, str]]] = {
    "Recepție":  [
        ("📞", "Comenzi Noi",        "/receptie"),
        ("📋", "Rezumat Livrări",    "/receptie/rezumat"),
    ],
    "Bucătărie": [
        ("🍳", "Gătire",             "/bucatarie/gatire"),
        ("📦", "Impachetare",        "/bucatarie/impachetare"),
        ("🔁", "Buffer",             "/bucatarie/buffer"),
        ("🗑️", "Nevândut",           "/bucatarie/nevandut"),
    ],
    "Livrare":   [
        ("🚚", "Ruta Mea",           "/livrare"),
    ],
    "Ghișeu":    [
        ("🏢", "Firme Contract",     "/ghiseu/firme"),
        ("🛒", "Bon Casă",           "/ghiseu/bon"),
        ("🎉", "Evenimente",         "/ghiseu/eveniment"),
    ],
    "Admin":     [
        ("📅", "Planificare",        "/admin/planificare"),
        ("🚀", "Lansare Producție",  "/admin/lansare"),
        ("📋", "Nomenclator",        "/admin/nomenclator"),
        ("📊", "Rapoarte",           "/admin/rapoarte"),
        ("🏢", "Firme Admin",        "/admin/firme"),
    ],
}


# ── Layout comun ──────────────────────────────────────────────
def _layout(pagina_curenta: str = "") -> None:
    """Header + sidebar. Apelat la începutul fiecărei pagini."""
    state = app.storage.user
    rol   = state.get("rol", "Recepție")
    azi   = utils.get_ro_time()

    ui.colors(primary="#ef4444", secondary="#1e293b", accent="#f97316")
    ui.query("body").style("background-color: #0f172a")
    ui.query(".q-page").style("padding: 0 !important; align-items: flex-start !important; display: block !important")
    ui.query(".nicegui-content").style("width: 100% !important; max-width: 100% !important")

    # ── Header ────────────────────────────────────────────────
    with ui.header(elevated=True).classes("bg-red-600 text-white px-4 py-2 items-center gap-3 h-14"):
        ui.button(icon="menu", on_click=lambda: drawer.toggle()).props("flat color=white round dense")
        ui.label("🪷 Lotus").classes("text-xl font-bold tracking-wide")
        ui.space()
        ui.label(azi.strftime("%d %b %Y")).classes("text-sm opacity-75")
        with ui.element("div").classes("flex items-center gap-1 ml-3 bg-white/20 rounded-full px-3 py-1"):
            ui.icon("person", size="xs")
            ui.label(rol).classes("text-sm font-medium")

    # ── Sidebar ───────────────────────────────────────────────
    with ui.left_drawer(fixed=False, bottom_corner=True, bordered=True).classes(
        "bg-slate-900 border-r border-slate-700/50"
    ) as drawer:

        # Logo
        with ui.element("div").classes("px-6 py-5 border-b border-slate-700/50"):
            ui.label("🪷 LOTUS").classes("text-2xl font-bold text-red-400 leading-none")
            ui.label("Cantina Management").classes("text-[11px] text-slate-500 mt-1 uppercase tracking-widest")

        # Rol selector
        with ui.element("div").classes("px-4 py-4 border-b border-slate-700/50"):
            ui.label("ROL ACTIV").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2")
            ui.select(
                ROLURI,
                value=rol,
                on_change=lambda e: _change_rol(e.value),
            ).classes("w-full").props("dense outlined dark color=red-5")

        # Navigare
        with ui.element("div").classes("px-3 py-4 flex-1"):
            ui.label("NAVIGARE").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest px-3 mb-3")
            for icon, label, path in NAV.get(rol, []):
                activ = pagina_curenta == path
                with ui.element("div").classes(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 mb-0.5 cursor-pointer " +
                    ("bg-red-600 text-white shadow-lg shadow-red-900/30" if activ
                     else "text-slate-400 hover:bg-slate-800 hover:text-white")
                ).on("click", lambda p=path: ui.navigate.to(p)):
                    ui.label(icon).classes("text-base leading-none w-5 text-center")
                    ui.label(label).classes("text-sm font-medium")

        # Footer sidebar
        with ui.element("div").classes("px-6 py-3 border-t border-slate-700/50 mt-auto"):
            ui.label(azi.strftime("%H:%M")).classes("text-xs text-slate-600 text-center")


def _change_rol(rol_nou: str) -> None:
    app.storage.user["rol"] = rol_nou
    pagini = NAV.get(rol_nou, [])
    ui.navigate.to(pagini[0][2] if pagini else "/")


# ── Home ──────────────────────────────────────────────────────
@ui.page("/")
def pagina_home():
    _layout("/")
    rol = app.storage.user.get("rol", "Recepție")
    azi = utils.get_ro_time()

    with ui.element("div").classes("p-8 max-w-4xl mx-auto"):
        ui.label(f"Bună ziua! 👋").classes("text-3xl font-bold text-white mb-1")
        ui.label(
            f"Astăzi este {azi.strftime('%A, %d %B %Y')} — conectat ca {rol}"
        ).classes("text-slate-400 mb-8")

        ui.label("ACCES RAPID").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4")
        pagini_rol = NAV.get(rol, [])
        cols = min(len(pagini_rol), 3)
        with ui.grid(columns=cols).classes("gap-4 w-full"):
            for icon, label, path in pagini_rol:
                with (
                    ui.card()
                    .classes("bg-slate-800 border border-slate-700 cursor-pointer hover:border-red-500 transition-all group")
                    .on("click", lambda p=path: ui.navigate.to(p))
                ):
                    with ui.element("div").classes("p-5"):
                        ui.label(icon).classes("text-3xl mb-3")
                        ui.label(label).classes("text-white font-semibold text-base")
                        ui.label("Deschide →").classes("text-red-400 text-xs mt-1")


# ── Recepție ──────────────────────────────────────────────────
@ui.page("/receptie")
def pagina_receptie():
    _layout("/receptie")
    ng_receptie.show()


@ui.page("/receptie/rezumat")
def pagina_rezumat():
    _layout("/receptie/rezumat")
    ng_receptie.show_rezumat()


# ── Bucătărie ─────────────────────────────────────────────────
@ui.page("/bucatarie/gatire")
def pagina_gatire():
    _layout("/bucatarie/gatire")
    ng_bucatarie.show_gatire()


@ui.page("/bucatarie/impachetare")
def pagina_impachetare():
    _layout("/bucatarie/impachetare")
    ng_bucatarie.show_impachetare()


@ui.page("/bucatarie/buffer")
def pagina_buffer():
    _layout("/bucatarie/buffer")
    ng_bucatarie.show_buffer()


@ui.page("/bucatarie/nevandut")
def pagina_nevandut():
    _layout("/bucatarie/nevandut")
    ng_bucatarie.show_nevandut()


# ── Livrare ───────────────────────────────────────────────────
@ui.page("/livrare")
def pagina_livrare():
    _layout("/livrare")
    ng_livrare.show()


# ── Ghișeu ────────────────────────────────────────────────────
@ui.page("/ghiseu/firme")
def pagina_ghiseu_firme():
    _layout("/ghiseu/firme")
    ng_ghiseu.show_firme()


@ui.page("/ghiseu/bon")
def pagina_bon():
    _layout("/ghiseu/bon")
    ng_ghiseu.show_bon()


@ui.page("/ghiseu/eveniment")
def pagina_eveniment():
    _layout("/ghiseu/eveniment")
    ng_ghiseu.show_eveniment()


# ── Admin ─────────────────────────────────────────────────────
@ui.page("/admin/planificare")
def pagina_planificare():
    _layout("/admin/planificare")
    ng_admin.show_planificare()


@ui.page("/admin/lansare")
def pagina_lansare():
    _layout("/admin/lansare")
    ng_admin.show_lansare()


@ui.page("/admin/nomenclator")
def pagina_nomenclator():
    _layout("/admin/nomenclator")
    ng_admin.show_nomenclator()


@ui.page("/admin/rapoarte")
def pagina_rapoarte():
    _layout("/admin/rapoarte")
    ng_admin.show_rapoarte()


@ui.page("/admin/firme")
def pagina_admin_firme():
    _layout("/admin/firme")
    ng_admin.show_firme()


# ── Start ─────────────────────────────────────────────────────
ui.run(
    title="🪷 Lotus Cantina",
    port=8081,
    storage_secret="lotus-cantina-2024",
    dark=True,
    reload=True,
    favicon="🪷",
)
