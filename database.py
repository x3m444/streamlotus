from sqlalchemy import create_engine, text
import streamlit as st
import pandas as pd
import json
from datetime import date # Pentru gestionarea datelor calendaristice (date.today())
import utils

# 1. Configurare Motor SQLAlchemy cu Pooling
@st.cache_resource
def get_engine():
    # Construim URL-ul de conexiune din secrete
    conn_url = f"postgresql://{st.secrets['DB_USER']}:{st.secrets['DB_PASS']}@{st.secrets['DB_HOST']}:{st.secrets['DB_PORT']}/{st.secrets['DB_NAME']}"
    return create_engine(conn_url, pool_size=5, max_overflow=10)

# --- SECȚIUNEA: CITIRE (CU CACHE) ---

@st.cache_data(ttl=600) # Cache pentru 10 minute
def get_toate_produsele():
    """Returnează toate produsele sub formă de listă de dicționare."""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("SELECT * FROM produse ORDER BY id DESC")
        result = conn.execute(query)
        return [dict(row._mapping) for row in result]

#@st.cache_data(ttl=300) # Cache pentru 5 minute

def get_meniu_planificat(data_start, data_end=None, tip_plan="pranz"):
    engine = get_engine()
    with engine.connect() as conn:
        if data_end is None:
            # Varianta pentru o zi (include pret_standard)
            query = text("""
                SELECT p.*, prod.nume, prod.categorie, prod.pret_standard
                FROM planificare_meniu p
                JOIN produse prod ON p.produs_id = prod.id
                WHERE p.data_zi = :s AND LOWER(p.tip_plan) = LOWER(:t)
            """)
            res = conn.execute(query, {"s": str(data_start), "t": tip_plan})
            return [dict(r._mapping) for r in res]
        
        else:
            # Varianta pentru tabel (am adăugat pret_standard aici)
            query = text("""
                SELECT p.data_zi, p.tip_plan, prod.nume, prod.pret_standard
                FROM planificare_meniu p
                JOIN produse prod ON p.produs_id = prod.id
                WHERE p.data_zi BETWEEN :s AND :e
            """)
            res = conn.execute(query, {"s": str(data_start), "e": str(data_end)})
            
            plan_dict = {}
            for r in res:
                row = dict(r._mapping)
                key = (str(row['data_zi']), row['tip_plan'].lower())
                if key not in plan_dict:
                    plan_dict[key] = []
                
                # Salvăm tot obiectul row, nu doar numele, ca să avem și prețul la îndemână
                plan_dict[key].append(row) 
            return plan_dict

# --- SECȚIUNEA: SCRIERE (FĂRĂ CACHE + CLEAR CACHE) ---

def add_produs(nume, categorie, pret):
    """Adaugă un produs și golește cache-ul pentru a vedea modificarea."""
    engine = get_engine()
    with engine.begin() as conn:
        query = text("INSERT INTO produse (nume, categorie, pret_standard) VALUES (:n, :c, :p)")
        conn.execute(query, {"n": nume, "c": categorie, "p": pret})
    st.cache_data.clear() # Forțăm reîmprospătarea datelor

def salveaza_planificare(data_zi, produse_ids, tip_plan="pranz"):
    engine = get_engine()
    with engine.begin() as conn:
        # Ștergem planificarea existentă pentru acea zi ȘI acel tip
        conn.execute(
            text("DELETE FROM planificare_meniu WHERE data_zi = :d AND tip_plan = :t"),
            {"d": data_zi, "t": tip_plan}
        )
        
        # Inserăm noile produse
        for pid in produse_ids:
            conn.execute(
                text("INSERT INTO planificare_meniu (data_zi, produs_id, tip_plan) VALUES (:d, :p, :t)"),
                {"d": data_zi, "p": pid, "t": tip_plan}
            )

def update_produs(id_produs, nume, categorie, pret):
    """Actualizează datele unui produs."""
    engine = get_engine()
    with engine.begin() as conn:
        query = text("""
            UPDATE produse 
            SET nume = :n, categorie = :c, pret_standard = :p 
            WHERE id = :id
        """)
        conn.execute(query, {"n": nume, "c": categorie, "p": pret, "id": id_produs})
    st.cache_data.clear()

def delete_produs(id_produs):
    """Șterge un produs din baza de date."""
    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM produse WHERE id = :id"), {"id": id_produs})
    st.cache_data.clear()

