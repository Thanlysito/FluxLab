from django.contrib import admin
from django.urls import include, path

from farm import views as farm_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),  # selector ES/EN
    path("cuenta/registro/", farm_views.signup, name="signup"),
    path("cuenta/", include("django.contrib.auth.urls")),
    path("", include("farm.urls")),
]
