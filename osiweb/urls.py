"""osiweb URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from user_aut.views import *
from base.views import *
from consumer_care.views import *
from massive_creation.views import *
from osiviewer.views import *
from django.urls import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('massive_creation', include('massive_creation.urls')),
    path('consumer_care', include('consumer_care.urls')),
    path('osiviewer', include('osiviewer.urls')),
    path('user_aut', include('user_aut.urls')),
    path('base', include('base.urls')),
    path('', user_login, name='user_login'),
    path('index/', index, name='index'),
    path('logout/', user_logout, name='logout'),

    url(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    url(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
]
