from django.urls import path
from . import views


app_name = 'consumer_care'

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
]