def search_clienti(query):
    """Caută un client după nume sau telefon folosind SQLAlchemy."""
    engine = get_engine()
    with engine.connect() as conn:
        # Folosim ILIKE pentru căutare case-insensitive (nu contează literele mari/mici)
        sql = text("""
            SELECT * FROM clienti 
            WHERE nume_client ILIKE :q OR telefon ILIKE :q 
            LIMIT 10
        """)
        result = conn.execute(sql, {"q": f"%{query}%"})
        return [dict(row._mapping) for row in result]

def add_client(nume_client, telefon, adresa_principala, observatii_client=""):
    """Adaugă un client folosind exact numele coloanelor din tabelă."""
    engine = get_engine()
    with engine.begin() as conn:
        query = text("""
            INSERT INTO clienti (nume_client, telefon, adresa_principala, observatii_client) 
            VALUES (:n, :t, :a, :o)
            RETURNING id, nume_client, telefon, adresa_principala
        """)
        result = conn.execute(query, {
            "n": nume_client, 
            "t": telefon, 
            "a": adresa_principala, 
            "o": observatii_client
        })
        st.cache_data.clear()
        return dict(result.fetchone()._mapping)
# --- SECȚIUNEA: COMENZI ---

def save_comanda_finala(client_id, produse, total, sofer, ora, obs):
    engine = get_engine()
    data_actuala_ro = utils.get_ro_time().date()
    with engine.begin() as conn:
        sql_c = text("""
            INSERT INTO comenzi (
                client_id, ora_livrare_estimata, status, 
                metoda_plata, total_plata, sofer, observatii
            )
            VALUES (
                :cid, :ora, 'nou', 'cash', :total, :sofer, :obs
            ) 
            RETURNING id
        """)
        
        ora_sql = ora.split('-')[0].strip() if '-' in ora else ora[:5]
        
        res = conn.execute(sql_c, {
            "cid": client_id, "ora": ora_sql, "total": total, "sofer": sofer, "obs": obs
        })
        new_id = res.fetchone()[0]
        
        # Salvăm produsele în tabelul de linii
        for p in produse:
            conn.execute(text("""
                INSERT INTO comenzi_linii (comanda_id, nume_produs, cantitate, pret_unitar)
                VALUES (:mid, :nume, :qty, :pret)
            """), {"mid": new_id, "nume": p['nume'], "qty": p['cantitate'], "pret": p['pret']})
    return True

def get_comenzi_zi(zi=None):
    """
    Extrage toate comenzile pentru o anumită zi (implicit azi).
    Include numele și telefonul clientului prin JOIN.
    """
    # 1. Dacă nu primim o zi, folosim data curentă
    if zi is None:
        zi = date.today()
    
    engine = get_engine()
    try:
        with engine.connect() as conn:
            # 2. SQL-ul care unește tabela comenzi cu tabela clienti
            # Folosim c.* pentru toate coloanele din comenzi
            # și selectăm specific numele și telefonul din clienti
            sql = text("""
                SELECT 
                    c.id, 
                    c.created_at, 
                    c.data_livrare, 
                    c.adresa_specifica_livrare, 
                    c.detalii_comanda, 
                    c.total_plata, 
                    c.status_comanda, 
                    c.observatii_comanda,
                    cl.nume_client, 
                    cl.telefon
                FROM comenzi c
                JOIN clienti cl ON c.client_id = cl.id
                WHERE c.data_livrare = :d
                ORDER BY c.id DESC
            """)
            
            result = conn.execute(sql, {"d": zi})
            
            # 3. Transformăm rezultatul într-o listă de dicționare pentru Streamlit
            comenzi = [dict(row._mapping) for row in result]
            return comenzi

    except Exception as e:
        st.error(f"Eroare la preluarea comenzilor: {e}")
        return []
def update_client(id_client, nume, telefon, adresa):
    """Actualizează datele unui client existent."""
    engine = get_engine()
    with engine.begin() as conn:
        sql = text("""
            UPDATE clienti 
            SET nume_client = :n, telefon = :t, adresa_principala = :a 
            WHERE id = :id
        """)
        conn.execute(sql, {"n": nume, "t": telefon, "a": adresa, "id": id_client})
    st.cache_data.clear()

def delete_client(id_client):
    """Șterge un client (Atenție: va eșua dacă are comenzi active din cauza FK)."""
    engine = get_engine()
    try:
        with engine.begin() as conn:
            conn.execute(text("DELETE FROM clienti WHERE id = :id"), {"id": id_client})
        st.cache_data.clear()
        return True
    except Exception:
        return False   
