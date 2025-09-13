from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename
from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker, scoped_session
import os
import io
import zipfile
import fitz

from config import Config
from models import Base, Document, DocumentChunk
from pdf_processor import process_pdf, allowed_file
from table_extractor import export_document_tables
from report_generator import generate_search_report

app = Flask(__name__)
app.config.from_object(Config)

engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
Session = scoped_session(sessionmaker(bind=engine))

Base.metadata.create_all(engine)

@app.teardown_appcontext
def shutdown_session(exception=None):
    Session.remove()

@app.route('/')
def index():
    session = Session()
    try:
        documents = session.query(Document).order_by(Document.upload_date.desc()).all()
        return render_template('index.html', documents=documents)
    except Exception as e:
        return render_template('index.html', documents=[])
    finally:
        Session.remove()

@app.route('/upload', methods=['POST'])
def upload_file():
    
    if 'file' not in request.files:
        flash('Файл не выбран')
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран')
        return redirect(url_for('index'))
    
    if file and allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
        except Exception as e:
            flash(f'Ошибка сохранения файла: {str(e)}')
            return redirect(url_for('index'))
        
        session = Session()
        try:
            doc = process_pdf(filepath, file.filename, session, Document, DocumentChunk)
            session.commit()
            flash(f'Файл "{file.filename}" успешно загружен и обработан!')
        except Exception as e:
            session.rollback()
            if os.path.exists(filepath):
                os.remove(filepath)
            flash(f'Ошибка обработки файла: {str(e)}')
        finally:
            Session.remove()
        
        return redirect(url_for('index'))
    
    flash('Неверный тип файла. Загружайте только PDF файлы.')
    return redirect(url_for('index'))

@app.route('/export/tables/<int:doc_id>')
def export_tables(doc_id):
    session = Session()
    try:
        document = session.query(Document).get(doc_id)
        if not document:
            flash('Документ не найден')
            return redirect(url_for('index'))
        
        tables = export_document_tables(doc_id, session, app.config['UPLOAD_FOLDER'])
        
        if not tables:
            flash('В документе не найдено таблиц')
            return redirect(url_for('view_document', doc_id=doc_id))
        
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            for table in tables:
                zip_file.writestr(table['filename'], table['content'])
        
        zip_buffer.seek(0)
        
        return send_file(
            zip_buffer,
            mimetype='application/zip',
            as_attachment=True,
            download_name=f"{document.original_name}_tables.zip"
        )
        
    except Exception as e:
        flash('Ошибка экспорта таблиц')
        return redirect(url_for('view_document', doc_id=doc_id))
    finally:
        Session.remove()

@app.route('/export/global-report')
def export_global_report():
    query = request.args.get('q', '')
    
    session = Session()
    try:
        if not query:
            flash('Поисковый запрос не указан')
            return redirect(url_for('search'))
        
        search_results = (session.query(DocumentChunk, Document)
                        .join(Document)
                        .filter(func.lower(DocumentChunk.text).like(f'%{query.lower()}%'))
                        .order_by(Document.original_name, DocumentChunk.page_number)
                        .all())
        
        if not search_results:
            flash('Нет результатов для экспорта')
            return redirect(url_for('search', q=query))
        
        processed_results = []
        for chunk, document in search_results:
            context = get_text_context(chunk.text, query, context_chars=50)
            highlighted_context = highlight_text(context, query)
            processed_results.append({
                'chunk': chunk,
                'document': document,
                'context': highlighted_context
            })
        
        report_content, filename = generate_search_report(processed_results, query)
        
        response = app.response_class(
            response=report_content,
            mimetype='text/html',
        )
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
            
    except Exception as e:
        flash('Ошибка генерации отчета')
        return redirect(url_for('search', q=query))
    finally:
        Session.remove()

def case_insensitive_search(query):
    return func.lower(DocumentChunk.text).ilike(f'%{query.lower()}%')

