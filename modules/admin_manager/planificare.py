import streamlit as st
import pandas as pd
from datetime import date

def show(db, utils, toate):
    st.subheader("🚀 Configurare Fluxuri Producție")
        
    # 1. Selector Dată și Date de Bază
    data_plan = st.date_input("Selectează data:", date.today(), key="dp")
    nume_zi_ro = utils.format_nume_zi(data_plan)
    st.write(f"Gestionezi fluxurile pentru: **{nume_zi_ro}**")
    
    toate = db.get_toate_produsele()
    if not toate:
        st.warning("Nomenclatorul este gol. Adaugă produse în Tab-ul 2.")
        return

    # ---------------------------------------------------------
    # MODUL A: PLANIFICARE (Salvarea în bază a ceea ce urmează să se gătească)
    # ---------------------------------------------------------
    st.markdown("### 📝 1. Planificare Meniuri")
    
    # A.1. Sub-Modul: Plan Meniu Prânz (F1, F2a, F2b, Salata)
    with st.expander("🥣 PLANIFICĂ PRÂNZ", expanded=True):
        f1_opts = [None] + [p for p in toate if p['categorie'] == 'felul_1']
        f2_opts = [None] + [p for p in toate if p['categorie'] == 'felul_2']
        acc_opts = [None] + [p for p in toate if p['categorie'] == 'salate' or p['pret_standard'] == 0]
        
        def format_p(x): return x['nume'] if x else "-- Alege --"

        c1, c2, c3, c4 = st.columns(4)
        with c1: sel_f1 = st.selectbox("Felul 1:", f1_opts, format_func=format_p, key="plan_f1")
        with c2: sel_f2_1 = st.selectbox("Felul 2 (A):", f2_opts, format_func=format_p, key="plan_f2a")
        with c3: sel_f2_2 = st.selectbox("Felul 2 (B):", f2_opts, format_func=format_p, key="plan_f2b")
        with c4: sel_acc = st.selectbox("Salată/Acc.:", acc_opts, format_func=format_p, key="plan_acc")

        if st.button("💾 Salvează Plan Prânz", use_container_width=True):
            if sel_f1 and sel_f2_1 and sel_f2_2 and sel_acc:
                id_uri = [sel_f1['id'], sel_f2_1['id'], sel_f2_2['id'], sel_acc['id']]
                db.salveaza_planificare(data_plan, id_uri, tip_plan="pranz")
                st.success("Planificat: Prânz ✅")
                st.rerun()
            else:
                st.error("Selectează toate componentele prânzului!")

    # A.2. Sub-Modul: Plan Cină
    with st.expander("🌙 PLANIFICĂ CINĂ"):
        # 1. Pregătim listele filtrate special pentru cină
        # Primul picker: doar felul 2
        f2_options_cina = [None] + [p for p in toate if p['categorie'] == 'felul_2']
        # Al doilea picker: doar salate
        salate_options_cina = [None] + [p for p in toate if p['categorie'] == 'salate']
        
        def format_p(x): return x['nume'] if x else "-- Alege --"

        c1, c2 = st.columns(2)
        with c1: 
            sel_f2_c = st.selectbox("🍖 Felul Principal (Cină):", f2_options_cina, format_func=format_p, key="plan_f2_c_only")
        with c2: 
            sel_sal_c = st.selectbox("🥗 Salată (Cină):", salate_options_cina, format_func=format_p, key="plan_sal_c_only")
        
        if st.button("💾 Salvează Plan Cină", use_container_width=True):
            # Validăm să fie ambele selectate
            if sel_f2_c and sel_sal_c:
                # Salvăm ID-urile în baza de date cu tip_plan="cina"
                db.salveaza_planificare(data_plan, [sel_f2_c['id'], sel_sal_c['id']], tip_plan="cina")
                st.success(f"Cina pentru {nume_zi_ro} a fost salvată!")
                st.toast(f"Cina pentru {nume_zi_ro} a fost salvată!", icon="✅")
                st.rerun()
            else:
                st.error("⚠️ Te rugăm să alegi atât felul principal, cât și salata pentru cină!")

    # A.3. Sub-Modul: Plan Sandwich-uri (Programarea celor de 12 lei)
    with st.expander("🥪 PLANIFICĂ SANDWICH-URILE ZILEI"):
        sw_opts = [p for p in toate if p['categorie'] == 'sandwich']
        sel_sw_zi = st.multiselect("Ce sandwich-uri avem azi?", sw_opts, format_func=lambda x: x['nume'], key="plan_sw")
        
        if st.button("💾 Salvează Plan Sandwich", use_container_width=True):
            if sel_sw_zi:
                db.salveaza_planificare(data_plan, [s['id'] for s in sel_sw_zi], tip_plan="sandwich")
                st.success("Planificat: Sandwich-uri ✅")
                st.rerun()

    st.divider()
    st.header("📋 Planificare Săptămânală (Privire de Ansamblu)")

    zile_sapt = utils.get_zile_saptamana(data_plan)
    
    # 1. PRELUARE DATE (O singură dată pentru toată săptămâna)
    plan_saptamanal = db.get_meniu_planificat(zile_sapt[0], zile_sapt[-1])

    # 2. GENERARE ANTET (Header)
    header_html = "".join([
        f"<th style='border: 1px solid #444; padding: 12px; background-color: #262730; color: #FAFAFA; min-width: 150px;'>"
        f"<div style='color: #FF4B4B; font-size: 1.1em;'>{utils.format_nume_zi(z)}</div>"
        f"<div style='font-size: 0.9em; font-weight: normal; opacity: 0.7;'>{z.strftime('%d.%m')}</div></th>" 
        for z in zile_sapt
    ])

    # 3. GENERARE RÂNDURI (Rows)
    rows_html = ""
    tipuri_masa = [
        ("pranz", "🥣 PRÂNZ"),
        ("cina", "🌙 CINĂ"),
        ("sandwich", "🥪 SANDWICH")
    ]

    for cod_tip, nume_afisat in tipuri_masa:
        # Începem rândul cu eticheta mesei (Prânz, Cină etc.)
        row_content = f"""<tr>
            <td style='border: 1px solid #444; padding: 15px; font-weight: bold; background-color: #262730; color: #FAFAFA; text-align: left; border-right: 3px solid #FF4B4B;'>
                {nume_afisat}
            </td>"""
        
        for zi in zile_sapt:
            # Căutăm în dicționarul rapid în loc de db.get_meniu_planificat
            m = plan_saptamanal.get((str(zi), cod_tip.lower()), [])
            
            if m:
                p_items = []
                for p in m:
                    p_label = p['nume']
                    # Verificăm dacă avem preț și îl formatăm
                    if p.get('pret_standard') and p['pret_standard'] > 0:
                        p_label += f" <span style='color: #888; font-size: 0.85em;'>({int(p['pret_standard'])} lei)</span>"
                    p_items.append(f"<div style='margin-bottom: 5px;'>• {p_label}</div>")
                
                celula_text = "".join(p_items)
                row_content += f"<td style='border: 1px solid #444; padding: 12px; vertical-align: top; color: #FAFAFA; font-size: 0.95em;'>{celula_text}</td>"
            else:
                row_content += "<td style='border: 1px solid #444; padding: 12px; color: #555; font-style: italic; text-align: center; vertical-align: middle;'>---</td>"
        
        row_content += "</tr>"
        rows_html += row_content

    # 4. CONSTRUCȚIE TABEL FINAL
    tabel_html = f"""
    <div style="overflow-x: auto; border-radius: 8px; border: 1px solid #444; margin: 20px 0;">
        <table style="width: 100%; border-collapse: collapse; font-family: sans-serif; background-color: #1e1e1e;">
            <thead>
                <tr>
                    <th style="border: 1px solid #444; padding: 12px; background-color: #262730; color: #888; width: 150px;">FLUX</th>
                    {header_html}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    </div>"""

    # 5. AFIȘARE
    st.markdown(tabel_html, unsafe_allow_html=True)
