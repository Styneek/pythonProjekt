import json
from route import Route

class RouteDataManager:
    def __init__(self, filepath):
        with open(filepath, encoding='utf-8') as f:
            self.routes = [Route(data) for data in json.load(f)]

    def filterRoutes(self, preference, region=None):
        result = []
        for route in self.routes:
            if region and route.region != region:
                continue
            if route.matchesPreference(preference):
                result.append(route)
        return result
