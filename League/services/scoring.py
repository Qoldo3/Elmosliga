def calculate_points(prediction, result):
    """
    Calculate points for a prediction based on the league result.
    Points are awarded for each correct position and come from the league settings.
    
    Args:
        prediction: Prediction object with first/second/third_place_team
        result: LeagueResult object with first/second/third_place
    
    Returns:
        int: Total points earned
    """
    score = 0
    league = prediction.league

    # Award points for correct first place
    if prediction.first_place_team == result.first_place:
        score += league.first_place_points

    # Award points for correct second place
    if prediction.second_place_team == result.second_place:
        score += league.second_place_points

    # Award points for correct third place
    if prediction.third_place_team == result.third_place:
        score += league.third_place_points

    return score