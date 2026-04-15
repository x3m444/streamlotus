import streamlit as st
import pandas as pd
from datetime import date
import database as db

def show(db, utils, toate):
    st.subheader("⚙️ Gestiune Produse")
        
    # 1. Formular Adăugare (cu placeholdere text și fără 0.00 la preț)
    with st.expander("➕ Adaugă Produs Nou", expanded=False):
        with st.form("add_produs", clear_on_submit=True):
            col_nume, col_cat, col_pret = st.columns([2, 1, 1])
            with col_nume: 
                nume_n = st.text_input("Denumire Produs", placeholder="ex: Ciorbă de văduvă...")
            with col_cat: 
                cat_n = st.selectbox("Categorie", 
                                    options=[None, "felul_1", "felul_2", "salate", "special", "desert"],
                                    format_func=lambda x: "--- Alege ---" if x is None else x)
            with col_pret: 
                # Folosim value=None pentru a avea placeholder text curat
                pret_n = st.number_input("Preț (RON)", min_value=0.0, step=0.5, value=None, placeholder="Introduceți prețul...")
            
            submit_add = st.form_submit_button("Salvează în Nomenclator", use_container_width=True)

        if submit_add:
            if nume_n and cat_n and pret_n is not None:
                db.add_produs(nume_n, cat_n, pret_n)
                st.success(f"✅ Adăugat cu succes: {nume_n}")
                st.rerun()
            else:
                st.error("⚠️ Te rugăm să completezi toate câmpurile!")

    st.divider()

    # 2. Tabel Editabil și Ștergere
    st.subheader("📋 Gestiune Tabelară")
    st.info("💡 Poți edita direct în tabel sau poți bifa 'Șterge' pentru a elimina înregistrări.")
    
    toate_produsele = db.get_toate_produsele()
    
    if toate_produsele:
        df_nom = pd.DataFrame(toate_produsele)
        
        # Adăugăm o coloană temporară pentru ștergere (nu există în DB, e doar pentru UI)
        df_nom["șterge"] = False
        
        # Reordonăm coloanele să fie ID, Nume, Categorie, Preț, Șterge
        df_nom = df_nom[["id", "nume", "categorie", "pret_standard", "șterge"]]

        # Configurăm st.data_editor
        edited_data = st.data_editor(
            df_nom,
            column_config={
                "id": st.column_config.NumberColumn("ID", disabled=True),
                "nume": st.column_config.TextColumn("Denumire Produs", required=True),
                "categorie": st.column_config.SelectboxColumn(
                    "Categorie", 
                    options=["felul_1", "felul_2", "salate", "special", "desert"],
                    required=True
                ),
                "pret_standard": st.column_config.NumberColumn("Preț (RON)", min_value=0, format="%.2f"),
                "șterge": st.column_config.CheckboxColumn("Elimină?", help="Bifează pentru a șterge produsul")
            },
            hide_index=True,
            use_container_width=True,
            key="nomenclator_editor"
        )

        # Buton pentru salvarea tuturor modificărilor (Update + Delete)
        if st.button("💾 Salvează Modificările (Editări și Ștergeri)", use_container_width=True, type="primary"):
            # 1. Identificăm rândurile de șters
            ids_de_sters = edited_data[edited_data["șterge"] == True]["id"].tolist()
            
            # 2. Identificăm rândurile modificate (cele care nu sunt de șters)
            for index, row in edited_data.iterrows():
                if row['id'] in ids_de_sters:
                    db.delete_produs(row['id'])
                else:
                    # Verificăm dacă s-a schimbat ceva față de original
                    original_row = df_nom.iloc[index]
                    if not row.equals(original_row):
                        db.update_produs(row['id'], row['nume'], row['categorie'], row['pret_standard'])
            
            st.success("✅ Baza de date a fost actualizată!")
            st.rerun()

        # 3. Export (folosim datele din tabelul afișat)
        st.write("")
        df_export = edited_data[edited_data["șterge"] == False][["nume", "categorie", "pret_standard"]]
        excel_data = utils.export_to_excel(df_export, sheet_name="Nomenclator")
        st.download_button(
            label="📥 Exportă Nomenclatorul (fără cele marcate de șters)",
            data=excel_data,
            file_name=f"Nomenclator_{date.today().strftime('%d_%m_%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
    else:
        st.info("Nomenclatorul este gol.")