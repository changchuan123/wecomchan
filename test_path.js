// 路径检查调试脚本
const fs = require('fs');
const path = require('path');
const config = require('./config');

console.log('🔍 路径检查调试开始...');
console.log('操作系统:', process.platform);
console.log('当前工作目录:', process.cwd());

// 检查配置文件中的路径
console.log('\n📁 检查配置中的文件夹路径:');
config.folders.forEach((folder, index) => {
    console.log(`\n${index + 1}. 表: ${folder.tableName}`);
    console.log(`   路径: ${folder.path}`);
    
    const startTime = Date.now();
    try {
        const exists = fs.existsSync(folder.path);
        const checkTime = Date.now() - startTime;
        console.log(`   存在: ${exists ? '✅' : '⚠️'} (检查耗时: ${checkTime}ms)`);
        
        if (exists) {
            const files = fs.readdirSync(folder.path);
            console.log(`   文件数: ${files.length}`);
            const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));
            console.log(`   Excel文件: ${excelFiles.length}`);
        }
    } catch (error) {
        console.log(`   错误: ${error.message} (耗时: ${Date.now() - startTime}ms)`);
    }
});

// 检查单文件路径
console.log('\n📄 检查单文件路径:');
config.singleFiles.forEach((file, index) => {
    console.log(`\n${index + 1}. 表: ${file.tableName}`);
    console.log(`   文件: ${file.filePath}`);
    
    const startTime = Date.now();
    try {
        const exists = fs.existsSync(file.filePath);
        const checkTime = Date.now() - startTime;
        console.log(`   存在: ${exists ? '✅' : '⚠️'} (检查耗时: ${checkTime}ms)`);
    } catch (error) {
        console.log(`   错误: ${error.message} (耗时: ${Date.now() - startTime}ms)`);
    }
});

console.log('\n✅ 路径检查完成！');
process.exit(0);