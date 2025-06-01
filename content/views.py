from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Count, Avg, Prefetch
from django.core.paginator import Paginator
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

from .models import (
    CreativeContent, Tag, Category, Comment, Rating, Like, Favorite, 
    UserProfile, UserActivity
)
from .forms import (
    CreativeContentForm, CommentForm, RatingForm, 
    UserProfileForm, SearchForm
)
from .utils import (
    record_user_activity, get_recommendations_for_user,
    generate_ai_summary, generate_ai_comment, calculate_content_score
)


class ContentListView(ListView):
    """内容列表视图"""
    model = CreativeContent
    template_name = 'content/list.html'
    context_object_name = 'contents'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = CreativeContent.objects.filter(
            privacy='public'
        ).select_related('author').prefetch_related('tags', 'likes', 'favorites')
        
        # 搜索功能
        search_query = self.request.GET.get('q')  # 修复参数名
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(tags__name__icontains=search_query)
            ).distinct()
        
        # 分类筛选
        category_id = self.request.GET.get('category')
        if category_id:
            queryset = queryset.filter(category__id=category_id)
        
        # 隐私筛选
        privacy = self.request.GET.get('privacy')
        if privacy:
            queryset = queryset.filter(privacy=privacy)
        
        # 标签筛选
        tag_id = self.request.GET.get('tag')
        if tag_id:
            queryset = queryset.filter(tags__id=tag_id)
        
        # 排序
        sort_by = self.request.GET.get('sort', '-created_at')  # 修复参数名
        if sort_by == 'views_count':
            queryset = queryset.order_by('-views_count')
        elif sort_by == 'likes_count':
            queryset = queryset.annotate(
                likes_count=Count('likes')
            ).order_by('-likes_count')
        elif sort_by == 'favorites_count':
            queryset = queryset.annotate(
                favorites_count=Count('favorites')
            ).order_by('-favorites_count')
        else:
            queryset = queryset.order_by('-created_at')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = SearchForm(self.request.GET)
        context['current_tag'] = self.request.GET.get('tag')
        context['current_sort'] = self.request.GET.get('sort', '-created_at')
        context['search_query'] = self.request.GET.get('q', '')
        context['current_category'] = self.request.GET.get('category')
        context['current_privacy'] = self.request.GET.get('privacy')
        
        # 获取所有分类
        context['categories'] = Category.objects.all()
        
        # 热门标签
        context['popular_tags'] = Tag.objects.annotate(
            content_count=Count('creativecontent')
        ).filter(content_count__gt=0).order_by('-content_count')[:10]
        
        # 为每个内容添加是否被当前用户点赞的标记
        if self.request.user.is_authenticated:
            contents = context['contents']
            user_likes = set(Like.objects.filter(
                user=self.request.user,
                content__in=contents
            ).values_list('content_id', flat=True))
            
            for content in contents:
                content.is_liked_by_user = content.id in user_likes
                content.comments_count = content.comments.count()
        else:
            for content in context['contents']:
                content.is_liked_by_user = False
                content.comments_count = content.comments.count()
        
        return context


