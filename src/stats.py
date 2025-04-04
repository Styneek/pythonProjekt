from functools import reduce

def averageTemperature(data):
    temps = list(map(lambda tempInfo: float(tempInfo['avg_temp']), data))
    return reduce(lambda total, temp: total + temp, temps) / len(temps) if temps else 0

def precipitation(data):
    values = list(map(lambda valueInfo: float(valueInfo['precipitation']), data))
    return reduce(lambda total, temp: total + temp, values) if values else 0

def sunnyDays(data, sunMin):
    sunny = list(map(lambda sunnyInfo: float(sunnyInfo['sunshine_hours']) >= sunMin, data))
    return reduce(lambda total, temp: total + temp, sunny) if sunny else 0