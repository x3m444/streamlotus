"""
bucatarie/impachetare.py
-------------------------
TAB Împachetare — comenzile reale ale clientilor (de la receptie).
O comanda poate fi ambalata DOAR cand:
  1. Toate produsele sunt 'gatit'
  2. Stocul lansat de admin acopera cantitatea ceruta
Dupa ambalare → status = 'pregatit' → dispare din flux.
Include si pachetele firmelor (angajati care ridica de la ghiseu).
"""

import streamlit as st
import database as db


@st.fragment
def show(data_selectata, engine):
    st.subheader("📦 Comenzi de Ambalat")

    # -------------------------------------------------------
    # PACHETE FIRME (angajati care ridica de la ghiseu)
    # -------------------------------------------------------
    pachete = db.get_pachete_firma_azi(data_selectata)
    if pachete:
        st.markdown("#### 🏢 Pachete Firme de Ambalat")
        firma_curenta = None
        for pct in pachete:
            if pct['nume_firma'] != firma_curenta:
                firma_curenta = pct['nume_firma']
                st.markdown(f"**{firma_curenta}**")
            col_ang, col_prod, col_btn = st.columns([2, 4, 1.5])
            col_ang.write(pct['nume_angajat'] or '—')
            col_prod.caption(pct['produse'])
            if pct['status_pachet'] == 'astept':
                if col_btn.button("📦 Ambalat", key=f"amb_{pct['servire_id']}",
                                  use_container_width=True, type="primary"):
                    db.update_status_pachet(pct['servire_id'], 'ambalat')
                    st.rerun()
            else:
                col_btn.success("✅ Ambalat")
        st.divider()

    comenzi = db.get_comenzi_receptie(data_selectata, status_filtru='nou')
    stoc = db.get_stoc_zi(data_selectata)

    if not comenzi:
        st.success("✅ Nicio comandă în așteptare. Toate au fost ambalate!")
        return

    gata_count = sum(
        1 for c in comenzi
        if c.get('detalii') and all('|gatit' in l for l in c['detalii'].split(', '))
    )
    st.caption(f"Total comenzi: {len(comenzi)} | Gata de ambalat: {gata_count} | În așteptare: {len(comenzi) - gata_count}")

    for cmd in comenzi:
        detalii_str = cmd.get('detalii') or ""
        linii = detalii_str.split(', ') if detalii_str else []

        nr_total = len(linii)
        nr_gatite = sum(1 for l in linii if '|gatit' in l)
        toate_gata = (nr_total > 0 and nr_total == nr_gatite)

        # Verificare stoc
        lipsa_stoc = []
        for linie in linii:
            try:
                produs_txt, _ = linie.split('|')
                qty_str, nume = produs_txt.split('x ', 1)
                nume = nume.strip()
                qty = int(qty_str.strip())
                if nume in stoc and stoc[nume]['ramas'] < qty:
                    lipsa_stoc.append(
                        f"{nume}: necesar {qty}, disponibil {max(stoc[nume]['ramas'], 0)}"
                    )
            except Exception:
                continue

        stoc_ok = len(lipsa_stoc) == 0

        icon = "🟢" if (toate_gata and stoc_ok) else ("🔴" if lipsa_stoc else "🟡")
        if not stoc_ok:
            status_txt = "STOC INSUFICIENT"
        elif toate_gata:
            status_txt = "GATA DE AMBALAT"
        else:
            status_txt = f"ASTEAPTA ({nr_gatite}/{nr_total} gatite)"

        ora = str(cmd.get('ora_livrare_estimata', ''))[:5]
        sofer_txt = f" | 🚗 {cmd['sofer']}" if cmd.get('sofer') else ""
        titlu = f"{icon} {status_txt} | #{cmd['id']} — {cmd['client']} | ora {ora}{sofer_txt}"

        with st.expander(titlu, expanded=(toate_gata or bool(lipsa_stoc))):
            col_produse, col_actiuni = st.columns([3, 1])

            with col_produse:
                st.write("**Produse:**")
                for linie in linii:
                    try:
                        produs_txt, stare = linie.split('|')
                        if stare == 'gatit':
                            st.markdown(f"✅ {produs_txt}")
                        else:
                            st.markdown(f"⏳ :red[{produs_txt}] — în bucătărie")
                    except Exception:
                        st.write(f"• {linie}")

                sofer_cap = f" | 🚗 {cmd['sofer']}" if cmd.get('sofer') else ""
                st.caption(
                    f"📞 {cmd.get('telefon', 'N/A')} | "
                    f"📍 {cmd.get('adresa_principala', 'N/A')} | "
                    f"💳 {cmd.get('metoda_plata', '').upper()}{sofer_cap}"
                )

                if lipsa_stoc:
                    st.error("⚠️ Stoc insuficient:\n" + "\n".join(f"• {l}" for l in lipsa_stoc))

            with col_actiuni:
                st.write("")
                if toate_gata and stoc_ok:
                    if st.button(
                        "📦 Ambalat!",
                        key=f"pack_{cmd['id']}",
                        use_container_width=True,
                    ):
                        db.update_status_comanda(engine, cmd['id'], 'pregatit')
                        st.success(f"Comanda #{cmd['id']} marcată ca PREGĂTITĂ!")
                        st.rerun()
                elif lipsa_stoc:
                    if st.button(
                        "❌ Anulează",
                        key=f"cancel_{cmd['id']}",
                        use_container_width=True,
                        type="primary",
                        help="Stoc insuficient — anulează comanda"
                    ):
                        db.delete_comanda(cmd['id'])
                        st.warning(f"Comanda #{cmd['id']} anulată.")
                        st.rerun()
                else:
                    st.button(
                        "⏳ Așteaptă",
                        key=f"wait_{cmd['id']}",
                        disabled=True,
                        use_container_width=True,
                        help="Asteapta ca bucatarul sa marcheze toate produsele ca gatite"
                    )
