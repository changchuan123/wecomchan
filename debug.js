// 调试版本 - 逐步检查
console.log('🚀 开始调试...');

// 检查基础依赖
console.log('📦 检查依赖模块...');
try {
    console.log('✅ xlsx:', require('xlsx'));
    console.log('✅ mysql2:', require('mysql2/promise'));
    console.log('✅ fs:', require('fs'));
    console.log('✅ path:', require('path'));
    console.log('✅ https:', require('https'));
    console.log('✅ os:', require('os'));
    console.log('✅ process:', require('process'));
} catch (e) {
    console.error('❌ 依赖加载失败:', e.message);
    process.exit(1);
}

// 检查配置文件
console.log('\n📄 检查配置文件...');
try {
    const config = require('./config');
    console.log('✅ 配置文件加载成功');
    console.log('数据库配置:', config.database ? '已配置' : '未配置');
    console.log('文件夹配置:', config.folders ? `${config.folders.length}个` : '未配置');
    console.log('企业微信配置:', config.wecom ? '已配置' : '未配置');
} catch (e) {
    console.error('❌ 配置文件加载失败:', e.message);
    process.exit(1);
}

// 检查MySQL连接
console.log('\n🔗 检查MySQL连接...');
try {
    const mysql = require('mysql2/promise');
    const config = require('./config');
    
    async function testConnection() {
        console.log('尝试连接数据库...');
        const pool = mysql.createPool(config.database);
        const connection = await pool.getConnection();
        console.log('✅ 数据库连接成功');
        
        // 测试查询
        const [result] = await connection.execute('SELECT 1 as test');
        console.log('✅ 查询测试成功:', result);
        
        connection.release();
        await pool.end();
    }
    
    testConnection().then(() => {
        console.log('\n🎉 所有测试通过！');
        process.exit(0);
    }).catch(e => {
        console.error('❌ 数据库测试失败:', e.message);
        process.exit(1);
    });
    
} catch (e) {
    console.error('❌ MySQL测试失败:', e.message);
    process.exit(1);
}