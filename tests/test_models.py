from models import Document, DocumentChunk
from datetime import datetime

def test_document_model():
    doc = Document(
        filename='test.pdf',
        original_name='Test Document',
        file_size=1024,
        upload_date=datetime.now(),
        language='ru'
    )
    assert doc.original_name == 'Test Document'
    assert doc.language == 'ru'

def test_document_chunk_model():
    chunk = DocumentChunk(
        text='Тестовый текст',
        page_number=1,
        chunk_index=0
    )
    assert chunk.page_number == 1
    assert 'Тестовый' in chunk.text