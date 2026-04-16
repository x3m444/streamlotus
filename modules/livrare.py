"""
modules/livrare.py
-------------------
Ecranul livratorului.

Flow:
  Bucataria marcheaza comanda 'pregatit'
      ↓
  Livratorul vede comanda in lista lui
      ↓
  "Am preluat" → status = 'pedrum'
      ↓
  "Livrat" → status = 'livrat' → dispare din lista

Livratorul este identificat prin selectbox (pana la implementarea loginului real).
Vede DOAR comenzile asignate lui, cu status 'pregatit' sau 'pedrum'.
"""

import streamlit as st
import database as db
import utils


engine = db.get_engine()


def show_livrare(sofer):
    """
    Randeaza ecranul livratorului pentru soferul dat.
    sofer: numele soferului selectat din sidebar
    """
    data_azi = utils.get_ro_time().date()

    st.title(f"🚚 Ruta mea — {sofer}")
    st.caption(f"Data: {data_azi.strftime('%d.%m.%Y')}")

    # Comenzile active ale soferului: 'pregatit' + 'pedrum'
    comenzi_pregatite = db.get_comenzi_receptie(data_azi, status_filtru='pregatit', sofer_filtru=sofer)
    comenzi_pe_drum   = db.get_comenzi_receptie(data_azi, status_filtru='pedrum',   sofer_filtru=sofer)

    total_comenzi = len(comenzi_pregatite) + len(comenzi_pe_drum)

    if total_comenzi == 0:
        st.success("✅ Nu ai comenzi active pentru astăzi. Tura încheiată!")
        return

    # Sumar rapid in capul paginii
    cash_total = sum(
        c.get('total_plata', 0)
        for c in comenzi_pregatite + comenzi_pe_drum
        if c.get('metoda_plata') == 'cash'
    )

    col1, col2, col3 = st.columns(3)
    col1.metric("De preluat", len(comenzi_pregatite))
    col2.metric("Pe drum", len(comenzi_pe_drum))
    col3.metric("Cash de incasat", f"{cash_total:.0f} lei")

    # -------------------------------------------------------
    # SECTIUNEA 1: DE PRELUAT (status = 'pregatit')
    # -------------------------------------------------------
    if comenzi_pregatite:
        st.divider()
        st.subheader(f"📦 De preluat ({len(comenzi_pregatite)})")

        for cmd in comenzi_pregatite:
            _render_card_livrare(cmd, actiune="preluat")

    # -------------------------------------------------------
    # SECTIUNEA 2: PE DRUM (status = 'pedrum')
    # -------------------------------------------------------
    if comenzi_pe_drum:
        st.divider()
        st.subheader(f"🛣️ Pe drum ({len(comenzi_pe_drum)})")

        for cmd in comenzi_pe_drum:
            _render_card_livrare(cmd, actiune="livrat")


def _render_card_livrare(cmd, actiune):
    """
    Randeaza cardul unei comenzi pentru livrator.
    actiune: 'preluat' | 'livrat'
    """
    ora = str(cmd.get('ora_livrare_estimata', ''))[:5]
    suma = cmd.get('total_plata', 0)
    metoda = cmd.get('metoda_plata', '').upper()
    este_cash = cmd.get('metoda_plata') == 'cash'

    with st.container(border=True):
        # Header card: ora + client + suma
        col_ora, col_client, col_suma = st.columns([1, 3, 1.5])
        col_ora.metric("Ora", ora)
        col_client.markdown(f"**{cmd['client']}**  \n📞 {cmd.get('telefon', 'N/A')}")
        if este_cash:
            col_suma.metric("Cash", f"{suma:.0f} lei")
        else:
            col_suma.metric(metoda, f"{suma:.0f} lei")

        # Adresa
        adresa = cmd.get('adresa_principala', 'N/A')
        st.info(f"📍 {adresa}")

        # Produse
        detalii = cmd.get('detalii') or ""
        if detalii:
            produse_txt = "  \n".join([
                f"• {parte.split('|')[0].strip()}"
                for parte in detalii.split(', ')
                if parte
            ])
            st.caption(produse_txt)

        # Buton actiune
        if actiune == "preluat":
            if st.button(
                "🚚 Am preluat comanda",
                key=f"preluat_{cmd['id']}",
                use_container_width=True
            ):
                db.update_status_comanda(engine, cmd['id'], 'pedrum')
                st.rerun()

        elif actiune == "livrat":
            if st.button(
                "✅ Livrat!",
                key=f"livrat_{cmd['id']}",
                use_container_width=True
            ):
                db.update_status_comanda(engine, cmd['id'], 'livrat')
                st.rerun()