class ContentDetailView(DetailView):
    """内容详情视图"""
    model = CreativeContent
    template_name = 'content/content_detail.html'
    context_object_name = 'content'
    
    def get_queryset(self):
        return CreativeContent.objects.select_related('author').prefetch_related(
            'tags', 'comments__author', 'ratings', 'likes', 'favorites'
        )
    
    def get_object(self):
        obj = super().get_object()
        
        # 检查权限
        if obj.privacy == 'private' and obj.author != self.request.user:
            if not self.request.user.is_superuser:
                raise Http404("内容不存在")
        
        # 增加浏览量
        obj.views_count += 1
        obj.save(update_fields=['views_count'])
        
        # 记录用户活动
        if self.request.user.is_authenticated:
            record_user_activity(
                self.request.user, 
                'view', 
                obj, 
                f"浏览了内容：{obj.title}"
            )
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.object
        user = self.request.user
        
        # 评论表单
        context['comment_form'] = CommentForm()
        
        # 评分表单
        context['rating_form'] = RatingForm()
        
        # 用户交互状态
        if user.is_authenticated:
            context['user_liked'] = Like.objects.filter(
                user=user, content=content
            ).exists()
            content.is_liked_by_user = context['user_liked']
            context['user_favorited'] = Favorite.objects.filter(
                user=user, content=content
            ).exists()
            context['user_rating'] = Rating.objects.filter(
                user=user, content=content
            ).first()
        else:
            content.is_liked_by_user = False
        
        # 统计信息
        context['likes_count'] = content.likes.count()
        context['favorites_count'] = content.favorites.count()
        context['comments_count'] = content.comments.count()
        
        # 平均评分
        avg_rating = content.ratings.aggregate(avg=Avg('score'))['avg']
        context['avg_rating'] = round(avg_rating, 1) if avg_rating else 0
        context['ratings_count'] = content.ratings.count()
        
        # 相关内容推荐
        related_contents = CreativeContent.objects.filter(
            tags__in=content.tags.all(),
            privacy='public'
        ).exclude(id=content.id).distinct()[:4]
        context['related_contents'] = related_contents
        
        # 二创内容
        derivative_contents = CreativeContent.objects.filter(
            original_content=content,
            privacy='public'
        ).select_related('author')[:5]
        context['derivative_contents'] = derivative_contents
        
        return context


class ContentCreateView(LoginRequiredMixin, CreateView):
    """创建内容视图"""
    model = CreativeContent
    form_class = CreativeContentForm
    template_name = 'content/content_form.html'
    
    def form_valid(self, form):
        form.instance.author = self.request.user
        
        # 生成AI摘要
        if not form.instance.summary:
            try:
                form.instance.summary = generate_ai_summary(
                    form.instance.title, 
                    form.instance.content
                )
            except Exception as e:
                print(f"AI摘要生成失败: {e}")
        
        response = super().form_valid(form)
        
        # 记录用户活动
        record_user_activity(
            self.request.user, 
            'create', 
            self.object, 
            f"创建了内容：{self.object.title}"
        )
        
        messages.success(self.request, '创意内容发布成功！')
        return response
    
    def get_success_url(self):
        return reverse('content:content_detail', kwargs={'pk': self.object.pk})


class ContentUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """更新内容视图"""
    model = CreativeContent
    form_class = CreativeContentForm
    template_name = 'content/content_form.html'
    
    def test_func(self):
        content = self.get_object()
        return content.author == self.request.user or self.request.user.is_superuser
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # 记录用户活动
        record_user_activity(
            self.request.user, 
            'update', 
            self.object, 
            f"更新了内容：{self.object.title}"
        )
        
        messages.success(self.request, '内容更新成功！')
        return response
    
    def get_success_url(self):
        return reverse('content:content_detail', kwargs={'pk': self.object.pk})


class ContentDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """删除内容视图"""
    model = CreativeContent
    template_name = 'content/content_confirm_delete.html'
    success_url = reverse_lazy('content:content_list')
    
    def test_func(self):
        content = self.get_object()
        return content.author == self.request.user or self.request.user.is_superuser
    
    def delete(self, request, *args, **kwargs):
        content = self.get_object()
        
        # 记录用户活动
        record_user_activity(
            request.user, 
            'delete', 
            content, 
            f"删除了内容：{content.title}"
        )
        
        messages.success(request, '内容删除成功！')
        return super().delete(request, *args, **kwargs)


