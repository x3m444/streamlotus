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

    total_incasat = sum(c.get('total_plata', 0) for c in comenzi)
    st.metric("Total CASH de încasat", f"{total_incasat} lei")

    livratori = db.get_lista_livratori()

    for l in livratori:
        comenzi_sofer = [c for c in comenzi if c['sofer'] == l]

        if comenzi_sofer:
            suma_l = sum(s.get('total_plata', 0) for s in comenzi_sofer)
            with st.expander(f"🚚 {l.upper()} — Total Cash: {suma_l} lei"):
                h1, h2, h3, h4, h5 = st.columns([0.8, 3, 4, 1.2, 0.8])
                h1.write("**Ora**")
                h2.write("**Client & Adresă**")
                h3.write("**Produse (Listă)**")
                h4.write("**Suma Cash**")
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
                        st.subheader(f"{cz['total_plata']} lei")
                        st.caption(f"Metoda: {cz['metoda_plata']}")

                    with c5:
                        if st.button("🗑️", key=f"del_{cz['id']}", help="Șterge comanda"):
                            if db.delete_comanda(cz['id']):
                                st.rerun()

                    st.divider()
