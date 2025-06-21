# cards/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('card/<slug:url_slug>/', views.card_detail, name='card_detail'),
    path('card/<slug:url_slug>/vcard/', views.download_vcard, name='download_vcard'),
    path('api/card/<slug:url_slug>/stats/', views.card_stats, name='card_stats'),

    # Admin statistics URLs
    path('admin/cards/statistics/', views.global_statistics, name='global_statistics'),
    path('admin/cards/<uuid:card_id>/statistics/', views.card_statistics, name='card_statistics'),
]