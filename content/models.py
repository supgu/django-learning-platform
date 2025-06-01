from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from PIL import Image


class Tag(models.Model):
    """标签模型"""
    name = models.CharField(max_length=50, unique=True, verbose_name="标签名")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "标签"
        verbose_name_plural = "标签"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """内容分类模型"""
    name = models.CharField(max_length=100, unique=True, verbose_name="分类名称")
    description = models.TextField(blank=True, verbose_name="分类描述")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    
    class Meta:
        verbose_name = "分类"
        verbose_name_plural = "分类"
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    @property
    def content_count(self):
        return self.creativecontent_set.filter(privacy='public').count()


class CreativeContent(models.Model):
    """创意内容模型"""
    PRIVACY_CHOICES = [
        ('public', '公开'),
        ('private', '私有'),
    ]
    
    title = models.CharField(max_length=200, verbose_name="标题")
    content = models.TextField(verbose_name="内容")
    summary = models.TextField(max_length=500, blank=True, verbose_name="摘要")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="作者")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="分类")
    tags = models.ManyToManyField(Tag, blank=True, verbose_name="标签")
    privacy = models.CharField(max_length=10, choices=PRIVACY_CHOICES, default='public', verbose_name="隐私设置")
    cover_image = models.ImageField(upload_to='covers/', blank=True, null=True, verbose_name="封面图")
    
    # 统计字段
    views_count = models.PositiveIntegerField(default=0, verbose_name="浏览量")
    likes_count = models.PositiveIntegerField(default=0, verbose_name="点赞数")
    comments_count = models.PositiveIntegerField(default=0, verbose_name="评论数")
    favorites_count = models.PositiveIntegerField(default=0, verbose_name="收藏数")
    
    # 时间字段
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="创建时间")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="更新时间")
    
    # 原创内容引用（用于续写功能）
    original_content = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                                       related_name='derivatives', verbose_name="原创内容")
    
    class Meta:
        verbose_name = "创意内容"
        verbose_name_plural = "创意内容"
        ordering = ['-created_at']
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('content:content_detail', kwargs={'pk': self.pk})
    
    def get_average_rating(self):
        """获取平均评分"""
        ratings = self.ratings.all()
        if ratings:
            return sum([r.score for r in ratings]) / len(ratings)
        return 0
    
    def get_rating_count(self):
        """获取评分数量"""
        return self.ratings.count()
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # 压缩封面图片
        if self.cover_image:
            img = Image.open(self.cover_image.path)
            if img.height > 300 or img.width > 300:
                output_size = (300, 300)
                img.thumbnail(output_size)
                img.save(self.cover_image.path)


class Rating(models.Model):
    """评分模型"""
    content = models.ForeignKey(CreativeContent, on_delete=models.CASCADE, related_name='ratings', verbose_name="内容")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="评分")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评分时间")
    
    class Meta:
        verbose_name = "评分"
        verbose_name_plural = "评分"
        unique_together = ['content', 'user']  # 每个用户对每个内容只能评分一次
    
    def __str__(self):
        return f"{self.user.username} - {self.content.title} - {self.score}星"


class Comment(models.Model):
    """评论模型"""
    content = models.ForeignKey(CreativeContent, on_delete=models.CASCADE, related_name='comments', verbose_name="内容")
    author = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="评论者")
    text = models.TextField(verbose_name="评论内容")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="评论时间")
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, 
                              related_name='replies', verbose_name="父评论")
    
    class Meta:
        verbose_name = "评论"
        verbose_name_plural = "评论"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.author.username} - {self.content.title[:20]}"


class Like(models.Model):
    """点赞模型"""
    content = models.ForeignKey(CreativeContent, on_delete=models.CASCADE, related_name='likes', verbose_name="内容")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="点赞时间")
    
    class Meta:
        verbose_name = "点赞"
        verbose_name_plural = "点赞"
        unique_together = ['content', 'user']
    
    def __str__(self):
        return f"{self.user.username} 点赞了 {self.content.title}"


class Favorite(models.Model):
    """收藏模型"""
    content = models.ForeignKey(CreativeContent, on_delete=models.CASCADE, related_name='favorites', verbose_name="内容")
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="收藏时间")
    
    class Meta:
        verbose_name = "收藏"
        verbose_name_plural = "收藏"
        unique_together = ['content', 'user']
    
    def __str__(self):
        return f"{self.user.username} 收藏了 {self.content.title}"


class UserProfile(models.Model):
    """用户扩展信息"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, verbose_name="用户")
    bio = models.TextField(max_length=500, blank=True, verbose_name="个人简介")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="头像")
    website = models.URLField(blank=True, verbose_name="个人网站")
    location = models.CharField(max_length=100, blank=True, verbose_name="所在地")
    birth_date = models.DateField(null=True, blank=True, verbose_name="生日")
    
    class Meta:
        verbose_name = "用户资料"
        verbose_name_plural = "用户资料"
    
    def __str__(self):
        return f"{self.user.username}的资料"


class UserActivity(models.Model):
    """用户活动日志"""
    ACTION_CHOICES = [
        ('view', '浏览'),
        ('like', '点赞'),
        ('favorite', '收藏'),
        ('comment', '评论'),
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="用户")
    action = models.CharField(max_length=20, choices=ACTION_CHOICES, verbose_name="操作")
    content = models.ForeignKey(CreativeContent, on_delete=models.CASCADE, null=True, blank=True, verbose_name="相关内容")
    description = models.CharField(max_length=200, verbose_name="描述")
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name="IP地址")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="操作时间")
    
    class Meta:
        verbose_name = "用户活动"
        verbose_name_plural = "用户活动"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} {self.get_action_display()} - {self.created_at}"


# 信号处理器：自动更新统计字段
@receiver(post_save, sender=Like)
@receiver(post_delete, sender=Like)
def update_likes_count(sender, instance, **kwargs):
    """更新点赞数"""
    content = instance.content
    content.likes_count = content.likes.count()
    content.save(update_fields=['likes_count'])


@receiver(post_save, sender=Comment)
@receiver(post_delete, sender=Comment)
def update_comments_count(sender, instance, **kwargs):
    """更新评论数"""
    content = instance.content
    content.comments_count = content.comments.count()
    content.save(update_fields=['comments_count'])


@receiver(post_save, sender=Favorite)
@receiver(post_delete, sender=Favorite)
def update_favorites_count(sender, instance, **kwargs):
    """更新收藏数"""
    content = instance.content
    content.favorites_count = content.favorites.count()
    content.save(update_fields=['favorites_count'])
