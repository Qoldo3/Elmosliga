POINTS = {
    "first": 10,
    "second": 5,
    "third": 3,
}

def calculate_points(prediction, result):
    score = 0

    if prediction.first_place == result.first_place:
        score += POINTS["first"]
    if prediction.second_place == result.second_place:
        score += POINTS["second"]
    if prediction.third_place == result.third_place:
        score += POINTS["third"]

    return score
