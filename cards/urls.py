# cards/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('card/<slug:url_slug>/', views.card_detail, name='card_detail'),
    path('card/<slug:url_slug>/vcard/', views.download_vcard, name='download_vcard'),
    path('api/card/<slug:url_slug>/stats/', views.card_stats, name='card_stats'),

    # Admin statistics URLs
    path('statistics/<uuid:card_id>/', views.simple_card_statistics, name='card_statistics'),

    path('register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),

    path('create-card/', views.create_business_card, name='create_business_card'),
    path('edit-card/<uuid:card_id>/', views.edit_business_card, name='edit_business_card'),
    path('delete-card/<uuid:card_id>/', views.delete_business_card, name='delete_business_card'),
]