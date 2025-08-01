const mysql = require('mysql2/promise');
const fs = require('fs');
const config = require('./config');

console.log('🔍 快速诊断脚本启动...');

async function quickDiagnose() {
    console.log('\n1. 检查配置文件...');
    try {
        console.log('✅ 配置文件正常');
    } catch (error) {
        console.log('❌ 配置文件错误:', error.message);
        return;
    }

    console.log('\n2. 测试数据库连接...');
    let connection = null;
    try {
        const pool = mysql.createPool({
            ...config.database,
            acquireTimeout: 10000,
            timeout: 10000
        });
        connection = await pool.getConnection();
        console.log('✅ 数据库连接成功');
        await connection.release();
        await pool.end();
    } catch (error) {
        console.log('❌ 数据库连接失败:', error.message);
        return;
    }

    console.log('\n3. 检查文件路径...');
    let foundFiles = 0;
    for (const folder of config.folders) {
        if (fs.existsSync(folder.path)) {
            console.log(`✅ 文件夹存在: ${folder.path}`);
            foundFiles++;
        } else {
            console.log(`❌ 文件夹不存在: ${folder.path}`);
        }
    }

    console.log(`\n📊 找到 ${foundFiles} 个有效文件夹`);
    console.log('✅ 诊断完成，可以尝试运行上传脚本');
}

quickDiagnose().catch(console.error); 