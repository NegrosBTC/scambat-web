from django.urls import path
from django.contrib.auth import views as auth_views
from . import views
from .views import ReportHistoryView, ToggleBlockView

urlpatterns = [
    path('', views.home, name='home'),
    path('signup/', views.signup, name='signup'),
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('leaderboard/', views.LeaderboardView.as_view(), name='leaderboard'),
    path('game/', views.game, name='game'),
    path('api/game/generate/', views.generate_game_message, name='generate_game_message'),
    path('api/game/generate-stream/', views.generate_game_message_stream, name='generate_game_message_stream'),
    path('api/game/submit/', views.submit_game_answer, name='submit_game_answer'),
    
    # Extension URLs
    path('extension/auth/', views.extension_auth, name='extension_auth'),
    path('api/extension/auth/', views.extension_auth, name='extension_auth_api'),
    path('api/extension/verify-auth/', views.verify_extension_auth, name='verify_extension_auth'),
    path('api/extension/report-scam/', views.report_scam_from_extension, name='report_scam_extension'),
    path('api/extension/check-url/', views.check_url_status, name='check_url_status'),
    
    # Report History URLs
    path('reports/history/', ReportHistoryView.as_view(), name='report_history'),
    path('reports/toggle-block/<int:report_id>/', ToggleBlockView.as_view(), name='toggle_block'),
]