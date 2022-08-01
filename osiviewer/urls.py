from django.urls import path
from . import views


app_name = 'osiviewer'

urlpatterns = [
    path('upload/', views.upload_file, name='upload'),
    path('run/', views.ov_run, name='run'),
    path('columns/', views.columns, name='columns'),
    path('next/', views.next, name='next'),
]