class UserProfileView(DetailView):
    """用户个人主页"""
    model = User
    template_name = 'content/user_profile.html'
    context_object_name = 'profile_user'
    
    def get_object(self, queryset=None):
        """根据username获取用户对象"""
        username = self.kwargs.get('username')
        return get_object_or_404(User, username=username)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile_user = self.object
        
        # 获取或创建用户资料
        user_profile, created = UserProfile.objects.get_or_create(
            user=profile_user
        )
        context['user_profile'] = user_profile
        
        # 用户内容
        if self.request.user == profile_user or self.request.user.is_superuser:
            # 自己或管理员可以看到所有内容
            user_contents = CreativeContent.objects.filter(
                author=profile_user
            )
        else:
            # 其他人只能看到公开内容
            user_contents = CreativeContent.objects.filter(
                author=profile_user,
                privacy='public'
            )
        
        # 分页
        paginator = Paginator(user_contents.order_by('-created_at'), 12)
        page_number = self.request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        context['page_obj'] = page_obj
        
        # 统计信息
        context['total_contents'] = user_contents.count()
        context['total_views'] = sum(content.views_count for content in user_contents)
        context['total_likes'] = sum(content.likes_count for content in user_contents)
        context['total_favorites'] = sum(content.favorites_count for content in user_contents)
        
        # 最近活动
        context['recent_activities'] = UserActivity.objects.filter(
            user=profile_user
        ).select_related('content').order_by('-created_at')[:10]
        
        return context


@login_required
def edit_profile(request):
    """编辑用户资料"""
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, '资料更新成功！')
            return redirect('content:user_profile', pk=request.user.pk)
    else:
        form = UserProfileForm(instance=user_profile)
    
    context = {
        'form': form,
        'user_profile': user_profile
    }
    return render(request, 'content/edit_profile.html', context)


@login_required
@require_http_methods(["POST"])
def add_comment(request, content_id):
    """添加评论"""
    content = get_object_or_404(CreativeContent, id=content_id)
    
    if content.privacy == 'private' and content.author != request.user:
        return JsonResponse({'success': False, 'error': '无权限评论'})
    
    form = CommentForm(request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.content = content
        comment.save()
        
        # 记录用户活动
        record_user_activity(
            request.user, 
            'comment', 
            content, 
            f"评论了内容：{content.title}"
        )
        
        return JsonResponse({
            'success': True,
            'comment': {
                'id': comment.id,
                'text': comment.text,
                'author': comment.author.username,
                'created_at': comment.created_at.strftime('%Y-%m-%d %H:%M')
            }
        })
    
    return JsonResponse({'success': False, 'error': '评论内容不能为空'})


@login_required
@require_http_methods(["POST"])
def add_rating(request, content_id):
    """添加评分"""
    content = get_object_or_404(CreativeContent, id=content_id)
    
    if content.author == request.user:
        return JsonResponse({'success': False, 'error': '不能给自己的内容评分'})
    
    score = request.POST.get('score')
    try:
        score = int(score)
        if score < 1 or score > 5:
            raise ValueError
    except (ValueError, TypeError):
        return JsonResponse({'success': False, 'error': '评分必须是1-5之间的整数'})
    
    # 更新或创建评分
    rating, created = Rating.objects.update_or_create(
        user=request.user,
        content=content,
        defaults={'score': score}
    )
    
    # 记录用户活动
    action = 'rate' if created else 'update_rating'
    record_user_activity(
        request.user, 
        action, 
        content, 
        f"给内容评分：{score}星"
    )
    
    # 计算新的平均评分
    avg_rating = content.ratings.aggregate(avg=Avg('score'))['avg']
    
    return JsonResponse({
        'success': True,
        'avg_rating': round(avg_rating, 1) if avg_rating else 0,
        'ratings_count': content.ratings.count(),
        'user_rating': score
    })


@require_http_methods(["POST"])
def toggle_like(request, content_id):
    """切换点赞状态"""
    content = get_object_or_404(CreativeContent, id=content_id)
    
    # 检查用户是否已登录
    if not request.user.is_authenticated:
        return JsonResponse({
            'success': False,
            'error': 'login_required',
            'message': '请先登录后再进行点赞操作'
        }, status=401)
    
    like, created = Like.objects.get_or_create(
        user=request.user,
        content=content
    )
    
    if not created:
        like.delete()
        liked = False
        action = 'unlike'
    else:
        liked = True
        action = 'like'
    
    # 记录用户活动
    record_user_activity(
        request.user, 
        action, 
        content, 
        f"{'点赞' if liked else '取消点赞'}了内容：{content.title}"
    )
    
    return JsonResponse({
        'success': True,
        'liked': liked,
        'likes_count': content.likes.count()
    })


@login_required
@require_http_methods(["POST"])
def toggle_favorite(request, content_id):
    """切换收藏状态"""
    content = get_object_or_404(CreativeContent, id=content_id)
    
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        content=content
    )
    
    if not created:
        favorite.delete()
        favorited = False
        action = 'unfavorite'
    else:
        favorited = True
        action = 'favorite'
    
    # 记录用户活动
    record_user_activity(
        request.user, 
        action, 
        content, 
        f"{'收藏' if favorited else '取消收藏'}了内容：{content.title}"
    )
    
    return JsonResponse({
        'success': True,
        'favorited': favorited,
        'favorites_count': content.favorites.count()
    })


