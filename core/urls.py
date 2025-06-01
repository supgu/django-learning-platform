from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    # 主页
    path('', views.home, name='home'),
    
    # 用户仪表板
    path('dashboard/', views.dashboard, name='dashboard'),
    
    # 用户功能页面
    path('my-content/', views.my_content, name='my_content'),
    path('my-favorites/', views.my_favorites, name='my_favorites'),
    path('data-analysis/', views.data_analysis, name='data_analysis'),
    path('account-settings/', views.account_settings, name='account_settings'),
    
    # 管理员页面
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/users/', views.admin_users, name='admin_users'),
    path('admin/content/', views.admin_contents, name='admin_content'),
    path('admin/toggle-content-status/<int:content_id>/', 
         views.admin_toggle_content_status, name='toggle_content_status'),
    
    # 通知
    path('notifications/', views.notifications, name='notifications'),
    
    # API
    path('api/my-comments/', views.my_comments_api, name='my_comments_api'),
]