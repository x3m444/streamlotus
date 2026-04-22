"""ng_modules/ghiseu.py — Ghișeu (skeleton)"""
from nicegui import ui
import database as db
import utils


def show_firme() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🏢", "Firme cu Contract", "Servire angajați pe bază de abonament")
        _stat_bar([("🏢 Firme active", "0", "text-blue-400"),
                   ("👤 Angajați total", "0", "text-slate-300"),
                   ("✅ Serviți azi", "0", "text-green-400"),
                   ("⏳ Rămași", "0", "text-amber-400")])
        _placeholder("Card per firmă cu lista angajaților și selecție meniu")


def show_bon() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🛒", "Bon Casă", "Vânzare directă la ghișeu")
        _stat_bar([("🧾 Bonuri azi", "0", "text-blue-400"),
                   ("💰 Încasat", "0 lei", "text-green-400")])
        _placeholder("Selecție produse + cantitate + emitere bon")


def show_eveniment() -> None:
    with ui.element("div").classes("p-4 w-full"):
        _titlu("🎉", "Evenimente", "Comenzi pentru catering și evenimente speciale")
        _stat_bar([("📋 Evenimente active", "0", "text-purple-400"),
                   ("🍽️ Porții totale", "0", "text-blue-400")])
        _placeholder("Lista evenimente cu status servire per lot")


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
