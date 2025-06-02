// 主要JavaScript功能

// DOM加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化所有功能
    initializeTooltips();
    initializeAlerts();
    initializeFileUpload();
    initializeSearch();
    initializeRating();
    initializeComments();
    initializeLikes();
    initializeDropdownPortal();
    initializeThemeToggle();
});

// 初始化工具提示
function initializeTooltips() {
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// 初始化警告框自动关闭
function initializeAlerts() {
    // 自动关闭成功消息
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert-success');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);
}

// 初始化文件上传
function initializeFileUpload() {
    var fileUploadAreas = document.querySelectorAll('.file-upload');
    
    fileUploadAreas.forEach(function(area) {
        var input = area.querySelector('input[type="file"]');
        
        // 点击上传区域触发文件选择
        area.addEventListener('click', function() {
            input.click();
        });
        
        // 拖拽上传
        area.addEventListener('dragover', function(e) {
            e.preventDefault();
            area.classList.add('dragover');
        });
        
        area.addEventListener('dragleave', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
        });
        
        area.addEventListener('drop', function(e) {
            e.preventDefault();
            area.classList.remove('dragover');
            
            var files = e.dataTransfer.files;
            if (files.length > 0) {
                input.files = files;
                handleFileSelect(files[0], area);
            }
        });
        
        // 文件选择处理
        input.addEventListener('change', function(e) {
            if (e.target.files.length > 0) {
                handleFileSelect(e.target.files[0], area);
            }
        });
    });
}

// 处理文件选择
function handleFileSelect(file, area) {
    var preview = area.querySelector('.file-preview');
    if (!preview) {
        preview = document.createElement('div');
        preview.className = 'file-preview mt-2';
        area.appendChild(preview);
    }
    
    if (file.type.startsWith('image/')) {
        var reader = new FileReader();
        reader.onload = function(e) {
            preview.innerHTML = '<img src="' + e.target.result + '" class="img-thumbnail" style="max-width: 200px; max-height: 200px;">';
        };
        reader.readAsDataURL(file);
    } else {
        preview.innerHTML = '<p class="text-muted"><i class="fas fa-file"></i> ' + file.name + '</p>';
    }
}

// 初始化搜索功能
function initializeSearch() {
    var searchForm = document.querySelector('.search-form');
    var searchInput = document.querySelector('.search-input');
    var searchResults = document.querySelector('.search-results');
    
    if (searchInput) {
        // 实时搜索
        var searchTimeout;
        searchInput.addEventListener('input', function() {
            clearTimeout(searchTimeout);
            var query = this.value.trim();
            
            if (query.length >= 2) {
                searchTimeout = setTimeout(function() {
                    performSearch(query);
                }, 300);
            } else if (searchResults) {
                searchResults.innerHTML = '';
                searchResults.style.display = 'none';
            }
        });
    }
}

// 执行搜索
function performSearch(query) {
    // 这里可以实现AJAX搜索
    console.log('搜索:', query);
    // 示例实现
    // fetch('/api/search/?q=' + encodeURIComponent(query))
    //     .then(response => response.json())
    //     .then(data => displaySearchResults(data));
}

// 显示搜索结果
function displaySearchResults(results) {
    var searchResults = document.querySelector('.search-results');
    if (!searchResults) return;
    
    if (results.length === 0) {
        searchResults.innerHTML = '<p class="text-muted p-3">未找到相关内容</p>';
    } else {
        var html = results.map(function(item) {
            return '<a href="' + item.url + '" class="list-group-item list-group-item-action">' +
                   '<h6 class="mb-1">' + item.title + '</h6>' +
                   '<p class="mb-1 text-muted">' + item.summary + '</p>' +
                   '</a>';
        }).join('');
        searchResults.innerHTML = html;
    }
    
    searchResults.style.display = 'block';
}


