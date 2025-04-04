def filterTrails(trails, min_length, max_length, difficulty, region):
    result = []
    for trail in trails:
        length = float(trail['length_km'])
        diff = int(trail['difficulty'])
        trail_region = trail['region']

        if length < min_length or length > max_length:
            continue
        if difficulty is not None and diff != difficulty:
            continue
        if region is not None and trail_region != region:
            continue

        result.append(trail)

    return result