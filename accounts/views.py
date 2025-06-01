from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse_lazy
from django.views.generic import CreateView
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.auth.views import LoginView, LogoutView
from django import forms

from content.models import UserProfile
from core.utils import record_user_activity


class CustomUserCreationForm(UserCreationForm):
    """自定义用户注册表单"""
    email = forms.EmailField(required=True, label='邮箱')
    first_name = forms.CharField(max_length=30, required=False, label='姓名')
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'email', 'password1', 'password2')
        labels = {
            'username': '用户名',
            'first_name': '姓名',
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 添加CSS类
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
        
        # 自定义帮助文本
        self.fields['username'].help_text = '用户名只能包含字母、数字和@/./+/-/_字符'
        self.fields['password1'].help_text = '密码至少8位，不能全是数字'
        self.fields['password2'].help_text = '请再次输入密码确认'
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
            # 创建用户资料
            UserProfile.objects.create(user=user)
        return user


class CustomLoginView(LoginView):
    """自定义登录视图"""
    template_name = 'accounts/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        return reverse_lazy('core:home')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, f'欢迎回来，{self.request.user.username}！')
        return response
    
    def form_invalid(self, form):
        messages.error(self.request, '用户名或密码错误，请重试。')
        return super().form_invalid(form)


class CustomLogoutView(LogoutView):
    """自定义注销视图"""
    next_page = reverse_lazy('core:home')
    http_method_names = ['get', 'post', 'options']
    
    def get(self, request, *args, **kwargs):
        """处理GET请求，直接执行退出登录"""
        if request.user.is_authenticated:
            messages.success(request, '您已成功退出登录。')
        return self.post(request, *args, **kwargs)
    
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)


class SignUpView(CreateView):
    """用户注册视图"""
    form_class = CustomUserCreationForm
    template_name = 'accounts/signup.html'
    success_url = reverse_lazy('accounts:login')
    
    def form_valid(self, form):
        response = super().form_valid(form)
        username = form.cleaned_data.get('username')
        messages.success(
            self.request, 
            f'账户 {username} 创建成功！请登录。'
        )
        return response
    
    def form_invalid(self, form):
        for field, errors in form.errors.items():
            for error in errors:
                messages.error(self.request, f'{form.fields[field].label}: {error}')
        return super().form_invalid(form)


@login_required
def profile_view(request):
    """用户资料页面"""
    user_profile, created = UserProfile.objects.get_or_create(
        user=request.user
    )
    
    if request.method == 'POST':
        # 处理用户基本信息
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.username = request.POST.get('username', user.username)
        user.email = request.POST.get('email', user.email)
        
        # 检查用户名和邮箱是否已被其他用户使用
        if User.objects.filter(username=user.username).exclude(pk=user.pk).exists():
            messages.error(request, '该用户名已被其他用户使用')
        elif User.objects.filter(email=user.email).exclude(pk=user.pk).exists():
            messages.error(request, '该邮箱已被其他用户使用')
        else:
            user.save()
            
            # 处理用户资料信息
            user_profile.bio = request.POST.get('bio', '')
            user_profile.location = request.POST.get('location', '')
            user_profile.website = request.POST.get('website', '')
            
            # 处理头像上传
            if 'avatar' in request.FILES:
                user_profile.avatar = request.FILES['avatar']
            
            user_profile.save()
            messages.success(request, '资料更新成功！')
            return redirect('accounts:profile')
    
    context = {
        'user_profile': user_profile,
    }
    return render(request, 'accounts/profile.html', context)


@require_http_methods(["POST"])
def check_username(request):
    """检查用户名是否可用"""
    username = request.POST.get('username')
    if not username:
        return JsonResponse({'available': False, 'message': '用户名不能为空'})
    
    if User.objects.filter(username=username).exists():
        return JsonResponse({'available': False, 'message': '用户名已被使用'})
    
    return JsonResponse({'available': True, 'message': '用户名可用'})


@require_http_methods(["POST"])
def check_email(request):
    """检查邮箱是否可用"""
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'available': False, 'message': '邮箱不能为空'})
    
    if User.objects.filter(email=email).exists():
        return JsonResponse({'available': False, 'message': '邮箱已被使用'})
    
    return JsonResponse({'available': True, 'message': '邮箱可用'})
