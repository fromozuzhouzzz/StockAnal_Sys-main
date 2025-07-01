// Animation Controller
(function() {
    'use strict';

    // Animation configuration
    const ANIMATION_CONFIG = {
        duration: {
            fast: 200,
            normal: 300,
            slow: 500
        },
        easing: {
            easeOut: 'cubic-bezier(0.25, 0.46, 0.45, 0.94)',
            easeIn: 'cubic-bezier(0.55, 0.055, 0.675, 0.19)',
            easeInOut: 'cubic-bezier(0.645, 0.045, 0.355, 1)'
        },
        stagger: 100 // milliseconds between staggered animations
    };

    // Animation state
    let animationQueue = [];
    let isAnimating = false;

    // Initialize animations
    function initAnimations() {
        setupHeroAnimations();
        setupScrollAnimations();
        setupHoverAnimations();
        setupCounterAnimations();
        setupTypewriterEffect();
        setupParticleEffect();
    }

    // Hero section animations
    function setupHeroAnimations() {
        const heroElements = {
            title: document.querySelector('.hero-title'),
            subtitle: document.querySelector('.hero-subtitle'),
            stats: document.querySelector('.hero-stats'),
            actions: document.querySelector('.hero-actions'),
            visual: document.querySelector('.hero-visual')
        };

        // Animate hero elements with stagger
        Object.values(heroElements).forEach((element, index) => {
            if (element) {
                element.style.opacity = '0';
                element.style.transform = 'translateY(30px)';
                
                setTimeout(() => {
                    animateElement(element, {
                        opacity: 1,
                        transform: 'translateY(0)'
                    }, ANIMATION_CONFIG.duration.slow);
                }, index * 200);
            }
        });

        // Animate hero card with floating effect
        const heroCard = document.querySelector('.hero-card');
        if (heroCard) {
            setTimeout(() => {
                heroCard.classList.add('animate-float');
            }, 1000);
        }
    }

    // Scroll-triggered animations
    function setupScrollAnimations() {
        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -100px 0px'
        };

        const scrollObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const animationType = element.dataset.animation || 'fadeInUp';
                    const delay = parseInt(element.dataset.delay) || 0;
                    
                    setTimeout(() => {
                        triggerScrollAnimation(element, animationType);
                    }, delay);
                    
                    scrollObserver.unobserve(element);
                }
            });
        }, observerOptions);

        // Observe elements with data-animation attribute
        const animatedElements = document.querySelectorAll('[data-animation]');
        animatedElements.forEach(element => {
            scrollObserver.observe(element);
        });

        // Observe feature cards for stagger animation
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach((card, index) => {
            card.dataset.animation = 'fadeInUp';
            card.dataset.delay = index * ANIMATION_CONFIG.stagger;
            scrollObserver.observe(card);
        });

        // Observe screenshot items
        const screenshotItems = document.querySelectorAll('.screenshot-item');
        screenshotItems.forEach((item, index) => {
            item.dataset.animation = 'scaleIn';
            item.dataset.delay = index * ANIMATION_CONFIG.stagger;
            scrollObserver.observe(item);
        });
    }

    // Trigger scroll animation
    function triggerScrollAnimation(element, animationType) {
        switch (animationType) {
            case 'fadeInUp':
                animateElement(element, {
                    opacity: 1,
                    transform: 'translateY(0)'
                }, ANIMATION_CONFIG.duration.normal);
                break;
            case 'fadeInLeft':
                animateElement(element, {
                    opacity: 1,
                    transform: 'translateX(0)'
                }, ANIMATION_CONFIG.duration.normal);
                break;
            case 'fadeInRight':
                animateElement(element, {
                    opacity: 1,
                    transform: 'translateX(0)'
                }, ANIMATION_CONFIG.duration.normal);
                break;
            case 'scaleIn':
                animateElement(element, {
                    opacity: 1,
                    transform: 'scale(1)'
                }, ANIMATION_CONFIG.duration.normal);
                break;
            default:
                element.classList.add('animate');
        }
    }

    // Setup hover animations
    function setupHoverAnimations() {
        // Feature cards hover effect
        const featureCards = document.querySelectorAll('.feature-card');
        featureCards.forEach(card => {
            const icon = card.querySelector('.feature-icon');
            
            card.addEventListener('mouseenter', () => {
                if (icon) {
                    icon.style.transform = 'scale(1.1) rotate(5deg)';
                }
            });
            
            card.addEventListener('mouseleave', () => {
                if (icon) {
                    icon.style.transform = 'scale(1) rotate(0deg)';
                }
            });
        });

        // Button hover effects
        const buttons = document.querySelectorAll('.btn');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
            });
            
            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
            });
        });

        // Screenshot hover effects
        const screenshots = document.querySelectorAll('.screenshot-item');
        screenshots.forEach(screenshot => {
            const image = screenshot.querySelector('.screenshot-image img');
            const overlay = screenshot.querySelector('.screenshot-overlay');
            
            screenshot.addEventListener('mouseenter', () => {
                if (image) {
                    image.style.transform = 'scale(1.05)';
                }
                if (overlay) {
                    overlay.style.opacity = '1';
                }
            });
            
            screenshot.addEventListener('mouseleave', () => {
                if (image) {
                    image.style.transform = 'scale(1)';
                }
                if (overlay) {
                    overlay.style.opacity = '0';
                }
            });
        });
    }

    // Counter animations
    function setupCounterAnimations() {
        const counters = document.querySelectorAll('.stat-number');
        
        const counterObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const counter = entry.target;
                    const target = parseInt(counter.textContent) || 0;
                    
                    if (target > 0) {
                        animateCounter(counter, 0, target, 2000);
                    }
                    
                    counterObserver.unobserve(counter);
                }
            });
        }, { threshold: 0.5 });

        counters.forEach(counter => {
            counterObserver.observe(counter);
        });
    }

    // Animate counter
    function animateCounter(element, start, end, duration) {
        const startTime = performance.now();
        const isNumber = !isNaN(end);
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            
            if (isNumber) {
                const current = Math.floor(start + (end - start) * easeOutQuart(progress));
                element.textContent = current;
            }
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            } else {
                element.textContent = end;
            }
        }
        
        requestAnimationFrame(updateCounter);
    }

    // Easing function
    function easeOutQuart(t) {
        return 1 - (--t) * t * t * t;
    }

    // Typewriter effect
    function setupTypewriterEffect() {
        const typewriterElements = document.querySelectorAll('[data-typewriter]');
        
        typewriterElements.forEach(element => {
            const text = element.textContent;
            const speed = parseInt(element.dataset.speed) || 50;
            
            element.textContent = '';
            element.style.borderRight = '2px solid';
            element.style.animation = 'blink 1s infinite';
            
            let i = 0;
            const typeInterval = setInterval(() => {
                element.textContent += text.charAt(i);
                i++;
                
                if (i >= text.length) {
                    clearInterval(typeInterval);
                    setTimeout(() => {
                        element.style.borderRight = 'none';
                        element.style.animation = 'none';
                    }, 1000);
                }
            }, speed);
        });
    }

    // Particle effect for hero background
    function setupParticleEffect() {
        const heroBackground = document.querySelector('.hero-background');
        if (!heroBackground) return;

        // Check if user prefers reduced motion
        if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

        const canvas = document.createElement('canvas');
        const ctx = canvas.getContext('2d');
        
        canvas.style.position = 'absolute';
        canvas.style.top = '0';
        canvas.style.left = '0';
        canvas.style.width = '100%';
        canvas.style.height = '100%';
        canvas.style.pointerEvents = 'none';
        canvas.style.opacity = '0.3';
        
        heroBackground.appendChild(canvas);
        
        let particles = [];
        let animationId;
        
        function resizeCanvas() {
            canvas.width = heroBackground.offsetWidth;
            canvas.height = heroBackground.offsetHeight;
        }
        
        function createParticle() {
            return {
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                vx: (Math.random() - 0.5) * 0.5,
                vy: (Math.random() - 0.5) * 0.5,
                size: Math.random() * 2 + 1,
                opacity: Math.random() * 0.5 + 0.2
            };
        }
        
        function initParticles() {
            particles = [];
            for (let i = 0; i < 50; i++) {
                particles.push(createParticle());
            }
        }
        
        function updateParticles() {
            particles.forEach(particle => {
                particle.x += particle.vx;
                particle.y += particle.vy;
                
                if (particle.x < 0 || particle.x > canvas.width) particle.vx *= -1;
                if (particle.y < 0 || particle.y > canvas.height) particle.vy *= -1;
            });
        }
        
        function drawParticles() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            
            particles.forEach(particle => {
                ctx.beginPath();
                ctx.arc(particle.x, particle.y, particle.size, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${particle.opacity})`;
                ctx.fill();
            });
        }
        
        function animate() {
            updateParticles();
            drawParticles();
            animationId = requestAnimationFrame(animate);
        }
        
        resizeCanvas();
        initParticles();
        animate();
        
        window.addEventListener('resize', () => {
            resizeCanvas();
            initParticles();
        });
        
        // Cleanup on page unload
        window.addEventListener('beforeunload', () => {
            if (animationId) {
                cancelAnimationFrame(animationId);
            }
        });
    }

    // Generic element animation function
    function animateElement(element, properties, duration = 300, easing = 'ease-out') {
        return new Promise(resolve => {
            const startTime = performance.now();
            const startProperties = {};
            
            // Get initial values
            Object.keys(properties).forEach(prop => {
                const computedStyle = window.getComputedStyle(element);
                startProperties[prop] = computedStyle[prop];
            });
            
            function animate(currentTime) {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / duration, 1);
                
                Object.keys(properties).forEach(prop => {
                    const startValue = parseFloat(startProperties[prop]) || 0;
                    const endValue = parseFloat(properties[prop]) || 0;
                    const currentValue = startValue + (endValue - startValue) * easeOutQuart(progress);
                    
                    if (prop === 'opacity') {
                        element.style[prop] = currentValue;
                    } else if (prop === 'transform') {
                        element.style[prop] = properties[prop];
                    }
                });
                
                if (progress < 1) {
                    requestAnimationFrame(animate);
                } else {
                    resolve();
                }
            }
            
            requestAnimationFrame(animate);
        });
    }

    // Initialize animations when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAnimations);
    } else {
        initAnimations();
    }

    // Export animation functions
    window.AnimationController = {
        animateElement,
        animateCounter,
        ANIMATION_CONFIG
    };

})();
