from pdf_processor import allowed_file, chunk_text

def test_allowed_file():
    assert allowed_file('test.pdf', {'pdf'}) == True
    assert allowed_file('test.txt', {'pdf'}) == False
    assert allowed_file('test.PDF', {'pdf'}) == True

def test_chunk_text_basic():
    text = "Это простой текст для тестирования разбивки на чанки"
    chunks = chunk_text(text, chunk_size=5)
    assert len(chunks) > 0

def test_chunk_text_empty():
    chunks = chunk_text('', chunk_size=100)
    assert len(chunks) == 0