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
from django.urls import path, re_path, include
from .views import PlaceView, CommitView, OrderPayView, PaySearchView, CommentView

urlpatterns = [
    re_path(r'^place$', PlaceView.as_view(), name='place'),
    re_path(r'^commit$', CommitView.as_view(), name='commit'),
    re_path(r'^pay$', OrderPayView.as_view(), name='pay'),
    re_path(r'^checkorder$', PaySearchView.as_view(), name='checkorder'),
    re_path(r'^comment/(?P<order_id>.*)$', CommentView.as_view(), name='comment'),

]
