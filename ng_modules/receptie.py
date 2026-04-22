"""ng_modules/receptie.py — Recepție Comenzi (NiceGUI)"""
from nicegui import ui, app
import database as db
import utils


INTERVALE_ORA = [
    "11:00-11:30", "11:30-12:00", "12:00-12:30",
    "12:30-13:00", "13:00-13:30", "13:30-14:00", "URGENT"
]


def show() -> None:
    state = app.storage.user
    azi   = utils.get_ro_time().date()

    if "receptie_data" not in state:
        state["receptie_data"] = azi.isoformat()
    if "receptie_cos" not in state:
        state["receptie_cos"] = []
    if "receptie_client_id" not in state:
        state["receptie_client_id"] = None

    with ui.element("div").classes("p-4 w-full"):

        # ── Header ───────────────────────────────────────────────
        with ui.element("div").classes("flex items-center gap-3 mb-4"):
            ui.label("📞").classes("text-3xl")
            with ui.element("div"):
                ui.label("Recepție Comenzi").classes("text-2xl font-bold text-white")

        # ── Selector dată compact (popup) ────────────────────────
        with ui.element("div").classes("mb-4"):
            data_display = ui.input(
                label="Data comenzii",
                value=state["receptie_data"],
            ).props("outlined dark readonly").classes("w-64")

            with data_display.add_slot("append"):
                ui.icon("edit_calendar").classes("cursor-pointer text-slate-400 hover:text-white").on(
                    "click", lambda: date_menu.open()
                )

            with ui.menu().classes("bg-slate-800") as date_menu:
                def on_date_pick(e):
                    if e.value:
                        state["receptie_data"] = e.value
                        data_display.value = e.value
                        date_menu.close()
                        ui.navigate.reload()

                ui.date(value=state["receptie_data"], on_change=on_date_pick).props("dark")

        _render_body(state)


