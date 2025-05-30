import re

class ReviewAnalyzer:
    @staticmethod
    def extract_rating(text):
        text = text.lower()

        patterns = [
            r'daj(?:ę|e|a|łem|ła|liśmy)?\s*(\d)\s*gwiazdek?',
            r'oceniam\s*(?:na)?\s*(\d)\s*gwiazdek?',
            r'(\d)\s*gwiazdek?',
            r'(\d)\s*gwiazdki',
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                value = int(match.group(1)) #zwraca pierwsza cyfre
                return value
    
    @staticmethod
    def detect_sentiment(text):
        text = text.lower()
        good = ['piękne', 'super', 'przyjemna', 'idealna']
        bad = ['niestety']

        if any(word in text for word in good):
            return 'pozytywny'
        elif any(word in text for word in bad):
            return 'negatywny'
        return 'neutralny'

    @classmethod
    def analyze_reviews(cls, reviews):
        analyzed = []
        for r in reviews:
            rating = cls.extract_rating(r['text'])
            sentiment = cls.detect_sentiment(r['text'])
            analyzed.append({
                'author': r.get('author'),
                'text': r['text'],
                'rating': rating,
                'sentiment': sentiment,
                'date': r.get('date')
            })
        return analyzed
