"""
admin_manager/rapoarte.py
--------------------------
Sectiunea "Monitorizare Comenzi" din pagina Admin.
Afiseaza:
  - Rezumat total cantitati (bucatarie)
  - Rezumat financiar pe sectii (pranz, cina, livrare etc.)
  - Lista detaliata a comenzilor cu optiune de stergere
  - Raportare periodica (interval de date)

Primeste `data_plan` (datetime.date) din main.py — nu are selector propriu de data.
"""

import streamlit as st
import pandas as pd
import database as db
import utils
from datetime import date


def show(data_plan):
    """Randeaza sectiunea de monitorizare pentru data_plan."""
    st.subheader("📊 Control General Producție & Livrări")

    engine = db.get_engine()
    toate_comenzile = db.get_rezumat_zi(data_plan)

    if not toate_comenzile:
        st.info("Nicio comandă sau lot de producție găsit pentru această dată.")
    else:
        # -------------------------------------------------------
        # 1. REZUMAT CANTITATI (pentru bucatarie)
        # -------------------------------------------------------
        with st.expander("👨‍🍳 REZUMAT TOTAL CANTITĂȚI (Bucătărie)", expanded=False):
            dict_totaluri = {}
            for c in toate_comenzile:
                detalii_raw = c.get('detalii')
                if not detalii_raw:
                    continue
                for parte in detalii_raw.split(', '):
                    try:
                        if 'x ' in parte:
                            qty_str, nume_p = parte.split('x ', 1)
                            dict_totaluri[nume_p] = dict_totaluri.get(nume_p, 0) + int(qty_str)
                    except Exception:
                        continue

            if dict_totaluri:
                df_summary = pd.DataFrame([
                    {"Produs": k, "Total Porții": v}
                    for k, v in dict_totaluri.items()
                ])
                st.table(df_summary)
            else:
                st.write("Nu există produse de centralizat.")

        # -------------------------------------------------------
        # 2. REZUMAT FINANCIAR PE SECTII
        # -------------------------------------------------------
        sectii = {}
        total_general = 0

        for c in toate_comenzile:
            tip = str(c.get('tip_comanda', 'ALTELE')).upper().strip()
            valoare = c.get('total_plata', 0)

            if tip not in sectii:
                sectii[tip] = {"produse": {}, "bani": 0}

            sectii[tip]["bani"] += valoare
            total_general += valoare

            detalii_raw = c.get('detalii')
            if not detalii_raw:
                continue

            for parte in detalii_raw.split(', '):
                if 'x ' in parte:
                    try:
                        qty_str, rest = parte.split('x ', 1)
                        # Eliminam statusul "|gatit" sau "|nou" din nume
                        nume_p = rest.split('|')[0]
                        sectii[tip]["produse"][nume_p] = sectii[tip]["produse"].get(nume_p, 0) + int(qty_str)
                    except Exception:
                        continue

        # Titlul expanderului contine sumarul financiar
        elemente_titlu = [f"{cat}: {d['bani']:.0f} lei" for cat, d in sectii.items()]
        titlu_financiar = "💰 Rezumat Zi: " + " | ".join(elemente_titlu) + f"  ——  TOTAL: {total_general:.2f} lei"

        with st.expander(titlu_financiar, expanded=False):
            for nume_cat, date_cat in sectii.items():
                with st.container(border=True):
                    c1, c2 = st.columns([3, 1])
                    c1.markdown(f"#### 📍 {nume_cat}")
                    c2.metric("Vânzări", f"{date_cat['bani']:.2f} lei")

                    if date_cat["produse"]:
                        df_cat = pd.DataFrame([
                            {"Produs": k, "Cantitate": v}
                            for k, v in date_cat["produse"].items()
                        ])
                        st.table(df_cat)

        # -------------------------------------------------------
        # 3. LISTA DETALIATA PE COMENZI
        # -------------------------------------------------------
        st.markdown("### 📝 Detalii Comenzi & Status Real-Time")

        for cz in toate_comenzile:
            icon_tip = "🚚" if cz['tip_comanda'] == 'livrare' else "🏢"
            ora = str(cz['ora_livrare_estimata'])[:5]
            status_emoji = {'nou': "🔵", 'pregatit': "🟢", 'livrat': "⚪"}.get(cz['status_comanda'], "❓")
            titlu = (
                f"{status_emoji} {cz['status_comanda'].upper()} | "
                f"{ora} | {cz['client']} | {cz.get('total_plata', 0):.2f} lei | {icon_tip}"
            )

            with st.expander(titlu):
                col_stanga, col_dreapta = st.columns([3, 1])

                with col_stanga:
                    st.write("**Produse și Stadiu Producție:**")
                    if cz['detalii']:
                        for linie in cz['detalii'].split(', '):
                            try:
                                produs_full, stare = linie.split('|')
                                if stare == 'gatit':
                                    st.markdown(f"✅ :green[{produs_full}]")
                                else:
                                    st.markdown(f"⏳ :orange[{produs_full}]")
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
    # 4. RAPORTARE PERIODICA (interval de date)
    # -------------------------------------------------------
    st.divider()
    st.subheader("📊 Raportare Periodică")

    today = utils.get_ro_time().date()
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
                nr_total = sum(r['nr_comenzi'] for r in date_raport)

                c1, c2 = st.columns(2)
                c1.metric("Total Încasări (brut)", f"{total_per_perioada:.2f} lei")
                c2.metric("Număr Total Comenzi", nr_total)

                df_raport = pd.DataFrame(date_raport)
                df_raport.columns = ['Secția', 'Total Valoare (lei)', 'Nr. Comenzi']
                st.table(df_raport)
