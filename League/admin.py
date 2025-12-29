from django.contrib import admin
from League.models import League, Team, Prediction, LeagueResult

admin.site.register(League)
admin.site.register(Team)
admin.site.register(Prediction)
admin.site.register(LeagueResult)
