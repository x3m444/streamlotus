"""ng_modules/livrare.py — Livrare (skeleton)"""
from nicegui import ui
import database as db
import utils


def show() -> None:
    state = __import__('nicegui').app.storage.user
    azi   = utils.get_ro_time().date()

    with ui.element("div").classes("p-6 max-w-4xl mx-auto"):
        _titlu("🚚", "Ruta Mea", "Comenzile asignate pentru livrare")

        # Selector livrator
        with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
            ui.label("LIVRATOR").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-2")
            livratori = db.get_lista_livratori()
            sofer_curent = state.get("sofer", livratori[0] if livratori else "")
            ui.select(
                livratori,
                value=sofer_curent,
                on_change=lambda e: state.update({"sofer": e.value})
            ).classes("w-full").props("outlined dark")

        with ui.grid(columns=3).classes("gap-4 mb-6"):
            with ui.card().classes("bg-slate-800 border border-slate-700 p-4"):
                ui.label("📦 De preluat").classes("text-slate-400 text-xs mb-1")
                ui.label("0").classes("text-2xl font-bold text-blue-400")
            with ui.card().classes("bg-slate-800 border border-slate-700 p-4"):
                ui.label("🛣️ Pe drum").classes("text-slate-400 text-xs mb-1")
                ui.label("0").classes("text-2xl font-bold text-amber-400")
            with ui.card().classes("bg-slate-800 border border-slate-700 p-4"):
                ui.label("💵 Cash de încasat").classes("text-slate-400 text-xs mb-1")
                ui.label("0 lei").classes("text-2xl font-bold text-green-400")

        with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-8 text-center"):
            ui.icon("local_shipping", size="2.5rem").classes("text-slate-600 mb-3")
            ui.label("Carduri comenzi cu butoane Am preluat / Livrat").classes("text-slate-500 text-sm")


def _titlu(icon: str, titlu: str, subtitlu: str) -> None:
    with ui.element("div").classes("flex items-center gap-4 mb-6"):
        ui.label(icon).classes("text-4xl")
        with ui.element("div"):
            ui.label(titlu).classes("text-2xl font-bold text-white")
            ui.label(subtitlu).classes("text-slate-400 text-sm")
