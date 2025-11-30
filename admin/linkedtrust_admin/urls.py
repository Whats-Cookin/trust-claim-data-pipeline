"""
URL configuration for linkedtrust_admin project.
"""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    # Use /nodeadmin/ to avoid conflict with potential frontend /admin routes
    path('nodeadmin/', admin.site.urls),
]