def _render_body(state) -> None:
    from datetime import date

    data_str = state.get("receptie_data", utils.get_ro_time().date().isoformat())
    try:
        data_sel = date.fromisoformat(data_str)
    except Exception:
        data_sel = utils.get_ro_time().date()

    plan_zi       = db.get_meniu_planificat(data_sel)
    toti_clientii = db.get_all_clienti()
    livratori     = db.get_lista_livratori()
    nomenclator   = db.get_toate_produsele()

    lista_f1  = [p for p in plan_zi if p['categorie'] == 'felul_1']
    lista_f2  = [p for p in plan_zi if p['categorie'] == 'felul_2']
    lista_sal = [p for p in plan_zi if p['categorie'] == 'salate']
    are_meniu = bool(lista_f1 and lista_f2)

    # ── Cos refreshable ──────────────────────────────────────────
    @ui.refreshable
    def render_cos():
        cos   = list(state.get("receptie_cos", []))
        total = sum(i["pret"] * i["cantitate"] for i in cos)

        with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4"):
            with ui.element("div").classes("flex items-center justify-between mb-3"):
                ui.label("COȘ COMANDĂ").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest")
                ui.label(f"Total: {total} lei").classes("text-lg font-bold text-red-400")

            if not cos:
                ui.label("Coșul este gol.").classes("text-slate-500 text-sm text-center py-4")
            else:
                for i, item in enumerate(cos):
                    with ui.element("div").classes("flex items-center gap-3 py-2 border-b border-slate-700"):
                        if item["tip_linie"] == "special":
                            ui.badge("S").props("color=orange")
                        ui.label(item["nume"]).classes("flex-1 text-white text-sm")
                        ui.label(f"{item['cantitate']} buc").classes("text-slate-400 text-sm w-16 text-center")
                        ui.label(f"{item['pret'] * item['cantitate']} lei").classes("text-green-400 text-sm w-20 text-right")
                        idx = i
                        def sterge(ix=idx):
                            cos2 = list(state.get("receptie_cos", []))
                            if 0 <= ix < len(cos2):
                                cos2.pop(ix)
                            state["receptie_cos"] = cos2
                            render_cos.refresh()
                        ui.button(icon="close", on_click=sterge).props("flat round dense color=red size=xs")

                def goleste():
                    state["receptie_cos"] = []
                    render_cos.refresh()
                ui.button("Golește coșul", icon="delete", on_click=goleste).props("flat no-caps").classes("text-red-400 text-xs mt-2")

    def adauga(nume, cantitate, pret, tip_linie):
        cos = list(state.get("receptie_cos", []))
        qty = int(cantitate) if cantitate else 1
        for item in cos:
            if item["nume"] == nume and item["tip_linie"] == tip_linie:
                item["cantitate"] += qty
                state["receptie_cos"] = cos
                ui.notify(f"+{qty}x {nume}", type="positive", position="top-right")
                render_cos.refresh()
                return
        cos.append({"nume": nume, "cantitate": qty, "pret": pret, "tip_linie": tip_linie})
        state["receptie_cos"] = cos
        ui.notify(f"Adăugat: {nume}", type="positive", position="top-right")
        render_cos.refresh()

    # ── 1. CLIENT ────────────────────────────────────────────────
    with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
        ui.label("CLIENT").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3")

        optiuni   = {f"{c['nume_client']} | {c['telefon']}": c for c in toti_clientii}
        lista_opt = sorted(optiuni.keys())

        refs = {"client_id": state.get("receptie_client_id")}

        def on_select_client(e):
            val = e.value
            if val and val in optiuni:
                c = optiuni[val]
                refs["client_id"] = c["id"]
                state["receptie_client_id"] = c["id"]
                nume_inp.value   = c["nume_client"]
                tel_inp.value    = c["telefon"]
                adresa_inp.value = c["adresa_principala"]
                ui.notify(f"Client selectat: {c['nume_client']}", type="positive", position="top-right")
            else:
                refs["client_id"] = None
                state["receptie_client_id"] = None

        client_select = ui.select(
            options=lista_opt, label="Caută client...", with_input=True,
            on_change=on_select_client,
        ).classes("w-full").props("outlined dark clearable")

        with ui.expansion("Date client (nou / editare)", icon="person").classes("w-full mt-2 text-slate-300"):
            with ui.element("div").classes("flex flex-col gap-2 pt-2"):
                nume_inp   = ui.input("Nume client").classes("w-full").props("outlined dark")
                tel_inp    = ui.input("Telefon").classes("w-full").props("outlined dark")
                adresa_inp = ui.input("Adresă principală").classes("w-full").props("outlined dark")

                def salveaza_client():
                    if not refs["client_id"]:
                        db.add_client(nume_inp.value, tel_inp.value, adresa_inp.value)
                        ui.notify("Client adăugat!", type="positive")
                    else:
                        db.update_client(refs["client_id"], nume_inp.value, tel_inp.value, adresa_inp.value)
                        ui.notify("Date actualizate!", type="positive")
                    ui.navigate.reload()

                ui.button("Salvează", icon="save", on_click=salveaza_client).props("no-caps outlined").classes("text-green-400 border-green-700")

    # ── 2. MENIURI RAPIDE ────────────────────────────────────────
    with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
        ui.label("MENIURI RAPIDE").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3")

        if not are_meniu:
            ui.label(f"Nu există meniu planificat pentru {data_sel.strftime('%d.%m.%Y')}.").classes("text-amber-400 text-sm")
        else:
            f1   = lista_f1[0]
            f2v1 = lista_f2[0]
            f2v2 = lista_f2[1] if len(lista_f2) >= 2 else lista_f2[0]
            sal  = lista_sal[0] if lista_sal else None

            ui.label("Meniu complet").classes("text-slate-400 text-xs mb-2")
            with ui.grid(columns=2).classes("gap-3 mb-4"):
                for eticheta, f2 in [("V1", f2v1), ("V2", f2v2)]:
                    desc = f"{f1['nume']} + {f2['nume']}" + (f" + {sal['nume']}" if sal else "")
                    with ui.card().classes("bg-slate-700 border border-slate-600 p-3"):
                        ui.label(f"Meniu {eticheta}").classes("text-white font-semibold text-sm")
                        ui.label(desc).classes("text-slate-400 text-xs mb-2")
                        with ui.element("div").classes("flex items-center gap-2"):
                            qty = ui.number(value=1, min=1, step=1).classes("w-20").props("outlined dark dense")
                            _f2, _et = f2, eticheta
                            def add_meniu(q=qty, _f=_f2):
                                n = int(q.value) if q.value else 1
                                adauga(f1['nume'], n, f1.get('pret_standard', 0), 'standard')
                                adauga(_f['nume'], n, _f.get('pret_standard', 0), 'standard')
                                if sal:
                                    adauga(sal['nume'], n, sal.get('pret_standard', 0), 'standard')
                            ui.button(f"➕ {_et}", on_click=add_meniu).props("no-caps dense").classes("bg-red-700 text-white text-xs")

            ui.label("Porție solo").classes("text-slate-400 text-xs mb-2")
            solo = [(f1, "Felul 1"), (f2v1, "F2 V1"), (f2v2, "F2 V2")] + ([(sal, "Salată")] if sal else [])
            with ui.grid(columns=len(solo)).classes("gap-3"):
                for prod, label in solo:
                    with ui.card().classes("bg-slate-700 border border-slate-600 p-3"):
                        ui.label(label).classes("text-white text-xs font-semibold")
                        ui.label(prod['nume']).classes("text-slate-400 text-xs mb-2")
                        with ui.element("div").classes("flex items-center gap-1"):
                            qty = ui.number(value=1, min=1, step=1).classes("w-16").props("outlined dark dense")
                            _p = prod
                            def add_solo(q=qty, p=_p):
                                adauga(p['nume'], int(q.value) if q.value else 1, p.get('pret_standard', 0), 'standard')
                            ui.button("➕", on_click=add_solo).props("no-caps dense flat").classes("text-red-400")

    # ── 3. PRODUSE SPECIALE ──────────────────────────────────────
    with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
        ui.label("PRODUSE SPECIALE").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3")

        speciale = [p for p in nomenclator if p['categorie'] == 'special']
        opt_spec = {f"{p['nume']} — {p.get('pret_standard',0)} lei": p for p in speciale}

        with ui.element("div").classes("flex gap-3 items-end"):
            sel_spec = ui.select(options=list(opt_spec.keys()), label="Alege produs special", with_input=True).classes("flex-1").props("outlined dark clearable")
            qty_spec = ui.number(value=1, min=1, step=1, label="Buc").classes("w-24").props("outlined dark")

            def add_special():
                if not sel_spec.value or sel_spec.value not in opt_spec:
                    ui.notify("Selectează un produs!", type="warning")
                    return
                p = opt_spec[sel_spec.value]
                adauga(p['nume'], int(qty_spec.value) if qty_spec.value else 1, p.get('pret_standard', 0), 'special')

            ui.button("➕ Adaugă", on_click=add_special).props("no-caps").classes("bg-red-700 text-white")

    # ── 4. COȘ ───────────────────────────────────────────────────
    render_cos()

    # ── 5. LOGISTICĂ ─────────────────────────────────────────────
    with ui.card().classes("bg-slate-800 border border-slate-700 w-full p-4 mb-4"):
        ui.label("LOGISTICĂ & LIVRARE").classes("text-[10px] font-bold text-slate-500 uppercase tracking-widest mb-3")

        with ui.grid(columns=2).classes("gap-4"):
            ora_sel   = ui.select(options=INTERVALE_ORA, value="12:00-12:30", label="Ora livrare").props("outlined dark")
            sofer_sel = ui.select(options=livratori, value=livratori[0] if livratori else "", label="Livrator").props("outlined dark")

        plata_sel = ui.select(options=["cash", "card", "factura"], value="cash", label="Metodă plată").classes("w-full mt-3").props("outlined dark")
        obs_inp   = ui.input(label="Observații / Adresă").classes("w-full mt-2").props("outlined dark")

    # ── 6. SALVARE ───────────────────────────────────────────────
    def salveaza():
        cos = state.get("receptie_cos", [])
        cid = state.get("receptie_client_id")
        if not cos:
            ui.notify("Coșul este gol!", type="warning")
            return
        if not cid:
            ui.notify("Selectează un client!", type="warning")
            return
        total = sum(i["pret"] * i["cantitate"] for i in cos)
        ok = db.save_comanda_finala(
            client_id   = cid,
            produse     = cos,
            total       = total,
            sofer       = sofer_sel.value,
            ora         = ora_sel.value,
            obs         = obs_inp.value,
            plata       = plata_sel.value,
            tip_comanda = "livrare",
            data_comanda= data_sel,
        )
        if ok:
            ui.notify(f"Comandă salvată! Livrator: {sofer_sel.value}", type="positive")
            state["receptie_cos"] = []
            state["receptie_client_id"] = None
            ui.navigate.reload()
        else:
            ui.notify("Eroare la salvare!", type="negative")

    ui.button("💾 SALVEAZĂ COMANDA", on_click=salveaza, icon="save").classes("w-full bg-red-600 text-white text-base font-bold mt-2").props("no-caps")


