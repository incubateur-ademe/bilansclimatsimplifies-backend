from django.urls import include, path
from rest_framework import routers
from rest_framework.authtoken import views as authviews
from . import views

router = routers.DefaultRouter()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns = [
    path("", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    path("api/v1/auth/", authviews.obtain_auth_token),
    path("api/v1/", include("api.urls")),
    path("csrf/", views.csrf),
]
