-- ============================================================
-- StreamLotus — Setup baza de date
-- PostgreSQL 14+
-- Ruleaza o singura data pe o baza de date goala.
-- ============================================================

-- Client intern pentru loturi admin (nu se sterge niciodata)
-- client_id = 999 este rezervat pentru loturile de productie

-- ============================================================
-- 1. PRODUSE & PLANIFICARE
-- ============================================================

CREATE TABLE IF NOT EXISTS produse (
    id             SERIAL PRIMARY KEY,
    nume           VARCHAR(200) NOT NULL,
    categorie      VARCHAR(50)  NOT NULL,  -- felul_1 | felul_2 | salate | sandwich | desert | etc.
    pret_standard  NUMERIC(8,2) NOT NULL DEFAULT 0,
    activ          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS planificare_meniu (
    id          SERIAL PRIMARY KEY,
    data_zi     DATE        NOT NULL,
    produs_id   INTEGER     NOT NULL REFERENCES produse(id) ON DELETE CASCADE,
    tip_plan    VARCHAR(20) NOT NULL,  -- pranz | cina | sandwich
    UNIQUE (data_zi, produs_id, tip_plan)
);

-- ============================================================
-- 2. CLIENTI & LIVRATORI
-- ============================================================

CREATE TABLE IF NOT EXISTS clienti (
    id                   SERIAL PRIMARY KEY,
    nume_client          VARCHAR(200) NOT NULL,
    telefon              VARCHAR(20),
    adresa_principala    TEXT,
    observatii_client    TEXT,
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

-- Client intern rezervat pentru loturi de productie admin
INSERT INTO clienti (id, nume_client, telefon, adresa_principala)
VALUES (999, 'INTERN — Loturi Productie', 'N/A', 'Cantina')
ON CONFLICT (id) DO NOTHING;

-- Reseteaza secventa ca sa nu colizioneze cu id=999
SELECT setval('clienti_id_seq', 1000, false);

CREATE TABLE IF NOT EXISTS livratori (
    id    SERIAL PRIMARY KEY,
    nume  VARCHAR(100) NOT NULL UNIQUE
);

-- ============================================================
-- 3. COMENZI
-- ============================================================

CREATE TABLE IF NOT EXISTS comenzi (
    id                    SERIAL PRIMARY KEY,
    client_id             INTEGER     NOT NULL REFERENCES clienti(id),
    data_comanda          DATE        NOT NULL DEFAULT CURRENT_DATE,
    ora_livrare_estimata  TIME,
    status                VARCHAR(20) NOT NULL DEFAULT 'nou',
        -- nou | pregatit | pedrum | livrat | anulat
    metoda_plata          VARCHAR(20) NOT NULL DEFAULT 'cash',
        -- cash | card | transfer | cantina
    total_plata           NUMERIC(10,2) NOT NULL DEFAULT 0,
    sofer                 VARCHAR(100),
    observatii            TEXT,
    tip_comanda           VARCHAR(20) NOT NULL DEFAULT 'livrare',
        -- livrare | cantina | pranz | cina | sandwich | special | eveniment
    created_at            TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_comenzi_data ON comenzi(data_comanda);
CREATE INDEX IF NOT EXISTS idx_comenzi_status ON comenzi(status);
CREATE INDEX IF NOT EXISTS idx_comenzi_client ON comenzi(client_id);

CREATE TABLE IF NOT EXISTS comenzi_linii (
    id          SERIAL PRIMARY KEY,
    comanda_id  INTEGER     NOT NULL REFERENCES comenzi(id) ON DELETE CASCADE,
    nume_produs VARCHAR(200) NOT NULL,
    cantitate   INTEGER     NOT NULL DEFAULT 1,
    pret_unitar NUMERIC(8,2) NOT NULL DEFAULT 0,
    tip_linie   VARCHAR(20) NOT NULL DEFAULT 'standard',
        -- standard | special
    status      VARCHAR(20) NOT NULL DEFAULT 'nou'
        -- nou | gatit
);

CREATE INDEX IF NOT EXISTS idx_comenzi_linii_comanda ON comenzi_linii(comanda_id);
CREATE INDEX IF NOT EXISTS idx_comenzi_linii_data ON comenzi_linii(comanda_id);

-- ============================================================
-- 4. FIRME CU CONTRACT
-- ============================================================

CREATE TABLE IF NOT EXISTS firme (
    id            SERIAL PRIMARY KEY,
    nume_firma    VARCHAR(200) NOT NULL UNIQUE,
    tip_contract  VARCHAR(20)  NOT NULL DEFAULT 'pranz_cina',
        -- pranz_cina | pranz | cina
    activ         BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS angajati_firme (
    id             SERIAL PRIMARY KEY,
    firma_id       INTEGER     NOT NULL REFERENCES firme(id) ON DELETE CASCADE,
    nume_angajat   VARCHAR(200) NOT NULL,
    activ          BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_angajati_firma ON angajati_firme(firma_id);

CREATE TABLE IF NOT EXISTS rezervari_firme (
    firma_id   INTEGER NOT NULL REFERENCES firme(id) ON DELETE CASCADE,
    data_rez   DATE    NOT NULL,
    cantitate  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (firma_id, data_rez)
);

-- ============================================================
-- 5. SERVIRI GHISEU
-- ============================================================

CREATE TABLE IF NOT EXISTS serviri_ghiseu (
    id              SERIAL PRIMARY KEY,
    data_servire    DATE        NOT NULL DEFAULT CURRENT_DATE,
    tip_servire     VARCHAR(20) NOT NULL DEFAULT 'bon_casa',
        -- bon_casa | firma | eveniment
    firma_id        INTEGER     REFERENCES firme(id),
    angajat_id      INTEGER     REFERENCES angajati_firme(id),
    comanda_ref_id  INTEGER     REFERENCES comenzi(id),
    tip_ridicare    VARCHAR(20) NOT NULL DEFAULT 'la_masa',
        -- la_masa | pachet
    status_pachet   VARCHAR(20),
        -- astept | ambalat | ridicat (doar pentru tip_ridicare='pachet')
    din_buffer      BOOLEAN     NOT NULL DEFAULT FALSE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_serviri_data ON serviri_ghiseu(data_servire);
CREATE INDEX IF NOT EXISTS idx_serviri_firma ON serviri_ghiseu(firma_id);

CREATE TABLE IF NOT EXISTS serviri_ghiseu_linii (
    id           SERIAL PRIMARY KEY,
    servire_id   INTEGER      NOT NULL REFERENCES serviri_ghiseu(id) ON DELETE CASCADE,
    nume_produs  VARCHAR(200) NOT NULL,
    cantitate    INTEGER      NOT NULL DEFAULT 1,
    din_nevandut BOOLEAN      NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_serviri_linii_servire ON serviri_ghiseu_linii(servire_id);

-- ============================================================
-- 6. STOC NEVANDUT
-- ============================================================

CREATE TABLE IF NOT EXISTS stoc_nevandut (
    id                SERIAL PRIMARY KEY,
    data              DATE        NOT NULL,
    nume_produs       VARCHAR(200) NOT NULL,
    cantitate         INTEGER     NOT NULL DEFAULT 0,
    cantitate_servita INTEGER     NOT NULL DEFAULT 0,
    declarat_la       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (data, nume_produs)
);

-- ============================================================
-- 7. BUFFER AMBALARE
-- ============================================================

CREATE TABLE IF NOT EXISTS buffer_ambalare (
    id          SERIAL PRIMARY KEY,
    data_zi     DATE        NOT NULL,
    tip_meniu   VARCHAR(20) NOT NULL,
        -- v1 | v2 | solo_f1 | solo_f2v1 | solo_f2v2 | solo_salata
    cantitate   INTEGER     NOT NULL DEFAULT 0,
    distribuit  INTEGER     NOT NULL DEFAULT 0,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (data_zi, tip_meniu)
);

-- ============================================================
-- DONE
-- ============================================================
-- Ruleaza cu:
--   psql -U postgres -d streamlotus -f setup_db.sql
-- sau din pgAdmin / DBeaver / Adminer
-- ============================================================
