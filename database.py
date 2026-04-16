"""
database.py
-----------
Toate operatiunile cu baza de date (Supabase / PostgreSQL).
Organizat pe sectiuni:
  - Conexiune
  - Produse & Planificare
  - Clienti & Livratori
  - Comenzi (scriere)
  - Comenzi (citire) — functii specializate pe rol
  - Update statusuri
  - Stergeri
"""

from sqlalchemy import create_engine, text
import streamlit as st
import utils


# =============================================================
# CONEXIUNE
# =============================================================

@st.cache_resource
def get_engine():
    conn_url = (
        f"postgresql://{st.secrets['DB_USER']}:{st.secrets['DB_PASS']}"
        f"@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
    )
    return create_engine(conn_url, pool_size=5, max_overflow=10)


# =============================================================
# PRODUSE & PLANIFICARE
# =============================================================

@st.cache_data(ttl=600)
def get_toate_produsele():
    """Toate produsele din nomenclator, ordonate dupa ID descrescator."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT * FROM produse ORDER BY id DESC"))
        return [dict(r._mapping) for r in result]


def get_meniu_planificat(data_start, data_end=None, tip_plan="pranz"):
    """
    Planificarea meniului pentru o zi sau un interval.

    - data_end=None  → returneaza lista de produse pentru ziua si tipul dat
    - data_end=data  → returneaza dict { (str(zi), tip_plan): [produse] } pentru saptamana
    """
    engine = get_engine()
    with engine.connect() as conn:
        if data_end is None:
            res = conn.execute(text("""
                SELECT p.*, prod.nume, prod.categorie, prod.pret_standard
                FROM planificare_meniu p
                JOIN produse prod ON p.produs_id = prod.id
                WHERE p.data_zi = :s AND LOWER(p.tip_plan) = LOWER(:t)
            """), {"s": str(data_start), "t": tip_plan})
            return [dict(r._mapping) for r in res]
        else:
            res = conn.execute(text("""
                SELECT p.data_zi, p.tip_plan, prod.nume, prod.pret_standard
                FROM planificare_meniu p
                JOIN produse prod ON p.produs_id = prod.id
                WHERE p.data_zi BETWEEN :s AND :e
            """), {"s": str(data_start), "e": str(data_end)})

            plan_dict = {}
            for r in res:
                row = dict(r._mapping)
                key = (str(row['data_zi']), row['tip_plan'].lower())
                plan_dict.setdefault(key, []).append(row)
            return plan_dict


def add_produs(nume, categorie, pret):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO produse (nume, categorie, pret_standard) VALUES (:n, :c, :p)"),
            {"n": nume, "c": categorie, "p": pret}
        )
    st.cache_data.clear()


def update_produs(id_produs, nume, categorie, pret):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE produse SET nume = :n, categorie = :c, pret_standard = :p WHERE id = :id
        """), {"n": nume, "c": categorie, "p": pret, "id": id_produs})
    st.cache_data.clear()


def delete_produs(id_produs):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM produse WHERE id = :id"), {"id": id_produs})
    st.cache_data.clear()


def salveaza_planificare(data_zi, produse_ids, tip_plan="pranz"):
    """Suprascrie planificarea pentru ziua si tipul dat (delete + insert)."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(
            text("DELETE FROM planificare_meniu WHERE data_zi = :d AND tip_plan = :t"),
            {"d": data_zi, "t": tip_plan}
        )
        for pid in produse_ids:
            conn.execute(
                text("INSERT INTO planificare_meniu (data_zi, produs_id, tip_plan) VALUES (:d, :p, :t)"),
                {"d": data_zi, "p": pid, "t": tip_plan}
            )


# =============================================================
# CLIENTI & LIVRATORI
# =============================================================

def get_all_clienti():
    """Toti clientii, ordonati alfabetic."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT id, nume_client, telefon, adresa_principala FROM clienti ORDER BY nume_client ASC"
        ))
        return [dict(r._mapping) for r in result]


def add_client(nume_client, telefon, adresa_principala, observatii_client=""):
    engine = get_engine()
    with engine.begin() as conn:
        result = conn.execute(text("""
            INSERT INTO clienti (nume_client, telefon, adresa_principala, observatii_client)
            VALUES (:n, :t, :a, :o)
            RETURNING id, nume_client, telefon, adresa_principala
        """), {"n": nume_client, "t": telefon, "a": adresa_principala, "o": observatii_client})
        st.cache_data.clear()
        return dict(result.fetchone()._mapping)


