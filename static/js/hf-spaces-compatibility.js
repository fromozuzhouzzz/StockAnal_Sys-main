/**
 * Hugging Face Spaces 兼容性脚本
 * 检测环境并应用相应的样式修复
 */
(function() {
    'use strict';

    // 检测是否在 Hugging Face Spaces 环境中
    function isHuggingFaceSpaces() {
        return window.location.hostname.includes('hf.space') || 
               window.location.hostname.includes('huggingface.co') ||
               document.querySelector('meta[name="hf-spaces"]') !== null;
    }

    // 检测CSS变量支持
    function supportsCSSVariables() {
        return window.CSS && CSS.supports && CSS.supports('color', 'var(--test)');
    }

    // 检测静态资源加载状态
    function checkStaticResourcesLoading() {
        const cssLinks = document.querySelectorAll('link[rel="stylesheet"]');
        const loadedCount = 0;
        const totalCount = cssLinks.length;
        
        cssLinks.forEach(function(link) {
            link.addEventListener('load', function() {
                console.log('CSS文件加载成功:', link.href);
            });
            
            link.addEventListener('error', function() {
                console.error('CSS文件加载失败:', link.href);
                // 尝试重新加载
                setTimeout(function() {
                    const newLink = document.createElement('link');
                    newLink.rel = 'stylesheet';
                    newLink.href = link.href + '&retry=' + Date.now();
                    document.head.appendChild(newLink);
                }, 1000);
            });
        });
    }

    // 应用HF Spaces特定的修复
    function applyHFSpacesFixes() {
        console.log('应用 Hugging Face Spaces 兼容性修复...');
        
        // 添加环境标识类
        document.body.classList.add('hf-spaces-env');
        
        // 强制刷新样式
        const styleSheets = document.styleSheets;
        for (let i = 0; i < styleSheets.length; i++) {
            try {
                if (styleSheets[i].href && styleSheets[i].href.includes('md3-styles.css')) {
                    // 触发样式重新计算
                    document.body.style.display = 'none';
                    document.body.offsetHeight; // 触发重排
                    document.body.style.display = '';
                    break;
                }
            } catch (e) {
                console.warn('无法访问样式表:', e);
            }
        }
        
        // 检查关键样式是否正确应用
        setTimeout(function() {
            checkCriticalStyles();
        }, 500);
    }

    // 检查关键样式是否正确应用
    function checkCriticalStyles() {
        const testElement = document.createElement('div');
        testElement.className = 'md3-card';
        testElement.style.visibility = 'hidden';
        testElement.style.position = 'absolute';
        document.body.appendChild(testElement);
        
        const computedStyle = window.getComputedStyle(testElement);
        const backgroundColor = computedStyle.backgroundColor;
        
        // 检查是否有正确的背景色
        if (backgroundColor === 'rgba(0, 0, 0, 0)' || backgroundColor === 'transparent') {
            console.warn('检测到样式加载问题，应用紧急修复...');
            applyEmergencyStyles();
        } else {
            console.log('样式检查通过，背景色:', backgroundColor);
        }
        
        document.body.removeChild(testElement);
    }

    // 应用紧急样式修复
    function applyEmergencyStyles() {
        const emergencyCSS = `
            <style id="hf-emergency-styles">
                body {
                    font-family: 'Roboto', 'Noto Sans SC', sans-serif !important;
                    background-color: #FEFBFF !important;
                    color: #1C1B1F !important;
                }
                .md3-navbar {
                    background-color: #F7F2FA !important;
                    border-bottom: 1px solid #CAC4D0 !important;
                }
                .md3-card {
                    background-color: #F7F2FA !important;
                    border: 1px solid #CAC4D0 !important;
                    border-radius: 16px !important;
                }
                .md3-button-filled {
                    background-color: #1565C0 !important;
                    color: #FFFFFF !important;
                }
                .trend-up, .md3-text-bull {
                    color: #d32f2f !important;
                }
                .trend-down, .md3-text-bear {
                    color: #2e7d32 !important;
                }
                .md3-text-primary {
                    color: #1565C0 !important;
                }
                .md3-text-on-surface {
                    color: #1C1B1F !important;
                }
                .md3-text-on-surface-variant {
                    color: #49454F !important;
                }
            </style>
        `;
        
        document.head.insertAdjacentHTML('beforeend', emergencyCSS);
        console.log('紧急样式修复已应用');
    }

    // 监听主题变化事件
    function setupThemeChangeListener() {
        document.addEventListener('themechange', function(event) {
            console.log('主题变化检测到:', event.detail.theme);
            // 在主题变化后重新检查样式
            setTimeout(function() {
                checkCriticalStyles();
            }, 100);
        });
    }

    // 添加调试信息
    function addDebugInfo() {
        if (window.location.search.includes('debug=true')) {
            const debugInfo = document.createElement('div');
            debugInfo.id = 'hf-debug-info';
            debugInfo.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0,0,0,0.8);
                color: white;
                padding: 10px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 10000;
                max-width: 300px;
            `;
            
            const info = [
                'HF Spaces: ' + isHuggingFaceSpaces(),
                'CSS Variables: ' + supportsCSSVariables(),
                'User Agent: ' + navigator.userAgent.substring(0, 50) + '...',
                'Hostname: ' + window.location.hostname
            ];
            
            debugInfo.innerHTML = info.join('<br>');
            document.body.appendChild(debugInfo);
            
            // 5秒后自动隐藏
            setTimeout(function() {
                debugInfo.style.display = 'none';
            }, 5000);
        }
    }

    // 主初始化函数
    function init() {
        console.log('HF Spaces 兼容性脚本初始化...');
        console.log('环境检测 - HF Spaces:', isHuggingFaceSpaces());
        console.log('环境检测 - CSS Variables:', supportsCSSVariables());
        
        // 检查静态资源加载
        checkStaticResourcesLoading();
        
        // 如果在HF Spaces环境或不支持CSS变量，应用修复
        if (isHuggingFaceSpaces() || !supportsCSSVariables()) {
            applyHFSpacesFixes();
        }
        
        // 设置主题变化监听器
        setupThemeChangeListener();
        
        // 添加调试信息
        addDebugInfo();
        
        console.log('HF Spaces 兼容性脚本初始化完成');
    }

    // DOM加载完成后初始化
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // 导出到全局作用域供调试使用
    window.HFSpacesCompatibility = {
        isHuggingFaceSpaces: isHuggingFaceSpaces,
        supportsCSSVariables: supportsCSSVariables,
        checkCriticalStyles: checkCriticalStyles,
        applyEmergencyStyles: applyEmergencyStyles
    };

})();
