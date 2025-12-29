from django.apps import AppConfig

class LeagueConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "League"

    def ready(self):
        import League.signals