def update_client(id_client, nume, telefon, adresa):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE clienti SET nume_client = :n, telefon = :t, adresa_principala = :a WHERE id = :id
        """), {"n": nume, "t": telefon, "a": adresa, "id": id_client})
    st.cache_data.clear()


def delete_client(id_client):
    """Sterge client. Esueaza daca are comenzi active (FK constraint)."""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clienti WHERE id = :id"), {"id": id_client})
        st.cache_data.clear()
        return True
    except Exception:
        return False


def get_lista_livratori():
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("SELECT nume FROM livratori ORDER BY id ASC"))
        return [row[0] for row in result]


# =============================================================
# COMENZI — SCRIERE
# =============================================================

def save_comanda_finala(client_id, produse, total, sofer, ora, obs, plata, tip_comanda, data_comanda):
    """
    Salveaza o comanda noua cu liniile ei de produse.

    Fiecare produs din lista trebuie sa aiba:
      { 'nume', 'cantitate', 'pret', 'tip_linie' }
      tip_linie: 'standard' (din meniu zilei) | 'special' (merge direct la bucatarie)
    """
    engine = get_engine()
    with engine.begin() as conn:
        ora_sql = ora.split('-')[0].strip() if '-' in ora else ora[:5]

        res = conn.execute(text("""
            INSERT INTO comenzi (
                client_id, data_comanda, ora_livrare_estimata,
                status, metoda_plata, total_plata, sofer, observatii, tip_comanda
            )
            VALUES (:cid, :data_c, :ora, 'nou', :plata, :total, :sofer, :obs, :tip)
            RETURNING id
        """), {
            "cid": client_id, "data_c": data_comanda, "ora": ora_sql,
            "total": total, "sofer": sofer, "obs": obs,
            "plata": plata, "tip": tip_comanda
        })
        new_id = res.fetchone()[0]

        for p in produse:
            conn.execute(text("""
                INSERT INTO comenzi_linii (comanda_id, nume_produs, cantitate, pret_unitar, tip_linie)
                VALUES (:mid, :nume, :qty, :pret, :tip_linie)
            """), {
                "mid": new_id, "nume": p['nume'], "qty": p['cantitate'],
                "pret": p['pret'], "tip_linie": p.get('tip_linie', 'standard')
            })
    return True


# =============================================================
# COMENZI — CITIRE
# =============================================================

def get_rezumat_zi(data_filtrare=None, tip_comanda=None, status_filtru=None):
    """
    Toate comenzile pentru o zi (admin + clienti).
    Folosit de Admin → Monitorizare Comenzi.
    Filtre optionale: tip_comanda, status_filtru.
    """
    engine = get_engine()
    if data_filtrare is None:
        data_filtrare = utils.get_ro_time().date()

    with engine.connect() as conn:
        query = """
            SELECT
                c.id,
                c.status            AS status_comanda,
                c.sofer,
                cl.nume_client      AS client,
                cl.telefon,
                cl.adresa_principala,
                c.metoda_plata,
                c.tip_comanda,
                c.total_plata,
                c.ora_livrare_estimata,
                string_agg(l.cantitate || 'x ' || l.nume_produs || '|' || l.status, ', ') AS detalii
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            LEFT JOIN comenzi_linii l ON c.id = l.comanda_id
            WHERE c.data_comanda = :data
        """
        params = {"data": data_filtrare}

        if tip_comanda:
            query += " AND c.tip_comanda = :tip"
            params["tip"] = tip_comanda
        if status_filtru:
            query += " AND c.status = :stat"
            params["stat"] = status_filtru

        query += """
            GROUP BY
                c.id, c.status, c.sofer, cl.nume_client, cl.telefon,
                cl.adresa_principala, c.metoda_plata, c.tip_comanda,
                c.total_plata, c.ora_livrare_estimata
            ORDER BY c.ora_livrare_estimata
        """
        return [dict(r._mapping) for r in conn.execute(text(query), params)]


def get_loturi_productie(data):
    """
    Loturile lansate de admin (client_id=999) pentru o zi.
    Folosit de Bucatarie → Gatire (sectiunea loturi).
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                c.id,
                c.status            AS status_comanda,
                c.tip_comanda,
                c.ora_livrare_estimata,
                c.observatii        AS descriere,
                string_agg(
                    l.cantitate || 'x ' || l.nume_produs || '|' || l.status,
                    ', ' ORDER BY l.id
                ) AS detalii
            FROM comenzi c
            LEFT JOIN comenzi_linii l ON c.id = l.comanda_id
            WHERE c.data_comanda = :data
              AND c.client_id = 999
            GROUP BY c.id, c.status, c.tip_comanda, c.ora_livrare_estimata, c.observatii
            ORDER BY c.tip_comanda, c.ora_livrare_estimata
        """), {"data": data})
        return [dict(r._mapping) for r in result]


def get_produse_speciale_zi(data):
    """
    Produsele cu tip_linie='special' din comenzile clientilor, agregate pe produs.
    Folosit de Bucatarie → Gatire (sectiunea speciale).
    Returneaza: { nume_produs, nou, gatit, nr_comenzi }
    """
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                l.nume_produs,
                COALESCE(SUM(l.cantitate) FILTER (WHERE l.status = 'nou'),   0) AS nou,
                COALESCE(SUM(l.cantitate) FILTER (WHERE l.status = 'gatit'), 0) AS gatit,
                COUNT(DISTINCT l.comanda_id) AS nr_comenzi
            FROM comenzi_linii l
            JOIN comenzi c ON l.comanda_id = c.id
            WHERE c.data_comanda = :data
              AND c.client_id != 999
              AND l.tip_linie = 'special'
            GROUP BY l.nume_produs
            ORDER BY l.nume_produs
        """), {"data": data})
        return [dict(r._mapping) for r in result]


