import tabula
import pandas as pd
import io
import os

def extract_tables_from_pdf(filepath):
    try:
        tables = tabula.read_pdf(filepath, pages='all', multiple_tables=True)
        
        table_data = []
        for i, table in enumerate(tables):
            if not table.empty and len(table.columns) > 1:
                csv_buffer = io.StringIO()
                table.to_csv(csv_buffer, index=False, encoding='utf-8')
                csv_content = csv_buffer.getvalue()
                csv_buffer.close()
                
                table_data.append({
                    'filename': f"table_{i+1}.csv",
                    'content': csv_content,
                    'rows': len(table),
                    'columns': len(table.columns)
                })
        
        return table_data
    except Exception as e:
        print(f"Ошибка извлечения таблиц: {e}")
        return []

def export_document_tables(doc_id, db_session, upload_folder):
    from models import Document
    
    document = db_session.query(Document).get(doc_id)
    if not document:
        return []
    
    filepath = os.path.join(upload_folder, document.filename)
    return extract_tables_from_pdf(filepath)