# --- SECȚIUNE EXPORT EXCEL (Fără Sandwich) ---
# --- SECȚIUNE EXPORT EXCEL (FORMAT CONFORM IMAGINE) ---
# --- SECȚIUNE EXPORT EXCEL (CU PREȚURI ȘI FORMAT CORECT) ---
# --- SECȚIUNE EXPORT LANDSCAPE ---
# --- SECȚIUNE EXPORT VERTICAL (CANTINA LOTUS) ---
# --- GENERARE EXPORT LANDSCAPE (RĂSTURNAT) ---
    try:
        rows_landscape = []
        
        for zi in zile_sapt:
            # Eticheta zilei
            data_label = f"{utils.format_nume_zi(zi)}\n{zi.strftime('%d.%m')}"
            
            # Formatare preparate Prânz
            m_pranz = plan_saptamanal.get((str(zi), "pranz"), [])
            txt_pranz = "\n".join([
                f"• {p['nume']} ({int(p['pret_standard'])} lei)" if p.get('pret_standard') and p['pret_standard'] > 0 else f"• {p['nume']}" 
                for p in m_pranz
            ])
            
            # Formatare preparate Cină
            m_cina = plan_saptamanal.get((str(zi), "cina"), [])
            txt_cina = "\n".join([
                f"• {p['nume']} ({int(p['pret_standard'])} lei)" if p.get('pret_standard') and p['pret_standard'] > 0 else f"• {p['nume']}" 
                for p in m_cina
            ])
            
            rows_landscape.append({
                "DATA / ZIUA": data_label,
                "🥣 MENIU PRÂNZ": txt_pranz if txt_pranz else "---",
                "🌙 MENIU CINĂ": txt_cina if txt_cina else "---"
            })

        df_final = pd.DataFrame(rows_landscape)
        # ATENȚIE: Apelăm funcția de landscape (v2)
        excel_file = utils.export_to_excel_landscape_v2(df_final)

        st.download_button(
            label="🖨️ Descarcă Meniu Landscape Răsturnat (Cantina LOTUS)",
            data=excel_file,
            file_name=f"Meniu_Lotus_Landscape_{zile_sapt[0].strftime('%d_%m')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    except Exception as e:
        st.error(f"Eroare la generare: {e}")