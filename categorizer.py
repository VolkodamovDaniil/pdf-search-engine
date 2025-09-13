KEYWORD_CATEGORIES = {
    'science': ['theory', 'hypothesis', 'experiment', 'research', 'study', 'scientific', 'physics', 'chemistry', 'biology'],
    'technical': ['gost', 'standard', 'parameter', 'technical', 'specification', 'protocol', 'engineering', 'design', 'scheme'],
    'legal': ['law', 'article', 'legal', 'contract', 'regulation', 'clause', 'court', 'judge', 'legislation'],
    'business': ['report', 'financial', 'market', 'analysis', 'strategy', 'business', 'company', 'profit', 'investment'],
    'medical': ['patient', 'treatment', 'diagnosis', 'medical', 'health', 'hospital', 'disease', 'therapy', 'medicine'],
    'education': ['education', 'school', 'university', 'student', 'teacher', 'course', 'learning', 'training'],
    'technology': ['software', 'hardware', 'computer', 'programming', 'algorithm', 'data', 'digital', 'internet']
}

RU_KEYWORD_CATEGORIES = {
    'наука': ['теория', 'гипотеза', 'эксперимент', 'исследование', 'научный', 'анализ', 'физика', 'химия', 'биология'],
    'техника': ['гост', 'стандарт', 'параметр', 'технический', 'спецификация', 'протокол', 'инженерный', 'чертеж', 'схема'],
    'юриспруденция': ['закон', 'статья', 'правовой', 'договор', 'регулирование', 'пункт', 'суд', 'судья', 'законодательство'],
    'бизнес': ['отчет', 'финансовый', 'рынок', 'анализ', 'стратегия', 'план', 'бизнес', 'компания', 'прибыль'],
    'медицина': ['пациент', 'лечение', 'диагноз', 'медицинский', 'здоровье', 'больница', 'болезнь', 'терапия'],
    'образование': ['образование', 'школа', 'университет', 'студент', 'преподаватель', 'курс', 'обучение'],
    'технологии': ['программное', 'аппаратное', 'компьютер', 'программирование', 'алгоритм', 'данные', 'цифровой', 'интернет']
}

def categorize_document(text):
    if not text:
        return 'unknown'
    
    text_lower = text.lower()
    scores = {}
    
    for category, keywords in RU_KEYWORD_CATEGORIES.items():
        scores[category] = sum(1 for keyword in keywords if keyword in text_lower)
    
    if max(scores.values()) == 0:
        for category, keywords in KEYWORD_CATEGORIES.items():
            scores[category] = sum(1 for keyword in keywords if keyword in text_lower)
    
    if max(scores.values()) > 0:
        best_category = max(scores.items(), key=lambda x: x[1])[0]
        confidence = scores[best_category] / len(text_lower.split()) * 1000
        return best_category, min(confidence, 100)
    return 'other', 0