// 初始化评分功能
function initializeRating() {
    var ratingContainers = document.querySelectorAll('.rating-container');
    
    ratingContainers.forEach(function(container) {
        var stars = container.querySelectorAll('.fa-star');
        var ratingInput = container.querySelector('input[name="rating"]');
        
        stars.forEach(function(star, index) {
            star.addEventListener('click', function() {
                var rating = index + 1;
                updateStarDisplay(stars, rating);
                if (ratingInput) {
                    ratingInput.value = rating;
                }
                submitRating(container.dataset.contentId, rating);
            });
            
            star.addEventListener('mouseenter', function() {
                updateStarDisplay(stars, index + 1);
            });
        });
        
        container.addEventListener('mouseleave', function() {
            var currentRating = ratingInput ? ratingInput.value : 0;
            updateStarDisplay(stars, currentRating);
        });
    });
}

// 更新星星显示
function updateStarDisplay(stars, rating) {
    stars.forEach(function(star, index) {
        if (index < rating) {
            star.classList.remove('far');
            star.classList.add('fas');
        } else {
            star.classList.remove('fas');
            star.classList.add('far');
        }
    });
}

// 提交评分
function submitRating(contentId, rating) {
    // 这里可以实现AJAX提交评分
    console.log('提交评分:', contentId, rating);
    // fetch('/api/rating/', {
    //     method: 'POST',
    //     headers: {
    //         'Content-Type': 'application/json',
    //         'X-CSRFToken': getCookie('csrftoken')
    //     },
    //     body: JSON.stringify({
    //         content_id: contentId,
    //         rating: rating
    //     })
    // });
}

// 初始化评论功能
function initializeComments() {
    // 回复按钮
    var replyButtons = document.querySelectorAll('.reply-btn');
    replyButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var commentId = this.dataset.commentId;
            toggleReplyForm(commentId);
        });
    });
    
    // 加载更多评论
    var loadMoreBtn = document.querySelector('.load-more-comments');
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener('click', function() {
            loadMoreComments();
        });
    }
}

// 切换回复表单
function toggleReplyForm(commentId) {
    var replyForm = document.querySelector('.reply-form-' + commentId);
    if (replyForm) {
        replyForm.style.display = replyForm.style.display === 'none' ? 'block' : 'none';
    }
}

// 加载更多评论
function loadMoreComments() {
    var btn = document.querySelector('.load-more-comments');
    var page = parseInt(btn.dataset.page) + 1;
    var contentId = btn.dataset.contentId;
    
    btn.innerHTML = '<span class="loading"></span> 加载中...';
    btn.disabled = true;
    
    // 这里可以实现AJAX加载更多评论
    console.log('加载更多评论:', page);
    // fetch('/api/comments/?content_id=' + contentId + '&page=' + page)
    //     .then(response => response.json())
    //     .then(data => appendComments(data));
}

// 初始化点赞功能
function initializeLikes() {
    var likeButtons = document.querySelectorAll('.like-btn');
    
    likeButtons.forEach(function(btn) {
        btn.addEventListener('click', function() {
            var contentId = this.dataset.contentId;
            var isLiked = this.classList.contains('liked');
            toggleLike(contentId, !isLiked, this);
        });
    });
}

// 切换点赞状态
function toggleLike(contentId, isLike, button) {
    var icon = button.querySelector('i');
    var countSpan = button.querySelector('.like-count');
    var currentCount = parseInt(countSpan.textContent);
    
    // 保存原始状态，用于错误时恢复
    var originalLiked = button.classList.contains('liked');
    var originalCount = currentCount;
    
    // 立即更新UI给用户反馈
    if (isLike) {
        button.classList.add('liked');
        countSpan.textContent = currentCount + 1;
    } else {
        button.classList.remove('liked');
        countSpan.textContent = currentCount - 1;
    }
    
    // 发送AJAX请求
    fetch('/content/' + contentId + '/toggle-like/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => {
        if (response.status === 401) {
            return response.json().then(data => {
                // 用户未登录，显示提示信息
                alert(data.message || '请先登录后再进行点赞操作');
                // 恢复原始状态
                restoreButtonState();
                // 可选择是否跳转到登录页面
                if (confirm('是否前往登录页面？')) {
                    window.location.href = '/accounts/login/';
                }
                return null;
            });
        }
        return response.json();
    })
    .then(data => {
        if (data && data.success) {
            // 更新点赞数
            countSpan.textContent = data.likes_count;
            // 更新按钮状态
            if (data.liked) {
                button.classList.add('liked');
            } else {
                button.classList.remove('liked');
            }
        } else if (data && !data.success) {
            console.error('点赞操作失败:', data.error || '未知错误');
            alert('点赞操作失败: ' + (data.message || data.error || '未知错误'));
            // 恢复原始状态
            restoreButtonState();
        }
    })
    .catch(error => {
        console.error('点赞操作失败:', error);
        alert('网络错误，请稍后重试');
        // 恢复原始状态
        restoreButtonState();
    });
    
    function restoreButtonState() {
        // 恢复到原始状态
        if (originalLiked) {
            button.classList.add('liked');
        } else {
            button.classList.remove('liked');
        }
        countSpan.textContent = originalCount;
    }
}