class DerivativeCreateView(LoginRequiredMixin, CreateView):
    """创建二创内容"""
    model = CreativeContent
    form_class = CreativeContentForm
    template_name = 'content/derivative_form.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        original_id = self.kwargs.get('original_id')
        context['original_content'] = get_object_or_404(
            CreativeContent, 
            id=original_id,
            privacy='public'
        )
        return context
    
    def form_valid(self, form):
        original_id = self.kwargs.get('original_id')
        original_content = get_object_or_404(
            CreativeContent, 
            id=original_id,
            privacy='public'
        )
        
        form.instance.author = self.request.user
        form.instance.original_content = original_content
        
        # 生成AI摘要
        if not form.instance.summary:
            try:
                form.instance.summary = generate_ai_summary(
                    form.instance.title, 
                    form.instance.content
                )
            except Exception as e:
                print(f"AI摘要生成失败: {e}")
        
        response = super().form_valid(form)
        
        # 记录用户活动
        record_user_activity(
            self.request.user, 
            'derivative', 
            self.object, 
            f"基于'{original_content.title}'创建了二创内容"
        )
        
        messages.success(self.request, '二创内容发布成功！')
        return response
    
    def get_success_url(self):
        return reverse('content:content_detail', kwargs={'pk': self.object.pk})


@login_required
def my_contents(request):
    """我的内容"""
    contents = CreativeContent.objects.filter(
        author=request.user
    ).order_by('-created_at')
    
    # 分页
    paginator = Paginator(contents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_contents': contents.count()
    }
    return render(request, 'content/my_contents.html', context)


@login_required
def my_favorites(request):
    """我的收藏"""
    favorites = Favorite.objects.filter(
        user=request.user
    ).select_related('content__author').order_by('-created_at')
    
    # 分页
    paginator = Paginator(favorites, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_favorites': favorites.count()
    }
    return render(request, 'content/my_favorites.html', context)


@login_required
def recommendations(request):
    """推荐内容"""
    try:
        recommended_contents = get_recommendations_for_user(request.user, limit=20)
    except Exception as e:
        print(f"获取推荐内容失败: {e}")
        recommended_contents = []
    
    # 分页
    paginator = Paginator(recommended_contents, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'total_recommendations': len(recommended_contents)
    }
    return render(request, 'content/recommendations.html', context)


@login_required
@require_http_methods(["POST"])
def generate_ai_content_comment(request, content_id):
    """生成AI点评"""
    content = get_object_or_404(CreativeContent, id=content_id)
    
    try:
        from .utils import create_ai_comment_for_content
        
        # 创建AI评论
        ai_comment = create_ai_comment_for_content(content)
        
        if ai_comment:
            return JsonResponse({
                'success': True,
                'comment': ai_comment.text,
                'comment_data': {
                    'id': ai_comment.id,
                    'text': ai_comment.text,
                    'author': ai_comment.author.username,
                    'created_at': ai_comment.created_at.strftime('%Y-%m-%d %H:%M'),
                    'is_ai': True
                }
            })
        else:
            return JsonResponse({
                'success': False,
                'error': 'AI评论创建失败'
            })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'AI点评生成失败: {str(e)}'
        })
