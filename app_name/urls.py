# app_name/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('similar-images/', views.similar_images, name='similar_images'),
]