// 获取Cookie值
function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 显示通知
function showNotification(message, type) {
    if (typeof type === 'undefined') {
        type = 'info';
    }
    var notification = document.createElement('div');
    notification.className = 'alert alert-' + type + ' alert-dismissible fade show notification';
    notification.innerHTML = message + 
        '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>';
    
    document.body.appendChild(notification);
    
    // 自动关闭
    setTimeout(function() {
        if (notification.parentNode) {
            notification.remove();
        }
    }, 5000);
}

// 确认对话框
function confirmAction(message, callback) {
    if (confirm(message)) {
        callback();
    }
}

// 平滑滚动
function smoothScrollTo(element) {
    element.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
    });
}

// 格式化时间
function formatTime(timestamp) {
    var date = new Date(timestamp);
    var now = new Date();
    var diff = now - date;
    
    var seconds = Math.floor(diff / 1000);
    var minutes = Math.floor(seconds / 60);
    var hours = Math.floor(minutes / 60);
    var days = Math.floor(hours / 24);
    
    if (days > 0) {
        return days + '天前';
    } else if (hours > 0) {
        return hours + '小时前';
    } else if (minutes > 0) {
        return minutes + '分钟前';
    } else {
        return '刚刚';
    }
}

// 防抖函数
function debounce(func, wait) {
    var timeout;
    return function executedFunction() {
        var args = arguments;
        var context = this;
        var later = function() {
            clearTimeout(timeout);
            func.apply(context, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// 节流函数
function throttle(func, limit) {
    var inThrottle;
    return function() {
        var args = arguments;
        var context = this;
        if (!inThrottle) {
            func.apply(context, args);
            inThrottle = true;
            setTimeout(function() {
                inThrottle = false;
            }, limit);
        }
    };
}

// 下拉菜单Portal机制 - 解决堆叠上下文问题
function initializeDropdownPortal() {
    const dropdowns = document.querySelectorAll('.dropdown');
    
    dropdowns.forEach(dropdown => {
        const toggle = dropdown.querySelector('.dropdown-toggle');
        const menu = dropdown.querySelector('.dropdown-menu');
        
        if (!toggle || !menu) return;
        
        // 点击切换显示
        toggle.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            // 关闭其他下拉菜单
            hideAllDropdownMenus();
            
            // 切换当前菜单
            const portal = document.querySelector('.dropdown-portal');
            if (portal && portal.classList.contains('show')) {
                hideDropdownMenu();
            } else {
                showDropdownMenu(toggle, menu);
            }
        });
    });
    
    // 点击外部关闭
    document.addEventListener('click', function(e) {
        if (!e.target.closest('.dropdown') && !e.target.closest('.dropdown-portal')) {
            hideAllDropdownMenus();
        }
    });
    
    // ESC键关闭
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') {
            hideAllDropdownMenus();
        }
    });
}