def get_all_clienti():
    """Returnează toți clienții ordonați alfabetic după nume."""
    engine = get_engine()
    with engine.connect() as conn:
        query = text("SELECT id, nume_client, telefon, adresa_principala FROM clienti ORDER BY nume_client ASC")
        result = conn.execute(query)
        # Returnăm lista de dicționare folosind _mapping
        return [dict(row._mapping) for row in result]   
def get_nomenclator_produse():
    """Extrage produsele folosind numele corecte ale coloanelor din DB."""
    engine = get_engine()
    with engine.connect() as conn:
        # Folosim coloana 'nume' așa cum apare în poza ta
        sql = text("SELECT id, nume, pret_standard, categorie FROM produse ORDER BY nume")
        result = conn.execute(sql)
        
        # Mappăm rezultatul pentru a fi folosit ușor în Python
        return [dict(row._mapping) for row in result]

def get_lista_livratori():
    """Returnează lista numelor livratorilor conform ordinii din DB."""
    engine = get_engine()
    with engine.connect() as conn:
        # Folosim ORDER BY id pentru a păstra ordinea în care i-am introdus mai sus
        result = conn.execute(text("SELECT nume FROM livratori ORDER BY id ASC"))
        return [row[0] for row in result]
    
from datetime import datetime

def save_comanda_finala(client_id, produse, total, sofer, ora, obs, plata, tip_comanda, data_comanda):
    engine = get_engine()
    
    # Acum folosim direct 'data_comanda' primită de la selectorul paginii
    # Nu mai generăm data_azi_ro aici, pentru a permite precomenzile

    with engine.begin() as conn:
        # Inserăm comanda în tabelul principal
        sql_c = text("""
            INSERT INTO comenzi (
                client_id, data_comanda, ora_livrare_estimata, 
                status, metoda_plata, total_plata, sofer, observatii,
                tip_comanda
            )
            VALUES (
                :cid, :data_c, :ora, 'nou', :plata, :total, :sofer, :obs,
                :tip
            )
            RETURNING id
        """)
        
        # Curățăm formatul orei pentru SQL
        ora_sql = ora.split('-')[0].strip() if '-' in ora else ora[:5]
        
        res = conn.execute(sql_c, {
            "cid": client_id,
            "data_c": data_comanda, # <--- Data preluată de pe pagină
            "ora": ora_sql,
            "total": total,
            "sofer": sofer,
            "obs": obs,
            "plata": plata,
            "tip": tip_comanda
        })
        
        new_id = res.fetchone()[0]
        
        # Salvăm liniile de produse în tabelul secundar
        for p in produse:
            conn.execute(text("""
                INSERT INTO comenzi_linii (comanda_id, nume_produs, cantitate, pret_unitar)
                VALUES (:mid, :nume, :qty, :pret)
            """), {
                "mid": new_id, 
                "nume": p['nume'], 
                "qty": p['cantitate'], 
                "pret": p['pret']
            })
            
    return True

def get_comenzi_zi_curenta():

    engine = get_engine()
    data_azi = datetime.now().strftime("%Y-%m-%d")
    
    with engine.connect() as conn:
        # Facem un JOIN între comenzi și clienți ca să avem și numele clientului în rezumat
        sql = text("""
            SELECT c.total_plata, c.sofer, c.status_comanda, cl.nume as nume_client, c.detalii_comanda
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            WHERE c.data_comanda = :data_azi
        """)
        result = conn.execute(sql, {"data_azi": data_azi})
        return [dict(row._mapping) for row in result]    
    
def get_raport_zilei():
    engine = get_engine()
    data_azi = datetime.now().strftime("%Y-%m-%d")
    
    with engine.connect() as conn:
        sql = text("""
            SELECT 
                c.sofer, 
                cl.nume as client, 
                c.detalii_comanda, 
                c.total_plata, 
                c.ora_livrare, 
                c.status_comanda
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            WHERE c.data_comanda = :data_azi
            ORDER BY c.sofer, c.ora_livrare
        """)
        result = conn.execute(sql, {"data_azi": data_azi})
        return [dict(row._mapping) for row in result]   
    
from datetime import datetime

def get_comenzi_zi_curenta():
    """Extrage comenzile de azi cu numele clientului inclus."""
    engine = get_engine()
    data_azi = datetime.now().strftime("%Y-%m-%d")
    
    with engine.connect() as conn:
        sql = text("""
            SELECT c.total_plata, c.sofer, c.status_comanda, cl.nume as nume_client, 
                   c.detalii_comanda, c.ora_livrare
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            WHERE c.data_comanda = :data_azi
            ORDER BY c.sofer, c.ora_livrare
        """)
        result = conn.execute(sql, {"data_azi": data_azi})
        return [dict(row._mapping) for row in result]    
            
