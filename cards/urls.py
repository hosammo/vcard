# cards/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('card/<slug:url_slug>/', views.card_detail, name='card_detail'),
    path('card/<slug:url_slug>/vcard/', views.download_vcard, name='download_vcard'),
    path('api/card/<slug:url_slug>/stats/', views.card_stats, name='card_stats'),

    # Statistics URLs
    path('statistics/<uuid:card_id>/',         views.simple_card_statistics, name='card_statistics'),
    path('statistics/<uuid:card_id>/export/',  views.export_statistics_csv,  name='export_statistics_csv'),

    # Interaction tracking API
    path('api/track-interaction/', views.track_interaction, name='track_interaction'),

    path('register/', views.user_register, name='user_register'),
    path('login/', views.user_login, name='user_login'),
    path('logout/', views.user_logout, name='user_logout'),
    path('dashboard/', views.user_dashboard, name='user_dashboard'),
    path('profile/', views.edit_profile, name='edit_profile'),

    # Password reset (Django built-in views, custom templates)
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='auth/password_reset.html',
             email_template_name='auth/emails/password_reset_email.txt',
             subject_template_name='auth/emails/password_reset_subject.txt',
             success_url='/password-reset/done/',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='auth/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('password-reset/confirm/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='auth/password_reset_confirm.html',
             success_url='/password-reset/complete/',
         ),
         name='password_reset_confirm'),
    path('password-reset/complete/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='auth/password_reset_complete.html',
         ),
         name='password_reset_complete'),

    path('upgrade/',                          views.upgrade_plan,        name='upgrade_plan'),
    path('upgrade/pay/<str:plan>/',           views.simulate_payment,    name='simulate_payment'),
    path('upgrade/downgrade/',                views.simulate_downgrade,  name='simulate_downgrade'),

    path('billing/',                          views.billing,             name='billing'),

    path('card/<slug:url_slug>/contact/', views.submit_lead,   name='submit_lead'),
    path('leads/',                        views.leads_inbox,   name='leads_inbox'),

    # Team management
    path('team/',                              views.team_management,   name='team_management'),
    path('team/invite/',                       views.invite_member,     name='invite_member'),
    path('team/remove/<int:member_id>/',       views.remove_member,     name='remove_member'),
    path('team/role/<int:member_id>/',         views.change_member_role,name='change_member_role'),
    path('invite/<uuid:token>/',               views.accept_invite,     name='accept_invite'),

    path('create-card/', views.create_business_card, name='create_business_card'),
    path('edit-card/<uuid:card_id>/', views.edit_business_card, name='edit_business_card'),
    path('delete-card/<uuid:card_id>/', views.delete_business_card, name='delete_business_card'),
]