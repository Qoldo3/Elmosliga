from django.db.models.signals import post_save
from django.dispatch import receiver
from League.models import LeagueResult, Prediction
from League.services.scoring import calculate_points

@receiver(post_save, sender=LeagueResult)
def recalculate_points(sender, instance, **kwargs):
    """
    Recalculate points for all predictions when league result is saved.
    Uses bulk_update for better performance.
    """
    predictions = Prediction.objects.filter(league=instance.league).select_related(
        'predicted_team'
    )

    predictions_to_update = []
    for prediction in predictions:
        prediction.points = calculate_points(prediction, instance)
        predictions_to_update.append(prediction)
    
    if predictions_to_update:
        Prediction.objects.bulk_update(predictions_to_update, ['points'])
