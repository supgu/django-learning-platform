from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from datetime import datetime, timedelta
import json

from .models import SiteVisit, SiteSettings, Recommendation
from content.models import CreativeContent, UserActivity, Tag


def home(request):
    """首页视图"""
    # 记录访问
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    # 获取客户端IP
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    # 使用 get_or_create 避免重复记录
    today = timezone.now().date()
    visit, created = SiteVisit.objects.get_or_create(
        session_key=session_key,
        ip_address=ip,
        defaults={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'user': request.user if request.user.is_authenticated else None
        }
    )
    
    # 如果记录已存在但不是今天创建的，更新访问时间
    if not created and visit.visited_at.date() != today:
        visit.visited_at = timezone.now()
        visit.save()
    
    # 获取今日访问统计
    today_visits = SiteVisit.objects.filter(visited_at__date=today).count()
    total_visits = SiteVisit.objects.count()
    
    # 获取总内容数和用户数
    total_contents = CreativeContent.objects.filter(privacy='public').count()
    total_users = User.objects.count()
    
    # 获取热门内容
    popular_contents = CreativeContent.objects.filter(
        privacy='public'
    ).annotate(
        total_score=Count('likes') + Count('favorites') * 2
    ).order_by('-total_score', '-created_at')[:6]
    
    # 获取最新内容
    latest_contents = CreativeContent.objects.filter(
        privacy='public'
    ).order_by('-created_at')[:6]
    
    # 获取推荐内容（仅登录用户）
    recommended_contents = []
    if request.user.is_authenticated:
        try:
            from content.utils import get_recommendations_for_user
            recommended_contents = get_recommendations_for_user(request.user)[:4]
        except Exception as e:
            print(f"推荐系统错误: {e}")
    
    # 获取热门标签
    popular_tags = Tag.objects.annotate(
        content_count=Count('creativecontent')
    ).filter(content_count__gt=0).order_by('-content_count')[:10]
    
    # 统计数据
    stats = {
        'total_contents': total_contents,
        'total_users': total_users,
        'today_visits': today_visits,
        'total_visits': total_visits,
    }
    
    context = {
        'stats': stats,
        'today_visits': today_visits,
        'total_visits': total_visits,
        'popular_contents': popular_contents,
        'latest_contents': latest_contents,
        'recommended_contents': recommended_contents,
        'popular_tags': popular_tags,
    }
    
    return render(request, 'core/home.html', context)


@login_required
def dashboard(request):
    """用户仪表板"""
    user = request.user
    
    # 用户统计
    user_contents = CreativeContent.objects.filter(author=user)
    total_contents = user_contents.count()
    total_views = sum(content.views_count for content in user_contents)
    total_likes = sum(content.likes_count for content in user_contents)
    total_favorites = sum(content.favorites_count for content in user_contents)
    
    # 最近活动
    recent_activities = UserActivity.objects.filter(
        user=user
    ).order_by('-created_at')[:10]
    
    # 最近内容
    recent_contents = user_contents.order_by('-created_at')[:5]
    
    # 推荐内容
    try:
        from content.utils import get_recommendations_for_user
        recommendations = get_recommendations_for_user(user)[:5]
    except Exception as e:
        recommendations = []
        print(f"推荐系统错误: {e}")
    
    context = {
        'total_contents': total_contents,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_favorites': total_favorites,
        'recent_activities': recent_activities,
        'recent_contents': recent_contents,
        'recommendations': recommendations,
    }
    
    return render(request, 'core/dashboard.html', context)


def is_superuser(user):
    """检查是否为超级用户"""
    return user.is_superuser


@user_passes_test(is_superuser)
def admin_dashboard(request):
    """管理员仪表板"""
    # 基础统计
    total_users = User.objects.count()
    total_contents = CreativeContent.objects.count()
    total_visits = SiteVisit.objects.count()
    
    # 今日统计
    today = timezone.now().date()
    today_visits = SiteVisit.objects.filter(visited_at__date=today).count()
    today_contents = CreativeContent.objects.filter(created_at__date=today).count()
    today_users = User.objects.filter(date_joined__date=today).count()
    
    # 最近7天访问趋势
    visit_trend = []
    for i in range(7):
        date = today - timedelta(days=i)
        count = SiteVisit.objects.filter(visited_at__date=date).count()
        visit_trend.append({
            'date': date.strftime('%m-%d'),
            'count': count
        })
    visit_trend.reverse()
    
    # 最活跃用户
    active_users = User.objects.annotate(
        content_count=Count('creativecontent'),
        activity_count=Count('useractivity')
    ).filter(
        content_count__gt=0
    ).order_by('-content_count', '-activity_count')[:10]
    
    # 热门内容
    popular_contents = CreativeContent.objects.annotate(
        total_score=Count('likes') + Count('favorites') * 2
    ).order_by('-total_score')[:10]
    
    # 最近活动
    recent_activities = UserActivity.objects.select_related(
        'user', 'content'
    ).order_by('-created_at')[:20]
    
    # 用户活动统计
    activity_stats = UserActivity.objects.values('action').annotate(
        count=Count('id')
    ).order_by('-count')
    
    context = {
        'total_users': total_users,
        'total_contents': total_contents,
        'total_visits': total_visits,
        'today_visits': today_visits,
        'today_contents': today_contents,
        'today_users': today_users,
        'visit_trend': json.dumps(visit_trend),
        'active_users': active_users,
        'popular_contents': popular_contents,
        'recent_activities': recent_activities,
        'activity_stats': activity_stats,
    }
    
    return render(request, 'core/admin_dashboard.html', context)


