from django.urls import path
from . import views

app_name = 'content'

urlpatterns = [
    # 内容列表和搜索
    path('', views.ContentListView.as_view(), name='content_list'),
    
    # 内容详情
    path('<int:pk>/', views.ContentDetailView.as_view(), name='content_detail'),
    
    # 内容创建、编辑、删除
    path('create/', views.ContentCreateView.as_view(), name='content_create'),
    path('<int:pk>/edit/', views.ContentUpdateView.as_view(), name='content_update'),
    path('<int:pk>/delete/', views.ContentDeleteView.as_view(), name='content_delete'),
    
    # 二创内容
    path('<int:pk>/derive/', views.DerivativeCreateView.as_view(), name='derive_content'),
    
    # 用户相关
    path('user/<str:username>/', views.UserProfileView.as_view(), name='user_profile'),
    
    # 评论和评分
    path('<int:content_id>/comment/', views.add_comment, name='add_comment'),
    path('<int:content_id>/rate/', views.add_rating, name='add_rating'),
    
    # 点赞和收藏 (AJAX)
    path('<int:content_id>/toggle-like/', views.toggle_like, name='toggle_like'),
    path('<int:content_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    
    # AI功能
    path('<int:content_id>/ai-comment/', views.generate_ai_content_comment, name='ai_comment'),
]