# utils.py
from datetime import date, timedelta
import pandas as pd
import io

from datetime import datetime, timedelta

def get_ro_time():
    # UTC+3 pentru ora de vară în România
    return datetime.utcnow() + timedelta(hours=3)
def get_zile_saptamana(data_referinta=None):
    """Returnează o listă cu datele de luni până sâmbătă pentru săptămâna datei date."""
    if data_referinta is None:
        data_referinta = date.today()
    
    luni = data_referinta - timedelta(days=data_referinta.weekday())
    return [luni + timedelta(days=i) for i in range(6)]

def format_nume_zi(data_obiect):
    """Returnează numele zilei în română."""
    zile = ["Luni", "Marți", "Miercuri", "Joi", "Vineri", "Sâmbătă", "Duminică"]
    return zile[data_obiect.weekday()]



def export_to_excel(df, sheet_name="Date"):
    """
    Transformă un DataFrame într-un fișier Excel (.xlsx) formatat de bază.
    """
    output = io.BytesIO()
    
    # Creăm scriitorul Excel
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
        
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # --- FORMATĂRI ---
        # 1. Header îngroșat cu fundal gri deschis
        header_format = workbook.add_format({
            'bold': True,
            'text_wrap': True,
            'valign': 'top',
            'fg_color': '#D7E4BC',
            'border': 1
        })

        # Aplicăm formatarea pe header
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(0, col_num, value, header_format)
            
        # 2. Ajustăm lățimea coloanelor automat
        for i, col in enumerate(df.columns):
            column_len = max(df[col].astype(str).str.len().max(), len(col)) + 2
            worksheet.set_column(i, i, column_len)
            
    return output.getvalue()

def export_to_excel_vertical(df, sheet_name="Planificare"):
    import io
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Scriem datele începând cu rândul 4 (index 3) pentru a lăsa loc titlului
        df.to_excel(writer, index=False, sheet_name=sheet_name, startrow=3)
        
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]
        
        # --- FORMATE ---
        title_format = workbook.add_format({
            'bold': True, 'font_size': 18, 'align': 'center', 'valign': 'vcenter', 'font_color': '#D32F2F'
        })
        subtitle_format = workbook.add_format({
            'italic': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter'
        })
        header_format = workbook.add_format({
            'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center',
            'fg_color': '#D7E4BC', 'border': 1
        })
        cell_format = workbook.add_format({
            'text_wrap': True, 'valign': 'top', 'border': 1, 'font_size': 10
        })

        # --- TITLU ȘI ANTET ---
        # Îmbinăm celulele A1-C1 pentru titlu
        worksheet.merge_range('A1:C1', 'Cantina LOTUS', title_format)
        worksheet.merge_range('A2:C2', 'Planificare Meniu Săptămânal', subtitle_format)
        
        # --- CONFIGURARE PAGINĂ ---
        worksheet.set_portrait() # Format vertical
        worksheet.set_margins(0.5, 0.5, 0.5, 0.5)
        
        # --- LĂȚIMI COLOANE ---
        worksheet.set_column(0, 0, 15, cell_format) # Data
        worksheet.set_column(1, 1, 40, cell_format) # Prânz
        worksheet.set_column(2, 2, 40, cell_format) # Cină
        
        # Aplicăm formatul de header manual pe rândul unde am început scrierea (rândul 4)
        for col_num, value in enumerate(df.columns.values):
            worksheet.write(3, col_num, value, header_format)

        # Re-aplicăm formatul de celulă pe toate datele pentru a forța text_wrap
        for row_num in range(4, len(df) + 4):
            for col_num in range(len(df.columns)):
                val = df.iloc[row_num-4, col_num]
                worksheet.write(row_num, col_num, val, cell_format)
                
    return output.getvalue()

