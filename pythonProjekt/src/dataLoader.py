import json

def getFile(file):
    with open(file, 'r', encoding='utf-8') as fileName:
        return json.load(fileName)