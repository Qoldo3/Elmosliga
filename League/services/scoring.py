def calculate_points(prediction, result):
    """
    Calculate points for a prediction based on the league result.
    User predicts one team, and points are awarded based on where that team finished (1st-6th place).
    Points come from the league settings which are unique per league.
    
    Args:
        prediction: Prediction object with predicted_team
        result: LeagueResult object with first_place through sixth_place
    
    Returns:
        int: Total points earned (0 if team didn't finish in top 6)
    """
    league = prediction.league
    predicted_team = prediction.predicted_team
    
    # Check which position the predicted team finished in
    if predicted_team == result.first_place:
        return league.first_place_points
    elif predicted_team == result.second_place:
        return league.second_place_points
    elif predicted_team == result.third_place:
        return league.third_place_points
    elif predicted_team == result.fourth_place:
        return league.fourth_place_points
    elif predicted_team == result.fifth_place:
        return league.fifth_place_points
    elif predicted_team == result.sixth_place:
        return league.sixth_place_points
    else:
        # Team didn't finish in top 6
        return 0