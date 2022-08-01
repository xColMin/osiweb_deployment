from django.urls import path
from user_aut import views

app_name = 'user_aut'

urlpatterns = [
    path('user_login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='logout'),
    ]