def get_comenzi_receptie(data, status_filtru=None, sofer_filtru=None):
    """
    Comenzile reale ale clientilor (client_id != 999).
    Folosit de: Bucatarie → Impachetare, Receptie → Rezumat, Livratori.
    status_filtru: 'nou' | 'pregatit' | 'pedrum' | 'livrat' | None (toate)
    sofer_filtru:  numele soferului | None (toti)
    """
    engine = get_engine()
    with engine.connect() as conn:
        query = """
            SELECT
                c.id,
                c.status            AS status_comanda,
                c.sofer,
                cl.nume_client      AS client,
                cl.telefon,
                cl.adresa_principala,
                c.metoda_plata,
                c.tip_comanda,
                c.total_plata,
                c.ora_livrare_estimata,
                string_agg(
                    l.cantitate || 'x ' || l.nume_produs || '|' || l.status,
                    ', ' ORDER BY l.id
                ) AS detalii
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            LEFT JOIN comenzi_linii l ON c.id = l.comanda_id
            WHERE c.data_comanda = :data
              AND c.client_id != 999
        """
        params = {"data": data}

        if status_filtru:
            query += " AND c.status = :stat"
            params["stat"] = status_filtru

        if sofer_filtru:
            query += " AND c.sofer = :sofer"
            params["sofer"] = sofer_filtru

        query += """
            GROUP BY
                c.id, c.status, c.sofer, cl.nume_client, cl.telefon,
                cl.adresa_principala, c.metoda_plata, c.tip_comanda,
                c.total_plata, c.ora_livrare_estimata
            ORDER BY c.ora_livrare_estimata
        """
        return [dict(r._mapping) for r in conn.execute(text(query), params)]


def get_raport_interval(data_start, data_end):
    """Totaluri pe tip_comanda pentru un interval de date. Folosit de Admin → Rapoarte."""
    engine = get_engine()
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT
                tip_comanda,
                SUM(total_plata) AS total_valoare,
                COUNT(id)        AS nr_comenzi
            FROM comenzi
            WHERE data_comanda BETWEEN :start AND :end
            GROUP BY tip_comanda
        """), {"start": data_start, "end": data_end})
        return [dict(r._mapping) for r in result]


# =============================================================
# UPDATE STATUSURI
# =============================================================

def update_status_comanda(engine, comanda_id, noul_status):
    """Schimba statusul unei comenzi intregi (nou → pregatit → livrat)."""
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE comenzi SET status = :status WHERE id = :id"),
            {"status": noul_status, "id": comanda_id}
        )


def update_status_batch(engine, data, nume_produs, noul_status):
    """
    Marcheaza toate liniile cu un anumit produs ca gatit/nou pentru o zi.
    Afecteaza atat loturile admin cat si comenzile clientilor — intentionat,
    pentru ca gatirea unui produs deblocheaza impachetarea tuturor comenzilor.
    """
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE comenzi_linii
            SET status = :noul_status
            WHERE nume_produs = :nume
              AND comanda_id IN (SELECT id FROM comenzi WHERE data_comanda = :data)
        """), {"noul_status": noul_status, "data": data, "nume": nume_produs})


# =============================================================
# STOC PRODUCTIE
# =============================================================

