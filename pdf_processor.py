import os
import PyPDF2
from langdetect import detect, LangDetectException
import magic
from datetime import datetime
from categorizer import categorize_document

def allowed_file(filename, allowed_extensions):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def validate_pdf(filepath):
    try:
        file_type = magic.from_file(filepath, mime=True)
        return file_type == 'application/pdf'
    except:
        return False

def extract_text_pypdf2(filepath):
    text = ""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page_num, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
    except Exception as e:
        print(f"PyPDF2 extraction error: {e}")
    return text

def extract_text_from_pdf(filepath):
    text = extract_text_pypdf2(filepath)
    return text

def detect_language(text):
    if not text or len(text.strip()) < 50:
        return "unknown"
    
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"

def chunk_text(text, chunk_size=1000):
    chunks = []
    lines = text.split('\n')
    current_chunk = []
    current_size = 0
    current_page = 1
    
    for line in lines:
        if line.startswith('--- Page '):
            if current_chunk:
                chunks.append((' '.join(current_chunk), current_page))
                current_chunk = []
                current_size = 0
            
            try:
                current_page = int(line.split(' ')[2])
            except:
                current_page += 1
            continue
        
        words = line.split()
        if current_size + len(words) > chunk_size and current_chunk:
            chunks.append((' '.join(current_chunk), current_page))
            current_chunk = words
            current_size = len(words)
        else:
            current_chunk.extend(words)
            current_size += len(words)
    
    if current_chunk:
        chunks.append((' '.join(current_chunk), current_page))
    
    return chunks

def process_pdf(filepath, original_filename, db_session, Document, DocumentChunk):
    try:
        if not validate_pdf(filepath):
            raise ValueError("Файл не является корректным PDF")
        
        text = extract_text_from_pdf(filepath)
        if not text.strip():
            raise ValueError("Не удалось извлечь текст из PDF")
        
        language = detect_language(text)
        category, confidence = categorize_document(text)
        
        doc = Document(
            filename=os.path.basename(filepath),
            original_name=original_filename,
            file_size=os.path.getsize(filepath),
            upload_date=datetime.now(),
            language=language,
            category=category,
            file_metadata={
                'categorization_confidence': confidence,
                'word_count': len(text.split())
            }
        )
        
        db_session.add(doc)
        db_session.flush()
        
        chunks_data = chunk_text(text)
        for i, (chunk_data, page_num) in enumerate(chunks_data):
            chunk = DocumentChunk(
                document_id=doc.id,
                text=chunk_data,
                page_number=page_num,
                chunk_index=i
            )
            db_session.add(chunk)
        
        return doc
        
    except Exception as e:
        db_session.rollback()
        raise e