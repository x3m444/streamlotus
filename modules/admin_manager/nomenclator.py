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
import io


@st.fragment
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

            submit_add = st.form_submit_button("Salvează în Nomenclator", width="stretch")

        if submit_add:
            if nume_n and cat_n and pret_n is not None:
                db.add_produs(nume_n, cat_n, pret_n)
                st.success(f"✅ Adăugat: {nume_n}")
                st.rerun()
            else:
                st.error("⚠️ Completează toate câmpurile!")

    # -------------------------------------------------------
    # IMPORT EXCEL
    # -------------------------------------------------------
    CATEGORII_VALIDE = ["felul_1", "felul_2", "salate", "sandwich", "special", "desert"]

    with st.expander("📂 Import din Excel", expanded=False):
        st.markdown("**Format obligatoriu al fișierului Excel:**")
        col_spec1, col_spec2, col_spec3 = st.columns(3)
        col_spec1.info("**Coloana A: `Denumire`**\nText, obligatoriu\nex: Ciorbă de burtă")
        col_spec2.info("**Coloana B: `Categorie`**\nUnul din:\n`felul_1` `felul_2` `salate`\n`sandwich` `special` `desert`")
        col_spec3.info("**Coloana C: `Pret`**\nNumăr pozitiv (RON)\nex: 15.50")

        # Template descarcabil
        df_template = pd.DataFrame({
            "Denumire":  ["Ciorbă de burtă", "Mușchi de porc", "Salată de varză"],
            "Categorie": ["felul_1",          "felul_2",         "salate"],
            "Pret":      [12.0,               18.0,              5.0],
        })
        buf_tmpl = io.BytesIO()
        with pd.ExcelWriter(buf_tmpl, engine="xlsxwriter") as wr:
            df_template.to_excel(wr, index=False, sheet_name="Nomenclator")
            ws = wr.sheets["Nomenclator"]
            hfmt = wr.book.add_format({"bold": True, "bg_color": "#D7E4BC", "border": 1})
            for i, col in enumerate(df_template.columns):
                ws.write(0, i, col, hfmt)
                ws.set_column(i, i, 25)
        st.download_button(
            "⬇️ Descarcă template Excel",
            data=buf_tmpl.getvalue(),
            file_name="template_nomenclator.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

        st.divider()
        fisier = st.file_uploader("Încarcă fișierul Excel completat:", type=["xlsx", "xls"])

        if fisier:
            try:
                df_import = pd.read_excel(fisier)
            except Exception as e:
                st.error(f"❌ Fișierul nu poate fi citit: {e}")
                df_import = None

            if df_import is not None:
                # Normalizare coloane (trim + lowercase)
                df_import.columns = [str(c).strip() for c in df_import.columns]
                coloane_necesare = {"Denumire", "Categorie", "Pret"}
                coloane_lipsa = coloane_necesare - set(df_import.columns)

                if coloane_lipsa:
                    st.error(f"❌ Lipsesc coloanele: **{', '.join(coloane_lipsa)}**. Folosește template-ul de mai sus.")
                else:
                    # Validare rând cu rând
                    erori = []
                    randuri_ok = []

                    for idx, row in df_import.iterrows():
                        nr = idx + 2  # nr rând Excel (header = 1)
                        den = str(row["Denumire"]).strip() if pd.notna(row["Denumire"]) else ""
                        cat = str(row["Categorie"]).strip() if pd.notna(row["Categorie"]) else ""
                        pret_raw = row["Pret"]

                        erori_rand = []
                        if not den:
                            erori_rand.append("Denumire lipsă")
                        if cat not in CATEGORII_VALIDE:
                            erori_rand.append(f"Categorie invalidă: `{cat}` (valide: {', '.join(CATEGORII_VALIDE)})")
                        try:
                            pret = float(pret_raw)
                            if pret < 0:
                                erori_rand.append("Prețul nu poate fi negativ")
                        except (ValueError, TypeError):
                            pret = None
                            erori_rand.append(f"Preț invalid: `{pret_raw}`")

                        if erori_rand:
                            erori.append((nr, den or "—", erori_rand))
                        else:
                            randuri_ok.append({"Denumire": den, "Categorie": cat, "Pret": pret})

                    # Raport validare
                    c_ok, c_err = st.columns(2)
                    c_ok.metric("✅ Rânduri valide", len(randuri_ok))
                    c_err.metric("❌ Rânduri cu erori", len(erori))

                    if erori:
                        st.error("**Erori găsite — rândurile de mai jos nu vor fi importate:**")
                        for nr_rand, den_rand, msgs in erori:
                            st.markdown(f"- Rând **{nr_rand}** (`{den_rand}`): " + "; ".join(msgs))

                    if randuri_ok:
                        st.markdown("**Preview produse valide:**")
                        st.dataframe(pd.DataFrame(randuri_ok), use_container_width=True, hide_index=True)

                        # Verifica duplicate fata de nomenclatorul existent
                        existente = {p["nume"].lower() for p in db.get_toate_produsele()}
                        duplicate = [r for r in randuri_ok if r["Denumire"].lower() in existente]
                        noi = [r for r in randuri_ok if r["Denumire"].lower() not in existente]

                        if duplicate:
                            st.warning(f"⚠️ {len(duplicate)} produs(e) există deja în nomenclator și vor fi **ignorate**: " +
                                       ", ".join(r["Denumire"] for r in duplicate))

                        if noi:
                            if st.button(f"✅ Importă {len(noi)} produs(e) noi", type="primary", width="stretch"):
                                for r in noi:
                                    db.add_produs(r["Denumire"], r["Categorie"], r["Pret"])
                                st.success(f"✅ {len(noi)} produse importate cu succes!")
                                st.rerun()
                        else:
                            st.info("Toate produsele valide există deja în nomenclator.")

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
        width="stretch",
        key="nomenclator_editor"
    )

    if st.button("💾 Salvează Modificările", width="stretch", type="primary"):
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
        width="stretch"
    )