def get_text_context(text, query, context_chars=50):
    if not text or not query:
        return text[:200] + '...' if len(text) > 200 else text
    
    text_lower = text.lower()
    query_lower = query.lower()
    pos = text_lower.find(query_lower)
    
    if pos == -1:
        return text[:200] + '...' if len(text) > 200 else text
    
    sentence_start = max(0, text.rfind('.', 0, pos) + 1)
    if sentence_start > 0 and sentence_start > pos - context_chars:
        sentence_start = max(0, pos - context_chars)
    
    sentence_end = text.find('.', pos + len(query))
    if sentence_end == -1:
        sentence_end = len(text)
    else:
        sentence_end += 1
    
    if sentence_end < pos + len(query) + context_chars:
        sentence_end = min(len(text), pos + len(query) + context_chars)
    
    start_pos = sentence_start
    end_pos = sentence_end
    
    prefix = '... ' if start_pos > 0 else ''
    suffix = ' ...' if end_pos < len(text) else ''
    
    context = text[start_pos:end_pos].strip()
    
    return prefix + context + suffix

def highlight_text(text, query):
    if not text or not query:
        return text
    
    text_lower = text.lower()
    query_lower = query.lower()
    pos = text_lower.find(query_lower)
    
    if pos == -1:
        return text
    
    actual_query = text[pos:pos + len(query)]
    
    highlighted = text.replace(actual_query, f'<span class="search-highlight">{actual_query}</span>', 1)
    
    return highlighted

@app.route('/search')
def search():
    query = request.args.get('q', '').strip()
    
    session = Session()
    try:
        if not query:
            return render_template('search.html', results=[], query='')
        
        search_condition = case_insensitive_search(query)
        
        results = (session.query(DocumentChunk, Document)
                  .join(Document)
                  .filter(search_condition)
                  .order_by(Document.original_name, DocumentChunk.page_number)
                  .all())
        
        processed_results = []
        for chunk, document in results:
            context = get_text_context(chunk.text, query, context_chars=50)
            highlighted_context = highlight_text(context, query)
            processed_results.append({
                'chunk': chunk,
                'document': document,
                'context': highlighted_context
            })
        
        return render_template('search.html', results=processed_results, query=query)
        
    except Exception as e:
        return render_template('search.html', results=[], query=query)
    finally:
        Session.remove()

@app.route('/document/<int:doc_id>')
def view_document(doc_id):
    session = Session()
    try:
        document = session.query(Document).get(doc_id)
        if not document:
            flash('Документ не найден')
            return redirect(url_for('index'))
        
        query = request.args.get('q', '')
        search_results = []
        processed_results = []
        highlighting_text = ""
        
        if query:
            search_results = (session.query(DocumentChunk, Document)
                            .join(Document)
                            .filter(
                                DocumentChunk.document_id == doc_id,
                                func.lower(DocumentChunk.text).like(f'%{query.lower()}%')
                            )
                            .order_by(DocumentChunk.page_number)
                            .all())
            
            for chunk, document in search_results:
                context = get_text_context(chunk.text, query, context_chars=50)
                highlighted_context = highlight_text(context, query)
                processed_results.append({
                    'chunk': chunk,
                    'document': document,
                    'context': highlighted_context
                })

            highlighting_text = query
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        total_pages = get_pdf_page_count(filepath)
        
        result_pages = sorted(list(set(chunk.page_number for chunk, doc in search_results))) if search_results else []
        
        return render_template('pdf_viewer.html', 
                             document=document, 
                             search_results=processed_results,
                             query=query,
                             highlight_text=highlighting_text,
                             total_pages=total_pages,
                             result_pages=result_pages)
        
    except Exception as e:
        flash('Ошибка загрузки документа. Пожалуйста, попробуйте снова.')
        return redirect(url_for('index'))
    finally:
        Session.remove()

@app.route('/delete/<int:doc_id>', methods=['POST'])
def delete_document(doc_id):
    session = Session()
    try:
        document = session.query(Document).get(doc_id)
        if not document:
            flash('Документ не найден')
            return redirect(url_for('index'))
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], document.filename)
        
        session.query(DocumentChunk).filter(DocumentChunk.document_id == doc_id).delete()
        
        session.delete(document)
        session.commit()
        
        if os.path.exists(filepath):
            os.remove(filepath)
        
        flash(f'Документ "{document.original_name}" успешно удален!')
        
    except Exception as e:
        session.rollback()
        flash('Ошибка удаления документа. Пожалуйста, попробуйте снова.')
    finally:
        Session.remove()
    
    return redirect(url_for('index'))

@app.route('/pdf/<filename>')
def serve_pdf(filename):
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(filepath):
        response = send_file(filepath, mimetype='application/pdf')
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        return response
    flash('PDF файл не найден')
    return redirect(url_for('index'))

def get_pdf_page_count(filepath):
    try:
        with fitz.open(filepath) as doc:
            return len(doc)
    except Exception as e:
        return 1

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)