def get_stoc_zi(data):
    """
    Calculeaza stocul disponibil per produs pentru o zi.

    Returneaza dict: { nume_produs: { 'lansat': X, 'ambalat': Y, 'ramas': Z } }

    - lansat  = cantitatea totala din loturile admin (client_id=999)
    - ambalat = cantitatea din comenzile clientilor deja ambalate/livrate
                (status IN pregatit, pedrum, livrat) cu tip_linie='standard'
    - ramas   = lansat - ambalat  (poate fi negativ daca s-au primit prea multe comenzi)
    """
    engine = get_engine()
    with engine.connect() as conn:
        # Stocul lansat de admin
        r_lansat = conn.execute(text("""
            SELECT l.nume_produs, SUM(l.cantitate) AS total
            FROM comenzi_linii l
            JOIN comenzi c ON l.comanda_id = c.id
            WHERE c.data_comanda = :data
              AND c.client_id = 999
            GROUP BY l.nume_produs
        """), {"data": data})
        lansat = {row[0]: int(row[1]) for row in r_lansat}

        # Cantitatea deja angajata in comenzi ambalate/pe drum/livrate
        r_ambalat = conn.execute(text("""
            SELECT l.nume_produs, SUM(l.cantitate) AS total
            FROM comenzi_linii l
            JOIN comenzi c ON l.comanda_id = c.id
            WHERE c.data_comanda = :data
              AND c.client_id != 999
              AND c.status IN ('pregatit', 'pedrum', 'livrat')
              AND l.tip_linie = 'standard'
            GROUP BY l.nume_produs
        """), {"data": data})
        ambalat = {row[0]: int(row[1]) for row in r_ambalat}

    stoc = {}
    for nume, qty_lansat in lansat.items():
        qty_ambalat = ambalat.get(nume, 0)
        stoc[nume] = {
            "lansat":  qty_lansat,
            "ambalat": qty_ambalat,
            "ramas":   qty_lansat - qty_ambalat
        }
    return stoc


# =============================================================
# PRODUSE GATITE
# =============================================================

def get_produse_gatite_azi(data):
    """
    Returneaza set cu numele produselor marcate ca 'gatit' de bucatarie azi.
    Folosit de Ghiseu ca sa afiseze doar ce e gata de servit.
    """
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT DISTINCT l.nume_produs
            FROM comenzi_linii l
            JOIN comenzi c ON l.comanda_id = c.id
            WHERE c.data_comanda = :data
              AND c.client_id = 999
              AND l.status = 'gatit'
        """), {"data": data})
        return {row[0] for row in r}


# =============================================================
# FIRME & ANGAJATI
# =============================================================

def get_all_firme(doar_active=True):
    engine = get_engine()
    with engine.connect() as conn:
        query = "SELECT id, nume_firma, tip_contract, activ FROM firme"
        if doar_active:
            query += " WHERE activ = TRUE"
        query += " ORDER BY nume_firma"
        return [dict(r._mapping) for r in conn.execute(text(query))]


def add_firma(nume_firma, tip_contract='pranz_cina'):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO firme (nume_firma, tip_contract) VALUES (:n, :t)
        """), {"n": nume_firma, "t": tip_contract})


def update_firma(firma_id, nume_firma, tip_contract, activ):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE firme SET nume_firma=:n, tip_contract=:t, activ=:a WHERE id=:id
        """), {"n": nume_firma, "t": tip_contract, "a": activ, "id": firma_id})


def get_angajati_firma(firma_id, doar_activi=True):
    engine = get_engine()
    with engine.connect() as conn:
        query = "SELECT id, nume_angajat, activ FROM angajati_firme WHERE firma_id = :fid"
        if doar_activi:
            query += " AND activ = TRUE"
        query += " ORDER BY nume_angajat"
        return [dict(r._mapping) for r in conn.execute(text(query), {"fid": firma_id})]


def add_angajat(firma_id, nume_angajat):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO angajati_firme (firma_id, nume_angajat) VALUES (:fid, :n)
        """), {"fid": firma_id, "n": nume_angajat})


def toggle_angajat(angajat_id, activ):
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            UPDATE angajati_firme SET activ = :a WHERE id = :id
        """), {"a": activ, "id": angajat_id})


def get_angajati_serviti_azi(firma_id, data):
    """Returneaza set de angajat_id care au fost deja serviti azi."""
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT angajat_id FROM serviri_ghiseu
            WHERE firma_id = :fid AND data_servire = :data AND angajat_id IS NOT NULL
        """), {"fid": firma_id, "data": data})
        return {row[0] for row in r}