function showDropdownMenu(toggle, menu) {
    // 创建Portal容器 - 强制挂载到body末尾
    let portal = document.querySelector('.dropdown-portal');
    if (!portal) {
        portal = document.createElement('div');
        portal.className = 'dropdown-portal content-dropdown';
        portal.style.position = 'absolute';
        portal.style.top = '0';
        portal.style.left = '0';
        portal.style.zIndex = '2147483647'; // 超高层级
        portal.style.transform = 'none'; // 避免transform上下文干扰
        portal.style.pointerEvents = 'none';
        document.body.appendChild(portal); // 必须是body直接子元素
    }
    
    // 克隆菜单到Portal
    const clonedMenu = menu.cloneNode(true);
    clonedMenu.style.position = 'absolute';
    clonedMenu.style.display = 'block';
    clonedMenu.style.zIndex = '2147483647';
    clonedMenu.style.pointerEvents = 'auto';
    portal.innerHTML = '';
    portal.appendChild(clonedMenu);
    
    // 计算位置
    const toggleRect = toggle.getBoundingClientRect();
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollLeft = window.pageXOffset || document.documentElement.scrollLeft;
    
    clonedMenu.style.top = (toggleRect.bottom + scrollTop + 4) + 'px';
    clonedMenu.style.left = (toggleRect.left + scrollLeft) + 'px';
    
    // 复制事件监听器
    const originalItems = menu.querySelectorAll('.dropdown-item');
    const clonedItems = clonedMenu.querySelectorAll('.dropdown-item');
    
    clonedItems.forEach((item, index) => {
        const originalItem = originalItems[index];
        if (originalItem) {
            // 复制点击事件
            item.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                
                // 如果是链接，直接跳转
                if (originalItem.tagName === 'A' && originalItem.href) {
                    window.location.href = originalItem.href;
                    return;
                }
                
                // 否则触发原始点击事件
                originalItem.click();
                hideDropdownMenu();
            });
        }
    });
    
    // 触发显示动画
    requestAnimationFrame(() => {
        portal.classList.add('show');
    });
}

function hideDropdownMenu() {
    const portal = document.querySelector('.dropdown-portal');
    if (portal) {
        portal.classList.remove('show');
        // 等待动画完成后移除
        setTimeout(() => {
            if (portal.parentNode) {
                portal.remove();
            }
        }, 300);
    }
}

function hideAllDropdownMenus() {
    const portals = document.querySelectorAll('.dropdown-portal');
    portals.forEach(portal => {
        portal.classList.remove('show');
        setTimeout(() => {
            if (portal.parentNode) {
                portal.remove();
            }
        }, 300);
    });
}

// 主题切换功能
function initializeThemeToggle() {
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.querySelector('.theme-icon');
    
    if (!themeToggle || !themeIcon) return;
    
    // 从localStorage获取保存的主题，默认为浅色主题
    const savedTheme = localStorage.getItem('theme');
    const currentTheme = savedTheme || 'light';
    
    // 应用初始主题
    applyTheme(currentTheme);
    
    // 点击切换主题
    themeToggle.addEventListener('click', function() {
        const body = document.body;
        const isDark = body.classList.contains('theme-dark');
        const newTheme = isDark ? 'light' : 'dark';
        
        applyTheme(newTheme);
        localStorage.setItem('theme', newTheme);
        
        // 添加点击动画
        themeToggle.style.transform = 'scale(0.9)';
        setTimeout(() => {
            themeToggle.style.transform = '';
        }, 150);
    });
    
    // 监听系统主题变化（仅在用户未手动设置时生效）
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', function(e) {
        if (!localStorage.getItem('theme')) {
            applyTheme('light'); // 始终默认浅色主题
        }
    });
}

function applyTheme(theme) {
    const body = document.body;
    const themeIcon = document.querySelector('.theme-icon');
    
    // 清除所有主题类
    body.classList.remove('theme-light', 'theme-dark');
    
    if (theme === 'dark') {
        body.classList.add('theme-dark');
        if (themeIcon) themeIcon.textContent = '☀️'; // 深色模式显示太阳图标
    } else {
        // 浅色主题不需要添加类，使用默认的:root变量
        if (themeIcon) themeIcon.textContent = '🌙'; // 浅色模式显示月亮图标
    }
    
    // 添加过渡效果
    body.style.transition = 'background-color 0.3s ease, color 0.3s ease';
    setTimeout(() => {
        body.style.transition = '';
    }, 300);
}