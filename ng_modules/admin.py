"""ng_modules/admin.py — Admin (skeleton)"""
from nicegui import ui
import database as db
import utils


def show_planificare() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("📅", "Planificare Meniu", "Setează meniul pentru zilele viitoare")
        with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
            ui.label("DATA PLANIFICATĂ").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2")
            ui.date(value=utils.get_ro_time().date().isoformat()).props("dark outlined")
        _placeholder("Selecție Felul 1 / Felul 2 V1 / Felul 2 V2 / Salată din nomenclator")


def show_lansare() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🚀", "Lansare Producție", "Cantități de gătit per produs")
        _stat_bar([("📋 Produse planificate", "0", "text-blue-400"),
                   ("🏢 Rezervări firme", "0", "text-purple-400"),
                   ("📞 Comenzi livrare", "0", "text-amber-400")])
        _placeholder("Tabel lansare cu cantități calculate automat + ajustări manuale")


def show_nomenclator() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("📋", "Nomenclator Produse", "Gestionează produsele disponibile")
        _stat_bar([("🍽️ Total produse", "0", "text-blue-400"),
                   ("✅ Active", "0", "text-green-400")])

        with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-6 mt-4"):
            ui.label("TABEL PRODUSE (editabil)").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-4")
            ui.aggrid({
                "columnDefs": [
                    {"headerName": "ID",         "field": "id",         "width": 70,  "editable": False},
                    {"headerName": "Denumire",    "field": "nume",       "flex": 2,    "editable": True},
                    {"headerName": "Categorie",   "field": "categorie",  "flex": 1,    "editable": True},
                    {"headerName": "Preț (RON)",  "field": "pret",       "width": 120, "editable": True},
                ],
                "rowData": [],
                "rowSelection": "multiple",
            }).classes("w-full").style("height: 300px")
            ui.button("💾 Salvează modificările", icon="save").classes("mt-3 bg-red-600 text-white").props("no-caps")


def show_rapoarte() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("📊", "Rapoarte", "Statistici vânzări și serviri")
        _stat_bar([("💰 Venituri azi", "0 lei", "text-green-400"),
                   ("🍽️ Porții servite", "0",   "text-blue-400"),
                   ("🚚 Comenzi livrate", "0",  "text-purple-400")])
        _placeholder("Grafice vânzări + export Excel per interval")


def show_firme() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🏢", "Administrare Firme", "Gestionează contractele și angajații")
        _placeholder("Lista firme cu angajați, tip contract, status activ")


# ── helpers ──────────────────────────────────────────────────

def _titlu(icon: str, titlu: str, subtitlu: str) -> None:
    with ui.element("div").classes("flex items-center gap-4 mb-6"):
        ui.label(icon).classes("text-4xl")
        with ui.element("div"):
            ui.label(titlu).classes("text-2xl font-bold text-white")
            ui.label(subtitlu).classes("text-slate-400 text-sm")


def _stat_bar(items: list) -> None:
    with ui.grid(columns=len(items)).classes("gap-4 mb-6"):
        for label, val, culoare in items:
            with ui.card().classes("bg-slate-800 border border-slate-700 p-4"):
                ui.label(label).classes("text-slate-400 text-xs mb-1")
                ui.label(val).classes(f"text-2xl font-bold {culoare}")


def _placeholder(desc: str) -> None:
    with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-8 text-center"):
        ui.icon("construction", size="2.5rem").classes("text-slate-600 mb-3")
        ui.label(desc).classes("text-slate-500 text-sm")
