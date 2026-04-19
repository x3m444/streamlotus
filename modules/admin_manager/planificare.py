"""
admin_manager/planificare.py
-----------------------------
Sectiunea "Planificare Saptamanala" din pagina Admin.
Permite:
  - Planificarea meniului zilnic (pranz, cina, sandwich)
  - Vizualizarea tabelara a intregii saptamani
  - Export Excel landscape

Primeste `data_plan` (datetime.date) din main.py — nu are selector propriu de data.
"""

import streamlit as st
import pandas as pd
import database as db
import utils
from datetime import date


@st.fragment
def show(data_plan):
    """Randeaza sectiunea de planificare pentru saptamana care contine data_plan."""
    st.subheader("🚀 Configurare Fluxuri Producție")

    # Aratam pentru ce zi lucram (data vine din selectorul global din main.py)
    nume_zi_ro = utils.format_nume_zi(data_plan)
    st.write(f"Gestionezi fluxurile pentru: **{nume_zi_ro}**")

    toate = db.get_toate_produsele()
    if not toate:
        st.warning("Nomenclatorul este gol. Adaugă produse în 'Gestiune Nomenclator'.")
        return

    # -------------------------------------------------------
    # PLANIFICARE PRANZ
    # -------------------------------------------------------
    with st.expander("🥣 PLANIFICĂ PRÂNZ", expanded=True):
        f1_opts = [None] + [p for p in toate if p['categorie'] == 'felul_1']
        f2_opts = [None] + [p for p in toate if p['categorie'] == 'felul_2']
        acc_opts = [None] + [p for p in toate if p['categorie'] == 'salate' or p['pret_standard'] == 0]

        def format_p(x):
            return x['nume'] if x else "-- Alege --"

        c1, c2, c3, c4 = st.columns(4)
        with c1: sel_f1 = st.selectbox("Felul 1:", f1_opts, format_func=format_p, key="plan_f1")
        with c2: sel_f2_1 = st.selectbox("Felul 2 (A):", f2_opts, format_func=format_p, key="plan_f2a")
        with c3: sel_f2_2 = st.selectbox("Felul 2 (B):", f2_opts, format_func=format_p, key="plan_f2b")
        with c4: sel_acc = st.selectbox("Salată/Acc.:", acc_opts, format_func=format_p, key="plan_acc")

        if st.button("💾 Salvează Plan Prânz", use_container_width=True, key="btn_salv_pranz"):
            if sel_f1 and sel_f2_1 and sel_f2_2 and sel_acc:
                db.salveaza_planificare(
                    data_plan,
                    [sel_f1['id'], sel_f2_1['id'], sel_f2_2['id'], sel_acc['id']],
                    tip_plan="pranz"
                )
                st.success("Planificat: Prânz ✅")
                st.rerun()
            else:
                st.error("Selectează toate componentele prânzului!")

    # -------------------------------------------------------
    # PLANIFICARE CINA
    # -------------------------------------------------------
    with st.expander("🌙 PLANIFICĂ CINĂ"):
        f2_cina = [None] + [p for p in toate if p['categorie'] == 'felul_2']
        salate_cina = [None] + [p for p in toate if p['categorie'] == 'salate']

        c1, c2 = st.columns(2)
        with c1:
            sel_f2_c = st.selectbox(
                "🍖 Felul Principal (Cină):", f2_cina,
                format_func=lambda x: x['nume'] if x else "-- Alege --",
                key="plan_f2_c_only"
            )
        with c2:
            sel_sal_c = st.selectbox(
                "🥗 Salată (Cină):", salate_cina,
                format_func=lambda x: x['nume'] if x else "-- Alege --",
                key="plan_sal_c_only"
            )

        if st.button("💾 Salvează Plan Cină", use_container_width=True, key="btn_salv_cina"):
            if sel_f2_c and sel_sal_c:
                db.salveaza_planificare(data_plan, [sel_f2_c['id'], sel_sal_c['id']], tip_plan="cina")
                st.success(f"Cina pentru {nume_zi_ro} a fost salvată! ✅")
                st.toast(f"Cina pentru {nume_zi_ro} salvată!", icon="✅")
                st.rerun()
            else:
                st.error("⚠️ Alege atât felul principal cât și salata!")

    # -------------------------------------------------------
    # PLANIFICARE SANDWICH
    # -------------------------------------------------------
    with st.expander("🥪 PLANIFICĂ SANDWICH-URILE ZILEI"):
        sw_opts = [p for p in toate if p['categorie'] == 'sandwich']
        sel_sw_zi = st.multiselect(
            "Ce sandwich-uri avem azi?", sw_opts,
            format_func=lambda x: x['nume'],
            key="plan_sw"
        )

        if st.button("💾 Salvează Plan Sandwich", use_container_width=True, key="btn_salv_sw"):
            if sel_sw_zi:
                db.salveaza_planificare(data_plan, [s['id'] for s in sel_sw_zi], tip_plan="sandwich")
                st.success("Planificat: Sandwich-uri ✅")
                st.rerun()
            else:
                st.error("⚠️ Selectează cel puțin un sandwich!")

    st.divider()

    # -------------------------------------------------------
    # TABEL SAPTAMANAL (privire de ansamblu)
    # -------------------------------------------------------
    st.header("📋 Planificare Săptămânală")

    zile_sapt = utils.get_zile_saptamana(data_plan)
    plan_saptamanal = db.get_meniu_planificat(zile_sapt[0], zile_sapt[-1])

    # Construim antetul tabelului HTML
    header_html = "".join([
        f"<th style='border:1px solid #444;padding:12px;background:#262730;color:#FAFAFA;min-width:150px;'>"
        f"<div style='color:#FF4B4B;font-size:1.1em;'>{utils.format_nume_zi(z)}</div>"
        f"<div style='font-size:0.9em;font-weight:normal;opacity:0.7;'>{z.strftime('%d.%m')}</div></th>"
        for z in zile_sapt
    ])

    # Construim randurile pentru fiecare tip de masa
    rows_html = ""
    tipuri_masa = [
        ("pranz",    "🥣 PRÂNZ"),
        ("cina",     "🌙 CINĂ"),
        ("sandwich", "🥪 SANDWICH"),
    ]

    for cod_tip, eticheta in tipuri_masa:
        rand = (
            f"<tr><td style='border:1px solid #444;padding:15px;font-weight:bold;"
            f"background:#262730;color:#FAFAFA;text-align:left;border-right:3px solid #FF4B4B;'>"
            f"{eticheta}</td>"
        )
        for zi in zile_sapt:
            produse = plan_saptamanal.get((str(zi), cod_tip), [])
            if produse:
                items_html = "".join([
                    f"<div style='margin-bottom:5px;'>• {p['nume']}"
                    + (f" <span style='color:#888;font-size:0.85em;'>({int(p['pret_standard'])} lei)</span>"
                       if p.get('pret_standard') and p['pret_standard'] > 0 else "")
                    + "</div>"
                    for p in produse
                ])
                rand += f"<td style='border:1px solid #444;padding:12px;vertical-align:top;color:#FAFAFA;font-size:0.95em;'>{items_html}</td>"
            else:
                rand += "<td style='border:1px solid #444;padding:12px;color:#555;font-style:italic;text-align:center;vertical-align:middle;'>---</td>"
        rand += "</tr>"
        rows_html += rand

    tabel_html = f"""
    <div style="overflow-x:auto;border-radius:8px;border:1px solid #444;margin:20px 0;">
        <table style="width:100%;border-collapse:collapse;font-family:sans-serif;background:#1e1e1e;">
            <thead>
                <tr>
                    <th style="border:1px solid #444;padding:12px;background:#262730;color:#888;width:150px;">FLUX</th>
                    {header_html}
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>"""

    st.markdown(tabel_html, unsafe_allow_html=True)

    # -------------------------------------------------------
    # EXPORT EXCEL LANDSCAPE
    # -------------------------------------------------------
    try:
        rows_export = []
        for zi in zile_sapt:
            m_pranz = plan_saptamanal.get((str(zi), "pranz"), [])
            m_cina  = plan_saptamanal.get((str(zi), "cina"),  [])

            def fmt_produse(lista):
                return "\n".join([
                    f"• {p['nume']} ({int(p['pret_standard'])} lei)"
                    if p.get('pret_standard') and p['pret_standard'] > 0
                    else f"• {p['nume']}"
                    for p in lista
                ])

            rows_export.append({
                "DATA / ZIUA": f"{utils.format_nume_zi(zi)}\n{zi.strftime('%d.%m')}",
                "🥣 MENIU PRÂNZ": fmt_produse(m_pranz) or "---",
                "🌙 MENIU CINĂ":  fmt_produse(m_cina)  or "---",
            })

        df_export = pd.DataFrame(rows_export)
        excel_file = utils.export_to_excel_landscape_v2(df_export)

        st.download_button(
            label="🖨️ Descarcă Meniu Landscape (Cantina LOTUS)",
            data=excel_file,
            file_name=f"Meniu_Lotus_{zile_sapt[0].strftime('%d_%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Eroare la generare Excel: {e}")
