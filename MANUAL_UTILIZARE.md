# Manual de Utilizare — Cantina Lotus

> Aplicație de gestiune cantină: planificare meniu, lansare producție, comenzi clienți, servire ghișeu și livrări.

---

## Cuprins

1. [Flux general al aplicației](#1-flux-general)
2. [Roluri și acces](#2-roluri-și-acces)
3. [Admin — Planificare și gestiune](#3-admin)
4. [Recepție — Preluare comenzi](#4-recepție)
5. [Bucătărie — Producție și ambalare](#5-bucătărie)
6. [Ghișeu — Servire directă](#6-ghișeu)
7. [Livrator — Distribuție comenzi](#7-livrator)
8. [Pagina publică](#8-pagina-publică)
9. [Scenarii complete pas cu pas](#9-scenarii-complete)

---

## 1. Flux general

Aplicația urmărește traseul complet al unei zile de cantină:

```
ADMIN
  └─ Planifică meniul săptămânal (ce se gătește în fiecare zi)
  └─ Lansează loturi de producție (câte porții se pregătesc)

RECEPȚIE
  └─ Preia comenzi de la clienți (livrare la domiciliu/birou)

BUCĂTĂRIE
  └─ Vede ce trebuie gătit și marchează produsele ca „gata"
  └─ Ambală comenzile clienților și pre-ambaleaza porții pentru ghișeu
  └─ Declară stocul nevândut la sfârșitul zilei

GHIȘEU
  └─ Servește clienți cu bon de casă (plată directă)
  └─ Servește angajații firmelor cu contract
  └─ Gestionează serviri speciale (evenimente)

LIVRATOR
  └─ Preia comenzile ambalate și le livrează
  └─ Marchează fiecare comandă ca livrată
```

---

## 2. Roluri și acces

Aplicația se accesează din bara laterală stângă → **Zona Staff**.

| Rol | Ce vede |
|-----|---------|
| **Admin** | Toate taburile: Admin, Recepție, Bucătărie, Livrare |
| **Recepție** | Introducere comenzi + Rezumat livrări |
| **Bucătărie** | Gătire, Împachetare, Buffer, Nevândut |
| **Ghișeu** | Bon Casă, Firme, Eveniment |
| **Livrator** | Ruta proprie de livrare |

> **Notă:** În versiunea curentă rolul se selectează manual din bara laterală (fără autentificare).

---

## 3. Admin

Modulul Admin conține 5 secțiuni accesibile prin taburi.

### 3.1 Planificare Săptămânală

**Scop:** Stabilești ce produse apar în meniu pentru fiecare zi.

**Cum funcționează:**
1. Alegi ziua din calendar
2. Selectezi produsele din nomenclator pentru fiecare categorie:
   - **Felul 1** — ex: Ciorbă de legume
   - **Felul 2 — Varianta 1** — ex: Pilaf cu pui
   - **Felul 2 — Varianta 2** — ex: Sarmale
   - **Salată** — ex: Salată de varză
   - **Sandwich** (opțional)
3. Apeși **Salvează planificarea**

**Exemplu:**
> Luni 20 ian: F1 = Ciorbă de burtă, F2v1 = Mușchi cu cartofi, F2v2 = Fasole cu cârnați, Salată = Murături

**Vizualizare săptămânală:** Tabelul colorat de sub formular arată planificarea pe 7 zile dintr-o privire. Poate fi exportat Excel pentru tipărire.

---

### 3.2 Lansare Producție

**Scop:** Spui bucătăriei câte porții să pregătească în ziua respectivă.

**Tipuri de loturi:**

| Tip | Când se folosește |
|-----|------------------|
| **Lot Prânz** | Meniu zilnic de prânz (11:00–14:00) |
| **Lot Cină** | Meniu de seară |
| **Sandwich** | Porții de sandwich din nomenclator |
| **Special / Eveniment** | Catering, protocol, comenzi speciale |

**Cum lansezi un lot de prânz:**
1. Selectezi data în bara de sus
2. Mergi la tab **Lansare Producție**
3. În secțiunea **Lot Prânz**, adaugi produse:
   - Alegi categoria (ex: felul_1) → alegi produsul → introduci cantitatea → **➕ Adaugă**
4. Verifici lista produselor adăugate
5. Apeși **🚀 Lansează Lot Prânz**

**Exemplu:**
```
Lot Prânz — 20 ian:
  Ciorbă de burtă     × 40
  Mușchi cu cartofi   × 25
  Fasole cu cârnați   × 15
  Murături            × 40
```

> **Atenție:** Lansarea creează o comandă internă cu client_id=999 (INTERN — Loturi Producție). Bucătăria o vede imediat în tab-ul Gătire.

---

### 3.3 Monitorizare Comenzi

**Scop:** Urmărești în timp real situația tuturor comenzilor din ziua selectată.

**Ce afișează:**
- **Rezumat pe produs:** câte porții din fiecare produs sunt gătite / de ambalat / livrate
- **Rezumat financiar:** total pe fiecare secție (Prânz, Cină, Sandwich, Eveniment)
- **Lista comenzilor:** detalii per comandă cu posibilitate de anulare

**Stările unei comenzi:**
```
nou → în pregătire → pregatit → pe_drum → livrat
                              ↓
                           (ghișeu) servit
```

---

### 3.4 Nomenclator

**Scop:** Gestionezi lista de produse disponibile în aplicație.

**Operații disponibile:**
- **Adaugă produs nou:** introduci Nume, Categorie (felul_1 / felul_2 / salate / sandwich / desert / bauturi), Preț standard → **Adaugă**
- **Editează:** modifici direct în tabel și salvezi
- **Șterge:** bifezi checkbox-ul din dreptul produsului → **Șterge selectate**
- **Export Excel:** generezi lista completă pentru arhivă

> **Categoriile importante:** `felul_1`, `felul_2`, `salate` — acestea apar automat în planificare și la ghișeu. Celelalte categorii apar la comenzi speciale.

---

### 3.5 Firme cu Contract

**Scop:** Gestionezi firmele care au contract de catering zilnic.

**Operații:**
- **Adaugă firmă:** introduci Nume firmă, tip contract (prânz_cina / doar_pranz etc.) → **Adaugă**
- **Activare/dezactivare firmă:** toggle direct din tabel
- **Gestiune angajați:** per firmă poți adăuga angajați, marca concediu, reactiva

**Exemplu structură:**
```
Firma: SC Exemplu SRL (activ)
  Angajați activi: Ion Popescu, Maria Ionescu, Gheorghe Stan
  Angajați concediu: Vasile Marinescu
```

> Angajații activi apar la Ghișeu → Firme pentru servire zilnică.

---

## 4. Recepție

### 4.1 Introducere Comenzi

**Scop:** Înregistrezi comenzile clienților care livrează la domiciliu/birou.

**Pași:**

**1. Client:**
- Cauți clientul din baza de date (după nume sau telefon)
- Dacă e client nou: introduci Nume + Telefon + Adresă → **Salvează client nou**

**2. Selectare produse:**
- **Meniuri rapide** — butoane pentru Meniu V1 și Meniu V2 cu câmp de cantitate (rapid pentru comenzi standard)
- **Porții solo** — alegi felul 1 / felul 2 / salată individual
- **Produse speciale** — orice produs din nomenclator cu cantitate și preț personalizat

**3. Coș comandă:**
- Verifici produsele adăugate, cantitățile și totalul
- Poți șterge orice linie

**4. Detalii livrare:**
- **Livrator:** selectezi din lista de șoferi disponibili
- **Ora livrare:** interval orar (11:00, 11:30, 12:00 ... 14:00) sau URGENT
- **Adresă livrare:** completezi adresa exactă
- **Metodă plată:** Cash / Card / Factură
- **Observații:** instrucțiuni speciale (ex: „etaj 3, interfon 14")

**5. Confirmare:**
- Apeși **✅ Plasează Comanda** → comanda intră în sistem cu status `nou`

**Exemplu:**
```
Client: Popescu Ion — 0741 123 456
Adresă: Str. Florilor nr. 5, bl. A, ap. 12, et. 2
Produse:
  Meniu V1 (Ciorbă + Mușchi + Murături) × 2
  Solo Ciorbă × 1
Total: 75 lei
Livrator: Mihai, Ora: 12:30, Plată: Cash
```

---

### 4.2 Rezumat Livrări

Afișează per zi toate comenzile grupate pe livrator:
- Total cash de încasat per șofer
- Lista detaliată: oră, client, adresă, produse, sumă

---

## 5. Bucătărie

### 5.1 Gătire

**Scop:** Bucătarul urmărește ce trebuie gătit și marchează progresul.

**Ce apare:**
- **Loturi lansate de admin** — produse agregate din toate loturile zilei (ex: Ciorbă × 40 din lotul de prânz)
- **Comenzi speciale** — dacă recepția a introdus comenzi cu produse custom

**Cum marchezi:**
- Când un produs este gata complet: **✅ Gata** → status devine `gatit`
- Dacă e nevoie de corecție: butonul **Reset** revine la `nou`

> **Important:** Un produs apare la Ghișeu și la Împachetare **doar** dacă este marcat `gatit` și există stoc suficient.

---

### 5.2 Buffer Pre-ambalare

**Scop:** Bucătăria pre-ambalează porții generice pe care ghișeul le servește rapid (fără să construiască meniu individual).

**Tipuri de buffer:**
- `V1` — Meniu complet varianta 1 (F1 + F2v1 + Salată)
- `V2` — Meniu complet varianta 2 (F1 + F2v2 + Salată)
- `Solo F1` — Doar felul 1
- `Solo F2 v1` — F2v1 + Salată
- `Solo F2 v2` — F2v2 + Salată

**Cum se declară:**
1. Mergi la tab **Buffer Pre-ambalare**
2. Lângă tipul de meniu ambalat, introduci cantitatea → **➕ Adaugă**
3. Metricile se actualizează: Ambalate / Distribuite / **Disponibile**
4. Dacă ai greșit cantitatea: folosești **Corecție** → introduci valoarea exactă → **Setează**

**Exemplu:**
```
V1 (Ciorbă + Mușchi + Murături): Ambalate=15, Distribuite=3, Disponibile=12
V2 (Ciorbă + Fasole + Murături): Ambalate=10, Distribuite=0, Disponibile=10
```

---

### 5.3 Împachetare

**Scop:** Bucătarul ambalează comenzile clienților individuali pentru livrare.

**Condiții ca o comandă să apară:**
- Toate produsele din comandă sunt marcate `gatit`
- Există stoc suficient (lotul acoperă cantitățile cerute)

**Operații:**
- **📦 Ambalat** → status comandă devine `pregatit` (apare la Livrator)
- **❌ Anulează** → dacă nu există stoc pentru a onora comanda

**Comenzi firme (pachete):**
- Apar angajații firmelor pentru care s-a ales „Pachet" la ghișeu
- Status urmărit: `astept` → **📦 Ambalat** → apare la ghișeu ca `ambalat` → angajatul îl ridică

---

### 5.4 Nevândut

**Scop:** La finalul zilei, bucătarul declară ce a rămas din stoc.

**Cum funcționează:**
1. Introduci câte porții au rămas din fiecare produs
2. Apeși **Declară Nevândut**
3. Porțiile intră în stocul de nevândut — ghișeul le poate oferi angajaților firmelor ca extra

**Exemplu:**
```
Fasole cu cârnați: 3 porții nevândute
Murături: 5 porții nevândute
```

---

## 6. Ghișeu

### 6.1 Bon Casă

**Scop:** Clientul a plătit deja la casă. Ghișeul confirmă ce a cumpărat și descarcă din stoc.

**Construirea bonului:**

**Pas 1 — Meniu pre-ambalat (din buffer):**
- Dacă bucătăria a pre-ambalat porții, apar butoane în partea de sus (ex: `📦 Ciorbă + Mușchi + Murături (12 disponibile)`)
- Apăsând butonul → se adaugă în bon (stocul se descarcă abia la confirmare)

**Pas 2 — Meniu complet:**
- `Meniu V1` — F1 + F2v1 + Salată (dacă toate sunt gătite și în stoc)
- `Meniu V2` — F1 + F2v2 + Salată

**Pas 3 — Porții solo:**
- `Solo F1` — doar felul 1
- `Solo V1` — F2v1 + Salată
- `Solo V2` — F2v2 + Salată

**Bon curent:**
- Fiecare produs/meniu adăugat apare ca un rând
- Dacă adaugi același meniu de 2 ori → cantitatea crește automat (ex: `🍱 Ciorbă + Mușchi — x2`)
- Apasă pe un rând pentru a reduce cantitatea (sau șterge dacă e ultima bucată)
- **✅ Confirmă Servirea** → totul se salvează și stocul se descarcă
- **🗑️ Golește** → resetezi bonul fără a salva

**Exemplu flux:**
```
Client plătit la casă → ghișeul adaugă:
  📦 V1 pre-ambalat    ×2   (din buffer)
  🍽️ Solo F1            ×1   (din stoc live)
→ Confirmă → 3 serviri salvate, stoc actualizat
```

---

### 6.2 Firme

**Scop:** Servești angajații firmelor cu contract zilnic.

**Structură ecran:**
- Fiecare firmă apare ca un expander: `🏢 SC Exemplu SRL — 3/8 serviți`
- Expanderul este deschis automat dacă mai sunt angajați neserviți

**Pentru fiecare angajat neservit:**
1. **Selectează meniu** (dropdown):
   - `V1: Ciorbă + Mușchi + Murături`
   - `V2: Ciorbă + Fasole + Murături`
   - `Solo F1: Ciorbă`
   - `Solo V1: Mușchi + Murături`
   - `Solo V2: Fasole + Murături`
2. **Selectează nevândut** (opțional): adaugi o porție din stocul nevândut
   - Dacă nevândutul este un fel 2, salata se atașează automat
3. **Alege tipul de servire:**
   - **🍽️ La masă** → angajatul mănâncă pe loc (apare tăiat imediat)
   - **📦 Pachet** → comanda merge la bucătărie pentru ambalare
     - Dacă există buffer disponibil: apare `📦 Pachet (buf)` — se ia direct din buffer

**Status pachete:**
```
⏳ Bucătărie (astept) → 📦 Gata! (ambalat) → 🚀 Ridicat (buton) → ~~Ridicat~~
```

**Adaugă angajat nou direct din ghișeu:**
- Câmpul de text din partea de sus a fiecărei firme → introduci numele → **➕**

**Marchează concediu:**
- Butonul roșu **🔴** din dreptul angajatului → trece la Inactivi
- Din secțiunea `💤 Inactivi` → butonul **🟢** reactivează

---

### 6.3 Eveniment

**Scop:** Gestionezi serviri din loturi speciale (protocol, catering intern).

**Cum funcționează:**
1. Selectezi lotul special lansat de admin (tipul `eveniment` sau `special`)
2. Introduci cantitățile servite per produs
3. Confirmi → stocul lotului se reduce corespunzător

---

## 7. Livrator

**Scop:** Șoferul urmărește comenzile de livrat și le marchează ca livrate.

**Ecranul livratorului:**

**Secțiunea „De preluat"** (status `pregatit`):
- Comenzile ambalate de bucătărie, gata de ridicat
- Per comandă: Ora, Client, Telefon, Adresă, Produse, Sumă + metodă plată
- Buton **🚚 Am preluat** → status devine `pe_drum`

**Secțiunea „Pe drum"** (status `pe_drum`):
- Comenzile în curs de livrare
- Buton **✅ Livrat!** → status devine `livrat` și dispare din ecran

**Totaluri rapide** (afișate în partea de sus):
- Comenzi de preluat / Pe drum / Total cash de încasat

**Exemplu rutar:**
```
DE PRELUAT:
  12:30 — Ion Popescu, Str. Florilor 5 — Meniu V1 ×2 — 50 lei cash
  12:30 — Maria Ionescu, Bd. Libertății 12 — Solo F1 — 20 lei card

→ Am preluat (ambele) → Pe drum

PE DRUM:
  12:30 — Ion Popescu ✅ Livrat!
```

---

## 8. Pagina Publică

Accesibilă din bara laterală → **🏠 Acasă (Public)** — vizibilă fără autentificare.

Afișează:
- Meniul zilei cu produse și prețuri
- Informații catering (evenimente, protocol)
- Contact: telefoane, adresă, program livrări

---

## 9. Scenarii Complete

### Scenariul A — Zi normală de prânz

```
08:00 ADMIN
  → Planificare (deja făcută săptămânal)
  → Lansare Lot Prânz: Ciorbă×40, Mușchi×25, Fasole×15, Murături×40

09:00 RECEPȚIE
  → Preia comenzi de la clienți:
     Popescu Ion — Meniu V1 ×2, livrare 12:30, cash 50 lei
     Ionescu Maria — Solo Ciorbă ×1, livrare 13:00, card 18 lei

10:00 BUCĂTĂRIE
  → Tab Gătire: vede Ciorbă×40, Mușchi×25, Fasole×15, Murături×40
  → Gătesc și marchează ✅ Gata pe rând
  → Tab Buffer: pre-ambalează V1×15, V2×10
  → Tab Împachetare: ambele comenzi apar → marchează 📦 Ambalat

11:00 GHIȘEU — Bon Casă
  → Clienți directi: servesc din buffer (📦 V1) sau din stoc live
  → Construiesc bon, confirmă

11:00 GHIȘEU — Firme
  → SC Exemplu SRL: Ion Popescu → V1 → La masă ✓
  → SC Exemplu SRL: Maria Ionescu → V2 → Pachet (buf) → status astept
  
11:30 BUCĂTĂRIE — Impachetare
  → Pachetul Mariei Ionescu: 📦 Ambalat → apare la ghișeu verde
  
11:35 GHIȘEU — Firme
  → Maria Ionescu: 📦 Gata! → 🚀 Ridicat ✓

12:00 LIVRATOR (Mihai)
  → De preluat: comanda Popescu → 🚚 Am preluat
  → Pe drum → livrare → ✅ Livrat!

14:00 BUCĂTĂRIE — Nevândut
  → Fasole: 3 porții rămase → Declară Nevândut

15:00 ADMIN — Monitorizare
  → Verifică toate comenzile livrate, situația financiară a zilei
```

---

### Scenariul B — Client nou la recepție

```
1. Recepție → Introducere comenzi
2. Câmp client → "Gheorghe" → nu apare în bază
3. Completezi: Gheorghe Vasile / 0741 999 888 / Str. Trandafirilor 3
4. → Salvează client nou → apare în dropdown
5. Adaugi produse → coș → plasează comanda
```

---

### Scenariul C — Angajat firmă nou, fără cont

```
1. Ghișeu → Firme → SC Exemplu SRL (expander deschis)
2. Câmpul „Angajat nou" din partea de sus a expanderului
3. Introduci: "Florin Dumitrescu"
4. → ➕ → angajatul apare imediat în lista activilor
5. Selectezi meniu, La masă → servit
```

---

### Scenariul D — Pachet din buffer la ghișeu Bon Casă

```
1. Bucătăria a ambalat V1 × 15 (apare în buffer)
2. Ghișeu → Bon Casă → apare buton "📦 Ciorbă + Mușchi + Murături (15 disponibile)"
3. Apăsare buton × 3 (3 clienți) → Bon curent: "📦 V1 — x3"
4. Confirmă → 3 × distribuie_din_buffer → stoc buffer scade la 12
```

---

## Note Operaționale

**Ordinea obligatorie a operațiunilor:**
1. Admin lansează lotul **înainte** ca bucătăria să marcheze gătit
2. Bucătăria marchează `gatit` **înainte** ca ghișeul să poată servi
3. Bucătăria marchează `ambalat` **înainte** ca livratorii să preia

**Stocul se calculează automat:**
- Din lotul lansat (total disponibil)
- Minus comenzile clienților (recepție)
- Minus servirile la ghișeu (bon casă + firme)
- Minus buffer-ul distribuit
- = **Stoc rămas** (vizibil în Monitorizare)

**Nevândut vs Buffer:**
- **Buffer** = porții ambalate azi de bucătărie, distribuite în aceeași zi
- **Nevândut** = porții rămase nedistribuite, oferite ca extra angajaților firmelor

---

*Versiune: Aprilie 2026 — StreamLotus / Cantina Lotus*
