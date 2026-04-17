-- ============================================================
-- StreamLotus — Setup baza de date
-- Generat din schema efectiva Supabase
-- PostgreSQL 14+
-- ============================================================

-- ============================================================
-- 1. USERS (stub pentru FK din comenzi)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id    SERIAL PRIMARY KEY,
    email TEXT
);

-- ============================================================
-- 2. PRODUSE
-- ============================================================
CREATE TABLE IF NOT EXISTS produse (
    id            SERIAL PRIMARY KEY,
    nume          TEXT    NOT NULL,
    categorie     TEXT,
    pret_standard NUMERIC NOT NULL DEFAULT 0
);

-- ============================================================
-- 3. PLANIFICARE MENIU
-- ============================================================
CREATE TABLE IF NOT EXISTS planificare_meniu (
    id         SERIAL PRIMARY KEY,
    data_zi    DATE                     NOT NULL,
    produs_id  INTEGER                  REFERENCES produse(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ              DEFAULT CURRENT_TIMESTAMP,
    tip_plan   VARCHAR                  NOT NULL DEFAULT 'pranz'
);

-- ============================================================
-- 4. CLIENTI & LIVRATORI
-- ============================================================
CREATE TABLE IF NOT EXISTS clienti (
    id                 SERIAL PRIMARY KEY,
    nume_client        TEXT    NOT NULL UNIQUE,
    adresa_livrare     TEXT,
    telefon            TEXT    NOT NULL UNIQUE,
    zona_livrare       TEXT,
    adresa_principala  TEXT,
    observatii_client  TEXT,
    puncte_fidelitate  INTEGER DEFAULT 0
);

-- Client intern rezervat pentru loturi de productie admin
INSERT INTO clienti (id, nume_client, telefon, adresa_principala)
VALUES (999, 'INTERN — Loturi Productie', '0000000000', 'Cantina')
ON CONFLICT DO NOTHING;

SELECT setval('clienti_id_seq', 1000, false);

CREATE TABLE IF NOT EXISTS livratori (
    id    SERIAL PRIMARY KEY,
    nume  TEXT    NOT NULL UNIQUE,
    activ BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- 5. COMENZI
-- ============================================================
CREATE TABLE IF NOT EXISTS comenzi (
    id                   SERIAL PRIMARY KEY,
    client_id            INTEGER    REFERENCES clienti(id),
    data_comanda         DATE       DEFAULT CURRENT_DATE,
    ora_livrare_estimata TIME       NOT NULL,
    status               TEXT       DEFAULT 'nou',
    metoda_plata         TEXT,
    total_plata          NUMERIC,
    superuser_id         INTEGER    REFERENCES users(id),
    sofer                TEXT,
    detalii_comanda      TEXT,
    observatii           TEXT,
    adresa_livrare       TEXT,
    tip_comanda          VARCHAR    NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_comenzi_data     ON comenzi(data_comanda);
CREATE INDEX IF NOT EXISTS idx_comenzi_status   ON comenzi(status);
CREATE INDEX IF NOT EXISTS idx_comenzi_client   ON comenzi(client_id);

CREATE TABLE IF NOT EXISTS comenzi_linii (
    id          SERIAL PRIMARY KEY,
    comanda_id  INTEGER  REFERENCES comenzi(id) ON DELETE CASCADE,
    produs_id   INTEGER  REFERENCES produse(id),
    nume_produs TEXT,
    cantitate   INTEGER,
    pret_unitar NUMERIC,
    status      VARCHAR  DEFAULT 'nou',
    tip_linie   VARCHAR  DEFAULT 'standard'
);

CREATE INDEX IF NOT EXISTS idx_comenzi_linii_comanda ON comenzi_linii(comanda_id);

-- ============================================================
-- 6. FIRME CU CONTRACT
-- ============================================================
CREATE TABLE IF NOT EXISTS firme (
    id                 SERIAL PRIMARY KEY,
    nume_firma         TEXT        NOT NULL,
    tip_contract       TEXT        DEFAULT 'pranz_cina',
    activ              BOOLEAN     DEFAULT TRUE,
    created_at         TIMESTAMPTZ DEFAULT NOW(),
    tip_firma          VARCHAR     DEFAULT 'ghiseu',
    cantitate_default  INTEGER     DEFAULT 0,
    client_id          INTEGER     REFERENCES clienti(id)
);
-- tip_firma: 'ghiseu' | 'ghiseu_livrare' | 'livrare' | 'special'
-- ghiseu          = servire nominala la ghiseu (default, existent)
-- ghiseu_livrare  = pranz livrat + cina la ghiseu, tabel nominal
-- livrare         = cantitate fixa livrata (scoli, sandwich)
-- special         = meniu construit manual, independent de planificare

CREATE TABLE IF NOT EXISTS angajati_firme (
    id           SERIAL PRIMARY KEY,
    firma_id     INTEGER  REFERENCES firme(id) ON DELETE CASCADE,
    nume_angajat TEXT     NOT NULL,
    activ        BOOLEAN  DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_angajati_firma ON angajati_firme(firma_id);

CREATE TABLE IF NOT EXISTS rezervari_firme (
    firma_id   INTEGER NOT NULL REFERENCES firme(id) ON DELETE CASCADE,
    data_rez   DATE    NOT NULL,
    cantitate  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (firma_id, data_rez)
);

-- ============================================================
-- 7. SERVIRI GHISEU
-- ============================================================
CREATE TABLE IF NOT EXISTS serviri_ghiseu (
    id             SERIAL PRIMARY KEY,
    data_servire   DATE        NOT NULL DEFAULT CURRENT_DATE,
    ora_servire    TIME        DEFAULT CURRENT_TIME,
    tip_servire    TEXT        NOT NULL,
    firma_id       INTEGER     REFERENCES firme(id),
    angajat_id     INTEGER     REFERENCES angajati_firme(id),
    comanda_ref_id INTEGER     REFERENCES comenzi(id),
    observatii     TEXT,
    tip_ridicare   TEXT        DEFAULT 'la_masa',
    status_pachet  TEXT,
    din_buffer     BOOLEAN     NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_serviri_data  ON serviri_ghiseu(data_servire);
CREATE INDEX IF NOT EXISTS idx_serviri_firma ON serviri_ghiseu(firma_id);

CREATE TABLE IF NOT EXISTS serviri_ghiseu_linii (
    id           SERIAL PRIMARY KEY,
    servire_id   INTEGER  REFERENCES serviri_ghiseu(id) ON DELETE CASCADE,
    nume_produs  TEXT     NOT NULL,
    cantitate    INTEGER  NOT NULL DEFAULT 1,
    din_nevandut BOOLEAN  DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_serviri_linii ON serviri_ghiseu_linii(servire_id);

-- ============================================================
-- 8. STOC NEVANDUT
-- ============================================================
CREATE TABLE IF NOT EXISTS stoc_nevandut (
    id                SERIAL PRIMARY KEY,
    data              DATE        NOT NULL,
    nume_produs       TEXT        NOT NULL,
    cantitate         INTEGER     NOT NULL,
    cantitate_servita INTEGER     DEFAULT 0,
    declarat_la       TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (data, nume_produs)
);

-- ============================================================
-- 9. BUFFER AMBALARE
-- ============================================================
CREATE TABLE IF NOT EXISTS buffer_ambalare (
    data_zi    DATE    NOT NULL,
    tip_meniu  VARCHAR NOT NULL,
    cantitate  INTEGER NOT NULL DEFAULT 0,
    distribuit INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (data_zi, tip_meniu)
);

-- ============================================================
-- DONE
-- Rulare:
--   psql -U postgres -d streamlotus -f setup_db.sql
-- ============================================================
