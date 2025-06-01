from django import forms
from django.contrib.auth.models import User
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Field
from .models import CreativeContent, Comment, Rating, Tag, UserProfile


class CreativeContentForm(forms.ModelForm):
    """创意内容表单"""
    tags_input = forms.CharField(
        max_length=200, 
        required=False, 
        help_text="用逗号分隔多个标签",
        widget=forms.TextInput(attrs={'placeholder': '例如：科技,创新,AI'})
    )
    
    class Meta:
        model = CreativeContent
        fields = ['title', 'content', 'summary', 'privacy', 'cover_image']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': '给你的创意起个好标题'}),
            'content': forms.Textarea(attrs={'rows': 10, 'placeholder': '在这里分享你的创意内容...'}),
            'summary': forms.Textarea(attrs={'rows': 3, 'placeholder': '简要描述你的创意（可选）'}),
            'privacy': forms.Select(attrs={'class': 'form-select'}),
            'cover_image': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('title', css_class='form-control'),
            Field('content', css_class='form-control'),
            Field('summary', css_class='form-control'),
            Row(
                Column('privacy', css_class='form-group col-md-6 mb-0'),
                Column('cover_image', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('tags_input', css_class='form-control'),
            Submit('submit', '发布创意', css_class='btn btn-primary btn-lg')
        )
        
        # 如果是编辑模式，填充标签
        if self.instance.pk:
            tags = self.instance.tags.all()
            self.fields['tags_input'].initial = ', '.join([tag.name for tag in tags])
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit:
            instance.save()
            # 处理标签
            tags_input = self.cleaned_data.get('tags_input', '')
            if tags_input:
                tag_names = [name.strip() for name in tags_input.split(',') if name.strip()]
                tags = []
                for tag_name in tag_names:
                    tag, created = Tag.objects.get_or_create(name=tag_name)
                    tags.append(tag)
                instance.tags.set(tags)
            else:
                instance.tags.clear()
        return instance


class CommentForm(forms.ModelForm):
    """评论表单"""
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': '写下你的评论...',
                'class': 'form-control'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('text', css_class='form-control'),
            Submit('submit', '发表评论', css_class='btn btn-primary')
        )


class RatingForm(forms.ModelForm):
    """评分表单"""
    class Meta:
        model = Rating
        fields = ['score']
        widgets = {
            'score': forms.Select(
                choices=[(i, f'{i}星') for i in range(1, 6)],
                attrs={'class': 'form-select'}
            )
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('score', css_class='form-select'),
            Submit('submit', '提交评分', css_class='btn btn-warning')
        )


class UserProfileForm(forms.ModelForm):
    """用户资料表单"""
    class Meta:
        model = UserProfile
        fields = ['bio', 'avatar', 'website', 'location', 'birth_date']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': '介绍一下你自己...'}),
            'website': forms.URLInput(attrs={'placeholder': 'https://your-website.com'}),
            'location': forms.TextInput(attrs={'placeholder': '你在哪里？'}),
            'birth_date': forms.DateInput(attrs={'type': 'date'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Field('bio', css_class='form-control'),
            Field('avatar', css_class='form-control'),
            Row(
                Column('website', css_class='form-group col-md-6 mb-0'),
                Column('location', css_class='form-group col-md-6 mb-0'),
                css_class='form-row'
            ),
            Field('birth_date', css_class='form-control'),
            Submit('submit', '更新资料', css_class='btn btn-success')
        )


class SearchForm(forms.Form):
    """搜索表单"""
    query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'placeholder': '搜索创意内容...',
            'class': 'form-control'
        })
    )
    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=False,
        empty_label="所有标签",
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    sort_by = forms.ChoiceField(
        choices=[
            ('created_at', '最新发布'),
            ('views_count', '最多浏览'),
            ('likes_count', '最多点赞'),
            ('favorites_count', '最多收藏'),
        ],
        initial='created_at',
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            Row(
                Column('query', css_class='form-group col-md-6 mb-0'),
                Column('tag', css_class='form-group col-md-3 mb-0'),
                Column('sort_by', css_class='form-group col-md-3 mb-0'),
                css_class='form-row'
            ),
            Submit('submit', '搜索', css_class='btn btn-primary')
        )