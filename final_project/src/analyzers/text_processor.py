import re

class TextProcessor:
    TIME_PATTERN = r'(\d+(?:\.\d+)?)\s*(?:h|godz|hours?)|(\d+)\s*(?:min|minut)'
    COORD_PATTERN = r'([NS]?\d{1,2}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)\s*,?\s*([EW]?\d{1,3}[°º]\d{1,2}[\'′]\d{1,2}[\"″]?)'
    WARNING_KEYWORDS = ["śliskie kamienie", "strome podejścia", "silne wiatry", "błotniste fragmenty"]
    ELEVATION_PATTERN = r'(\d{2,4})\s*m\s*n\.p\.m\.'
    GPS_PATTERN = r'(\d{1,2}°\d{1,2}′\d{1,2}″[NS])\s*,\s*(\d{1,3}°\d{1,2}′\d{1,2}″[EW])'


    @staticmethod
    def extract_time(description):
        matches = re.findall(TextProcessor.TIME_PATTERN, description.lower())
        total_minutes = 0
        for h, m in matches:
            if h:
                total_minutes += float(h.replace(',', '.')) * 60
            if m:
                total_minutes += int(m)
        return int(total_minutes) if total_minutes else None

    @staticmethod
    def extract_warnings(description):
        return [word for word in TextProcessor.WARNING_KEYWORDS if word in description.lower()]
 
    @staticmethod
    def extract_elevation(description):
        matches = re.findall(TextProcessor.ELEVATION_PATTERN, description)
        return [int(m) for m in matches]

    @staticmethod
    def extract_gps(description):
        return re.findall(TextProcessor.GPS_PATTERN, description)

   