def export_raport_excel(df, titlu, subtitlu=None, sheet_name="Raport"):
    """
    Export profesional landscape pentru rapoarte interne.
    Header: CANTINA LOTUS + titlu raport + data generarii.
    Tabel: header rosu, randuri alternate, coloane auto-dimensionate.
    Footer: adresa, telefon, program.
    """
    output = io.BytesIO()
    FONT   = "Segoe UI"

    # Paleta gri — prietenoasa cu imprimante alb-negru
    GRI_NEGRU  = "#1A1A1A"   # brand / titlu
    GRI_HDR    = "#3D3D3D"   # header coloane (inchis)
    GRI_HDR2   = "#6B6B6B"   # titlu raport (mediu)
    GRI_ALT    = "#EBEBEB"   # rand alternativ
    GRI_SEP    = "#555555"   # linii separator
    GRI_FOOTER = "#888888"   # text footer
    GRI_BORDER = "#AAAAAA"   # borduri celule

    nc           = len(df.columns)
    last_col     = nc - 1
    data_gen     = get_ro_time().strftime("%d.%m.%Y %H:%M")

    def col_letter(n):
        s = ""
        while n >= 0:
            s = chr(n % 26 + 65) + s
            n = n // 26 - 1
        return s

    last_col_ltr = col_letter(last_col)

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook  = writer.book
        worksheet = workbook.add_worksheet(sheet_name)
        writer.sheets[sheet_name] = worksheet

        # ── orientare, margini, centrare pe pagina ────────────
        worksheet.set_landscape()
        worksheet.set_margins(0.4, 0.4, 0.5, 0.5)
        worksheet.set_print_scale(90)
        worksheet.center_horizontally()   # centrat pe latime
        worksheet.center_vertically()     # centrat pe inaltime
        worksheet.repeat_rows(0, 4)       # header repetat la print multipagina
        worksheet.print_area(f"A1:{last_col_ltr}{5 + len(df) + 2}")

        # ── formate ──────────────────────────────────────────
        fmt_brand = workbook.add_format({
            "bold": True, "font_size": 20, "font_color": GRI_NEGRU,
            "font_name": FONT, "valign": "vcenter",
        })
        fmt_contact = workbook.add_format({
            "font_size": 8, "font_color": GRI_FOOTER, "font_name": FONT,
            "align": "right", "valign": "vcenter", "text_wrap": True,
        })
        fmt_titlu_rap = workbook.add_format({
            "bold": True, "font_size": 13, "font_name": FONT,
            "align": "center", "valign": "vcenter",
            "fg_color": GRI_HDR, "font_color": "white",
        })
        fmt_subtitlu = workbook.add_format({
            "italic": True, "font_size": 8, "font_name": FONT,
            "align": "center", "valign": "vcenter", "font_color": GRI_FOOTER,
            "fg_color": "#F5F5F5",
        })
        fmt_sep = workbook.add_format({
            "bottom": 2, "bottom_color": GRI_SEP,
        })
        fmt_col_hdr = workbook.add_format({
            "bold": True, "font_size": 10, "font_name": FONT,
            "fg_color": GRI_HDR2, "font_color": "white",
            "align": "center", "valign": "vcenter",
            "border": 1, "border_color": GRI_HDR, "text_wrap": True,
        })
        fmt_cell = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "text_wrap": True,
        })
        fmt_cell_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "fg_color": GRI_ALT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "text_wrap": True,
        })
        fmt_cell_num = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "align": "right", "num_format": "#,##0.00",
        })
        fmt_cell_num_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "fg_color": GRI_ALT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "align": "right", "num_format": "#,##0.00",
        })
        fmt_cell_int = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "align": "right",
        })
        fmt_cell_int_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "fg_color": GRI_ALT,
            "border": 1, "border_color": GRI_BORDER,
            "valign": "vcenter", "align": "right",
        })
        fmt_footer_sep = workbook.add_format({
            "top": 1, "top_color": GRI_SEP,
        })
        fmt_footer = workbook.add_format({
            "font_size": 8, "font_name": FONT, "font_color": GRI_FOOTER,
            "italic": True, "align": "center", "valign": "vcenter",
            "fg_color": "#F5F5F5",
        })

        # ── rand 0: brand stanga + contact dreapta (2 coloane) ──
        worksheet.set_row(0, 34)
        contact_cols = min(2, nc)           # contact ocupa 2 col sau mai putin daca nc mic
        brand_end    = nc - contact_cols - 1
        contact_str  = "0746.358.018 | 0743.090.212\nStr. Ing. Dumitru Ivanov 18, Tulcea"
        if brand_end >= 1:
            worksheet.merge_range(0, 0, 0, brand_end, "CANTINA LOTUS", fmt_brand)
        else:
            worksheet.write(0, 0, "CANTINA LOTUS", fmt_brand)
        if contact_cols > 1:
            worksheet.merge_range(0, nc - contact_cols, 0, last_col, contact_str, fmt_contact)
        else:
            worksheet.write(0, last_col, contact_str, fmt_contact)

        # ── rand 1: titlu raport ──────────────────────────────
        worksheet.set_row(1, 26)
        worksheet.merge_range(f"A2:{last_col_ltr}2", titlu.upper(), fmt_titlu_rap)

        # ── rand 2: subtitlu ─────────────────────────────────
        worksheet.set_row(2, 16)
        sub = subtitlu or f"Generat: {data_gen}"
        worksheet.merge_range(f"A3:{last_col_ltr}3", sub, fmt_subtitlu)

        # ── rand 3: separator ─────────────────────────────────
        worksheet.set_row(3, 3)
        for c in range(nc):
            worksheet.write(3, c, "", fmt_sep)

        # ── rand 4: header coloane ────────────────────────────
        worksheet.set_row(4, 28)
        for c, col_name in enumerate(df.columns):
            worksheet.write(4, c, str(col_name), fmt_col_hdr)

        # ── date tabel cu randuri alternate ───────────────────
        for r_idx, (_, row) in enumerate(df.iterrows()):
            alt = (r_idx % 2 == 1)
            worksheet.set_row(5 + r_idx, 18)
            for c_idx, val in enumerate(row):
                is_float = isinstance(val, float)
                is_int   = isinstance(val, int) and not isinstance(val, bool)
                if is_float:
                    fmt = fmt_cell_num_alt if alt else fmt_cell_num
                elif is_int:
                    fmt = fmt_cell_int_alt if alt else fmt_cell_int
                else:
                    fmt = fmt_cell_alt if alt else fmt_cell
                worksheet.write(5 + r_idx, c_idx, val, fmt)

        # ── dimensionare coloane ──────────────────────────────
        # Landscape A4 la 90% scala = ~105 unitati latime utilizabila
        MIN_PAGE_WIDTH = 105
        col_widths = []
        for col_name in df.columns:
            val_max = df[col_name].astype(str).str.len().max() if len(df) else 0
            w = min(max(int(val_max) + 2, len(str(col_name)) + 2), 45)
            col_widths.append(w)

        total_w = sum(col_widths)
        if total_w < MIN_PAGE_WIDTH:
            # distribui restul proportional
            extra = MIN_PAGE_WIDTH - total_w
            col_widths = [w + extra * w // total_w for w in col_widths]
            # ajustam ultima coloana pentru a absorbi restul de rotunjire
            col_widths[-1] += MIN_PAGE_WIDTH - sum(col_widths)

        for c_idx, w in enumerate(col_widths):
            worksheet.set_column(c_idx, c_idx, w)

        # ── footer ────────────────────────────────────────────
        footer_row = 5 + len(df) + 1
        worksheet.set_row(footer_row - 1, 3)
        for c in range(nc):
            worksheet.write(footer_row - 1, c, "", fmt_footer_sep)
        worksheet.set_row(footer_row, 18)
        worksheet.merge_range(
            footer_row, 0, footer_row, last_col,
            f"Cantina Lotus  •  Str. Ing. Dumitru Ivanov 18, Tulcea  •  0746.358.018  •  L-V 11:00–14:00  •  Generat: {data_gen}",
            fmt_footer,
        )

    return output.getvalue()


def export_raport_firme(serviri, data):
    """
    Export raport serviri firme — un sheet per firma.
    serviri: lista de dict din get_raport_serviri_firme()
    data: datetime.date
    """
    from collections import defaultdict
    output   = io.BytesIO()
    FONT     = "Segoe UI"
    GRI_HDR  = "#3D3D3D"
    GRI_ALT  = "#EBEBEB"
    GRI_BRD  = "#AAAAAA"
    GRI_FOOT = "#888888"
    data_str = data.strftime("%d.%m.%Y")

    # Grupam pe firma
    pe_firma = defaultdict(list)
    for row in serviri:
        pe_firma[row["nume_firma"]].append(row)

    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # Formate comune (create o singura data pe workbook)
        fmt_brand = workbook.add_format({
            "bold": True, "font_size": 18, "font_name": FONT, "valign": "vcenter",
        })
        fmt_contact = workbook.add_format({
            "font_size": 8, "font_color": GRI_FOOT, "font_name": FONT,
            "align": "right", "valign": "vcenter", "text_wrap": True,
        })
        fmt_firma_titlu = workbook.add_format({
            "bold": True, "font_size": 13, "font_name": FONT,
            "align": "center", "valign": "vcenter",
            "fg_color": GRI_HDR, "font_color": "white",
        })
        fmt_subtitlu = workbook.add_format({
            "italic": True, "font_size": 8, "font_name": FONT,
            "align": "center", "valign": "vcenter",
            "font_color": GRI_FOOT, "fg_color": "#F5F5F5",
        })
        fmt_sep = workbook.add_format({"bottom": 2, "bottom_color": "#555555"})
        fmt_col_hdr = workbook.add_format({
            "bold": True, "font_size": 10, "font_name": FONT,
            "fg_color": "#6B6B6B", "font_color": "white",
            "align": "center", "valign": "vcenter",
            "border": 1, "border_color": GRI_HDR, "text_wrap": True,
        })
        fmt_cell = workbook.add_format({
            "font_size": 10, "font_name": FONT,
            "border": 1, "border_color": GRI_BRD, "valign": "vcenter",
        })
        fmt_cell_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT, "fg_color": GRI_ALT,
            "border": 1, "border_color": GRI_BRD, "valign": "vcenter",
        })
        fmt_masa = workbook.add_format({
            "font_size": 10, "font_name": FONT, "font_color": "#1A5276",
            "border": 1, "border_color": GRI_BRD, "valign": "vcenter", "align": "center",
        })
        fmt_pachet = workbook.add_format({
            "font_size": 10, "font_name": FONT, "font_color": "#784212",
            "border": 1, "border_color": GRI_BRD, "valign": "vcenter", "align": "center",
        })
        fmt_masa_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT, "font_color": "#1A5276",
            "fg_color": GRI_ALT, "border": 1, "border_color": GRI_BRD,
            "valign": "vcenter", "align": "center",
        })
        fmt_pachet_alt = workbook.add_format({
            "font_size": 10, "font_name": FONT, "font_color": "#784212",
            "fg_color": GRI_ALT, "border": 1, "border_color": GRI_BRD,
            "valign": "vcenter", "align": "center",
        })
        fmt_total = workbook.add_format({
            "bold": True, "font_size": 10, "font_name": FONT,
            "fg_color": "#D5D8DC", "border": 1, "border_color": GRI_HDR,
            "valign": "vcenter",
        })
        fmt_footer_sep = workbook.add_format({"top": 1, "top_color": "#555555"})
        fmt_footer = workbook.add_format({
            "font_size": 8, "font_name": FONT, "font_color": GRI_FOOT,
            "italic": True, "align": "center", "valign": "vcenter",
            "fg_color": "#F5F5F5",
        })

        COL_HEADERS = ["Nr.", "Angajat", "Produse servite", "Tip servire", "Ora"]
        COL_W       = [5, 25, 50, 14, 10]

        for nume_firma, randuri in pe_firma.items():
            # Trunchez numele sheet-ului la 31 caractere (limita Excel)
            sheet_name_f = nume_firma[:31]
            ws = workbook.add_worksheet(sheet_name_f)
            writer.sheets[sheet_name_f] = ws

            ws.set_landscape()
            ws.set_margins(0.4, 0.4, 0.5, 0.5)
            ws.center_horizontally()
            ws.set_print_scale(95)
            ws.repeat_rows(0, 4)

            # Coloane
            for ci, w in enumerate(COL_W):
                ws.set_column(ci, ci, w)

            # Rand 0 — brand + contact
            ws.set_row(0, 32)
            ws.merge_range("A1:D1", "CANTINA LOTUS", fmt_brand)
            ws.write(0, 4, f"0746.358.018\n{data_str}", fmt_contact)

            # Rand 1 — titlu firma
            ws.set_row(1, 26)
            ws.merge_range("A2:E2", f"{nume_firma.upper()} — SERVIRI {data_str}", fmt_firma_titlu)

            # Rand 2 — subtitlu
            ws.set_row(2, 16)
            nr_la_masa  = sum(1 for r in randuri if r["tip_ridicare"] == "la_masa")
            nr_pachete  = sum(1 for r in randuri if r["tip_ridicare"] == "pachet")
            ws.merge_range("A3:E3",
                           f"Total serviti: {len(randuri)}  •  La masa: {nr_la_masa}  •  Pachete: {nr_pachete}",
                           fmt_subtitlu)

            # Rand 3 — separator
            ws.set_row(3, 3)
            for c in range(5):
                ws.write(3, c, "", fmt_sep)

            # Rand 4 — header coloane
            ws.set_row(4, 26)
            for ci, h in enumerate(COL_HEADERS):
                ws.write(4, ci, h, fmt_col_hdr)

            # Date
            for ri, row in enumerate(randuri):
                alt = (ri % 2 == 1)
                ws.set_row(5 + ri, 18)
                tip  = row["tip_ridicare"] or ""
                ora  = str(row["ora_servire"])[:5] if row["ora_servire"] else "—"

                ws.write(5 + ri, 0, ri + 1,               fmt_cell_alt if alt else fmt_cell)
                ws.write(5 + ri, 1, row["nume_angajat"] or "—", fmt_cell_alt if alt else fmt_cell)
                ws.write(5 + ri, 2, row["produse"] or "—",     fmt_cell_alt if alt else fmt_cell)

                if tip == "la_masa":
                    label_tip = "La masa"
                    fmt_tip = fmt_masa_alt if alt else fmt_masa
                else:
                    label_tip = "Pachet"
                    fmt_tip = fmt_pachet_alt if alt else fmt_pachet

                ws.write(5 + ri, 3, label_tip, fmt_tip)
                ws.write(5 + ri, 4, ora, fmt_cell_alt if alt else fmt_cell)

            # Rand total
            total_row = 5 + len(randuri)
            ws.set_row(total_row, 20)
            ws.merge_range(total_row, 0, total_row, 1, f"TOTAL: {len(randuri)} angajați serviți", fmt_total)
            ws.write(total_row, 2, "", fmt_total)
            ws.write(total_row, 3, f"La masă: {nr_la_masa}", fmt_total)
            ws.write(total_row, 4, f"Pachete: {nr_pachete}", fmt_total)

            # Footer
            footer_row = total_row + 2
            ws.set_row(footer_row - 1, 3)
            for c in range(5):
                ws.write(footer_row - 1, c, "", fmt_footer_sep)
            ws.set_row(footer_row, 16)
            ws.merge_range(footer_row, 0, footer_row, 4,
                           f"Cantina Lotus  •  Str. Ing. Dumitru Ivanov 18, Tulcea  •  0746.358.018  •  {data_str}",
                           fmt_footer)

        # Sheet sumar — toate firmele pe o pagina
        ws_sum = workbook.add_worksheet("SUMAR")
        writer.sheets["SUMAR"] = ws_sum
        ws_sum.set_landscape()
        ws_sum.set_margins(0.4, 0.4, 0.5, 0.5)
        ws_sum.center_horizontally()

        ws_sum.set_column(0, 0, 28)
        ws_sum.set_column(1, 1, 12)
        ws_sum.set_column(2, 2, 12)
        ws_sum.set_column(3, 3, 12)

        ws_sum.set_row(0, 32)
        ws_sum.merge_range("A1:C1", "CANTINA LOTUS", fmt_brand)
        ws_sum.write(0, 3, f"0746.358.018\n{data_str}", fmt_contact)

        ws_sum.set_row(1, 26)
        ws_sum.merge_range("A2:D2", f"SUMAR SERVIRI FIRME — {data_str}", fmt_firma_titlu)

        ws_sum.set_row(2, 3)
        for c in range(4): ws_sum.write(2, c, "", fmt_sep)

        ws_sum.set_row(3, 26)
        for ci, h in enumerate(["Firmă", "Total serviți", "La masă", "Pachete"]):
            ws_sum.write(3, ci, h, fmt_col_hdr)

        total_general = 0
        for ri, (nume_firma, randuri) in enumerate(pe_firma.items()):
            alt        = (ri % 2 == 1)
            la_masa_n  = sum(1 for r in randuri if r["tip_ridicare"] == "la_masa")
            pachete_n  = len(randuri) - la_masa_n
            total_general += len(randuri)
            ws_sum.set_row(4 + ri, 18)
            ws_sum.write(4 + ri, 0, nume_firma,     fmt_cell_alt if alt else fmt_cell)
            ws_sum.write(4 + ri, 1, len(randuri),   fmt_cell_alt if alt else fmt_cell)
            ws_sum.write(4 + ri, 2, la_masa_n,      fmt_cell_alt if alt else fmt_cell)
            ws_sum.write(4 + ri, 3, pachete_n,      fmt_cell_alt if alt else fmt_cell)

        tr = 4 + len(pe_firma)
        ws_sum.set_row(tr, 20)
        ws_sum.write(tr, 0, "TOTAL", fmt_total)
        ws_sum.write(tr, 1, total_general, fmt_total)
        ws_sum.write(tr, 2, "", fmt_total)
        ws_sum.write(tr, 3, "", fmt_total)

    return output.getvalue()


