"""ng_modules/bucatarie.py — Bucătărie (skeleton)"""
from nicegui import ui
import database as db
import utils


def show_gatire() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🍳", "Gătire", "Marchează produsele gătite și cantitățile")
        _stat_bar([("📋 Produse planificate", "0", "text-blue-400"),
                   ("✅ Gătite", "0", "text-green-400"),
                   ("⏳ Rămase", "0", "text-amber-400")])
        _placeholder("Lista produselor din planul zilei cu input cantitate gătită")


def show_impachetare() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("📦", "Impachetare", "Urmărește pachetele pentru firme și livrări")
        _stat_bar([("📦 De ambalat", "0", "text-blue-400"),
                   ("✅ Ambalate", "0", "text-green-400"),
                   ("🚚 Livrate", "0", "text-slate-400")])
        _placeholder("Lista pachete per firmă cu status ambalare")


def show_buffer() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🔁", "Buffer Prânz / Cină", "Meniuri pregătite în avans pentru firme")
        _stat_bar([("🍱 Buffer V1", "0", "text-blue-400"),
                   ("🍱 Buffer V2", "0", "text-purple-400"),
                   ("📊 Distribuite", "0", "text-green-400")])
        _placeholder("Configurare buffer meniuri și distribuire")


def show_nevandut() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🗑️", "Nevândut", "Stoc rămas la finalul zilei")
        _stat_bar([("🔴 Nevândut total", "0 porții", "text-red-400"),
                   ("💸 Valoare estimată", "0 lei", "text-amber-400")])
        _placeholder("Lista produse nevândute cu cantități rămase")


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
