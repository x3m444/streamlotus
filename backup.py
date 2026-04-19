"""
backup.py
---------
Backup complet PostgreSQL — tabele aplicatii (cantina + streamstoc).
Citeste credentialele din .streamlit/secrets.toml.
Salveaza pe Google Drive via rclone.

Rulare: python3 backup.py
Cron:   0 17-23 * * * python3 ~/streamlotus_backup/backup.py >> ~/streamlotus_backup/backup.log 2>&1
"""

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # pip install tomli pentru Python < 3.11

import os, subprocess, sys
from datetime import datetime
from pathlib import Path


def load_secrets():
    p = Path(__file__).parent / ".streamlit" / "secrets.toml"
    with open(p, "rb") as f:
        return tomllib.load(f)


CFG         = load_secrets()
DB_HOST     = CFG["DB_HOST"]
DB_PORT     = str(CFG["DB_PORT"])
DB_NAME     = CFG["DB_NAME"]
DB_USER     = CFG["DB_USER"]
DB_PASS     = CFG["DB_PASS"]
GDRIVE_DEST = CFG["GDRIVE_DEST"]

LOCAL_DIR   = os.path.expanduser("~/streamlotus_backup/files")
LOG_FILE    = os.path.expanduser("~/streamlotus_backup/backup.log")
os.makedirs(LOCAL_DIR, exist_ok=True)
KEEP_DAYS   = 30

TABLES = [
    # Cantina Lotus
    "angajati_firme", "buffer_ambalare", "clienti", "comenzi",
    "comenzi_linii", "firme", "livratori", "planificare_meniu",
    "planificare_saptamanala", "produse", "rezervari_firme",
    "serviri_ghiseu", "serviri_ghiseu_linii", "sesiuni",
    "stoc_nevandut", "utilizatori",
    # StreamStoc
    "list963", "tamburi", "centralizator_tamburi",
    "consum_detaliat", "consum_simplificat", "fisa_magazie_oficiala",
    "fisa_ordonata", "missingcable", "restante_costel",
    "CHECKLIST_SELECTIE_AZI", "INTRO978", "control_costel",
    "liste_sq_import", "planificare_zi", "comenzi_detalii",
]


def log(msg):
    line = f"[{datetime.now().strftime('%d.%m.%Y %H:%M')}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def upload_log():
    subprocess.run(["rclone", "copy", LOG_FILE, GDRIVE_DEST], check=False)


def backup_exists_today():
    today = datetime.now().strftime("%Y%m%d")
    result = subprocess.run(["rclone", "lsf", GDRIVE_DEST],
                            capture_output=True, text=True)
    return any(today in line for line in result.stdout.splitlines())


def main():
    if backup_exists_today():
        log("Backup deja exista pentru azi. Skip.")
        upload_log()
        sys.exit(0)

    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = os.path.join(LOCAL_DIR, f"backup_{ts}.sql")
    env = os.environ.copy()
    env["PGPASSWORD"] = DB_PASS

    try:
        args = [
            "pg_dump",
            "-h", DB_HOST, "-p", DB_PORT,
            "-U", DB_USER, "-d", DB_NAME,
            "--no-password", "--clean", "--if-exists",
            "--no-owner", "--no-privileges",
        ]
        for t in TABLES:
            args += ["-t", t]
        args += ["-f", out]

        subprocess.run(args, env=env, check=True)
        size_kb = os.path.getsize(out) // 1024
        subprocess.run(["rclone", "copy", out, GDRIVE_DEST], check=True)
        log(f"OK — backup_{ts}.sql ({size_kb} KB, {len(TABLES)} tabele) urcat pe Drive.")

        cutoff = datetime.now().timestamp() - KEEP_DAYS * 86400
        for fn in os.listdir(LOCAL_DIR):
            fp = os.path.join(LOCAL_DIR, fn)
            if os.path.getmtime(fp) < cutoff:
                os.remove(fp)

    except Exception as e:
        log(f"EROARE: {e}")

    upload_log()


if __name__ == "__main__":
    main()
