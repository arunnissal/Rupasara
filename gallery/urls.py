from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('search/', views.search_images, name='search'),
    path('favorites/', views.favorites, name='favorites'),
    path('ai/', views.ai_studio, name='ai_studio'),
]