def get_rezumat_zi(data_filtrare=None, tip_comanda=None, status_filtru=None):
    engine = get_engine()
    
    # Dacă nu dăm o dată, folosim data de azi
    if data_filtrare is None:
        import utils
        data_filtrare = utils.get_ro_time().date()

    with engine.connect() as conn:
        # SELECTĂM toate câmpurile necesare
        # string_agg combină produsele: "1x Ciorba|nou, 2x Pizza|gatit"
        query = """
            SELECT 
                c.id, 
                c.status as status_comanda, 
                c.sofer, 
                cl.nume_client as client, 
                cl.telefon,
                cl.adresa_principala, 
                c.metoda_plata, 
                c.tip_comanda,
                c.total_plata,
                c.ora_livrare_estimata,
                string_agg(l.cantitate || 'x ' || l.nume_produs || '|' || l.status, ', ') as detalii
            FROM comenzi c
            JOIN clienti cl ON c.client_id = cl.id
            LEFT JOIN comenzi_linii l ON c.id = l.comanda_id
            WHERE c.data_comanda = :data
        """
        
        params = {"data": data_filtrare}
        
        # Adăugăm filtrele dacă sunt cerute (Bucătărie/Ambalare)
        if tip_comanda:
            query += " AND c.tip_comanda = :tip"
            params["tip"] = tip_comanda
            
        if status_filtru:
            query += " AND c.status = :stat"
            params["stat"] = status_filtru
            
        # Grupăm după toate coloanele de mai sus pentru a putea folosi string_agg
        query += """ 
            GROUP BY 
                c.id, c.status, cl.nume_client, cl.telefon, cl.adresa_principala, 
                c.metoda_plata, c.total_plata, c.ora_livrare_estimata, c.tip_comanda
            ORDER BY c.ora_livrare_estimata
        """
        
        # Executăm și returnăm rezultatul ca listă de dicționare
        return [dict(r._mapping) for r in conn.execute(text(query), params)]


def update_status_comanda(engine, comanda_id, noul_status):
    """
    Schimbă statusul unei singure comenzi (tabelul principal).
    Folosită la Expediție (Gata de livrare) sau de către Șofer.
    """
    with engine.begin() as conn:
        query = text("UPDATE comenzi SET status = :status WHERE id = :id")
        conn.execute(query, {"status": noul_status, "id": comanda_id})

def update_status_batch(engine, data_selectata, nume_produs, noul_status):
    """
    Actualizează statusul individual pentru toate liniile care conțin 
    un anumit produs, într-o anumită zi.
    """
    with engine.begin() as conn:
        # Această interogare modifică statusul DIRECT în tabelul de linii
        # pentru a nu afecta celelalte produse din aceeași comandă.
        query = text("""
            UPDATE comenzi_linii
            SET status = :noul_status
            WHERE nume_produs = :nume
            AND comanda_id IN (
                SELECT id 
                FROM comenzi 
                WHERE data_comanda = :data
            )
        """)
        
        conn.execute(query, {
            "noul_status": noul_status, 
            "data": data_selectata, 
            "nume": nume_produs
        })  

def get_raport_interval(data_start, data_end):
    engine = get_engine()
    with engine.connect() as conn:
        query = """
            SELECT 
                tip_comanda,
                SUM(total_plata) as total_valoare,
                COUNT(id) as nr_comenzi
            FROM comenzi 
            WHERE data_comanda BETWEEN :start AND :end
            GROUP BY tip_comanda
        """
        params = {"start": data_start, "end": data_end}
        return [dict(r._mapping) for r in conn.execute(text(query), params)]   
    
def delete_comanda(id_comanda):
    """Șterge o comandă și toate liniile asociate ei."""
    engine = get_engine()
    try:
        with engine.begin() as conn:  # .begin() face commit automat la final
            # 1. Ștergem liniile produselor (pentru a respecta integritatea bazei de date)
            conn.execute(
                text("DELETE FROM comenzi_linii WHERE comanda_id = :id"),
                {"id": id_comanda}
            )
            # 2. Ștergem comanda principală
            conn.execute(
                text("DELETE FROM comenzi WHERE id = :id"),
                {"id": id_comanda}
            )
        return True
    except Exception as e:
        print(f"Eroare la ștergere: {e}")
        return False   