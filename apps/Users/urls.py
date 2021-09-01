"""day_project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
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
from django.urls import re_path
from django.contrib.auth.decorators import login_required
from apps.Users import views
from apps.Users.views import RedirectLine, ActiveView, LoginView, UserOrder, UserInfo, UserAddress, LogOut

urlpatterns = [
    # re_path(r'^register$', views.register, name='register'),
    # re_path(r'^login$', views.login, name='login'),
    re_path(r'^register$', RedirectLine.as_view(), name='register'),
    re_path(r'^active/(?P<token>.*)$', ActiveView.as_view(), name='active'),
    re_path(r'^login$', LoginView.as_view(), name='login'),
    re_path(r'^center$', UserInfo.as_view(), name='userinfo'),
    re_path(r'^userorder/(?P<page>.*)$', UserOrder.as_view(), name='userorder'),
    re_path(r'^address$', UserAddress.as_view(), name='useraddress'),
    re_path(r'^logout$', LogOut.as_view(), name='logout'),
]