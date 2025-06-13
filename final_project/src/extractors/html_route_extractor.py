from bs4 import BeautifulSoup

class HTMLRouteExtractor:
    def __init__(self, html):
        self.soup = BeautifulSoup(html, "html.parser")

    def extract_route_params(self):
        table = self.soup.find("table", class_="route-params")
        if not table:
            return None
        params = {}
        for row in table.find_all("tr"):
            key = row.find_all("td")[0].text.strip().rstrip(':')
            value = row.find_all("td")[1].text.strip()
            params[key] = value
        return params

    def extract_reviews(self):
        reviews = []
        for review in self.soup.find_all("div", class_="user-review"):
            rating = review.find("span", class_="rating").text.strip()
            text = review.find("p").text.strip()
            reviews.append({"rating": rating, "text": text})
        return reviews