def save_servire(data, tip_servire, produse, firma_id=None, angajat_id=None, comanda_ref_id=None):
    """
    Salveaza o servire la ghiseu.
    produse: [{ 'nume_produs': str, 'cantitate': int, 'din_nevandut': bool }]
    """
    engine = get_engine()
    with engine.begin() as conn:
        r = conn.execute(text("""
            INSERT INTO serviri_ghiseu (data_servire, tip_servire, firma_id, angajat_id, comanda_ref_id)
            VALUES (:data, :tip, :fid, :aid, :cid)
            RETURNING id
        """), {"data": data, "tip": tip_servire, "fid": firma_id, "aid": angajat_id, "cid": comanda_ref_id})
        servire_id = r.fetchone()[0]

        for p in produse:
            conn.execute(text("""
                INSERT INTO serviri_ghiseu_linii (servire_id, nume_produs, cantitate, din_nevandut)
                VALUES (:sid, :n, :q, :nev)
            """), {"sid": servire_id, "n": p['nume_produs'], "q": p['cantitate'], "nev": p.get('din_nevandut', False)})

            # Daca e din nevandut, actualizeaza cantitatea servita
            if p.get('din_nevandut'):
                conn.execute(text("""
                    UPDATE stoc_nevandut
                    SET cantitate_servita = cantitate_servita + :q
                    WHERE data = :data AND nume_produs = :n
                """), {"q": p['cantitate'], "data": data, "n": p['nume_produs']})


def get_loturi_eveniment(data):
    """Loturile de tip special/eveniment lansate de admin pentru o zi."""
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT c.id, c.observatii AS descriere, c.tip_comanda,
                   string_agg(l.cantitate || 'x ' || l.nume_produs, ', ' ORDER BY l.id) AS produse
            FROM comenzi c
            JOIN comenzi_linii l ON c.id = l.comanda_id
            WHERE c.data_comanda = :data
              AND c.client_id = 999
              AND c.tip_comanda IN ('special', 'eveniment')
            GROUP BY c.id, c.observatii, c.tip_comanda
            ORDER BY c.id
        """), {"data": data})
        return [dict(r._mapping) for r in r]


def get_serviri_eveniment_azi(comanda_ref_id, data):
    """Totalul servit dintr-un lot de eveniment."""
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT l.nume_produs, SUM(l.cantitate) AS total_servit
            FROM serviri_ghiseu_linii l
            JOIN serviri_ghiseu s ON l.servire_id = s.id
            WHERE s.comanda_ref_id = :cid AND s.data_servire = :data
            GROUP BY l.nume_produs
        """), {"cid": comanda_ref_id, "data": data})
        return {row[0]: row[1] for row in r}


# =============================================================
# NEVANDUT
# =============================================================

def get_stoc_nevandut(data):
    """Stocul declarat nevandut pentru o zi. { nume_produs: {cantitate, cantitate_servita, ramas} }"""
    engine = get_engine()
    with engine.connect() as conn:
        r = conn.execute(text("""
            SELECT nume_produs, cantitate, cantitate_servita
            FROM stoc_nevandut WHERE data = :data
        """), {"data": data})
        return {
            row[0]: {
                "cantitate": row[1],
                "cantitate_servita": row[2],
                "ramas": row[1] - row[2]
            }
            for row in r
        }


def declara_nevandut(data, nume_produs, cantitate):
    """
    Inregistreaza sau actualizeaza stocul nevandut pentru un produs.
    Foloseste UPSERT — daca produsul exista, suprascrie cantitatea.
    """
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            INSERT INTO stoc_nevandut (data, nume_produs, cantitate, cantitate_servita)
            VALUES (:data, :nume, :qty, 0)
            ON CONFLICT (data, nume_produs)
            DO UPDATE SET cantitate = :qty, declarat_la = NOW()
        """), {"data": data, "nume": nume_produs, "qty": cantitate})


def sterge_nevandut(data, nume_produs):
    """Sterge declaratia de nevandut pentru un produs (corectie)."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("""
            DELETE FROM stoc_nevandut WHERE data = :data AND nume_produs = :nume
        """), {"data": data, "nume": nume_produs})


# =============================================================
# STERGERI
# =============================================================

def delete_comanda(id_comanda):
    """Sterge o comanda si toate liniile ei (cascade manual)."""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM comenzi_linii WHERE comanda_id = :id"), {"id": id_comanda})
            conn.execute(text("DELETE FROM comenzi WHERE id = :id"), {"id": id_comanda})
        return True
    except Exception as e:
        print(f"Eroare la stergere comanda {id_comanda}: {e}")
        return False
