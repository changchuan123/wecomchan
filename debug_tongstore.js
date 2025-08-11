const xlsx = require('xlsx');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const config = require('./config');

console.log('🔍 开始调试tongstore处理逻辑...');

async function debugTongstore() {
    try {
        // 获取tongstore配置
        const tongstoreConfig = config.inventory.tongstore;
        console.log('📋 tongstore配置:', JSON.stringify(tongstoreConfig, null, 2));

        // 检查文件夹是否存在
        console.log(`🔍 检查文件夹: ${tongstoreConfig.path}`);
        if (!fs.existsSync(tongstoreConfig.path)) {
            console.log(`❌ 文件夹不存在: ${tongstoreConfig.path}`);
            return;
        }
        console.log(`✅ 文件夹存在: ${tongstoreConfig.path}`);

        // 获取所有文件
        const allFiles = fs.readdirSync(tongstoreConfig.path);
        console.log(`📋 文件夹中的所有文件: ${allFiles.join(', ')}`);

        // 将通配符模式转换为正则表达式
        const patternRegex = tongstoreConfig.pattern.replace(/\*/g, '.*').replace(/\./g, '\\.');
        console.log(`📋 通配符模式: ${tongstoreConfig.pattern}`);
        console.log(`📋 转换后的正则表达式: ${patternRegex}`);

        const files = allFiles.filter(f => f.match(new RegExp(patternRegex)));
        console.log(`📋 符合模式的文件: ${files.join(', ')}`);

        if (files.length === 0) {
            console.log(`❌ 未找到符合模式的文件`);
            return;
        }

        console.log(`✅ 找到 ${files.length} 个符合模式的文件`);

        // 测试文件名匹配
        console.log('\n🔍 测试文件名匹配...');
        files.forEach(file => {
            console.log(`\n📄 测试文件: ${file}`);
            console.log(`🔍 使用的正则表达式: ${tongstoreConfig.fileNamePattern}`);

            const match = file.match(new RegExp(tongstoreConfig.fileNamePattern));
            if (!match) {
                console.log(`❌ 文件名格式不匹配: ${file}`);
                return;
            }

            console.log(`✅ 文件名匹配成功!`);
            console.log(`📋 完整匹配: ${match[0]}`);
            console.log(`📋 账户ID: ${match[1]}`);
            console.log(`📋 日期: ${match[2]}`);

            const accountId = tongstoreConfig.hasAccountId ? match[1] : 'default';
            const dateStr = tongstoreConfig.hasAccountId ? match[2] : match[1];
            console.log(`📅 提取的账户ID: ${accountId}, 日期: ${dateStr}`);

            const fileDate = new Date(dateStr.replace(/-/g, '/'));
            console.log(`📅 解析的日期: ${fileDate.toISOString()}`);
        });

        // 按账户分组并找到最新文件
        console.log('\n🔍 按账户分组并找到最新文件...');
        const accountFiles = {};
        files.forEach(file => {
            const match = file.match(new RegExp(tongstoreConfig.fileNamePattern));
            if (!match) {
                return;
            }

            const accountId = tongstoreConfig.hasAccountId ? match[1] : 'default';
            const dateStr = tongstoreConfig.hasAccountId ? match[2] : match[1];
            const fileDate = new Date(dateStr.replace(/-/g, '/'));

            if (!accountFiles[accountId] || fileDate > accountFiles[accountId].date) {
                accountFiles[accountId] = { file, date: fileDate };
                console.log(`✅ 更新账户 ${accountId} 的最新文件: ${file}`);
            }
        });

        // 处理每个账户的最新文件
        const latestFiles = Object.values(accountFiles).map(item => item.file);
        console.log(`\n📋 找到最新文件: ${latestFiles.join(', ')}`);

        if (latestFiles.length === 0) {
            console.log(`❌ 没有找到有效的最新文件`);
            return;
        }

        // 测试Excel文件读取
        console.log('\n🔍 测试Excel文件读取...');
        for (const file of latestFiles) {
            const filePath = path.join(tongstoreConfig.path, file);
            console.log(`\n📄 读取文件: ${filePath}`);

            try {
                const workbook = xlsx.readFile(filePath);
                const sheetNames = workbook.SheetNames;
                console.log(`📋 工作表名称: ${sheetNames.join(', ')}`);

                if (sheetNames.length > 0) {
                    const sheetName = sheetNames[0];
                    const worksheet = workbook.Sheets[sheetName];
                    const data = xlsx.utils.sheet_to_json(worksheet, { header: 1 });

                    console.log(`📊 数据行数: ${data.length}`);
                    if (data.length > 0) {
                        console.log(`📋 第一行数据: ${JSON.stringify(data[0])}`);
                        console.log(`📋 第二行数据: ${JSON.stringify(data[1])}`);
                    }

                    // 转换为对象格式
                    const jsonData = xlsx.utils.sheet_to_json(worksheet);
                    console.log(`📊 JSON数据行数: ${jsonData.length}`);
                    if (jsonData.length > 0) {
                        console.log(`📋 第一行JSON: ${JSON.stringify(jsonData[0])}`);
                        console.log(`📋 列名: ${Object.keys(jsonData[0]).join(', ')}`);
                    }
                }
            } catch (error) {
                console.error(`❌ 读取文件失败: ${error.message}`);
            }
        }

        console.log('\n✅ 调试完成!');

    } catch (error) {
        console.error('❌ 调试过程中发生错误:', error);
    }
}

// 运行调试
debugTongstore(); 