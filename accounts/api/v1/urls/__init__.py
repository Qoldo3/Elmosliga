from django.urls import path, include

app_name = "accounts-v1"
urlpatterns = [
    path("", include("accounts.api.v1.urls.Accounts")),
    path("profile/", include("accounts.api.v1.urls.Profile")),
]
