#!/usr/bin/env node

// 图片优化脚本
const fs = require('fs');
const path = require('path');

console.log('🖼️  图片优化脚本');
console.log('================');

// 图片目录
const imageDir = path.join(__dirname, 'images');
const screenshotsDir = path.join(imageDir, 'screenshots');

// 检查目录是否存在
function checkDirectories() {
    console.log('📂 检查图片目录...');
    
    if (!fs.existsSync(imageDir)) {
        console.log('❌ images 目录不存在');
        return false;
    }
    
    if (!fs.existsSync(screenshotsDir)) {
        console.log('📁 创建 screenshots 目录...');
        fs.mkdirSync(screenshotsDir, { recursive: true });
    }
    
    console.log('✅ 目录检查完成');
    return true;
}

// 生成 WebP 格式说明
function generateWebPInfo() {
    console.log('\n📋 WebP 格式转换建议:');
    console.log('=====================================');
    console.log('为了更好的性能，建议将图片转换为 WebP 格式：');
    console.log('');
    console.log('在线工具：');
    console.log('- Squoosh: https://squoosh.app/');
    console.log('- TinyPNG: https://tinypng.com/');
    console.log('- Convertio: https://convertio.co/jpg-webp/');
    console.log('');
    console.log('命令行工具（需要安装 cwebp）：');
    console.log('cwebp input.jpg -q 80 -o output.webp');
    console.log('');
}

// 生成响应式图片 HTML 示例
function generateResponsiveImageHTML() {
    const htmlTemplate = `
<!-- 响应式图片示例 -->
<picture>
    <source 
        srcset="images/screenshots/dashboard-480.webp 480w,
                images/screenshots/dashboard-800.webp 800w,
                images/screenshots/dashboard-1200.webp 1200w"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        type="image/webp">
    <source 
        srcset="images/screenshots/dashboard-480.jpg 480w,
                images/screenshots/dashboard-800.jpg 800w,
                images/screenshots/dashboard-1200.jpg 1200w"
        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
        type="image/jpeg">
    <img 
        src="images/screenshots/dashboard-800.jpg" 
        alt="智能仪表盘界面"
        loading="lazy"
        width="800"
        height="500">
</picture>`;

    fs.writeFileSync(
        path.join(__dirname, 'responsive-image-example.html'),
        htmlTemplate.trim()
    );
    
    console.log('📄 已生成响应式图片 HTML 示例: responsive-image-example.html');
}

// 图片优化建议
function generateOptimizationTips() {
    const tips = `
# 图片优化建议

## 1. 格式选择
- **WebP**: 现代浏览器首选，文件小，质量高
- **AVIF**: 最新格式，压缩率更高（支持度较低）
- **JPEG**: 传统格式，兼容性好
- **PNG**: 透明背景图片
- **SVG**: 矢量图标和简单图形

## 2. 尺寸规格
### 截图图片
- 桌面版: 1200x750px
- 平板版: 800x500px  
- 手机版: 480x300px

### 背景图片
- 桌面版: 1920x1080px
- 平板版: 1024x768px
- 手机版: 768x1024px

## 3. 压缩设置
- **JPEG质量**: 80-85%
- **WebP质量**: 75-80%
- **PNG**: 使用 TinyPNG 等工具压缩

## 4. 性能优化
- 使用 \`loading="lazy"\` 属性
- 提供多种尺寸（响应式图片）
- 使用 \`<picture>\` 元素支持多格式
- 设置正确的 \`width\` 和 \`height\` 属性

## 5. 推荐工具
### 在线工具
- Squoosh: https://squoosh.app/
- TinyPNG: https://tinypng.com/
- Optimizilla: https://imagecompressor.com/

### 命令行工具
\`\`\`bash
# 安装 imagemin
npm install -g imagemin-cli imagemin-webp imagemin-mozjpeg

# 批量转换为 WebP
imagemin images/*.jpg --out-dir=images/webp --plugin=webp

# 压缩 JPEG
imagemin images/*.jpg --out-dir=images/compressed --plugin=mozjpeg
\`\`\`

## 6. 自动化脚本
可以使用 npm scripts 自动化图片处理：
\`\`\`json
{
  "scripts": {
    "optimize:images": "imagemin images/**/*.{jpg,png} --out-dir=images/optimized",
    "convert:webp": "imagemin images/**/*.{jpg,png} --out-dir=images/webp --plugin=webp"
  }
}
\`\`\`
`;

    fs.writeFileSync(
        path.join(__dirname, 'IMAGE_OPTIMIZATION.md'),
        tips.trim()
    );
    
    console.log('📚 已生成图片优化指南: IMAGE_OPTIMIZATION.md');
}

// 检查现有图片
function checkExistingImages() {
    console.log('\n🔍 检查现有图片...');
    
    const imageExtensions = ['.jpg', '.jpeg', '.png', '.webp', '.svg'];
    let imageCount = 0;
    
    function scanDirectory(dir, prefix = '') {
        if (!fs.existsSync(dir)) return;
        
        const files = fs.readdirSync(dir);
        files.forEach(file => {
            const filePath = path.join(dir, file);
            const stat = fs.statSync(filePath);
            
            if (stat.isDirectory()) {
                scanDirectory(filePath, prefix + file + '/');
            } else {
                const ext = path.extname(file).toLowerCase();
                if (imageExtensions.includes(ext)) {
                    const size = (stat.size / 1024).toFixed(2);
                    console.log(`  📷 ${prefix}${file} (${size} KB)`);
                    imageCount++;
                }
            }
        });
    }
    
    scanDirectory(imageDir);
    
    if (imageCount === 0) {
        console.log('  ℹ️  未找到图片文件');
        console.log('  💡 请使用 generate-placeholders.html 生成占位符图片');
    } else {
        console.log(`\n✅ 找到 ${imageCount} 个图片文件`);
    }
}

// 主函数
function main() {
    if (!checkDirectories()) {
        process.exit(1);
    }
    
    checkExistingImages();
    generateWebPInfo();
    generateResponsiveImageHTML();
    generateOptimizationTips();
    
    console.log('\n🎉 图片优化脚本执行完成！');
    console.log('');
    console.log('下一步：');
    console.log('1. 使用 generate-placeholders.html 生成占位符图片');
    console.log('2. 使用推荐工具优化图片大小');
    console.log('3. 转换为 WebP 格式提升性能');
    console.log('4. 在 HTML 中使用响应式图片');
}

// 运行脚本
if (require.main === module) {
    main();
}

module.exports = {
    checkDirectories,
    generateWebPInfo,
    generateResponsiveImageHTML,
    generateOptimizationTips,
    checkExistingImages
};
