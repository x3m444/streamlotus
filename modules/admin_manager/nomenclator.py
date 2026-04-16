"""
admin_manager/nomenclator.py
-----------------------------
Sectiunea "Gestiune Nomenclator" din pagina Admin.
Permite:
  - Adaugarea de produse noi
  - Editarea si stergerea produselor existente direct din tabel
  - Export Excel al nomenclatorului

Nu depinde de data selectata — gestioneaza date statice de configurare.
"""

import streamlit as st
import pandas as pd
import database as db
import utils
from datetime import date


def show():
    """Randeaza sectiunea de gestiune a nomenclatorului de produse."""
    st.subheader("⚙️ Gestiune Produse")

    # -------------------------------------------------------
    # ADAUGARE PRODUS NOU
    # -------------------------------------------------------
    with st.expander("➕ Adaugă Produs Nou", expanded=False):
        with st.form("add_produs", clear_on_submit=True):
            col_nume, col_cat, col_pret = st.columns([2, 1, 1])
            with col_nume:
                nume_n = st.text_input("Denumire Produs", placeholder="ex: Ciorbă de văduvă...")
            with col_cat:
                cat_n = st.selectbox(
                    "Categorie",
                    options=[None, "felul_1", "felul_2", "salate", "sandwich", "special", "desert"],
                    format_func=lambda x: "--- Alege ---" if x is None else x
                )
            with col_pret:
                pret_n = st.number_input(
                    "Preț (RON)", min_value=0.0, step=0.5,
                    value=None, placeholder="Introduceți prețul..."
                )

            submit_add = st.form_submit_button("Salvează în Nomenclator", use_container_width=True)

        if submit_add:
            if nume_n and cat_n and pret_n is not None:
                db.add_produs(nume_n, cat_n, pret_n)
                st.success(f"✅ Adăugat: {nume_n}")
                st.rerun()
            else:
                st.error("⚠️ Completează toate câmpurile!")

    st.divider()

    # -------------------------------------------------------
    # TABEL EDITABIL (edit + stergere)
    # -------------------------------------------------------
    st.subheader("📋 Gestiune Tabelară")
    st.info("💡 Poți edita direct în tabel sau bifa 'Elimină?' pentru a șterge înregistrări.")

    toate_produsele = db.get_toate_produsele()

    if not toate_produsele:
        st.info("Nomenclatorul este gol. Adaugă primul produs mai sus.")
        return

    df_nom = pd.DataFrame(toate_produsele)
    df_nom["șterge"] = False
    df_nom = df_nom[["id", "nume", "categorie", "pret_standard", "șterge"]]

    edited_data = st.data_editor(
        df_nom,
        column_config={
            "id":           st.column_config.NumberColumn("ID", disabled=True),
            "nume":         st.column_config.TextColumn("Denumire Produs", required=True),
            "categorie":    st.column_config.SelectboxColumn(
                                "Categorie",
                                options=["felul_1", "felul_2", "salate", "sandwich", "special", "desert"],
                                required=True
                            ),
            "pret_standard": st.column_config.NumberColumn("Preț (RON)", min_value=0, format="%.2f"),
            "șterge":       st.column_config.CheckboxColumn("Elimină?", help="Bifează pentru ștergere"),
        },
        hide_index=True,
        use_container_width=True,
        key="nomenclator_editor"
    )

    if st.button("💾 Salvează Modificările", use_container_width=True, type="primary"):
        ids_de_sters = edited_data[edited_data["șterge"] == True]["id"].tolist()

        for index, row in edited_data.iterrows():
            if row['id'] in ids_de_sters:
                db.delete_produs(row['id'])
            else:
                # Salvam doar daca s-a modificat ceva fata de original
                original = df_nom.iloc[index]
                if not row.equals(original):
                    db.update_produs(row['id'], row['nume'], row['categorie'], row['pret_standard'])

        st.success("✅ Baza de date actualizată!")
        st.rerun()

    # -------------------------------------------------------
    # EXPORT EXCEL
    # -------------------------------------------------------
    st.write("")
    df_export = edited_data[edited_data["șterge"] == False][["nume", "categorie", "pret_standard"]]
    excel_data = utils.export_to_excel(df_export, sheet_name="Nomenclator")

    st.download_button(
        label="📥 Exportă Nomenclatorul",
        data=excel_data,
        file_name=f"Nomenclator_{date.today().strftime('%d_%m_%Y')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True
    )
