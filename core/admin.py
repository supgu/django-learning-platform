from django.contrib import admin
from .models import SiteVisit, SiteSettings, Recommendation


@admin.register(SiteVisit)
class SiteVisitAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'user', 'visited_at')
    list_filter = ('visited_at',)
    search_fields = ('ip_address', 'user__username', 'session_key')
    readonly_fields = ('visited_at',)
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加访问记录


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ['key', 'description', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['key', 'description']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ['user', 'content', 'score', 'reason', 'created_at', 'clicked']
    list_filter = ['created_at', 'clicked']
    search_fields = ['user__username', 'content__title', 'reason']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加推荐记录
