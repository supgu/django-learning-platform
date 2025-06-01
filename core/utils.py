from django.contrib.sessions.models import Session
from django.utils import timezone
from datetime import datetime, timedelta
from content.models import UserActivity


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def record_user_activity(user, action, content_object=None, description=''):
    """记录用户活动"""
    if user.is_authenticated:
        UserActivity.objects.create(
            user=user,
            action=action,
            content=content_object,
            description=description
        )


def get_today_visit_count(request):
    """获取今日访问次数（基于会话）"""
    today = timezone.now().date()
    
    # 获取今日所有活跃会话
    today_start = datetime.combine(today, datetime.min.time())
    today_end = datetime.combine(today, datetime.max.time())
    
    # 统计今日活跃会话数
    active_sessions = Session.objects.filter(
        expire_date__gte=timezone.now(),
        expire_date__range=[today_start, today_end]
    )
    
    return active_sessions.count()


def increment_visit_count(request):
    """增加访问计数"""
    # 检查会话中是否已记录今日访问
    today = timezone.now().date().isoformat()
    last_visit = request.session.get('last_visit_date')
    
    if last_visit != today:
        # 新的一天或首次访问
        request.session['last_visit_date'] = today
        request.session['visit_count'] = request.session.get('visit_count', 0) + 1
        return True
    return False


def get_user_visit_count(request):
    """获取用户访问次数"""
    return request.session.get('visit_count', 0)


def get_site_statistics():
    """获取网站统计信息"""
    from django.contrib.auth.models import User
    from content.models import CreativeContent, Comment, Like, Favorite
    
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    
    stats = {
        'total_users': User.objects.count(),
        'total_content': CreativeContent.objects.count(),
        'total_comments': Comment.objects.count(),
        'total_likes': Like.objects.count(),
        'total_favorites': Favorite.objects.count(),
        'new_users_this_week': User.objects.filter(
            date_joined__gte=week_ago
        ).count(),
        'new_content_this_week': CreativeContent.objects.filter(
            created_at__gte=week_ago
        ).count(),
        'active_users_today': UserActivity.objects.filter(
            created_at__date=today
        ).values('user').distinct().count(),
    }
    
    return stats