# ── Rezumat Livrări ───────────────────────────────────────────

def show_rezumat() -> None:
    state = app.storage.user
    azi   = utils.get_ro_time().date()

    if "rezumat_data" not in state:
        state["rezumat_data"] = azi.isoformat()

    with ui.element("div").classes("p-4 w-full"):

        # Header + selector dată
        with ui.element("div").classes("flex items-center gap-3 mb-4"):
            ui.label("📋").classes("text-3xl")
            with ui.element("div"):
                ui.label("Rezumat Livrări").classes("text-2xl font-bold text-white")

        with ui.element("div").classes("mb-4"):
            data_input = ui.input(
                label="Data rezumatului", value=state["rezumat_data"],
            ).props("outlined dark readonly").classes("w-64")
            with data_input.add_slot("append"):
                ui.icon("edit_calendar").classes("cursor-pointer text-slate-400 hover:text-white").on(
                    "click", lambda: date_menu.open()
                )
            with ui.menu().classes("bg-slate-800") as date_menu:
                def on_date(e):
                    if e.value:
                        state["rezumat_data"] = e.value
                        data_input.value = e.value
                        date_menu.close()
                        ui.navigate.reload()
                ui.date(value=state["rezumat_data"], on_change=on_date).props("dark")

        _render_rezumat(state)


