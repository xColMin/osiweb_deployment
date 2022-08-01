from django.urls import path
from . import views


app_name = 'massive_creation'

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
]