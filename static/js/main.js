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
                icon.classList.remove('far');
                icon.classList.add('fas');
            } else {
                button.classList.remove('liked');
                icon.classList.remove('fas');
                icon.classList.add('far');
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
            icon.classList.remove('far');
            icon.classList.add('fas');
        } else {
            button.classList.remove('liked');
            icon.classList.remove('fas');
            icon.classList.add('far');
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

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeLikes();
});