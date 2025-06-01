/**
 * Light Theme Bug 诊断脚本
 * 自动检测浅色主题下可能存在的样式问题
 * 作者：顾奕扬（少爷）
 */

class LightThemeBugDiagnoser {
    constructor() {
        this.issues = [];
        this.checkedElements = new Set();
    }

    /**
     * 主要诊断入口
     */
    diagnose() {
        console.log('🔍 开始诊断 Light Theme 样式问题...');
        
        this.checkTransparentTextIssues();
        this.checkContrastIssues();
        this.checkGradientTextIssues();
        this.checkInvisibleElements();
        
        this.reportResults();
        return this.issues;
    }

    /**
     * 检测透明文字问题
     */
    checkTransparentTextIssues() {
        const elements = document.querySelectorAll('*');
        
        elements.forEach(el => {
            const styles = window.getComputedStyle(el);
            const textFillColor = styles.webkitTextFillColor;
            const backgroundClip = styles.webkitBackgroundClip;
            
            // 检测使用了透明文字 + 背景裁剪的元素
            if (textFillColor === 'transparent' && backgroundClip === 'text') {
                const rect = el.getBoundingClientRect();
                if (rect.width > 0 && rect.height > 0) {
                    this.issues.push({
                        type: 'transparent-text',
                        element: el,
                        selector: this.getSelector(el),
                        description: '使用了透明文字 + 背景裁剪，在浅色主题下可能不可见',
                        severity: 'high',
                        suggestedFix: `body.theme-light ${this.getSelector(el)} { background: none !important; -webkit-background-clip: unset !important; -webkit-text-fill-color: inherit !important; color: #333 !important; }`
                    });
                }
            }
        });
    }

    /**
     * 检测对比度问题
     */
    checkContrastIssues() {
        const textElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, p, span, a, button, .text-primary, .text-secondary, .text-info, .text-warning, .text-danger, .text-success');
        
        textElements.forEach(el => {
            if (this.checkedElements.has(el)) return;
            this.checkedElements.add(el);
            
            const styles = window.getComputedStyle(el);
            const color = styles.color;
            const backgroundColor = this.getEffectiveBackgroundColor(el);
            
            const contrast = this.calculateContrast(color, backgroundColor);
            
            if (contrast < 4.5) { // WCAG AA 标准
                this.issues.push({
                    type: 'low-contrast',
                    element: el,
                    selector: this.getSelector(el),
                    description: `对比度过低 (${contrast.toFixed(2)})，在浅色主题下可读性差`,
                    severity: 'medium',
                    contrast: contrast,
                    suggestedFix: `body.theme-light ${this.getSelector(el)} { color: #333 !important; }`
                });
            }
        });
    }

    /**
     * 检测渐变文字问题
     */
    checkGradientTextIssues() {
        const elements = document.querySelectorAll('[class*="text-"], .stats-card h3, .counter');
        
        elements.forEach(el => {
            const styles = window.getComputedStyle(el);
            const background = styles.background;
            const backgroundImage = styles.backgroundImage;
            
            // 检测使用了渐变背景的文字
            if ((background.includes('gradient') || backgroundImage.includes('gradient')) && 
                styles.webkitBackgroundClip === 'text') {
                
                this.issues.push({
                    type: 'gradient-text',
                    element: el,
                    selector: this.getSelector(el),
                    description: '使用了渐变文字效果，在浅色主题下可能不可见',
                    severity: 'high',
                    suggestedFix: `body.theme-light ${this.getSelector(el)} { background: none !important; -webkit-background-clip: unset !important; -webkit-text-fill-color: inherit !important; color: #333 !important; text-shadow: 0 1px 2px rgba(0,0,0,0.1) !important; }`
                });
            }
        });
    }

    /**
     * 检测不可见元素
     */
    checkInvisibleElements() {
        const elements = document.querySelectorAll('*');
        
        elements.forEach(el => {
            const rect = el.getBoundingClientRect();
            const styles = window.getComputedStyle(el);
            
            // 跳过没有内容或隐藏的元素
            if (rect.width === 0 || rect.height === 0 || 
                styles.display === 'none' || styles.visibility === 'hidden') {
                return;
            }
            
            // 检测可能不可见的文字元素
            if (el.textContent && el.textContent.trim()) {
                const color = styles.color;
                const backgroundColor = this.getEffectiveBackgroundColor(el);
                
                // 如果文字颜色和背景色过于接近
                if (this.colorsAreSimilar(color, backgroundColor)) {
                    this.issues.push({
                        type: 'invisible-text',
                        element: el,
                        selector: this.getSelector(el),
                        description: '文字颜色与背景色过于接近，可能不可见',
                        severity: 'medium',
                        suggestedFix: `body.theme-light ${this.getSelector(el)} { color: #333 !important; }`
                    });
                }
            }
        });
    }

    /**
     * 获取元素的有效背景色
     */
    getEffectiveBackgroundColor(element) {
        let current = element;
        while (current && current !== document.body) {
            const styles = window.getComputedStyle(current);
            const bgColor = styles.backgroundColor;
            
            if (bgColor && bgColor !== 'rgba(0, 0, 0, 0)' && bgColor !== 'transparent') {
                return bgColor;
            }
            current = current.parentElement;
        }
        
        // 默认返回 body 的背景色或白色
        const bodyStyles = window.getComputedStyle(document.body);
        return bodyStyles.backgroundColor || '#ffffff';
    }

