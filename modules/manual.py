"""
modules/manual.py
------------------
Pagina de manual / ajutor integrata in aplicatie.
Accesibila din bara laterala de catre orice rol.
"""

import streamlit as st


def show_manual():
    st.title("📖 Manual de Utilizare — Cantina Lotus")
    st.caption("Ghid complet de operare al aplicației, structurat pe roluri.")

    # ── Flux general ──────────────────────────────────────────────────────────
    with st.expander("🔄 Fluxul zilei — privire de ansamblu", expanded=True):
        st.graphviz_chart("""
        digraph flux {
            rankdir=LR
            node [shape=box style=filled fontname="Arial" fontsize=12]

            Admin     [label="⚙️ ADMIN\nPlanificare + Lansare" fillcolor="#4A90D9" fontcolor=white]
            Receptie  [label="📝 RECEPȚIE\nPreluare comenzi" fillcolor="#7B68EE" fontcolor=white]
            Bucatarie [label="👨‍🍳 BUCĂTĂRIE\nGătire + Ambalare" fillcolor="#E8873A" fontcolor=white]
            Ghiseu    [label="🏪 GHIȘEU\nServire directă" fillcolor="#50C878" fontcolor=white]
            Livrare   [label="🚚 LIVRARE\nDistribuție comenzi" fillcolor="#E84545" fontcolor=white]

            Admin     -> Bucatarie [label="loturi lansate"]
            Admin     -> Receptie  [label="meniu planificat" style=dashed]
            Receptie  -> Bucatarie [label="comenzi clienți"]
            Bucatarie -> Ghiseu    [label="stoc gătit\n+ buffer"]
            Bucatarie -> Livrare   [label="comenzi ambalate"]
        }
        """, use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info("**Dimineața**\n\nAdmin lansează loturi → Bucătăria gătește → Recepția preia comenzi")
        with col2:
            st.success("**La prânz**\n\nGhișeu servește din stoc/buffer → Livratorii preiau și livrează")
        with col3:
            st.warning("**Final zi**\n\nBucătăria declară nevândut → Admin verifică situația financiară")

    # ── Tabs per rol ──────────────────────────────────────────────────────────
    tab_admin, tab_rec, tab_buc, tab_gh, tab_liv = st.tabs([
        "⚙️ Admin", "📝 Recepție", "👨‍🍳 Bucătărie", "🏪 Ghișeu", "🚚 Livrator"
    ])

    # ═══════════════════════════════════════════════════════════════════════════
    with tab_admin:
        st.markdown("### ⚙️ Modulul Admin")
        st.markdown("Adminul controlează întreaga operațiune: planifică meniul, lansează producția și monitorizează situația financiară.")

        col_a, col_b = st.columns(2)
        with col_a:
            st.success("**Ce poate face adminul:**")
            st.markdown("""
- Planifică meniul pe 7 zile
- Lansează loturi de producție (prânz, cină, sandwich, special)
- Monitorizează comenzile și statusurile
- Gestionează nomenclatorul de produse
- Administrează firmele cu contract și angajații lor
- Generează rapoarte financiare
            """)
        with col_b:
            st.info("**Ordinea corectă a operațiunilor:**")
            st.markdown("""
1. 📋 Adaugă produsele în **Nomenclator** (o singură dată)
2. 🗓️ Planifică meniul săptămânal (din nomenclator)
3. 🚀 Lansează lotul zilei (dimineața)
4. 📊 Monitorizează pe parcurs
5. 📋 Verifică situația la final de zi
            """)

        st.divider()

        with st.expander("📋 Nomenclator Produse — primul pas"):
            st.markdown("""
**Scop:** Lista completă a produselor disponibile în aplicație. Toate celelalte module (planificare, lansare, recepție) selectează **exclusiv** din nomenclator.

**Înainte de orice altceva**, produsele trebuie să existe aici cu:
- **Denumire** — numele exact care apare în meniu și pe bon
- **Categorie** — determină unde apare produsul:

| Categorie | Unde apare |
|-----------|-----------|
| `felul_1` | Planificare → F1, Ghișeu, Recepție |
| `felul_2` | Planificare → F2v1/F2v2, Ghișeu, Recepție |
| `salate` | Planificare → Salată, se atașează automat la meniuri |
| `sandwich` | Planificare → Sandwich |
| `special` | Lansare specială / Recepție produse custom |
| `desert` | Recepție produse custom |

- **Preț standard** — prețul implicit, editabil la comandă

> **Regulă:** Nu poți planifica sau lansa un produs care nu există în nomenclator.
            """)
            st.info("ℹ️ Nomenclatorul se completează o singură dată și se actualizează doar la adăugarea de preparate noi.")

        with st.expander("📅 Planificare Săptămânală"):
            st.markdown("""
**Scop:** Stabilești ce produse apar în meniu pentru fiecare zi — și implicit ce apare pe **pagina publică** a cantinei.

**Pași:**
1. Alegi ziua din calendar
2. Selectezi produsele **din nomenclator** pentru fiecare categorie: **Felul 1**, **Felul 2 v1**, **Felul 2 v2**, **Salată**, **Sandwich**
3. Apeși ✅ **Salvează planificarea**

**Exemplu:**
> Luni: F1 = Ciorbă de burtă | F2v1 = Mușchi cu cartofi | F2v2 = Fasole | Salată = Murături
            """)
            st.success("🌐 **Actualizare automată pagină publică:** imediat după salvarea planificării, meniul apare pe pagina vizibilă clienților — fără niciun pas suplimentar.")
            st.warning("⚠️ Fără planificare, Bucătăria și Ghișeul nu știu ce să pregătească, iar pagina publică afișează mesaj de indisponibilitate.")

        with st.expander("🚀 Lansare Producție"):
            st.markdown("""
**Scop:** Spui bucătăriei câte porții să prepare în ziua respectivă.

Fiecare lot poate fi lansat **o singură dată pe zi**. Dacă e nevoie de corecție: buton **✏️ Edit** (șterge și relansează) sau **🗑️ Șterge**.
            """)
            c1, c2, c3 = st.columns(3)
            c1.metric("🍲 Lot Prânz", "Meniu zilnic", "11:00–14:00")
            c2.metric("🌙 Lot Cină", "Meniu seară", "18:00–20:00")
            c3.metric("🎉 Special", "Catering/Protocol", "la cerere")
            st.markdown("""
**Cum lansezi:**
1. Selectezi data în bara de sus
2. Adaugi produse: **Categorie → Produs → Cantitate → ➕ Adaugă**
3. Verifici lista → ▶️ **Lansează Lot**

**Status vizibil în titlul expander-ului:** `✅ Lansat` sau `⏳ Nelansat`
            """)
            st.info("ℹ️ Sandwich-urile se lansează din **Gestiune Firme → Lansare Zilnică**, nu din acest tab.")
            st.info("ℹ️ Lotul creat apare imediat în Bucătărie → tab Gătire")

        with st.expander("📊 Monitorizare Comenzi"):
            st.markdown("""
**Statusurile unei comenzi:**
            """)
            cols = st.columns(5)
            statusuri = [
                ("🆕 nou", "#f0f0f0"),
                ("⏳ în pregătire", "#fff3cd"),
                ("📦 pregatit", "#d4edda"),
                ("🚚 pe drum", "#cce5ff"),
                ("✅ livrat", "#d1ecf1"),
            ]
            for col, (label, color) in zip(cols, statusuri):
                col.markdown(f'<div style="background:{color};padding:8px;border-radius:6px;text-align:center;font-size:13px">{label}</div>', unsafe_allow_html=True)
            st.markdown("""
**Secțiunile paginii:**
- 🏭 **Loturi Lansate în Producție** — loturile lansate de admin (prânz, cină, special)
- 📝 **Comenzi Clienți** — comenzile preluate de recepție + livrări firme
- 🏢 **Serviri Firme Ghișeu** — rezumat per firmă: `X/Y serviți | 🍽️ masă 📦 pachete | 💰 lei`
            """)

        with st.expander("🏢 Gestiune Firme cu Contract"):
            st.markdown("""
**4 tipuri de firme, fiecare cu flux diferit:**

| Tip | Descriere | Tabel nominal |
|-----|-----------|:---:|
| 🏪 **Ghișeu** | Angajații vin direct la ghișeu | ✅ |
| 🚚+🏪 **Ghișeu + Livrare** | Prânzul se livrează, cina la ghișeu | ✅ |
| 🚚 **Livrare fixă** | Cantitate fixă livrată zilnic (școli, sandwich) | ❌ |
| ⭐ **Special** | Meniu construit manual, independent de planificare | ❌ |

**Tab-uri disponibile:**
1. **🚀 Lansare Zilnică** — generezi comenzi reale pentru firmele cu livrare
   - Fiecare firmă se lansează **o singură dată pe zi** (✏️ Edit / 🗑️ Șterge pentru corecții)
   - Livrare fixă: produsul vine din **planificarea sandwich a zilei**
2. **⚙️ Gestiune Firme** — adaugă, editează, activează/dezactivează firme și angajați
3. **📋 Confirmare Prezență** — rezervi porții pentru firmele ghișeu (scad din stocul zilei)
4. **📊 Raport Serviri** — cine a fost servit azi, cu export Excel per firmă

**Tipuri contract:** `pranz_cina` / `doar_pranz` / `doar_cina`
            """)

    # ═══════════════════════════════════════════════════════════════════════════
    with tab_rec:
        st.markdown("### 📝 Modulul Recepție")
        st.markdown("Recepția preia comenzile telefonice sau online ale clienților și le introduce în sistem.")

        st.success("**Flux introducere comandă:**")
        pasi = st.columns(5)
        for col, (nr, txt) in zip(pasi, [
            ("1️⃣", "Identifici clientul"),
            ("2️⃣", "Adaugi produsele"),
            ("3️⃣", "Setezi livrarea"),
            ("4️⃣", "Alegi metoda plată"),
            ("5️⃣", "Plasezi comanda"),
        ]):
            col.markdown(f'<div style="background:#e8f4f8;padding:10px;border-radius:8px;text-align:center"><b>{nr}</b><br>{txt}</div>', unsafe_allow_html=True)

        st.divider()

        with st.expander("👤 Gestionare clienți"):
            st.markdown("""
- **Client existent:** cauți după nume sau telefon → apare automat
- **Client nou:** completezi Nume + Telefon + Adresă → **Salvează client nou**
- Adresa se păstrează pentru comenzile viitoare
            """)

        with st.expander("🛒 Adăugare produse"):
            st.markdown("""
**3 metode de selectare:**

| Metodă | Când se folosește |
|--------|------------------|
| **Meniuri rapide** (V1/V2 + cantitate) | Comenzi standard de prânz |
| **Porții solo** | Client vrea doar ciorbă sau doar fel 2 |
| **Produse speciale** | Desert, băutură, catering personalizat |

- Coșul se construiește progresiv
- Poți șterge orice linie înainte de confirmare
- Prețul total se calculează automat
            """)

        with st.expander("🚚 Detalii livrare și plată"):
            st.markdown("""
| Câmp | Opțiuni |
|------|---------|
| **Livrator** | selectezi din lista șoferilor activi |
| **Ora livrare** | 11:00 / 11:30 / 12:00 / 12:30 / 13:00 / 13:30 / 14:00 / URGENT |
| **Adresă** | se completează automat din profilul clientului, editabil |
| **Metodă plată** | 💵 Cash / 💳 Card / 🧾 Factură |
            """)
            st.warning("⚠️ Cash = șoferul încasează bani. Card/Factură = șoferul NU primește numerar!")

        with st.expander("📋 Rezumat Livrări"):
            st.markdown("""
Vizualizezi situația zilnică pe livrator:

- **💵 Cash de încasat** — banii pe care șoferul trebuie să-i predea
- **💳 Card** — plăți deja procesate electronic
- **🧾 Factură** — facturare ulterioară
- **📊 Total general** — suma tuturor comenzilor

Fiecare livrator are totalurile proprii afișate în antetul expanderului.
            """)

    # ═══════════════════════════════════════════════════════════════════════════
    with tab_buc:
        st.markdown("### 👨‍🍳 Modulul Bucătărie")
        st.markdown("Bucătăria urmărește producția de la gătire până la ambalare și declară stocul la final de zi.")

        col1, col2, col3, col4 = st.columns(4)
        col1.info("**🔥 Gătire**\nMarchezi produsele ca gătite")
        col2.success("**🗃️ Buffer**\nPre-ambalezi porții pentru ghișeu")
        col3.warning("**📦 Împachetare**\nAmbalezi comenzile clienților")
        col4.error("**📉 Nevândut**\nDeclari ce a rămas la final")

        st.divider()

        with st.expander("🔥 Tab Gătire"):
            st.markdown("""
**Ce apare:**
- Produsele din loturile lansate de admin (agregate pe produs)
- Comenzile speciale de la recepție

**Operații:**
- ✅ **Gata** → produsul devine disponibil pentru ghișeu și împachetare
- 🔄 **Reset** → revii la status `nou` dacă ai greșit

**Regulă importantă:** Un produs apare la ghișeu și în împachetare **DOAR** dacă e marcat `gatit`.
            """)

        with st.expander("🗃️ Tab Buffer Pre-ambalare"):
            st.markdown("""
**Ce este buffer-ul?**
Bucătăria pre-ambalează porții complete (V1, V2, Solo F1 etc.) pe care ghișeul le distribuie rapid fără să construiască meniu individual.

**Tipuri de buffer:**
| Tip | Conținut |
|-----|---------|
| V1 | Felul 1 + Felul 2 v1 + Salată |
| V2 | Felul 1 + Felul 2 v2 + Salată |
| Solo F1 | Doar Felul 1 |
| Solo V1 | Felul 2 v1 + Salată |
| Solo V2 | Felul 2 v2 + Salată |

**Cum declari:**
1. Introduci cantitatea ambalată → ➕ **Adaugă**
2. Metricile se actualizează: Ambalate / Distribuite / **Disponibile**
3. Corecție cantitate greșită: introduci valoarea exactă → **Setează**
            """)
            st.info("ℹ️ Buffer-ul disponibil apare cu buton special (📦) la ghișeu și la firme")

        with st.expander("📦 Tab Împachetare"):
            st.markdown("""
**Comenzile clienților de livrat:**
- Apar **doar** comenzile pentru care toate produsele sunt gătite și stocul e suficient
- 📦 **Ambalat** → comanda devine `pregatit` și apare la livrator
- ❌ **Anulează** → dacă nu ai stoc să onorezi comanda

**Pachete firme:**
- Apar angajații pentru care s-a ales „Pachet" la ghișeu
- Marchezi 📦 **Ambalat** → ghișeul vede că pachetul e gata → angajatul poate ridica
            """)

        with st.expander("📉 Tab Nevândut"):
            st.markdown("""
La finalul zilei, introduci câte porții au rămas din fiecare produs.

- Cantitățile declarate intră în **stocul de nevândut**
- Ghișeul poate oferi aceste porții ca extra angajaților firmelor
- Se urmărește câte au fost distribuite vs câte au rămas

**Exemplu:** Fasole cu cârnați: 3 porții rămase → declarate → oferite la firmă ca supliment
            """)

    # ═══════════════════════════════════════════════════════════════════════════
    with tab_gh:
        st.markdown("### 🏪 Modulul Ghișeu")
        st.markdown("Ghișeul servește clienții direcți, angajații firmelor cu contract și gestionează loturile speciale.")

        with st.expander("🧾 Tab Bon Casă — servire cu plată directă", expanded=True):
            st.markdown("""
Clientul a plătit deja la casă. Ghișeul confirmă ce a cumpărat.
            """)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("**Construiești bonul:**")
                st.markdown("""
1. 📦 Butoane **Buffer** (dacă bucătăria a pre-ambalat) — cel mai rapid
2. 🍱 **Meniu complet** V1 sau V2
3. 🍽️ **Porție solo**: Solo F1 / Solo V1 / Solo V2

→ Același meniu adăugat de 2 ori = cantitate crește automat (x2, x3...)
→ Apasă pe rând din bon pentru a reduce cantitatea
                """)
            with c2:
                st.markdown("**Confirmare:**")
                st.success("✅ **Confirmă Servirea** → stocul se descarcă, servirea se salvează")
                st.error("🗑️ **Golește** → resetezi bonul fără a salva nimic")
            st.warning("⚠️ Stocul se descarcă **doar la confirmare**, nu la adăugare în bon!")

        with st.expander("🏢 Tab Firme — angajați cu contract"):
            st.markdown("""
**Structura ecranului:**
- Fiecare firmă = un card expandabil
- Titlul arată progresul: `🏢 SC Exemplu SRL — 3/8 serviți`
- Se deschide automat dacă mai sunt angajați neserviți
            """)
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Pentru fiecare angajat:**")
                st.markdown("""
1. **Selectează meniu** (dropdown cu prefix clar):
   - `V1:` Meniu complet varianta 1
   - `V2:` Meniu complet varianta 2
   - `Solo F1:` Doar felul 1
   - `Solo V1/V2:` Felul 2 + Salată
2. **Nevândut** (opțional): extra porție din stocul declarat
3. **Tipul servirii:**
   - 🍽️ **La masă** → servit pe loc
   - 📦 **Pachet** → trimis la bucătărie pentru ambalare
                """)
            with col2:
                st.markdown("**Statusuri pachet:**")
                for stare, culoare, desc in [
                    ("⏳ Bucătărie", "#fff3cd", "pachetul e la ambalat"),
                    ("📦 Gata!", "#d4edda", "bucătăria a ambalat"),
                    ("🚀 Ridicat", "#cce5ff", "angajatul a luat pachetul"),
                    ("~~Ridicat~~", "#f8f9fa", "complet, barat"),
                ]:
                    st.markdown(f'<div style="background:{culoare};padding:6px 10px;border-radius:6px;margin:3px 0">{stare} — <small>{desc}</small></div>', unsafe_allow_html=True)

            st.divider()
            st.markdown("**Operații rapide din ghișeu:**")
            c1, c2 = st.columns(2)
            c1.info("**➕ Angajat nou:** câmpul din partea de sus a firmei → Nume → ➕")
            c2.warning("**🔴 Concediu:** butonul roșu de lângă angajat → trece la Inactivi")

    # ═══════════════════════════════════════════════════════════════════════════
    with tab_liv:
        st.markdown("### 🚚 Modulul Livrator")
        st.markdown("Șoferul vede comenzile de livrat și le marchează pe parcurs.")

        col1, col2 = st.columns(2)
        with col1:
            st.info("""
**📥 De preluat** *(status: pregatit)*

Comenzile ambalate de bucătărie, gata de ridicat.

Per comandă: oră, client, telefon, adresă, produse, sumă + metodă plată

→ 🚚 **Am preluat** → trece pe drum
            """)
        with col2:
            st.success("""
**🚗 Pe drum** *(status: pe_drum)*

Comenzile în curs de livrare.

→ ✅ **Livrat!** → dispare din ecran, status final
            """)

        st.divider()
        st.markdown("**Totaluri afișate:**")
        c1, c2, c3 = st.columns(3)
        c1.metric("📦 De preluat", "comenzi gata")
        c2.metric("🚗 Pe drum", "comenzi livrate")
        c3.metric("💵 Cash total", "de încasat azi")

        st.warning("""
⚠️ **Atenție la metoda de plată:**
- 💵 **Cash** → șoferul încasează bani și predă la final de zi
- 💳 **Card** → plată procesată electronic, șoferul NU primește numerar
- 🧾 **Factură** → facturare ulterioară, șoferul NU primește numerar
        """)

    # ── Pagina publică ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 🌐 Pagina Publică — cum se actualizează meniul")

    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
Pagina vizibilă clienților (**🏠 Acasă**) afișează automat meniul zilei curente.

**Lanțul de actualizare:**
```
Admin salvează Planificarea zilei
        ↓
Pagina publică citește planificarea pentru data de azi
        ↓
Meniul apare imediat, fără restart sau acțiuni suplimentare
```

**Ce vede clientul:**
- Produsele planificate pentru ziua curentă cu prețurile din nomenclator
- Dacă nu există planificare pentru ziua curentă → mesaj de indisponibilitate
- Informații contact, program livrări, servicii catering
        """)
    with col2:
        st.info("""
**⏱️ Când se actualizează?**

Imediat după ce adminul apasă
✅ Salvează planificarea

Fără delay, cache sau aprobare suplimentară.
        """)
        st.warning("""
**⚠️ Weekend:**

Dacă nu există planificare pentru ziua curentă, pagina publică nu afișează meniu.
        """)

    # ── Sfaturi generale ──────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 💡 Sfaturi operaționale")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.error("""
**❌ Greșeli frecvente**
- Ghișeul servește înainte ca bucătăria să marcheze gătit
- Livratorii preiau înainte de împachetare
- Admin uită să lanseze lotul dimineața
        """)
    with col2:
        st.success("""
**✅ Ordinea corectă**
1. Admin lansează lotul
2. Bucătăria marchează gătit
3. Bucătăria ambaleaza comenzile
4. Ghișeu servește / Livrator preia
        """)
    with col3:
        st.info("""
**ℹ️ Reguli stoc**
- Buffer = porții pre-ambalate azi
- Nevândut = porții rămase, oferite ca extra
- Stocul se descarcă la confirmare, nu la selectare
        """)
