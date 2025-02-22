from django.urls import path
from . import views
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import register

urlpatterns = [
    path('upload_bot/', views.upload_bot, name='upload_bot'),
    path('auth/register/', register, name='register'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    path('',views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('my_bots/', views.my_bots, name='my_bots'),
    path('replay/<int:match_id>/', views.replay, name='replay'),
    path('deploy_bot/', views.deploy_bot, name='deploy_bot'),
    path('contact_us/', views.contact_us, name='contact_us'),
    path('documentation/', views.documentation, name='documentation'),
    path('test_run/',views.test_run,name="test_run"),
    path('test_replay/<int:match_id>/', views.test_replay, name='test_replay'),
    path('test_match_results/<int:bot_id>/', views.test_match_results, name='test_run_response2'),
]