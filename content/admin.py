from django.contrib import admin
from .models import (
    Tag, CreativeContent, Rating, Comment, Like, Favorite, 
    UserProfile, UserActivity
)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_at')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(CreativeContent)
class CreativeContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'privacy', 'views_count', 'likes_count', 'created_at']
    list_filter = ['privacy', 'created_at', 'tags']
    search_fields = ['title', 'content', 'author__username']
    filter_horizontal = ['tags']
    readonly_fields = ['views_count', 'likes_count', 'favorites_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('基本信息', {
            'fields': ('title', 'content', 'author')
        }),
        ('设置', {
            'fields': ('is_public', 'tags', 'cover_image')
        }),
        ('二创信息', {
            'fields': ('original_content',),
            'classes': ('collapse',)
        }),
        ('时间信息', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )


@admin.register(Rating)
class RatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'score', 'created_at')
    list_filter = ('score', 'created_at')
    search_fields = ('user__username', 'content__title')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author', 'content', 'text_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('author__username', 'content__title', 'text')
    
    def text_preview(self, obj):
        return obj.text[:50] + '...' if len(obj.text) > 50 else obj.text
    text_preview.short_description = '评论预览'


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content__title')


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'content', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'content__title')


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'bio', 'location', 'birth_date']
    list_filter = ['location']
    search_fields = ['user__username', 'user__email', 'bio', 'location']


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ['user', 'action', 'content', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['user__username', 'description']
    readonly_fields = ['created_at']
    
    def has_add_permission(self, request):
        return False  # 不允许手动添加活动记录


# 自定义管理站点标题
admin.site.site_header = '创意内容管理平台'
admin.site.site_title = '管理后台'
admin.site.index_title = '欢迎使用创意内容管理平台'