def export_to_excel_landscape_v2(df, sheet_name="Flyer_Meniu"):
    import io
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, header=False, sheet_name=sheet_name, startrow=4)
        
        workbook  = writer.book
        worksheet = writer.sheets[sheet_name]
        font_main = 'Segoe UI'
        
        # --- CONFIGURARE PRINT ---
        worksheet.set_landscape()
        worksheet.set_margins(0.2, 0.2, 0.2, 0.2)
        worksheet.set_print_scale(95) 

        # --- FORMATE ---
        fmt_titlu = workbook.add_format({'bold': True, 'font_size': 28, 'align': 'right', 'valign': 'vcenter', 'font_name': font_main})
        fmt_contact_dreapta = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'right', 'valign': 'vcenter', 'font_name': font_main, 'text_wrap': True})
        fmt_subtitlu = workbook.add_format({'italic': True, 'font_size': 11, 'align': 'left', 'valign': 'top', 'font_name': font_main})
        fmt_header = workbook.add_format({'bold': True, 'bg_color': '#F2F2F2', 'border': 1, 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_name': font_main})
        fmt_celula = workbook.add_format({'text_wrap': True, 'valign': 'vcenter', 'align': 'left', 'indent': 1, 'border': 1, 'font_size': 10, 'font_name': font_main})
        fmt_alergeni_text = workbook.add_format({'font_size': 7.5, 'italic': True, 'font_color': '#666666', 'font_name': font_main})

        # --- 1. ANTET CENTRAT (FĂRĂ SUPRAPUNERE) ---
        worksheet.set_row(0, 45) # Înălțime rând titlu
        
        # Centrăm titlul doar pe primele două coloane (A și B)
        # Acest lucru îl pune pe mijlocul zonei principale fără să afecteze coloana C
        worksheet.merge_range('A1:B1', 'CANTINA LOTUS', fmt_titlu)
        
        # Datele de contact rămân clar în dreapta, pe coloana C
        contact_info = "📞 0746.358.018\n📞 0743.090.212"
        worksheet.write('C1', contact_info, fmt_contact_dreapta)
        
        # Subtitlul rămâne centrat pe toată lățimea (A-C)
        worksheet.merge_range('A2:C2', 'Mâncare gătită zilnic cu ingrediente proaspete | Rezervări și Livrări', fmt_subtitlu)

        # --- 2. LĂȚIRE COLOANE (Ajustat pe lățime) ---
        worksheet.set_column(0, 0, 20) # Mărit de la 18
        worksheet.set_column(1, 1, 58) # Mărit de la 53
        worksheet.set_column(2, 2, 58) # Mărit de la 53

        headers = ['DATA / ZIUA', '🥣 MENIU PRÂNZ', '🌙 MENIU CINĂ']
        for col_num, header in enumerate(headers):
            worksheet.write(3, col_num, header, fmt_header)

        # --- 3. DATE TABEL ---
        text_alergeni = "\n*Alergeni: gluten, ouă, lactate, țelină, muștar, nuci."
        for row_num in range(4, len(df) + 4):
            worksheet.set_row(row_num, 68) 
            for col_num in range(len(df.columns)):
                val = str(df.iloc[row_num-4, col_num])
                if col_num > 0 and val != "---":
                    worksheet.write_rich_string(row_num, col_num, val, fmt_alergeni_text, text_alergeni, fmt_celula)
                else:
                    worksheet.write(row_num, col_num, val, fmt_celula)

        # --- 4. FOOTER (Mutat cu 2 spații mai jos) ---
        # Am schimbat de la +5 la +7 pentru a crea cele 2 rânduri libere
        last_row = len(df) + 7 

        fmt_footer_titlu = workbook.add_format({'bold': True, 'font_size': 12, 'bottom': 1, 'font_name': font_main})
        fmt_footer_text = workbook.add_format({'text_wrap': True, 'font_size': 9.5, 'font_name': font_main, 'valign': 'top'})

        worksheet.merge_range(f'A{last_row}:C{last_row}', '🥗 SERVICII ȘI PROGRAM', fmt_footer_titlu)

        info_complet = (
            "• PROGRAM SERVIRE: Prânz (11:00-13:00) | Cină (16:00-18:00) • LIVRĂRI: Comenzi până la 10:30 • ADRESĂ: Str. Ing. Dumitru Ivanov, nr. 18, Tulcea\n"
            "• EVENIMENTE: Pomeni, parastase, majorate, aniversări și catering corporate.\n"
            "• NOTĂ: Toate preparatele noastre sunt gătite proaspăt în ziua servirii."
        )
        # Textul rămâne lipit sub titlu (last_row + 1)
        worksheet.merge_range(f'A{last_row+1}:C{last_row+2}', info_complet, fmt_footer_text)

        worksheet.set_row(last_row, 16)      
        worksheet.set_row(last_row + 1, 42)  
                
    return output.getvalue()