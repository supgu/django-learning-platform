from django.db.models import Count, Q, Avg
from django.contrib.auth.models import User
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from collections import defaultdict
import requests
import json

from .models import CreativeContent, Tag, Like, Favorite, Rating, UserActivity


def get_client_ip(request):
    """获取客户端IP地址"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def record_user_activity(user, action, content=None, description=""):
    """记录用户活动"""
    if user.is_authenticated:
        UserActivity.objects.create(
            user=user,
            action=action,
            content=content,
            description=description
        )


def get_user_preferences(user):
    """获取用户偏好标签"""
    # 基于用户点赞、收藏、评分的内容获取偏好标签
    liked_contents = CreativeContent.objects.filter(
        likes__user=user
    ).prefetch_related('tags')
    
    favorited_contents = CreativeContent.objects.filter(
        favorites__user=user
    ).prefetch_related('tags')
    
    rated_contents = CreativeContent.objects.filter(
        ratings__user=user,
        ratings__score__gte=4  # 高分评价
    ).prefetch_related('tags')
    
    # 统计标签权重
    tag_weights = defaultdict(float)
    
    # 点赞权重 1
    for content in liked_contents:
        for tag in content.tags.all():
            tag_weights[tag.id] += 1.0
    
    # 收藏权重 2
    for content in favorited_contents:
        for tag in content.tags.all():
            tag_weights[tag.id] += 2.0
    
    # 高分评价权重 1.5
    for content in rated_contents:
        for tag in content.tags.all():
            tag_weights[tag.id] += 1.5
    
    # 返回权重最高的标签
    sorted_tags = sorted(tag_weights.items(), key=lambda x: x[1], reverse=True)
    return [tag_id for tag_id, weight in sorted_tags[:10]]


def get_content_similarity_matrix():
    """计算内容相似度矩阵（基于TF-IDF）"""
    contents = CreativeContent.objects.filter(privacy='public')
    
    if not contents.exists():
        return {}, []
    
    # 准备文本数据
    texts = []
    content_ids = []
    
    for content in contents:
        # 组合标题、内容和标签
        text = f"{content.title} {content.content} {' '.join([tag.name for tag in content.tags.all()])}"
        texts.append(text)
        content_ids.append(content.id)
    
    # 计算TF-IDF
    try:
        vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words=None,  # 中文需要自定义停用词
            ngram_range=(1, 2)
        )
        tfidf_matrix = vectorizer.fit_transform(texts)
        
        # 计算余弦相似度
        similarity_matrix = cosine_similarity(tfidf_matrix)
        
        # 构建相似度字典
        similarity_dict = {}
        for i, content_id in enumerate(content_ids):
            similarity_dict[content_id] = {
                content_ids[j]: similarity_matrix[i][j] 
                for j in range(len(content_ids)) if i != j
            }
        
        return similarity_dict, content_ids
    except Exception as e:
        print(f"计算相似度矩阵错误: {e}")
        return {}, []


def get_collaborative_filtering_recommendations(user, limit=10):
    """协同过滤推荐"""
    # 获取用户的评分数据
    user_ratings = Rating.objects.filter(user=user).values_list('content_id', 'score')
    user_rated_contents = dict(user_ratings)
    
    if not user_rated_contents:
        return []
    
    # 找到相似用户
    similar_users = []
    all_users = User.objects.exclude(id=user.id)
    
    for other_user in all_users:
        other_ratings = Rating.objects.filter(user=other_user).values_list('content_id', 'score')
        other_rated_contents = dict(other_ratings)
        
        # 计算用户相似度（基于共同评分的内容）
        common_contents = set(user_rated_contents.keys()) & set(other_rated_contents.keys())
        
        if len(common_contents) >= 2:  # 至少有2个共同评分
            similarity = calculate_user_similarity(
                user_rated_contents, 
                other_rated_contents, 
                common_contents
            )
            if similarity > 0.3:  # 相似度阈值
                similar_users.append((other_user, similarity))
    
    # 根据相似用户推荐内容
    recommendations = []
    similar_users.sort(key=lambda x: x[1], reverse=True)  # 按相似度排序
    
    for similar_user, similarity in similar_users[:5]:  # 取前5个相似用户
        # 获取相似用户高分评价的内容
        high_rated_contents = CreativeContent.objects.filter(
            ratings__user=similar_user,
            ratings__score__gte=4,
            privacy='public'
        ).exclude(
            id__in=user_rated_contents.keys()
        ).distinct()
        
        for content in high_rated_contents:
            if content not in [rec[0] for rec in recommendations]:
                score = similarity * content.ratings.filter(user=similar_user).first().score
                recommendations.append((content, score))
    
    # 按推荐分数排序
    recommendations.sort(key=lambda x: x[1], reverse=True)
    return [content for content, score in recommendations[:limit]]


def calculate_user_similarity(user1_ratings, user2_ratings, common_contents):
    """计算用户相似度（皮尔逊相关系数）"""
    if not common_contents:
        return 0
    
    # 计算平均分
    user1_scores = [user1_ratings[content_id] for content_id in common_contents]
    user2_scores = [user2_ratings[content_id] for content_id in common_contents]
    
    user1_mean = np.mean(user1_scores)
    user2_mean = np.mean(user2_scores)
    
    # 计算皮尔逊相关系数
    numerator = sum((user1_ratings[content_id] - user1_mean) * 
                   (user2_ratings[content_id] - user2_mean) 
                   for content_id in common_contents)
    
    user1_sq_sum = sum((user1_ratings[content_id] - user1_mean) ** 2 
                      for content_id in common_contents)
    user2_sq_sum = sum((user2_ratings[content_id] - user2_mean) ** 2 
                      for content_id in common_contents)
    
    denominator = np.sqrt(user1_sq_sum * user2_sq_sum)
    
    if denominator == 0:
        return 0
    
    return numerator / denominator


def get_content_based_recommendations(user, limit=10):
    """基于内容的推荐"""
    # 获取用户偏好标签
    preferred_tag_ids = get_user_preferences(user)
    
    if not preferred_tag_ids:
        return []
    
    # 获取用户已经交互过的内容
    interacted_content_ids = set()
    
    # 已点赞的内容
    liked_ids = Like.objects.filter(user=user).values_list('content_id', flat=True)
    interacted_content_ids.update(liked_ids)
    
    # 已收藏的内容
    favorited_ids = Favorite.objects.filter(user=user).values_list('content_id', flat=True)
    interacted_content_ids.update(favorited_ids)
    
    # 已评分的内容
    rated_ids = Rating.objects.filter(user=user).values_list('content_id', flat=True)
    interacted_content_ids.update(rated_ids)
    
    # 用户自己创建的内容
    authored_ids = CreativeContent.objects.filter(author=user).values_list('id', flat=True)
    interacted_content_ids.update(authored_ids)
    
    # 推荐包含偏好标签的内容
    recommended_contents = CreativeContent.objects.filter(
        tags__id__in=preferred_tag_ids,
        privacy='public'
    ).exclude(
        id__in=interacted_content_ids
    ).annotate(
        tag_match_count=Count('tags', filter=Q(tags__id__in=preferred_tag_ids)),
        avg_rating=Avg('ratings__score'),
        popularity_score=Count('likes') + Count('favorites') * 2
    ).order_by(
        '-tag_match_count',
        '-avg_rating',
        '-popularity_score',
        '-created_at'
    ).distinct()[:limit]
    
    return list(recommended_contents)


def get_recommendations_for_user(user, limit=10):
    """为用户获取推荐内容（混合推荐）"""
    recommendations = []
    
    # 1. 协同过滤推荐（权重40%）
    try:
        cf_recommendations = get_collaborative_filtering_recommendations(user, limit//2)
        recommendations.extend(cf_recommendations)
    except Exception as e:
        print(f"协同过滤推荐错误: {e}")
    
    # 2. 基于内容的推荐（权重60%）
    try:
        cb_recommendations = get_content_based_recommendations(user, limit)
        recommendations.extend(cb_recommendations)
    except Exception as e:
        print(f"基于内容推荐错误: {e}")
    
    # 3. 热门内容补充
    if len(recommendations) < limit:
        # 获取用户已交互的内容ID
        interacted_ids = set()
        if hasattr(user, 'like_set'):
            interacted_ids.update(Like.objects.filter(user=user).values_list('content_id', flat=True))
        if hasattr(user, 'favorite_set'):
            interacted_ids.update(Favorite.objects.filter(user=user).values_list('content_id', flat=True))
        if hasattr(user, 'rating_set'):
            interacted_ids.update(Rating.objects.filter(user=user).values_list('content_id', flat=True))
        
        # 排除已推荐的内容
        recommended_ids = [content.id for content in recommendations]
        interacted_ids.update(recommended_ids)
        
        popular_contents = CreativeContent.objects.filter(
            privacy='public'
        ).exclude(
            id__in=interacted_ids
        ).exclude(
            author=user
        ).annotate(
            popularity_score=Count('likes') + Count('favorites') * 2 + Count('ratings')
        ).order_by('-popularity_score', '-created_at')[:limit - len(recommendations)]
        
        recommendations.extend(popular_contents)
    
    # 去重并限制数量
    seen_ids = set()
    unique_recommendations = []
    for content in recommendations:
        if content.id not in seen_ids:
            seen_ids.add(content.id)
            unique_recommendations.append(content)
            if len(unique_recommendations) >= limit:
                break
    
    return unique_recommendations


def generate_ai_summary(title, content):
    """使用DeepSeek AI生成内容摘要"""
    try:
        import requests
        import json
        from django.conf import settings
        
        # 检查API配置
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if not api_key or api_key == 'your-deepseek-api-key-here':
            return f"这是一个关于'{title}'的创意内容，包含了丰富的想法和见解。（请配置DeepSeek API密钥）"
        
        # 构建请求
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        prompt = f"请为以下创意内容生成一个简洁的摘要（不超过100字）：\n标题：{title}\n内容：{content[:500]}..."
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个专业的内容摘要助手，能够为各种创意内容生成简洁、准确的摘要。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 150,
            "temperature": 0.7,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                summary = result['choices'][0]['message']['content'].strip()
                return summary
            else:
                return f"这是一个关于'{title}'的创意内容，包含了丰富的想法和见解。"
        else:
            print(f"DeepSeek API错误: {response.status_code} - {response.text}")
            return f"这是一个关于'{title}'的创意内容，包含了丰富的想法和见解。"
            
    except Exception as e:
        print(f"AI摘要生成错误: {e}")
        return f"这是一个关于'{title}'的创意内容，包含了丰富的想法和见解。"


def generate_ai_comment(title, content):
    """使用DeepSeek AI生成内容点评"""
    try:
        import requests
        import json
        from django.conf import settings
        
        # 检查API配置
        api_key = getattr(settings, 'DEEPSEEK_API_KEY', None)
        base_url = getattr(settings, 'DEEPSEEK_BASE_URL', 'https://api.deepseek.com')
        
        if not api_key or api_key == 'your-deepseek-api-key-here':
            # 如果没有配置API，使用原来的随机评论逻辑
            # 根据内容长度和标题生成更个性化的评论
            import random
            import hashlib
            
            # 使用内容标题作为种子，确保同一内容总是生成相同的评论
            seed = hashlib.md5(title.encode()).hexdigest()
            random.seed(seed)
            
            # 根据内容特征选择不同类型的评论
            content_length = len(content)
            
            if content_length > 500:
                comments = [
                    "这是一篇内容丰富的文章！作者在这个主题上进行了深入的探讨，逻辑清晰，表达流畅。",
                    "详实的内容，可以看出作者的专业功底。这种深度分析很有价值，值得细细品读。",
                    "长篇大论却不失重点，作者的写作功力令人印象深刻。内容结构合理，阅读体验很好。",
                    "这样的深度内容在当下很难得，作者显然在这个领域有着丰富的经验和独到的见解。"
                ]
            elif content_length > 200:
                comments = [
                    "简洁而有力的表达！作者用不多的文字传达了丰富的信息，很有启发性。",
                    "观点清晰，论述有条理。这种中等篇幅的内容最适合快节奏的阅读需求。",
                    "内容恰到好处，既不冗长也不简陋。作者很好地把握了信息密度的平衡。",
                    "这样的内容长度刚好，既能深入主题又不会让读者感到疲劳。写得很棒！"
                ]
            else:
                comments = [
                    "简短精悍！有时候最有力的表达就是这样简洁明了，一针见血。",
                    "短小精悍的内容，但信息量不小。作者很会抓重点，值得点赞！",
                    "言简意赅，这种简洁的表达方式很有力量。期待看到更多这样的精彩分享。",
                    "虽然篇幅不长，但内容很有价值。有时候简单的话语最能打动人心。"
                ]
            
            selected_comment = random.choice(comments)
            
            # 添加API配置提示（随机出现）
            if random.random() < 0.3:  # 30%的概率显示提示
                selected_comment += "\n\n💡 提示：配置DeepSeek API密钥可获得更智能的个性化评论！"
            
            return selected_comment
        
        # 构建请求
        url = f"{base_url}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        prompt = f"请为以下创意内容生成一个友善、建设性的评论（50-80字）：\n标题：{title}\n内容：{content[:300]}..."
        
        data = {
            "model": "deepseek-chat",
            "messages": [
                {"role": "system", "content": "你是一个友善的内容评论助手，能够为各种创意内容生成积极、建设性的评论。评论应该鼓励作者，同时提供有价值的反馈。"},
                {"role": "user", "content": prompt}
            ],
            "max_tokens": 120,
            "temperature": 0.8,
            "stream": False
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                comment = result['choices'][0]['message']['content'].strip()
                return comment
            else:
                return "很棒的创意！感谢分享这么有价值的内容。"
        else:
            print(f"DeepSeek API错误: {response.status_code} - {response.text}")
            return "很棒的创意！感谢分享这么有价值的内容。"
            
    except Exception as e:
        print(f"AI点评生成错误: {e}")
        return "很棒的创意！感谢分享这么有价值的内容。"


def create_ai_user():
    """创建或获取AI用户"""
    from django.contrib.auth.models import User
    from .models import UserProfile
    
    try:
        ai_user, created = User.objects.get_or_create(
            username='AI助手',
            defaults={
                'email': 'ai@example.com',
                'first_name': 'AI',
                'last_name': '助手',
                'is_active': True
            }
        )
        
        # 创建或更新用户资料
        profile, profile_created = UserProfile.objects.get_or_create(
            user=ai_user,
            defaults={
                'bio': '我是AI智能助手，由DeepSeek AI驱动，专门为用户提供智能评论和内容分析。',
                'location': '云端',
                'website': 'https://www.deepseek.com'
            }
        )
        
        return ai_user
    except Exception as e:
        print(f"创建AI用户失败: {e}")
        return None


def create_ai_comment_for_content(content_obj):
    """为指定内容创建AI评论"""
    from .models import Comment
    
    try:
        ai_user = create_ai_user()
        if not ai_user:
            return None
            
        # 检查是否已经有AI评论（限制每个内容最多一个AI评论）
        existing_comment = Comment.objects.filter(
            content=content_obj,
            author=ai_user
        ).first()
        
        if existing_comment:
            # 如果已存在AI评论，重新生成并更新评论内容
            ai_comment_text = generate_ai_comment(content_obj.title, content_obj.content)
            existing_comment.text = ai_comment_text
            existing_comment.save()
            return existing_comment
            
        # 生成AI评论
        ai_comment_text = generate_ai_comment(content_obj.title, content_obj.content)
        
        # 创建评论
        comment = Comment.objects.create(
            content=content_obj,
            author=ai_user,
            text=ai_comment_text
        )
        
        return comment
    except Exception as e:
        print(f"创建AI评论失败: {e}")
        return None


def get_trending_tags(days=7, limit=10):
    """获取热门标签"""
    from django.utils import timezone
    from datetime import timedelta
    
    since_date = timezone.now() - timedelta(days=days)
    
    trending_tags = Tag.objects.filter(
        creativecontent__created_at__gte=since_date
    ).annotate(
        content_count=Count('creativecontent'),
        total_likes=Count('creativecontent__likes'),
        total_favorites=Count('creativecontent__favorites')
    ).filter(
        content_count__gt=0
    ).order_by(
        '-total_likes',
        '-total_favorites',
        '-content_count'
    )[:limit]
    
    return trending_tags


def calculate_content_score(content):
    """计算内容综合评分"""
    # 基础分数
    base_score = 0
    
    # 点赞数权重
    likes_score = content.likes_count * 1
    
    # 收藏数权重
    favorites_score = content.favorites_count * 2
    
    # 评论数权重
    comments_score = content.comments_count * 0.5
    
    # 浏览数权重
    views_score = content.views_count * 0.1
    
    # 评分权重
    rating_score = 0
    if content.ratings.exists():
        avg_rating = content.ratings.aggregate(avg=Avg('score'))['avg'] or 0
        rating_score = avg_rating * 2
    
    # 时间衰减（新内容有加分）
    from django.utils import timezone
    days_old = (timezone.now() - content.created_at).days
    time_factor = max(0.1, 1 - (days_old * 0.05))  # 每天衰减5%
    
    total_score = (
        base_score + likes_score + favorites_score + 
        comments_score + views_score + rating_score
    ) * time_factor
    
    return round(total_score, 2)