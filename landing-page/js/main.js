// Main JavaScript functionality
(function() {
    'use strict';

    // DOM elements
    const navbar = document.getElementById('navbar');
    const navToggle = document.getElementById('nav-toggle');
    const navMenu = document.getElementById('nav-menu');
    const loadingOverlay = document.getElementById('loading-overlay');
    const navLinks = document.querySelectorAll('.nav-link');

    // Initialize the application
    function init() {
        setupEventListeners();
        setupScrollAnimations();
        setupIntersectionObserver();
        hideLoadingOverlay();
        setupSmoothScrolling();
        setupParallaxEffect();
    }

    // Setup event listeners
    function setupEventListeners() {
        // Navigation toggle
        if (navToggle && navMenu) {
            navToggle.addEventListener('click', toggleMobileMenu);
        }

        // Navigation links
        navLinks.forEach(link => {
            link.addEventListener('click', handleNavLinkClick);
        });

        // Scroll events
        window.addEventListener('scroll', handleScroll, { passive: true });
        window.addEventListener('resize', handleResize, { passive: true });

        // Close mobile menu when clicking outside
        document.addEventListener('click', handleOutsideClick);

        // Keyboard navigation
        document.addEventListener('keydown', handleKeydown);
    }

    // Toggle mobile menu
    function toggleMobileMenu() {
        navToggle.classList.toggle('active');
        navMenu.classList.toggle('active');
        document.body.classList.toggle('menu-open');
    }

    // Close mobile menu
    function closeMobileMenu() {
        navToggle.classList.remove('active');
        navMenu.classList.remove('active');
        document.body.classList.remove('menu-open');
    }

    // Handle navigation link clicks
    function handleNavLinkClick(e) {
        const href = e.target.getAttribute('href');
        
        if (href && href.startsWith('#')) {
            e.preventDefault();
            const targetId = href.substring(1);
            const targetElement = document.getElementById(targetId);
            
            if (targetElement) {
                scrollToElement(targetElement);
                closeMobileMenu();
                updateActiveNavLink(href);
            }
        }
    }

    // Smooth scroll to element
    function scrollToElement(element) {
        const navbarHeight = navbar.offsetHeight;
        const targetPosition = element.offsetTop - navbarHeight;
        
        window.scrollTo({
            top: targetPosition,
            behavior: 'smooth'
        });
    }

    // Update active navigation link
    function updateActiveNavLink(activeHref) {
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === activeHref) {
                link.classList.add('active');
            }
        });
    }

    // Handle scroll events
    function handleScroll() {
        const scrollY = window.scrollY;
        
        // Update navbar appearance
        if (scrollY > 50) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }

        // Update active section
        updateActiveSection();
        
        // Parallax effect
        updateParallax(scrollY);
    }

    // Update active section based on scroll position
    function updateActiveSection() {
        const sections = document.querySelectorAll('section[id]');
        const navbarHeight = navbar.offsetHeight;
        const scrollPosition = window.scrollY + navbarHeight + 100;

        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');

            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                updateActiveNavLink(`#${sectionId}`);
            }
        });
    }

    // Handle window resize
    function handleResize() {
        // Close mobile menu on resize to desktop
        if (window.innerWidth > 991) {
            closeMobileMenu();
        }
    }

    // Handle clicks outside mobile menu
    function handleOutsideClick(e) {
        if (navMenu.classList.contains('active') && 
            !navMenu.contains(e.target) && 
            !navToggle.contains(e.target)) {
            closeMobileMenu();
        }
    }

    // Handle keyboard navigation
    function handleKeydown(e) {
        // Close mobile menu with Escape key
        if (e.key === 'Escape' && navMenu.classList.contains('active')) {
            closeMobileMenu();
        }
    }

    // Setup scroll animations
    function setupScrollAnimations() {
        const animatedElements = document.querySelectorAll('.scroll-animate');
        
        animatedElements.forEach(element => {
            element.style.opacity = '0';
            element.style.transform = 'translateY(30px)';
        });
    }

    // Setup Intersection Observer for scroll animations
    function setupIntersectionObserver() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate');
                    // Optional: unobserve after animation
                    // observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        // Observe elements with scroll-animate class
        const animatedElements = document.querySelectorAll('.scroll-animate, .fade-in-section');
        animatedElements.forEach(element => {
            observer.observe(element);
        });

        // Observe feature cards with stagger effect
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 0.1}s`;
            observer.observe(card);
        });
    }

    // Setup smooth scrolling for anchor links
    function setupSmoothScrolling() {
        // Polyfill for browsers that don't support smooth scrolling
        if (!('scrollBehavior' in document.documentElement.style)) {
            const script = document.createElement('script');
            script.src = 'https://cdn.jsdelivr.net/gh/iamdustan/smoothscroll@master/src/smoothscroll.js';
            document.head.appendChild(script);
        }
    }

    // Setup parallax effect
    function setupParallaxEffect() {
        const parallaxElements = document.querySelectorAll('.parallax');
        
        if (parallaxElements.length === 0) return;

        // Check if user prefers reduced motion
        const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
        if (prefersReducedMotion) return;

        parallaxElements.forEach(element => {
            element.style.willChange = 'transform';
        });
    }

    // Update parallax effect
    function updateParallax(scrollY) {
        const parallaxElements = document.querySelectorAll('.parallax');
        
        parallaxElements.forEach(element => {
            const speed = element.dataset.speed || 0.5;
            const yPos = -(scrollY * speed);
            element.style.transform = `translateY(${yPos}px)`;
        });
    }

    // Hide loading overlay
    function hideLoadingOverlay() {
        setTimeout(() => {
            if (loadingOverlay) {
                loadingOverlay.classList.add('hidden');
                setTimeout(() => {
                    loadingOverlay.style.display = 'none';
                }, 300);
            }
        }, 500);
    }

    // Utility functions
    const utils = {
        // Debounce function
        debounce: function(func, wait, immediate) {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    timeout = null;
                    if (!immediate) func(...args);
                };
                const callNow = immediate && !timeout;
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
                if (callNow) func(...args);
            };
        },

        // Throttle function
        throttle: function(func, limit) {
            let inThrottle;
            return function(...args) {
                if (!inThrottle) {
                    func.apply(this, args);
                    inThrottle = true;
                    setTimeout(() => inThrottle = false, limit);
                }
            };
        },

        // Check if element is in viewport
        isInViewport: function(element) {
            const rect = element.getBoundingClientRect();
            return (
                rect.top >= 0 &&
                rect.left >= 0 &&
                rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
                rect.right <= (window.innerWidth || document.documentElement.clientWidth)
            );
        },

        // Get scroll percentage
        getScrollPercentage: function() {
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - document.documentElement.clientHeight;
            return (scrollTop / scrollHeight) * 100;
        }
    };

    // Performance optimizations
    const optimizedHandleScroll = utils.throttle(handleScroll, 16); // ~60fps
    const optimizedHandleResize = utils.debounce(handleResize, 250);

    // Replace original event listeners with optimized versions
    window.removeEventListener('scroll', handleScroll);
    window.removeEventListener('resize', handleResize);
    window.addEventListener('scroll', optimizedHandleScroll, { passive: true });
    window.addEventListener('resize', optimizedHandleResize, { passive: true });

    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

    // Export utils for other scripts
    window.LandingPageUtils = utils;

})();
