#!/usr/bin/env node

// 性能测试脚本
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

console.log('🚀 性能测试脚本');
console.log('================');

// 配置
const config = {
    port: 3000,
    testUrl: 'http://localhost:3000',
    outputDir: 'performance-reports',
    lighthouse: {
        categories: ['performance', 'accessibility', 'best-practices', 'seo'],
        device: 'desktop',
        throttling: false
    }
};

// 创建输出目录
function createOutputDir() {
    if (!fs.existsSync(config.outputDir)) {
        fs.mkdirSync(config.outputDir, { recursive: true });
        console.log(`📁 创建输出目录: ${config.outputDir}`);
    }
}

// 启动本地服务器
function startLocalServer() {
    return new Promise((resolve, reject) => {
        console.log('🌐 启动本地服务器...');
        
        const server = spawn('npx', ['http-server', '.', '-p', config.port, '-s'], {
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        let serverReady = false;
        
        server.stdout.on('data', (data) => {
            const output = data.toString();
            if (output.includes('Available on:') && !serverReady) {
                serverReady = true;
                console.log(`✅ 服务器启动成功: ${config.testUrl}`);
                resolve(server);
            }
        });
        
        server.stderr.on('data', (data) => {
            console.error('服务器错误:', data.toString());
        });
        
        server.on('error', (error) => {
            reject(error);
        });
        
        // 超时处理
        setTimeout(() => {
            if (!serverReady) {
                reject(new Error('服务器启动超时'));
            }
        }, 10000);
    });
}

// 运行 Lighthouse 测试
function runLighthouseTest() {
    return new Promise((resolve, reject) => {
        console.log('📊 运行 Lighthouse 性能测试...');
        
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const reportPath = path.join(config.outputDir, `lighthouse-${timestamp}.html`);
        const jsonPath = path.join(config.outputDir, `lighthouse-${timestamp}.json`);
        
        const args = [
            'lighthouse',
            config.testUrl,
            '--output=html,json',
            `--output-path=${path.join(config.outputDir, `lighthouse-${timestamp}`)}`,
            '--chrome-flags=--headless --no-sandbox',
            `--only-categories=${config.lighthouse.categories.join(',')}`,
            '--disable-device-emulation',
            '--throttling-method=provided'
        ];
        
        const lighthouse = spawn('npx', args, {
            stdio: ['ignore', 'pipe', 'pipe']
        });
        
        lighthouse.stdout.on('data', (data) => {
            process.stdout.write(data);
        });
        
        lighthouse.stderr.on('data', (data) => {
            process.stderr.write(data);
        });
        
        lighthouse.on('close', (code) => {
            if (code === 0) {
                console.log(`✅ Lighthouse 测试完成`);
                console.log(`📄 HTML 报告: ${reportPath}`);
                console.log(`📄 JSON 报告: ${jsonPath}`);
                resolve({ reportPath, jsonPath });
            } else {
                reject(new Error(`Lighthouse 测试失败，退出码: ${code}`));
            }
        });
    });
}

// 分析 Lighthouse 结果
function analyzeLighthouseResults(jsonPath) {
    try {
        console.log('\n📈 分析性能测试结果...');
        
        const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
        const categories = data.categories;
        
        console.log('=====================================');
        console.log('🏆 性能测试结果汇总');
        console.log('=====================================');
        
        Object.keys(categories).forEach(key => {
            const category = categories[key];
            const score = Math.round(category.score * 100);
            const emoji = score >= 90 ? '🟢' : score >= 70 ? '🟡' : '🔴';
            console.log(`${emoji} ${category.title}: ${score}/100`);
        });
        
        console.log('=====================================');
        
        // 详细指标
        const audits = data.audits;
        const metrics = [
            'first-contentful-paint',
            'largest-contentful-paint',
            'cumulative-layout-shift',
            'total-blocking-time',
            'speed-index'
        ];
        
        console.log('\n📊 核心性能指标:');
        console.log('-------------------------------------');
        
        metrics.forEach(metric => {
            if (audits[metric]) {
                const audit = audits[metric];
                const value = audit.displayValue || audit.score;
                console.log(`  ${audit.title}: ${value}`);
            }
        });
        
        // 优化建议
        console.log('\n💡 优化建议:');
        console.log('-------------------------------------');
        
        const opportunities = Object.values(audits).filter(audit => 
            audit.details && audit.details.type === 'opportunity' && audit.score < 1
        );
        
        if (opportunities.length > 0) {
            opportunities.slice(0, 5).forEach(opportunity => {
                console.log(`  • ${opportunity.title}`);
            });
        } else {
            console.log('  🎉 没有发现明显的优化机会！');
        }
        
        return {
            scores: Object.fromEntries(
                Object.entries(categories).map(([key, cat]) => [key, Math.round(cat.score * 100)])
            ),
            opportunities: opportunities.length
        };
        
    } catch (error) {
        console.error('❌ 分析结果失败:', error.message);
        return null;
    }
}

// 生成性能报告摘要
function generateSummaryReport(results) {
    const timestamp = new Date().toISOString();
    const summary = {
        timestamp,
        testUrl: config.testUrl,
        scores: results.scores,
        recommendations: [
            '使用 WebP 格式图片',
            '启用 Gzip 压缩',
            '优化 CSS 和 JS 文件',
            '使用 CDN 加速',
            '实现懒加载'
        ]
    };
    
    const summaryPath = path.join(config.outputDir, 'performance-summary.json');
    fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
    
    console.log(`\n📋 性能摘要已保存: ${summaryPath}`);
}

// 检查文件大小
function checkFileSizes() {
    console.log('\n📏 检查文件大小...');
    console.log('=====================================');
    
    const checkFile = (filePath, maxSize, unit = 'KB') => {
        if (fs.existsSync(filePath)) {
            const stats = fs.statSync(filePath);
            const size = unit === 'KB' ? stats.size / 1024 : stats.size / (1024 * 1024);
            const status = size <= maxSize ? '✅' : '⚠️';
            console.log(`${status} ${path.basename(filePath)}: ${size.toFixed(2)} ${unit} (建议 ≤ ${maxSize} ${unit})`);
            return size <= maxSize;
        }
        return true;
    };
    
    // 检查主要文件
    checkFile('index.html', 50, 'KB');
    checkFile('css/main.css', 100, 'KB');
    checkFile('css/responsive.css', 50, 'KB');
    checkFile('css/animations.css', 30, 'KB');
    checkFile('js/main.js', 100, 'KB');
    checkFile('js/animations.js', 50, 'KB');
    checkFile('js/theme-switcher.js', 30, 'KB');
    
    // 检查图片文件
    const imageDir = 'images';
    if (fs.existsSync(imageDir)) {
        const images = fs.readdirSync(imageDir, { recursive: true })
            .filter(file => /\.(jpg|jpeg|png|webp)$/i.test(file));
        
        images.forEach(image => {
            const imagePath = path.join(imageDir, image);
            checkFile(imagePath, 200, 'KB');
        });
    }
}

// 主函数
async function main() {
    try {
        createOutputDir();
        checkFileSizes();
        
        // 启动服务器
        const server = await startLocalServer();
        
        try {
            // 等待服务器完全启动
            await new Promise(resolve => setTimeout(resolve, 2000));
            
            // 运行 Lighthouse 测试
            const { jsonPath } = await runLighthouseTest();
            
            // 分析结果
            const results = analyzeLighthouseResults(jsonPath);
            
            if (results) {
                generateSummaryReport(results);
                
                // 检查是否达到目标分数
                const targetScores = { performance: 90, accessibility: 95, 'best-practices': 90, seo: 90 };
                const passed = Object.entries(targetScores).every(([category, target]) => 
                    results.scores[category] >= target
                );
                
                if (passed) {
                    console.log('\n🎉 所有性能指标都达到了目标！');
                } else {
                    console.log('\n⚠️  部分性能指标需要优化');
                }
            }
            
        } finally {
            // 停止服务器
            console.log('\n🛑 停止本地服务器...');
            server.kill();
        }
        
        console.log('\n✅ 性能测试完成！');
        
    } catch (error) {
        console.error('❌ 性能测试失败:', error.message);
        process.exit(1);
    }
}

// 运行脚本
if (require.main === module) {
    main();
}

module.exports = {
    startLocalServer,
    runLighthouseTest,
    analyzeLighthouseResults,
    checkFileSizes
};