@user_passes_test(is_superuser)
def admin_users(request):
    """管理员用户管理"""
    search_query = request.GET.get('search', '')
    users = User.objects.all()
    
    if search_query:
        users = users.filter(
            Q(username__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # 添加统计信息
    users = users.annotate(
        content_count=Count('creativecontent'),
        activity_count=Count('useractivity')
    ).order_by('-date_joined')
    
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
    }
    
    return render(request, 'core/admin_users.html', context)


@user_passes_test(is_superuser)
def admin_contents(request):
    """管理员内容管理"""
    search_query = request.GET.get('search', '')
    privacy_filter = request.GET.get('privacy', '')
    
    contents = CreativeContent.objects.select_related('author').all()
    
    if search_query:
        contents = contents.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )
    
    if privacy_filter:
        contents = contents.filter(privacy=privacy_filter)
    
    contents = contents.order_by('-created_at')
    
    paginator = Paginator(contents, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'privacy_filter': privacy_filter,
    }
    
    return render(request, 'core/admin_contents.html', context)


@require_http_methods(["POST"])
@user_passes_test(is_superuser)
def admin_toggle_content_status(request, content_id):
    """切换内容状态"""
    try:
        content = CreativeContent.objects.get(id=content_id)
        # 这里可以添加内容状态切换逻辑
        # 比如添加一个 is_active 字段
        return JsonResponse({'success': True})
    except CreativeContent.DoesNotExist:
        return JsonResponse({'success': False, 'error': '内容不存在'})


@login_required
def notifications(request):
    """通知页面"""
    # 这里可以实现通知系统
    # 暂时返回空页面
    context = {
        'notifications': []
    }
    return render(request, 'core/notifications.html', context)


@login_required
def my_content(request):
    """我的内容页面"""
    user = request.user
    search_query = request.GET.get('search', '')
    privacy_filter = request.GET.get('privacy', '')
    
    contents = CreativeContent.objects.filter(author=user)
    
    if search_query:
        contents = contents.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    if privacy_filter:
        contents = contents.filter(privacy=privacy_filter)
    
    contents = contents.order_by('-created_at')
    
    paginator = Paginator(contents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'privacy_filter': privacy_filter,
        'total_contents': contents.count(),
    }
    
    return render(request, 'core/my_content.html', context)


@login_required
def my_favorites(request):
    """我的收藏页面"""
    user = request.user
    search_query = request.GET.get('search', '')
    
    # 获取用户收藏的内容
    favorites = CreativeContent.objects.filter(
        favorites__user=user
    ).distinct()
    
    if search_query:
        favorites = favorites.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(author__username__icontains=search_query)
        )
    
    favorites = favorites.order_by('-favorites__created_at')
    
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'total_favorites': favorites.count(),
    }
    
    return render(request, 'core/my_favorites.html', context)


@login_required
def data_analysis(request):
    """数据分析页面"""
    user = request.user
    
    # 用户内容统计
    user_contents = CreativeContent.objects.filter(author=user)
    total_contents = user_contents.count()
    total_views = sum(content.views_count for content in user_contents)
    total_likes = sum(content.likes_count for content in user_contents)
    total_favorites = sum(content.favorites_count for content in user_contents)
    
    # 最近30天的数据趋势
    today = timezone.now().date()
    trend_data = []
    for i in range(30):
        date = today - timedelta(days=i)
        daily_contents = user_contents.filter(created_at__date=date).count()
        trend_data.append({
            'date': date.strftime('%m-%d'),
            'contents': daily_contents
        })
    trend_data.reverse()
    
    # 内容类型分布（如果有分类字段）
    privacy_stats = user_contents.values('privacy').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # 最受欢迎的内容
    popular_contents = user_contents.annotate(
        total_score=Count('likes') + Count('favorites') * 2
    ).order_by('-total_score')[:5]
    
    context = {
        'total_contents': total_contents,
        'total_views': total_views,
        'total_likes': total_likes,
        'total_favorites': total_favorites,
        'trend_data': json.dumps(trend_data),
        'privacy_stats': privacy_stats,
        'popular_contents': popular_contents,
    }
    
    return render(request, 'core/data_analysis.html', context)


@login_required
def account_settings(request):
    """账号设置页面"""
    user = request.user
    
    if request.method == 'POST':
        # 处理表单提交
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        email = request.POST.get('email', '')
        
        # 验证邮箱唯一性
        if email != user.email and User.objects.filter(email=email).exists():
            messages.error(request, '该邮箱已被其他用户使用')
        else:
            user.first_name = first_name
            user.last_name = last_name
            user.email = email
            user.save()
            messages.success(request, '账号信息更新成功')
    
    context = {
        'user': user,
    }
    
    return render(request, 'core/account_settings.html', context)


@login_required
def my_comments_api(request):
    """获取用户收到的评论API"""
    try:
        # 获取用户创建的内容
        user_contents = CreativeContent.objects.filter(author=request.user)
        
        # 获取这些内容的评论（假设有Comment模型）
        # 由于当前项目中可能没有Comment模型，我们先返回模拟数据
        comments_data = [
            {
                'id': 1,
                'author': '用户A',
                'text': '这个内容很棒！',
                'created_at': '2024-01-15 10:30',
                'content_id': 1,
                'content_title': '示例内容标题'
            },
            {
                'id': 2,
                'author': '用户B',
                'text': '学到了很多，谢谢分享！',
                'created_at': '2024-01-14 15:20',
                'content_id': 2,
                'content_title': '另一个内容标题'
            }
        ]
        
        return JsonResponse({
            'success': True,
            'comments': comments_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
