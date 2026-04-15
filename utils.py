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