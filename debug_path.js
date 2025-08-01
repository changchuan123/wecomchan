// 调试脚本 - 修复Windows路径检查hang问题
const fs = require('fs');
const path = require('path');
const config = require('./config');

console.log('🔍 Windows路径检查调试开始...');
console.log('操作系统:', process.platform);
console.log('当前工作目录:', process.cwd());
console.log('脚本路径:', __dirname);

// 设置超时保护
const TIMEOUT_MS = 5000; // 5秒超时

async function checkPathWithTimeout(folderPath) {
    return new Promise((resolve) => {
        const timeout = setTimeout(() => {
            console.log(`⏰ 路径检查超时: ${folderPath}`);
            resolve({ exists: false, timeout: true });
        }, TIMEOUT_MS);

        try {
            // 使用异步检查避免阻塞
            fs.access(folderPath, fs.constants.F_OK, (err) => {
                clearTimeout(timeout);
                if (err) {
                    console.log(`❌ 路径不存在: ${folderPath}`);
                    resolve({ exists: false, timeout: false, error: err.message });
                } else {
                    console.log(`✅ 路径存在: ${folderPath}`);
                    resolve({ exists: true, timeout: false });
                }
            });
        } catch (error) {
            clearTimeout(timeout);
            console.log(`💥 检查出错: ${folderPath} - ${error.message}`);
            resolve({ exists: false, timeout: false, error: error.message });
        }
    });
}

async function debugWindowsPaths() {
    console.log('\n📁 开始检查配置中的文件夹路径...');
    
    let validFolders = [];
    let totalFolders = config.folders.length;
    
    for (let i = 0; i < totalFolders; i++) {
        const folder = config.folders[i];
        console.log(`\n[${i + 1}/${totalFolders}] 检查: ${folder.path}`);
        
        const result = await checkPathWithTimeout(folder.path);
        
        if (result.exists) {
            validFolders.push(folder);
            console.log(`   ✅ 有效路径: ${folder.tableName}`);
            
            // 检查文件
            try {
                const files = await new Promise((resolve) => {
                    fs.readdir(folder.path, (err, files) => {
                        if (err) resolve([]);
                        else resolve(files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls')));
                    });
                });
                console.log(`   📊 Excel文件: ${files.length} 个`);
            } catch (error) {
                console.log(`   ⚠️ 读取文件失败: ${error.message}`);
            }
        } else {
            console.log(`   ⚠️ 跳过无效路径: ${folder.tableName}`);
            if (result.timeout) {
                console.log(`   ⏰ 超时保护生效`);
            }
        }
    }
    
    console.log(`\n📊 检查结果总结:`);
    console.log(`   总路径数: ${totalFolders}`);
    console.log(`   有效路径: ${validFolders.length}`);
    console.log(`   无效路径: ${totalFolders - validFolders.length}`);
    
    return validFolders;
}

async function debugSingleFiles() {
    console.log('\n📄 检查单文件路径...');
    
    for (let i = 0; i < config.singleFiles.length; i++) {
        const file = config.singleFiles[i];
        console.log(`\n[${i + 1}/${config.singleFiles.length}] 检查: ${file.filePath}`);
        
        const result = await checkPathWithTimeout(file.filePath);
        
        if (result.exists) {
            console.log(`   ✅ 文件存在: ${file.tableName}`);
        } else {
            console.log(`   ❌ 文件不存在: ${file.tableName}`);
            if (result.timeout) {
                console.log(`   ⏰ 超时保护生效`);
            }
        }
    }
}

async function main() {
    try {
        console.log('🔧 调试配置: 使用超时保护机制');
        
        const validFolders = await debugWindowsPaths();
        await debugSingleFiles();
        
        console.log('\n✅ 调试完成！');
        
        // 模拟配置返回
        const testConfig = {
            ...config,
            folders: validFolders.length > 0 ? validFolders : [],
            isTestMode: validFolders.length === 0
        };
        
        console.log('\n📋 最终配置:');
        console.log(`   有效文件夹: ${testConfig.folders.length} 个`);
        console.log(`   单文件: ${config.singleFiles.length} 个`);
        console.log(`   测试模式: ${testConfig.isTestMode}`);
        
    } catch (error) {
        console.error('❌ 调试失败:', error.message);
    }
    
    process.exit(0);
}

// 立即执行调试
main();