    /**
     * 计算颜色对比度
     */
    calculateContrast(color1, color2) {
        const rgb1 = this.parseColor(color1);
        const rgb2 = this.parseColor(color2);
        
        const l1 = this.getLuminance(rgb1);
        const l2 = this.getLuminance(rgb2);
        
        const lighter = Math.max(l1, l2);
        const darker = Math.min(l1, l2);
        
        return (lighter + 0.05) / (darker + 0.05);
    }

    /**
     * 解析颜色值
     */
    parseColor(color) {
        const div = document.createElement('div');
        div.style.color = color;
        document.body.appendChild(div);
        const computedColor = window.getComputedStyle(div).color;
        document.body.removeChild(div);
        
        const match = computedColor.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
        if (match) {
            return {
                r: parseInt(match[1]),
                g: parseInt(match[2]),
                b: parseInt(match[3])
            };
        }
        return { r: 0, g: 0, b: 0 };
    }

    /**
     * 计算亮度
     */
    getLuminance(rgb) {
        const { r, g, b } = rgb;
        const [rs, gs, bs] = [r, g, b].map(c => {
            c = c / 255;
            return c <= 0.03928 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
        });
        return 0.2126 * rs + 0.7152 * gs + 0.0722 * bs;
    }

    /**
     * 判断两个颜色是否相似
     */
    colorsAreSimilar(color1, color2) {
        const rgb1 = this.parseColor(color1);
        const rgb2 = this.parseColor(color2);
        
        const diff = Math.abs(rgb1.r - rgb2.r) + Math.abs(rgb1.g - rgb2.g) + Math.abs(rgb1.b - rgb2.b);
        return diff < 50; // 阈值可调整
    }

    /**
     * 获取元素选择器
     */
    getSelector(element) {
        if (element.id) {
            return `#${element.id}`;
        }
        
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                return `.${classes.join('.')}`;
            }
        }
        
        return element.tagName.toLowerCase();
    }

    /**
     * 报告诊断结果
     */
    reportResults() {
        console.log('\n📊 Light Theme 诊断报告');
        console.log('=' .repeat(50));
        
        if (this.issues.length === 0) {
            console.log('✅ 未发现明显的浅色主题样式问题');
            return;
        }
        
        const highSeverity = this.issues.filter(i => i.severity === 'high');
        const mediumSeverity = this.issues.filter(i => i.severity === 'medium');
        
        console.log(`🔴 高优先级问题: ${highSeverity.length} 个`);
        console.log(`🟡 中优先级问题: ${mediumSeverity.length} 个`);
        console.log(`📝 总计问题: ${this.issues.length} 个\n`);
        
        this.issues.forEach((issue, index) => {
            const icon = issue.severity === 'high' ? '🔴' : '🟡';
            console.log(`${icon} 问题 ${index + 1}: ${issue.type}`);
            console.log(`   选择器: ${issue.selector}`);
            console.log(`   描述: ${issue.description}`);
            console.log(`   建议修复: ${issue.suggestedFix}`);
            console.log('');
        });
        
        // 生成修复 CSS
        this.generateFixCSS();
    }

    /**
     * 生成修复 CSS
     */
    generateFixCSS() {
        console.log('🔧 自动生成的修复 CSS:');
        console.log('=' .repeat(50));
        
        const css = this.issues.map(issue => {
            return `/* 修复: ${issue.description} */\n${issue.suggestedFix}`;
        }).join('\n\n');
        
        console.log(css);
        
        // 尝试复制到剪贴板
        if (navigator.clipboard) {
            navigator.clipboard.writeText(css).then(() => {
                console.log('\n📋 修复 CSS 已复制到剪贴板');
            }).catch(() => {
                console.log('\n❌ 无法复制到剪贴板，请手动复制上述 CSS');
            });
        }
    }

    /**
     * 实时监控主题切换
     */
    startMonitoring() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'attributes' && 
                    mutation.attributeName === 'class' && 
                    mutation.target === document.body) {
                    
                    if (document.body.classList.contains('theme-light')) {
                        console.log('🌞 检测到切换到浅色主题，开始诊断...');
                        setTimeout(() => this.diagnose(), 100);
                    }
                }
            });
        });
        
        observer.observe(document.body, {
            attributes: true,
            attributeFilter: ['class']
        });
        
        console.log('👁️ 已启动主题切换监控');
    }
}

// 全局暴露
window.LightThemeBugDiagnoser = LightThemeBugDiagnoser;

// 自动启动（如果当前是浅色主题）
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const diagnoser = new LightThemeBugDiagnoser();
        diagnoser.startMonitoring();
        
        if (document.body.classList.contains('theme-light')) {
            console.log('🌞 当前为浅色主题，开始自动诊断...');
            diagnoser.diagnose();
        }
    });
} else {
    const diagnoser = new LightThemeBugDiagnoser();
    diagnoser.startMonitoring();
    
    if (document.body.classList.contains('theme-light')) {
        console.log('🌞 当前为浅色主题，开始自动诊断...');
        diagnoser.diagnose();
    }
}

// 手动诊断命令
console.log('💡 使用方法:');
console.log('  const diagnoser = new LightThemeBugDiagnoser();');
console.log('  diagnoser.diagnose(); // 手动诊断');
console.log('  diagnoser.startMonitoring(); // 启动监控');