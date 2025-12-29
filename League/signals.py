from django.db.models.signals import post_save
from django.dispatch import receiver
from League.models import LeagueResult, Prediction
from League.services.scoring import calculate_points

@receiver(post_save, sender=LeagueResult)
def recalculate_points(sender, instance, **kwargs):
    predictions = Prediction.objects.filter(league=instance.league)

    for prediction in predictions:
        prediction.points = calculate_points(prediction, instance)
        prediction.save(update_fields=["points"])
