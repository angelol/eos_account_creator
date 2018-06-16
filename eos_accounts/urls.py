"""eos_accounts URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.views.generic.base import TemplateView
from buy.views import choose, submit_account_name, keys

urlpatterns = [
    path('', TemplateView.as_view(template_name='buy/index.html'), name="home"),
    path('choose/', choose, name='choose'),
    path('submit_account_name/', submit_account_name, name='submit_account_name'),
    path('keys/', keys, name='keys'),

]
