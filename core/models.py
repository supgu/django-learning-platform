from django.db import models
from django.contrib.auth.models import User


class SiteVisit(models.Model):
    """网站访问记录"""
    session_key = models.CharField(max_length=40, verbose_name='会话键')
    ip_address = models.GenericIPAddressField(verbose_name='IP地址')
    user_agent = models.TextField(blank=True, verbose_name='用户代理')
    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name='用户'
    )
    visited_at = models.DateTimeField(auto_now_add=True, verbose_name='访问时间')
    
    class Meta:
        verbose_name = '网站访问'
        verbose_name_plural = '网站访问记录'
        unique_together = ['session_key', 'ip_address']
    
    def __str__(self):
        return f'{self.ip_address} - {self.visited_at.date()}'


class SiteSettings(models.Model):
    """网站设置"""
    key = models.CharField(max_length=100, unique=True, verbose_name="设置键")
    value = models.TextField(verbose_name="设置值")
    description = models.CharField(max_length=200, blank=True, verbose_name="描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    class Meta:
        verbose_name = "网站设置"
        verbose_name_plural = "网站设置"
    
    def __str__(self):
        return f"{self.key}: {self.value[:50]}"


class Recommendation(models.Model):
    """推荐记录"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    content = models.ForeignKey('content.CreativeContent', on_delete=models.CASCADE, verbose_name="推荐内容")
    score = models.FloatField(verbose_name="推荐分数")
    reason = models.CharField(max_length=200, verbose_name="推荐理由")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="推荐时间")
    clicked = models.BooleanField(default=False, verbose_name="是否点击")
    
    class Meta:
        verbose_name = "推荐记录"
        verbose_name_plural = "推荐记录"
        ordering = ['-created_at']
        unique_together = ['user', 'content']
    
    def __str__(self):
        return f"推荐给 {self.user.username}: {self.content.title}"
