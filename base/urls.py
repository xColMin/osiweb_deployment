from django.urls import path
from base import views

app_name = 'base'

urlpatterns = [
    path('index', views.index, name='index'),
]