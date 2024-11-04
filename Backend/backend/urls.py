# main_project/urls.py

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),  # Admin route
    path('api/', include('app.urls')),  # API routes from the app `backend`
]
