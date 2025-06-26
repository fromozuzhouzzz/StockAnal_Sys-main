/**
 * 统一主题管理器 - 解决跨浏览器兼容性问题
 * 支持所有主流浏览器，包括移动设备
 */
(function() {
    'use strict';

    // 全局主题管理器
    window.ThemeManager = {
        // 配置选项
        config: {
            storageKey: 'theme',
            defaultTheme: 'light',
            themeAttribute: 'data-theme',
            buttonId: 'global-theme-toggle',
            iconId: 'global-theme-icon'
        },

        // 安全的localStorage操作
        storage: {
            isAvailable: function() {
                try {
                    var test = '__theme_test__';
                    localStorage.setItem(test, test);
                    localStorage.removeItem(test);
                    return true;
                } catch (e) {
                    return false;
                }
            },

            get: function(key) {
                if (!this.isAvailable()) {
                    console.warn('localStorage不可用，使用默认主题');
                    return null;
                }
                try {
                    return localStorage.getItem(key);
                } catch (e) {
                    console.warn('读取localStorage失败:', e);
                    return null;
                }
            },

            set: function(key, value) {
                if (!this.isAvailable()) {
                    console.warn('localStorage不可用，主题设置不会保存');
                    return false;
                }
                try {
                    localStorage.setItem(key, value);
                    return true;
                } catch (e) {
                    console.warn('保存到localStorage失败:', e);
                    return false;
                }
            }
        },

        // 浏览器兼容性检查
        compatibility: {
            hasQuerySelector: function() {
                return !!(document.querySelector);
            },

            hasAddEventListener: function() {
                return !!(document.addEventListener);
            },

            hasCSSVariables: function() {
                return window.CSS && CSS.supports && CSS.supports('color', 'var(--test)');
            },

            isSupported: function() {
                return this.hasQuerySelector() && this.hasAddEventListener();
            }
        },

        // 主题应用函数
        applyTheme: function(theme) {
            if (!this.compatibility.isSupported()) {
                console.warn('浏览器不支持主题切换功能');
                return false;
            }

            try {
                // 同时在body和documentElement上设置，确保兼容性
                if (theme === 'dark') {
                    document.body.setAttribute(this.config.themeAttribute, 'dark');
                    document.documentElement.setAttribute(this.config.themeAttribute, 'dark');
                } else {
                    document.body.removeAttribute(this.config.themeAttribute);
                    document.documentElement.removeAttribute(this.config.themeAttribute);
                }

                // 更新按钮图标和提示
                this.updateThemeButton(theme);

                // 触发自定义事件，供其他组件监听
                this.dispatchThemeChangeEvent(theme);

                return true;
            } catch (e) {
                console.error('应用主题失败:', e);
                return false;
            }
        },

        // 更新主题切换按钮
        updateThemeButton: function(theme) {
            var button = document.getElementById(this.config.buttonId);
            var icon = document.getElementById(this.config.iconId);

            if (button && icon) {
                if (theme === 'dark') {
                    // 使用兼容性更好的方式设置图标
                    if (icon.textContent !== undefined) {
                        icon.textContent = 'dark_mode';
                    } else if (icon.innerText !== undefined) {
                        icon.innerText = 'dark_mode';
                    }
                    button.title = '切换到浅色模式';
                    button.setAttribute('aria-label', '切换到浅色模式');
                } else {
                    if (icon.textContent !== undefined) {
                        icon.textContent = 'light_mode';
                    } else if (icon.innerText !== undefined) {
                        icon.innerText = 'light_mode';
                    }
                    button.title = '切换到深色模式';
                    button.setAttribute('aria-label', '切换到深色模式');
                }
            }
        },

        // 获取当前主题
        getCurrentTheme: function() {
            var bodyTheme = document.body.getAttribute(this.config.themeAttribute);
            var htmlTheme = document.documentElement.getAttribute(this.config.themeAttribute);
            return bodyTheme || htmlTheme || this.config.defaultTheme;
        },

        // 切换主题
        toggleTheme: function() {
            var currentTheme = this.getCurrentTheme();
            var newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            if (this.applyTheme(newTheme)) {
                this.storage.set(this.config.storageKey, newTheme);
                return newTheme;
            }
            return currentTheme;
        },

        // 初始化主题
        initTheme: function() {
            if (!this.compatibility.isSupported()) {
                console.warn('浏览器不支持主题切换功能');
                return false;
            }

            // 获取保存的主题或使用默认主题
            var savedTheme = this.storage.get(this.config.storageKey) || this.config.defaultTheme;
            
            // 应用主题
            this.applyTheme(savedTheme);

            return true;
        },

        // 绑定事件监听器
        bindEvents: function() {
            if (!this.compatibility.isSupported()) {
                return false;
            }

            var self = this;
            var button = document.getElementById(this.config.buttonId);

            if (button) {
                // 使用兼容性更好的事件绑定方式
                if (button.addEventListener) {
                    button.addEventListener('click', function(e) {
                        e.preventDefault();
                        self.toggleTheme();
                    });
                } else if (button.attachEvent) {
                    // IE8及以下版本的兼容性处理
                    button.attachEvent('onclick', function(e) {
                        e = e || window.event;
                        if (e.preventDefault) {
                            e.preventDefault();
                        } else {
                            e.returnValue = false;
                        }
                        self.toggleTheme();
                    });
                }

                // 添加键盘支持
                if (button.addEventListener) {
                    button.addEventListener('keydown', function(e) {
                        if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            self.toggleTheme();
                        }
                    });
                }

                return true;
            } else {
                console.warn('未找到主题切换按钮');
                return false;
            }
        },

        // 触发主题变化事件
        dispatchThemeChangeEvent: function(theme) {
            try {
                var event;
                if (typeof CustomEvent === 'function') {
                    event = new CustomEvent('themechange', {
                        detail: { theme: theme }
                    });
                } else {
                    // IE兼容性处理
                    event = document.createEvent('CustomEvent');
                    event.initCustomEvent('themechange', true, true, { theme: theme });
                }
                document.dispatchEvent(event);
            } catch (e) {
                console.warn('无法触发主题变化事件:', e);
            }
        },

        // 完整初始化
        init: function() {
            var self = this;
            
            // 检查浏览器兼容性
            if (!this.compatibility.isSupported()) {
                console.warn('当前浏览器不支持主题切换功能');
                return false;
            }

            // DOM加载完成后初始化
            function initialize() {
                self.initTheme();
                self.bindEvents();
            }

            // 兼容性更好的DOM ready检查
            if (document.readyState === 'loading') {
                if (document.addEventListener) {
                    document.addEventListener('DOMContentLoaded', initialize);
                } else if (document.attachEvent) {
                    document.attachEvent('onreadystatechange', function() {
                        if (document.readyState === 'complete') {
                            initialize();
                        }
                    });
                }
            } else {
                // DOM已经加载完成
                initialize();
            }

            return true;
        }
    };

    // 自动初始化
    ThemeManager.init();

})();
