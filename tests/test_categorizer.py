from categorizer import categorize_document

def test_categorize_russian_technical():
    text = "ГОСТ стандарт параметры технические характеристики"
    category, confidence = categorize_document(text)
    assert category == 'техника'
    assert confidence > 0

def test_categorize_empty_text():
    category, confidence = categorize_document('')
    assert category == 'unknown'
    assert confidence == 0