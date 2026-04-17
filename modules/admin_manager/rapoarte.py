"""
admin_manager/rapoarte.py
--------------------------
Sectiunea "Monitorizare Comenzi" din pagina Admin.
Afiseaza:
  - Rezumat total cantitati cu statusuri efective per portie
  - Rezumat financiar pe sectii cu statusuri efective
  - Lista detaliata a comenzilor cu optiune de stergere
  - Raportare periodica (interval de date)

Primeste `data_plan` (datetime.date) din main.py — nu are selector propriu de data.
"""

import streamlit as st
import pandas as pd
import database as db
import utils
from datetime import date


# ------------------------------------------------------------------
# Statusul efectiv al unei portii = combinatie status linie + comanda
# ------------------------------------------------------------------
EFF_STATUSES = [
    ('in_gatire',  '🔴', 'în gătire',  'red'),
    ('de_ambalat', '🔵', 'de ambalat', 'blue'),
    ('ambalat',    '🟡', 'ambalat',    'orange'),
    ('pe_drum',    '🚀', 'pe drum',    'violet'),
    ('livrat',     '✅', 'livrat',     'green'),
]

STATUS_COMANDA_EMOJI = {
    'nou':      '🔵',
    'pregatit': '🟡',
    'pedrum':   '🚀',
    'livrat':   '✅',
    'anulat':   '❌',
}


def _eff_key(line_status, order_status):
    """Returneaza cheia statusului efectiv al unei portii."""
    if line_status != 'gatit':
        return 'in_gatire'
    return {
        'nou':      'de_ambalat',
        'pregatit': 'ambalat',
        'pedrum':   'pe_drum',
        'livrat':   'livrat',
    }.get(order_status, 'de_ambalat')


def _parse_produse(detalii_raw, order_status, dest):
    """
    Parseaza string-ul detalii si adauga portiile in dest.
    dest: { produs: { eff_key: count } }
    """
    for parte in (detalii_raw or '').split(', '):
        if 'x ' not in parte:
            continue
        try:
            qty_str, rest = parte.split('x ', 1)
            parts = rest.split('|')
            produs  = parts[0].strip()
            line_st = parts[1].strip() if len(parts) > 1 else 'nou'
            qty     = int(qty_str.strip())
            eff     = _eff_key(line_st, order_status)
            if produs not in dest:
                dest[produs] = {}
            dest[produs][eff] = dest[produs].get(eff, 0) + qty
        except Exception:
            continue


def _show_produse_breakdown(produse_dict):
    """
    Afiseaza per produs: total + breakdown colorat per status efectiv.
    produse_dict: { produs: { eff_key: count } }
    """
    for produs, by_eff in produse_dict.items():
        total = sum(by_eff.values())
        parts = []
        for eff_key, icon, label, color in EFF_STATUSES:
            cnt = by_eff.get(eff_key, 0)
            if cnt > 0:
                parts.append(f"{icon} :{color}[**{cnt}** {label}]")
        breakdown = "  ·  ".join(parts)
        st.markdown(f"**{produs}** — {total} buc  ·  {breakdown}")


# ------------------------------------------------------------------

