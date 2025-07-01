// Theme Switcher
(function() {
    'use strict';

    // Theme configuration
    const THEMES = {
        LIGHT: 'light',
        DARK: 'dark',
        AUTO: 'auto'
    };

    const STORAGE_KEY = 'preferred-theme';
    const THEME_ATTRIBUTE = 'data-theme';

    // DOM elements
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = document.getElementById('theme-icon');
    const html = document.documentElement;

    // Current theme state
    let currentTheme = THEMES.LIGHT;

    // Initialize theme system
    function initTheme() {
        // Get saved theme or detect system preference
        const savedTheme = getSavedTheme();
        const systemTheme = getSystemTheme();
        
        currentTheme = savedTheme || systemTheme;
        applyTheme(currentTheme);
        updateThemeIcon();
        
        // Setup event listeners
        setupEventListeners();
        
        // Listen for system theme changes
        watchSystemTheme();
    }

    // Setup event listeners
    function setupEventListeners() {
        if (themeToggle) {
            themeToggle.addEventListener('click', toggleTheme);
        }

        // Keyboard shortcut (Ctrl/Cmd + Shift + T)
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'T') {
                e.preventDefault();
                toggleTheme();
            }
        });
    }

    // Toggle between themes
    function toggleTheme() {
        const newTheme = currentTheme === THEMES.LIGHT ? THEMES.DARK : THEMES.LIGHT;
        setTheme(newTheme);
        
        // Add visual feedback
        addToggleAnimation();
    }

    // Set theme
    function setTheme(theme) {
        currentTheme = theme;
        applyTheme(theme);
        saveTheme(theme);
        updateThemeIcon();
        
        // Dispatch custom event
        dispatchThemeChangeEvent(theme);
    }

    // Apply theme to document
    function applyTheme(theme) {
        // Remove existing theme attributes
        html.removeAttribute(THEME_ATTRIBUTE);
        
        // Apply new theme
        if (theme === THEMES.DARK) {
            html.setAttribute(THEME_ATTRIBUTE, THEMES.DARK);
        }
        
        // Update meta theme-color for mobile browsers
        updateMetaThemeColor(theme);
        
        // Smooth transition
        addThemeTransition();
    }

    // Update theme icon
    function updateThemeIcon() {
        if (!themeIcon) return;
        
        const iconName = currentTheme === THEMES.LIGHT ? 'dark_mode' : 'light_mode';
        const title = currentTheme === THEMES.LIGHT ? '切换到深色模式' : '切换到浅色模式';
        
        themeIcon.textContent = iconName;
        themeToggle.setAttribute('title', title);
        themeToggle.setAttribute('aria-label', title);
    }

    // Add toggle animation
    function addToggleAnimation() {
        if (!themeToggle) return;
        
        themeToggle.style.transform = 'scale(0.9)';
        themeToggle.style.transition = 'transform 0.1s ease';
        
        setTimeout(() => {
            themeToggle.style.transform = 'scale(1)';
            setTimeout(() => {
                themeToggle.style.transition = '';
            }, 100);
        }, 100);
    }

    // Add smooth transition during theme change
    function addThemeTransition() {
        const transitionClass = 'theme-transition';
        
        // Add transition class
        html.classList.add(transitionClass);
        
        // Remove after transition
        setTimeout(() => {
            html.classList.remove(transitionClass);
        }, 300);
    }

    // Update meta theme-color
    function updateMetaThemeColor(theme) {
        let metaThemeColor = document.querySelector('meta[name="theme-color"]');
        
        if (!metaThemeColor) {
            metaThemeColor = document.createElement('meta');
            metaThemeColor.name = 'theme-color';
            document.head.appendChild(metaThemeColor);
        }
        
        const color = theme === THEMES.DARK ? '#121212' : '#ffffff';
        metaThemeColor.content = color;
    }

    // Get saved theme from localStorage
    function getSavedTheme() {
        try {
            return localStorage.getItem(STORAGE_KEY);
        } catch (e) {
            console.warn('Unable to access localStorage for theme preference');
            return null;
        }
    }

    // Save theme to localStorage
    function saveTheme(theme) {
        try {
            localStorage.setItem(STORAGE_KEY, theme);
        } catch (e) {
            console.warn('Unable to save theme preference to localStorage');
        }
    }

    // Get system theme preference
    function getSystemTheme() {
        if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
            return THEMES.DARK;
        }
        return THEMES.LIGHT;
    }

    // Watch for system theme changes
    function watchSystemTheme() {
        if (!window.matchMedia) return;
        
        const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
        
        // Listen for changes
        mediaQuery.addEventListener('change', (e) => {
            // Only auto-switch if no manual preference is saved
            if (!getSavedTheme()) {
                const newTheme = e.matches ? THEMES.DARK : THEMES.LIGHT;
                setTheme(newTheme);
            }
        });
    }

    // Dispatch theme change event
    function dispatchThemeChangeEvent(theme) {
        const event = new CustomEvent('themechange', {
            detail: { theme }
        });
        document.dispatchEvent(event);
    }

    // Get current theme
    function getCurrentTheme() {
        return currentTheme;
    }

    // Check if dark theme is active
    function isDarkTheme() {
        return currentTheme === THEMES.DARK;
    }

    // Auto theme based on time of day
    function setAutoTheme() {
        const hour = new Date().getHours();
        const isDayTime = hour >= 6 && hour < 18;
        const autoTheme = isDayTime ? THEMES.LIGHT : THEMES.DARK;
        setTheme(autoTheme);
    }

    // Theme utilities
    const themeUtils = {
        // Get CSS custom property value for current theme
        getCSSVariable: function(property) {
            return getComputedStyle(html).getPropertyValue(property).trim();
        },
        
        // Set CSS custom property
        setCSSVariable: function(property, value) {
            html.style.setProperty(property, value);
        },
        
        // Get theme-aware color
        getThemeColor: function(lightColor, darkColor) {
            return isDarkTheme() ? darkColor : lightColor;
        },
        
        // Apply theme-specific styles to element
        applyThemeStyles: function(element, lightStyles, darkStyles) {
            const styles = isDarkTheme() ? darkStyles : lightStyles;
            Object.assign(element.style, styles);
        }
    };

    // Initialize theme system when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }

    // Export theme functions
    window.ThemeSwitcher = {
        setTheme,
        getCurrentTheme,
        isDarkTheme,
        setAutoTheme,
        THEMES,
        utils: themeUtils
    };

    // Listen for theme change events from other scripts
    document.addEventListener('themechange', (e) => {
        console.log('Theme changed to:', e.detail.theme);
        
        // Update any theme-dependent elements
        updateThemeDependentElements(e.detail.theme);
    });

    // Update elements that depend on theme
    function updateThemeDependentElements(theme) {
        // Update charts, graphs, or other dynamic content
        const charts = document.querySelectorAll('[data-theme-dependent]');
        charts.forEach(chart => {
            // Trigger chart redraw with new theme colors
            const event = new CustomEvent('theme-update', { detail: { theme } });
            chart.dispatchEvent(event);
        });
        
        // Update any embedded content
        const embeds = document.querySelectorAll('iframe[data-theme-sync]');
        embeds.forEach(embed => {
            try {
                embed.contentWindow.postMessage({ type: 'theme-change', theme }, '*');
            } catch (e) {
                // Cross-origin iframe, can't communicate
            }
        });
    }

    // Add CSS for theme transition
    const style = document.createElement('style');
    style.textContent = `
        .theme-transition * {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
        }
        
        .theme-transition *::before,
        .theme-transition *::after {
            transition: background-color 0.3s ease, color 0.3s ease, border-color 0.3s ease !important;
        }
    `;
    document.head.appendChild(style);

})();