def _render_rezumat(state) -> None:
    from datetime import date

    data_str = state.get("rezumat_data", utils.get_ro_time().date().isoformat())
    try:
        data_sel = date.fromisoformat(data_str)
    except Exception:
        data_sel = utils.get_ro_time().date()

    comenzi  = db.get_comenzi_receptie(data_sel)
    livratori = db.get_lista_livratori()

    if not comenzi:
        ui.label(f"Nicio comandă pentru {data_sel.strftime('%d.%m.%Y')}.").classes("text-slate-400 text-sm")
        return

    def suma(lista, metoda):
        return sum(c.get('total_plata', 0) for c in lista if c.get('metoda_plata') == metoda)

    total_cash    = suma(comenzi, 'cash')
    total_card    = suma(comenzi, 'card')
    total_factura = suma(comenzi, 'factura')
    total_gen     = sum(c.get('total_plata', 0) for c in comenzi)

    # Sumar general
    with ui.grid(columns=4).classes("gap-4 mb-6"):
        for label, val, col in [
            ("💵 Cash de încasat", f"{total_cash} lei",    "text-green-400"),
            ("💳 Card",            f"{total_card} lei",    "text-blue-400"),
            ("🧾 Factură",         f"{total_factura} lei", "text-purple-400"),
            ("📊 Total general",   f"{total_gen} lei",     "text-red-400"),
        ]:
            with ui.card().classes("bg-slate-800 border border-slate-700 p-4"):
                ui.label(label).classes("text-slate-400 text-xs mb-1")
                ui.label(val).classes(f"text-xl font-bold {col}")

    # Per livrator
    for sofer in livratori:
        comenzi_sofer = [c for c in comenzi if c['sofer'] == sofer]
        if not comenzi_sofer:
            continue

        cash_s = suma(comenzi_sofer, 'cash')
        card_s = suma(comenzi_sofer, 'card')
        fact_s = suma(comenzi_sofer, 'factura')

        parti = []
        if cash_s: parti.append(f"💵 {cash_s} lei")
        if card_s: parti.append(f"💳 {card_s} lei")
        if fact_s: parti.append(f"🧾 {fact_s} lei")
        subtitlu = "  |  ".join(parti) if parti else "0 lei"

        with ui.expansion(f"🚚 {sofer.upper()} — {subtitlu}", icon="local_shipping").classes("w-full mb-2 bg-slate-800 border border-slate-700 rounded-lg text-white"):
            with ui.element("div").classes("p-2"):
                for cz in comenzi_sofer:
                    with ui.card().classes("bg-slate-700 border border-slate-600 p-3 mb-2"):
                        # Header comandă
                        with ui.element("div").classes("flex items-start justify-between gap-3"):
                            with ui.element("div").classes("flex-1"):
                                ora = str(cz.get('ora_livrare_estimata', ''))[:5]
                                ui.label(f"🕒 {ora}  —  {cz['client']}").classes("text-white font-semibold text-sm")
                                if cz.get('telefon'):
                                    ui.label(f"📞 {cz['telefon']}").classes("text-slate-400 text-xs")
                                ui.label(f"📍 {cz.get('adresa_principala', 'N/A')}").classes("text-slate-400 text-xs")

                            # Sumă + metodă
                            with ui.element("div").classes("text-right"):
                                metoda = cz.get('metoda_plata', '')
                                icon_m = '💵' if metoda == 'cash' else ('💳' if metoda == 'card' else '🧾')
                                ui.label(f"{cz['total_plata']} lei").classes("text-green-400 font-bold")
                                ui.label(f"{icon_m} {metoda.upper()}").classes("text-slate-400 text-xs")

                            # Buton stergere
                            def sterge(cid=cz['id']):
                                if db.delete_comanda(cid):
                                    ui.notify("Comandă ștearsă!", type="positive")
                                    ui.navigate.reload()
                                else:
                                    ui.notify("Eroare la ștergere!", type="negative")
                            ui.button(icon="delete", on_click=sterge).props("flat round dense color=red size=xs")

                        # Produse
                        detalii = (cz.get('detalii') or '').split(', ')
                        with ui.element("div").classes("mt-2 flex flex-wrap gap-1"):
                            for parte in detalii:
                                if not parte:
                                    continue
                                try:
                                    produs_txt, stare = parte.split('|')
                                    culoare = "bg-green-900 text-green-300" if stare == 'gatit' else "bg-slate-600 text-slate-300"
                                    ui.label(produs_txt.strip()).classes(f"text-xs px-2 py-0.5 rounded {culoare}")
                                except Exception:
                                    ui.label(parte).classes("text-xs px-2 py-0.5 rounded bg-slate-600 text-slate-300")
