# Django学习平台

这是一个基于Django的学习平台，集成了DeepSeek AI功能，提供完整的内容创作、分享和互动体验。

## 功能特性

### 核心功能
- 用户注册、登录和个人资料管理
- 内容创作、发布和管理（支持公开/私有设置）
- 内容分类和标签系统
- 高级搜索和内容筛选
- 响应式设计，支持多设备访问

### AI智能功能
- AI智能摘要生成（基于DeepSeek API）
- AI智能评论生成（基于DeepSeek API）
- 智能内容推荐系统

### 互动功能
- 点赞系统（支持未登录用户友好提示）
- 评论系统（支持嵌套回复）
- 收藏功能
- 内容评分系统
- 用户活动记录和统计

### 数据分析
- 内容浏览量统计
- 用户互动数据分析
- 热门内容排行
- 个人数据仪表板

## 安装和配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置DeepSeek API

1. 访问 [DeepSeek官网](https://api-docs.deepseek.com/) 注册账号
2. 获取API密钥
3. 在 `learning_platform/settings.py` 中配置：

```python
# DeepSeek API 配置
DEEPSEEK_API_KEY = "your-actual-api-key-here"  # 替换为你的实际API密钥
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
```

### 3. 数据库迁移

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 创建超级用户

```bash
python manage.py createsuperuser
```

### 5. 运行开发服务器

```bash
python manage.py runserver
```

## DeepSeek API 使用说明

### API 配置

项目使用DeepSeek API来提供AI功能：

- **模型**: `deepseek-chat` (DeepSeek-V3)
- **功能**: 内容摘要生成、智能评论生成
- **兼容性**: 与OpenAI API格式兼容

### 获取API密钥

1. 访问 [DeepSeek API文档](https://api-docs.deepseek.com/)
2. 注册账号并登录
3. 在API Keys页面创建新的API密钥
4. 将密钥配置到settings.py中

### API调用示例

```python
import requests

url = "https://api.deepseek.com/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {your_api_key}"
}

data = {
    "model": "deepseek-chat",
    "messages": [
        {"role": "system", "content": "你是一个专业的内容摘要助手"},
        {"role": "user", "content": "请生成摘要..."}
    ],
    "max_tokens": 150,
    "temperature": 0.7
}

response = requests.post(url, headers=headers, json=data)
```

## 项目结构

```
learning_platform/
├── accounts/          # 用户账户管理
│   ├── views.py      # 登录、注册、个人资料
│   └── urls.py       # 账户相关路由
├── content/           # 内容管理核心模块
│   ├── models.py     # 数据模型（内容、评论、点赞、收藏等）
│   ├── views.py      # 视图逻辑（CRUD、AJAX接口）
│   ├── forms.py      # 表单定义
│   ├── utils.py      # AI功能和推荐算法
│   └── admin.py      # 后台管理配置
├── core/             # 核心功能模块
│   ├── views.py      # 首页、仪表板、数据分析
│   └── utils.py      # 通用工具函数
├── static/           # 静态资源
│   ├── css/
│   │   └── style.css # 样式文件（响应式设计）
│   └── js/
│       └── main.js   # 前端交互（点赞、评论等）
├── templates/        # 模板文件
│   ├── base.html     # 基础模板
│   ├── content/      # 内容相关模板
│   ├── core/         # 核心页面模板
│   └── accounts/     # 用户相关模板
├── media/            # 用户上传文件
│   ├── avatars/      # 用户头像
│   └── covers/       # 内容封面图
└── learning_platform/ # 项目配置
    ├── settings.py   # 项目设置
    └── urls.py       # 主路由配置
```

## 已修复的问题

### 1. DeepSeek API 接入

- ✅ 实现了真正的DeepSeek API调用
- ✅ 添加了API配置和错误处理
- ✅ 支持智能摘要和评论生成
- ✅ 兼容OpenAI API格式

### 2. 下拉菜单遮挡问题

- ✅ 修复了个人资料下拉菜单被界面遮挡的问题
- ✅ 添加了高z-index值确保菜单显示在最上层
- ✅ 优化了下拉菜单的样式和动画效果
- ✅ 添加了响应式设计支持

### 3. 点赞功能优化

- ✅ 修复了点赞按钮双重更新导致的数据错误问题
- ✅ 优化了前端JavaScript逻辑，确保单一数据源
- ✅ 改进了未登录用户的友好提示和引导
- ✅ 添加了完善的错误处理和状态恢复机制
- ✅ 实现了实时点赞数更新，无需刷新页面

### 4. 用户体验改进

- ✅ 优化了AJAX请求的错误处理
- ✅ 添加了加载状态指示
- ✅ 改进了表单验证和用户反馈
- ✅ 优化了移动端响应式布局

## 注意事项

1. **API密钥安全**: 请不要将API密钥提交到版本控制系统中
2. **API费用**: DeepSeek API按使用量计费，新用户通常有免费额度
3. **网络连接**: API调用需要稳定的网络连接
4. **错误处理**: 项目已包含完善的错误处理机制，API调用失败时会使用备用方案

## 技术栈

### 后端技术
- **框架**: Django 5.2.1
- **数据库**: SQLite (开发环境)
- **图像处理**: Pillow
- **表单处理**: django-crispy-forms, django-crispy-bootstrap4, django-widget-tweaks
- **HTTP请求**: requests >= 2.25.0

### 前端技术
- **UI框架**: Bootstrap 4
- **核心技术**: HTML5, CSS3, JavaScript (ES6+)
- **图标**: Font Awesome
- **AJAX**: Fetch API
- **响应式设计**: CSS Grid, Flexbox

### AI服务
- **API提供商**: DeepSeek
- **模型**: deepseek-chat (DeepSeek-V3)
- **功能**: 智能摘要生成、评论生成、内容推荐

### 开发工具
- **IDE**: PyCharm, Cursor
- **版本控制**: Git
- **包管理**: pip, requirements.txt

## 使用说明

### 基本操作

1. **注册和登录**
   - 访问 `/accounts/signup/` 注册新账户
   - 访问 `/accounts/login/` 登录系统

2. **内容管理**
   - 发布内容：点击导航栏的"发布内容"按钮
   - 管理内容：在个人中心查看和编辑已发布的内容
   - 设置隐私：可选择公开或私有发布

3. **互动功能**
   - 点赞：点击内容下方的点赞按钮（未登录用户会收到友好提示）
   - 评论：在内容详情页面发表评论
   - 收藏：收藏喜欢的内容到个人收藏夹

4. **AI功能**
   - 自动摘要：发布内容时系统会自动生成摘要
   - AI评论：系统会为热门内容生成智能评论

### 管理员功能

- 访问 `/admin/` 进入后台管理
- 管理用户、内容、分类和标签
- 查看系统统计数据

## 常见问题

### Q: DeepSeek API调用失败怎么办？
A: 检查API密钥配置是否正确，确保网络连接正常。系统会在API调用失败时使用备用方案。

### Q: 点赞功能不工作？
A: 确保JavaScript已启用，检查浏览器控制台是否有错误信息。未登录用户会收到登录提示。

### Q: 如何修改个人资料？
A: 登录后点击右上角头像，选择"个人资料"进行编辑。

### Q: 内容无法上传图片？
A: 检查media目录权限，确保Django有写入权限。支持的图片格式：JPG, PNG, GIF。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

### 贡献指南

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 联系方式

- 项目维护者：顾奕扬
- 学院：信息科技学院
- 专业：数据科学与大数据技术