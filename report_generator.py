from datetime import datetime

def generate_search_report(results, query):
    timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    return generate_html_report(results, query, timestamp)

def generate_html_report(results, query, timestamp):
    documents = {}
    for result in results:
        doc_id = result['document'].id
        if doc_id not in documents:
            documents[doc_id] = {
                'document': result['document'],
                'results': []
            }
        documents[doc_id]['results'].append(result)
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Отчёт поиска - "{query}"</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
            .header {{ background: #f8f9fa; padding: 25px; border-radius: 8px; margin-bottom: 30px; }}
            .document-section {{ margin: 25px 0; padding: 20px; border: 1px solid #dee2e6; border-radius: 8px; }}
            .document-header {{ background: #e9ecef; padding: 15px; border-radius: 5px; margin-bottom: 15px; }}
            .result-item {{ margin: 15px 0; padding: 15px; background: #f8f9fa; border-radius: 5px; border-left: 4px solid #007bff; }}
            .highlight {{ background: #ffeb3b; font-weight: bold; padding: 2px 0; }}
            .metadata {{ margin-top: 30px; padding-top: 20px; border-top: 2px solid #dee2e6; color: #6c757d; }}
            .stats {{ background: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>📊 Отчёт поиска</h1>
            <div class="stats">
                <p><strong>Поисковый запрос:</strong> "{query}"</p>
                <p><strong>Всего результатов:</strong> {len(results)}</p>
                <p><strong>Найдено документов:</strong> {len(documents)}</p>
                <p><strong>Сгенерирован:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
        </div>
    """
    
    for doc_id, data in documents.items():
        document = data['document']
        doc_results = data['results']
        
        html_content += f"""
        <div class="document-section">
            <div class="document-header">
                <h2>📄 {document.original_name}</h2>
                <p>
                    <strong>Размер:</strong> {(document.file_size / 1024):.1f} КБ | 
                    <strong>Язык:</strong> {document.language} | 
                    <strong>Категория:</strong> {document.category or 'Не определена'} | 
                    <strong>Результатов:</strong> {len(doc_results)}
                </p>
            </div>
        """
        
        for result in doc_results:
            html_content += f"""
            <div class="result-item">
                <p><strong>Страница {result['chunk'].page_number}:</strong></p>
                <p>{result['context']}</p>
            </div>
            """
        
        html_content += "</div>"
    
    html_content += f"""
        <div class="metadata">
            <hr>
            <p>Сгенерировано PDF Search Engine</p>
            <p>Отчёт содержит {len(results)} результатов из {len(documents)} документов</p>
        </div>
    </body>
    </html>
    """
    
    filename = f"search_report_{timestamp}.html".replace(' ', '_')
    return html_content, filename
