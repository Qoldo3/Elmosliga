from django.urls import path
from .. import views

urlpatterns = [
    # Profile API
    path("", views.ProfileView.as_view(), name="profile"),
]
