// 强制修复 .stats-card h3 透明文字问题
// 在页面加载后自动注入样式，通过 JS 强制覆盖样式

(function() {
    'use strict';
    
    // 等待 DOM 加载完成
    function applyStatsCardFix() {
        // 创建强制样式
        const forceStyle = document.createElement('style');
        forceStyle.id = 'force-stats-card-fix';
        forceStyle.innerHTML = `
            /* 强制修复 .stats-card h3 透明文字问题 - 最高优先级 */
            body.theme-light .stats-card h3,
            body.theme-light .stats-card h3.text-primary,
            body.theme-light .stats-card h3.text-success,
            body.theme-light .stats-card h3.text-danger,
            body.theme-light .stats-card h3.text-info,
            body.theme-light .stats-card h3.text-warning,
            body.theme-light .stats-card h3.counter,
            body.theme-light .stats-card h3[class*="text-"] {
                background: none !important;
                -webkit-background-clip: unset !important;
                -webkit-text-fill-color: unset !important;
                background-clip: unset !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
            }
            
            /* 特定颜色强制设置 */
            body.theme-light .stats-card h3.text-primary {
                color: #0d6efd !important;
            }
            
            body.theme-light .stats-card h3.text-success {
                color: #198754 !important;
            }
            
            body.theme-light .stats-card h3.text-danger {
                color: #dc3545 !important;
            }
            
            body.theme-light .stats-card h3.text-info {
                color: #0dcaf0 !important;
            }
            
            body.theme-light .stats-card h3.text-warning {
                color: #ffc107 !important;
            }
            
            /* 默认深色文字 */
            body.theme-light .stats-card h3:not([class*="text-"]),
            body.theme-light .stats-card h3.counter {
                color: #1a202c !important;
            }
        `;
        
        // 移除已存在的强制样式（如果有）
        const existingStyle = document.getElementById('force-stats-card-fix');
        if (existingStyle) {
            existingStyle.remove();
        }
        
        // 添加到 head
        document.head.appendChild(forceStyle);
        
        console.log('✅ 强制修复 .stats-card h3 透明文字样式已应用');
        
        // 额外检查：直接设置元素样式
        const statsCardH3Elements = document.querySelectorAll('.stats-card h3');
        if (statsCardH3Elements.length > 0) {
            console.log(`🔍 找到 ${statsCardH3Elements.length} 个 .stats-card h3 元素`);
            
            statsCardH3Elements.forEach((element, index) => {
                // 强制重置 webkit 属性
                element.style.setProperty('background', 'none', 'important');
                element.style.setProperty('-webkit-background-clip', 'unset', 'important');
                element.style.setProperty('-webkit-text-fill-color', 'unset', 'important');
                element.style.setProperty('background-clip', 'unset', 'important');
                
                // 根据类设置颜色
                if (element.classList.contains('text-primary')) {
                    element.style.setProperty('color', '#0d6efd', 'important');
                } else if (element.classList.contains('text-success')) {
                    element.style.setProperty('color', '#198754', 'important');
                } else if (element.classList.contains('text-danger')) {
                    element.style.setProperty('color', '#dc3545', 'important');
                } else if (element.classList.contains('text-info')) {
                    element.style.setProperty('color', '#0dcaf0', 'important');
                } else if (element.classList.contains('text-warning')) {
                    element.style.setProperty('color', '#ffc107', 'important');
                } else {
                    element.style.setProperty('color', '#1a202c', 'important');
                }
                
                console.log(`📝 元素 ${index + 1}: 类名 = ${element.className}, 最终颜色 = ${getComputedStyle(element).color}`);
            });
        } else {
            console.log('⚠️ 未找到 .stats-card h3 元素');
        }
    }
    
    // 主题切换监听
    function watchThemeChanges() {
        const observer = new MutationObserver(function(mutations) {
            mutations.forEach(function(mutation) {
                if (mutation.type === 'attributes' && mutation.attributeName === 'class') {
                    const body = document.body;
                    if (body.classList.contains('theme-light')) {
                        console.log('🌞 检测到切换到浅色主题，重新应用修复');
                        setTimeout(applyStatsCardFix, 100);
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class']
        });
    }
    
    // 页面加载完成后执行
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', function() {
            applyStatsCardFix();
            watchThemeChanges();
        });
    } else {
        applyStatsCardFix();
        watchThemeChanges();
    }
    
    // 窗口加载完成后再次执行（确保所有资源加载完毕）
    window.addEventListener('load', function() {
        setTimeout(applyStatsCardFix, 500);
    });
    
})();