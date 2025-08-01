// 测试脚本 - 最小化版本
const fs = require('fs');
const path = require('path');

console.log('🚀 测试开始...');
console.log('当前目录:', __dirname);
console.log('当前工作目录:', process.cwd());

try {
    console.log('📂 检查目录内容...');
    const files = fs.readdirSync('.');
    console.log('文件列表:', files);
    
    console.log('📄 检查config.js是否存在...');
    if (fs.existsSync('./config.js')) {
        console.log('✅ config.js存在');
        const config = require('./config');
        console.log('✅ config加载成功:', JSON.stringify(config, null, 2));
    } else {
        console.log('❌ config.js不存在');
    }
    
    console.log('🎉 测试完成');
    
} catch (error) {
    console.error('❌ 错误:', error.message);
    console.error('堆栈:', error.stack);
}

process.exit(0);