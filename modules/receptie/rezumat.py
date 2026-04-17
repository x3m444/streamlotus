"""
receptie/rezumat.py
--------------------
TAB Rezumat Livrări — situatia comenzilor pe zi, grupate pe livrator.
Afiseaza totalul de incasat si permite stergerea comenzilor.
"""

import streamlit as st
import database as db
import utils


def show():
    data_azi_ro = utils.get_ro_time().date()
    st.header(f"📋 Situație Livrări - {data_azi_ro.strftime('%d-%m-%Y')}")

    data_pt_rezumat = st.date_input("Selectează data pentru rezumat:", data_azi_ro)

    comenzi = db.get_comenzi_receptie(data_pt_rezumat)

    if not comenzi:
        st.info(f"Fără comenzi în data de {data_pt_rezumat.strftime('%d-%m-%Y')}.")
        return

    def suma_metoda(lista, metoda):
        return sum(c.get('total_plata', 0) for c in lista if c.get('metoda_plata') == metoda)

    total_cash    = suma_metoda(comenzi, 'cash')
    total_card    = suma_metoda(comenzi, 'card')
    total_factura = suma_metoda(comenzi, 'factura')
    total_general = sum(c.get('total_plata', 0) for c in comenzi)

    mc, mcard, mfact, mtot = st.columns(4)
    mc.metric("💵 Cash de încasat", f"{total_cash} lei")
    mcard.metric("💳 Card (încasat)", f"{total_card} lei")
    mfact.metric("🧾 Factură", f"{total_factura} lei")
    mtot.metric("📊 Total general", f"{total_general} lei")

    st.divider()

    livratori = db.get_lista_livratori()

    for l in livratori:
        comenzi_sofer = [c for c in comenzi if c['sofer'] == l]

        if comenzi_sofer:
            cash_l    = suma_metoda(comenzi_sofer, 'cash')
            card_l    = suma_metoda(comenzi_sofer, 'card')
            factura_l = suma_metoda(comenzi_sofer, 'factura')
            parti = []
            if cash_l:    parti.append(f"💵 Cash: {cash_l} lei")
            if card_l:    parti.append(f"💳 Card: {card_l} lei")
            if factura_l: parti.append(f"🧾 Fact: {factura_l} lei")
            titlu_sofer = f"🚚 {l.upper()} — " + "  |  ".join(parti) if parti else f"🚚 {l.upper()}"

            with st.expander(titlu_sofer):
                h1, h2, h3, h4, h5 = st.columns([0.8, 3, 4, 1.2, 0.8])
                h1.write("**Ora**")
                h2.write("**Client & Adresă**")
                h3.write("**Produse (Listă)**")
                h4.write("**Sumă**")
                h5.write("**Șterge**")
                st.divider()

                for cz in comenzi_sofer:
                    c1, c2, c3, c4, c5 = st.columns([0.8, 3, 4, 1.2, 0.8])

                    c1.write(f"🕒 {str(cz['ora_livrare_estimata'])[:5]}")

                    with c2:
                        st.write(f"👤 **{cz['client']}**")
                        if cz.get('telefon'):
                            st.write(f"📞 **{cz['telefon']}**")
                        st.caption(f"📍 {cz['adresa_principala']}")

                    with c3:
                        for parte in (cz['detalii'] or '').split(', '):
                            try:
                                produs_txt, stare = parte.split('|')
                                if stare == 'gatit':
                                    st.markdown(f"✅ :green[{produs_txt.strip()}]")
                                else:
                                    st.markdown(f"⏳ :orange[{produs_txt.strip()}]")
                            except Exception:
                                st.write(f"• {parte}")

                    with c4:
                        metoda = cz.get('metoda_plata', '')
                        icon = '💵' if metoda == 'cash' else ('💳' if metoda == 'card' else '🧾')
                        st.subheader(f"{cz['total_plata']} lei")
                        st.caption(f"{icon} {metoda.upper()}")

                    with c5:
                        if st.button("🗑️", key=f"del_{cz['id']}", help="Șterge comanda"):
                            if db.delete_comanda(cz['id']):
                                st.rerun()

                    st.divider()