def show(data_plan):
    """Randeaza sectiunea de monitorizare pentru data_plan."""
    st.subheader("📊 Control General Producție & Livrări")

    engine = db.get_engine()
    toate_comenzile = db.get_rezumat_zi(data_plan)

    if not toate_comenzile:
        st.info("Nicio comandă sau lot de producție găsit pentru această dată.")
    else:
        # -------------------------------------------------------
        # 1. REZUMAT TOTAL CANTITĂȚI (bucatarie)
        # -------------------------------------------------------
        with st.expander("👨‍🍳 REZUMAT TOTAL CANTITĂȚI (Bucătărie)", expanded=False):
            produse_total = {}
            for c in toate_comenzile:
                _parse_produse(c.get('detalii'), c.get('status_comanda', 'nou'), produse_total)

            if produse_total:
                _show_produse_breakdown(produse_total)

                # Nevandut declarat
                nevandut = db.get_stoc_nevandut(data_plan)
                if nevandut:
                    st.divider()
                    st.markdown("**🍽️ Nevândut declarat:**")
                    for produs, info in nevandut.items():
                        st.markdown(
                            f"**{produs}** — declarat: {info['cantitate']} | "
                            f"servit: {info['cantitate_servita']} | "
                            f":orange[disponibil: {info['ramas']}]"
                        )
            else:
                st.write("Nu există produse de centralizat.")

        # -------------------------------------------------------
        # 2. REZUMAT FINANCIAR PE SECȚII
        # -------------------------------------------------------
        sectii = {}
        total_general = 0

        for c in toate_comenzile:
            tip          = str(c.get('tip_comanda', 'ALTELE')).upper().strip()
            order_status = c.get('status_comanda', 'nou')
            valoare      = c.get('total_plata', 0)

            if tip not in sectii:
                sectii[tip] = {'bani': 0, 'comenzi_st': {}, 'produse': {}}

            sectii[tip]['bani'] += valoare
            total_general       += valoare
            sectii[tip]['comenzi_st'][order_status] = sectii[tip]['comenzi_st'].get(order_status, 0) + 1
            _parse_produse(c.get('detalii'), order_status, sectii[tip]['produse'])

        elemente_titlu = [f"{cat}: {d['bani']:.0f} lei" for cat, d in sectii.items()]
        titlu_financiar = (
            "💰 Rezumat Zi: " + " | ".join(elemente_titlu) +
            f"  ——  TOTAL: {total_general:.2f} lei"
        )

        with st.expander(titlu_financiar, expanded=False):
            for tip, date_tip in sectii.items():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"#### 📍 {tip}")
                    c2.metric("Vânzări", f"{date_tip['bani']:.2f} lei")

                    # Sumar comenzi per status
                    comenzi_parts = []
                    for st_key, cnt in date_tip['comenzi_st'].items():
                        emoji = STATUS_COMANDA_EMOJI.get(st_key, '❓')
                        comenzi_parts.append(f"{emoji} {cnt} {st_key}")
                    st.caption("Comenzi: " + "  |  ".join(comenzi_parts))

                    if date_tip['produse']:
                        _show_produse_breakdown(date_tip['produse'])

        # -------------------------------------------------------
        # EXPORT REZUMAT ZILNIC
        # -------------------------------------------------------
        rows_export = []
        for tip, date_tip in sectii.items():
            for produs, by_eff in date_tip['produse'].items():
                total = sum(by_eff.values())
                rows_export.append({
                    "Secție": tip,
                    "Produs": produs,
                    **{label: by_eff.get(eff_key, 0) for eff_key, _, label, _ in EFF_STATUSES},
                    "Total porții": total,
                })
        if rows_export:
            df_zilnic = pd.DataFrame(rows_export)
            rows_fin = [{"Secție": tip, "Vânzări (lei)": d["bani"], "Nr. comenzi": sum(d["comenzi_st"].values())}
                        for tip, d in sectii.items()]
            df_fin = pd.DataFrame(rows_fin)

            data_str = data_plan.strftime('%d.%m.%Y')
            col_exp1, col_exp2 = st.columns(2)
            with col_exp1:
                excel_cantitati = utils.export_raport_excel(
                    df_zilnic,
                    titlu=f"Raport Cantități — {data_str}",
                    subtitlu=f"Situație producție și distribuție porții • {data_str}",
                    sheet_name="Cantități",
                )
                st.download_button(
                    "📥 Export Cantități Zilnice",
                    data=excel_cantitati,
                    file_name=f"Cantitati_{data_plan.strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            with col_exp2:
                excel_financiar = utils.export_raport_excel(
                    df_fin,
                    titlu=f"Raport Financiar — {data_str}",
                    subtitlu=f"Vânzări și încasări pe secții • {data_str}",
                    sheet_name="Financiar",
                )
                st.download_button(
                    "📥 Export Financiar Zilnic",
                    data=excel_financiar,
                    file_name=f"Financiar_{data_plan.strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )

        # -------------------------------------------------------
        # 3. LISTA DETALIATA PE COMENZI
        # -------------------------------------------------------
        loturi     = [c for c in toate_comenzile if c.get('client_id') == 999]
        comenzi_cl = [c for c in toate_comenzile if c.get('client_id') != 999]

        TIP_LOT_LABEL = {
            'pranz':     '🍲 Lot Prânz',
            'cina':      '🌙 Lot Cină',
            'sandwich':  '🥪 Lot Sandwich',
            'eveniment': '🎉 Lot Eveniment',
            'special':   '⭐ Lot Special',
        }

        if loturi:
            st.markdown("### 🏭 Loturi Lansate în Producție")
            for cz in loturi:
                ora          = str(cz['ora_livrare_estimata'])[:5]
                order_status = cz.get('status_comanda', 'nou')
                st_emoji     = STATUS_COMANDA_EMOJI.get(order_status, '❓')
                tip_label    = TIP_LOT_LABEL.get(cz['tip_comanda'], f"📦 {cz['tip_comanda'].upper()}")
                titlu = (
                    f"{tip_label}  |  {ora}  |  "
                    f"{cz.get('total_plata', 0):.0f} lei  |  {st_emoji} {order_status.upper()}"
                )
                with st.expander(titlu):
                    col_stanga, col_dreapta = st.columns([3, 1])
                    with col_stanga:
                        if cz['detalii']:
                            for linie in cz['detalii'].split(', '):
                                try:
                                    produs_full, line_st = linie.split('|')
                                    eff = _eff_key(line_st.strip(), order_status)
                                    cfg = next((e for e in EFF_STATUSES if e[0] == eff), None)
                                    if cfg:
                                        _, icon, label, color = cfg
                                        st.markdown(f"{icon} :{color}[{produs_full.strip()}] — *{label}*")
                                    else:
                                        st.write(f"• {produs_full.strip()}")
                                except Exception:
                                    st.write(f"• {linie}")
                    with col_dreapta:
                        if st.button("🗑️ Șterge", key=f"admin_del_lot_{cz['id']}", use_container_width=True):
                            if db.delete_comanda(cz['id']):
                                st.rerun()

        if comenzi_cl:
            st.markdown("### 📝 Comenzi Clienți")
            for cz in comenzi_cl:
                icon_tip     = "🚚" if cz['tip_comanda'] == 'livrare' else "🏢"
                ora          = str(cz['ora_livrare_estimata'])[:5]
                order_status = cz.get('status_comanda', 'nou')
                st_emoji     = STATUS_COMANDA_EMOJI.get(order_status, '❓')
                titlu = (
                    f"{st_emoji} {order_status.upper()}  |  "
                    f"{ora}  |  {cz['client']}  |  "
                    f"{cz.get('total_plata', 0):.2f} lei  |  {icon_tip}"
                )
                with st.expander(titlu):
                    col_stanga, col_dreapta = st.columns([3, 1])
                    with col_stanga:
                        st.write("**Produse și Stadiu Producție:**")
                        if cz['detalii']:
                            for linie in cz['detalii'].split(', '):
                                try:
                                    produs_full, line_st = linie.split('|')
                                    eff = _eff_key(line_st.strip(), order_status)
                                    cfg = next((e for e in EFF_STATUSES if e[0] == eff), None)
                                    if cfg:
                                        _, icon, label, color = cfg
                                        st.markdown(f"{icon} :{color}[{produs_full.strip()}] — *{label}*")
                                    else:
                                        st.write(f"• {produs_full.strip()}")
                                except Exception:
                                    st.write(f"• {linie}")
                        else:
                            st.caption("Fără produse")
                        st.divider()
                        st.caption(f"📞 {cz.get('telefon', 'N/A')} | 💳 {cz.get('metoda_plata', '').upper()}")
                        if cz['tip_comanda'] == 'livrare':
                            st.caption(f"📍 {cz.get('adresa_principala', 'N/A')}")
                    with col_dreapta:
                        if st.button("Anulează", key=f"admin_cancel_{cz['id']}", use_container_width=True):
                            db.update_status_comanda(engine, cz['id'], 'anulat')
                            st.rerun()
                        if st.button("🗑️ Șterge", key=f"admin_del_{cz['id']}", use_container_width=True):
                            if db.delete_comanda(cz['id']):
                                st.rerun()

        # -------------------------------------------------------
        # 4. SERVIRI FIRME GHIȘEU
        # -------------------------------------------------------
        serviri_gh = db.get_rezumat_serviri_firme_ghiseu(data_plan)
        if serviri_gh:
            st.markdown("### 🏢 Serviri Firme Ghișeu")
            for f in serviri_gh:
                serviti     = f["serviti"]
                total_activi= f["total_activi"]
                suma        = f["suma"]
                la_masa     = f["la_masa"]
                pachete     = f["pachete"]
                progres     = f"{serviti}/{total_activi}" if total_activi else str(serviti)
                if serviti == 0:
                    culoare = "gray"
                elif serviti < total_activi:
                    culoare = "orange"
                else:
                    culoare = "green"
                titlu_f = (
                    f":{culoare}[**{f['nume_firma']}**]  —  "
                    f"{progres} serviți  |  "
                    f"🍽️ {la_masa} masă  📦 {pachete} pachete  |  "
                    f"💰 {suma:.0f} lei"
                )
                st.markdown(titlu_f)

    # -------------------------------------------------------
    # 5. RAPORTARE PERIODICA (interval de date)
    # -------------------------------------------------------
    st.divider()
    st.subheader("📊 Raportare Periodică")

    today     = utils.get_ro_time().date()
    first_day = today.replace(day=1)

    interval = st.date_input(
        "Selectează intervalul:",
        value=(first_day, today),
        max_value=today,
        key="admin_interval_raport"
    )

    if isinstance(interval, tuple) and len(interval) == 2:
        d_start, d_end = interval

        if st.button("Generează Raport", key="btn_genereaza_raport"):
            date_raport = db.get_raport_interval(d_start, d_end)

            if not date_raport:
                st.info(f"Nicio comandă găsită între {d_start} și {d_end}.")
            else:
                st.write(f"### Rezultat: {d_start} → {d_end}")

                total_per_perioada = sum(r['total_valoare'] for r in date_raport)
                nr_total           = sum(r['nr_comenzi']   for r in date_raport)

                c1, c2 = st.columns(2)
                c1.metric("Total Încasări (brut)", f"{total_per_perioada:.2f} lei")
                c2.metric("Număr Total Comenzi", nr_total)

                df_raport          = pd.DataFrame(date_raport)
                df_raport.columns  = ['Secția', 'Total Valoare (lei)', 'Nr. Comenzi']
                st.table(df_raport)

                excel_raport = utils.export_raport_excel(
                    df_raport,
                    titlu=f"Raport Periodic {d_start.strftime('%d.%m.%Y')} — {d_end.strftime('%d.%m.%Y')}",
                    subtitlu=f"Vânzări totale pe secții • interval {d_start.strftime('%d.%m.%Y')} – {d_end.strftime('%d.%m.%Y')}",
                    sheet_name="Raport Periodic",
                )
                st.download_button(
                    "📥 Exportă Raport Excel",
                    data=excel_raport,
                    file_name=f"Raport_{d_start.strftime('%d%m%Y')}_{d_end.strftime('%d%m%Y')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
