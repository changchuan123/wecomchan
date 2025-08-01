const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const config = require('./config');

console.log('🔍 Windows数据库上传诊断脚本启动...');
console.log('⏰ 时间:', new Date().toLocaleString('zh-CN'));

// 诊断步骤1：检查配置文件
async function diagnoseConfig() {
    console.log('\n📋 步骤1: 检查配置文件...');

    try {
        console.log('✅ 配置文件加载成功');
        console.log('📊 数据库配置:', {
            host: config.database.host,
            port: config.database.port,
            database: config.database.database,
            user: config.database.user
        });

        console.log(`📁 文件夹数量: ${config.folders.length}`);
        console.log(`📄 单文件数量: ${config.singleFiles.length}`);

        return true;
    } catch (error) {
        console.log('❌ 配置文件检查失败:', error.message);
        return false;
    }
}

// 诊断步骤2：测试数据库连接
async function diagnoseDatabase() {
    console.log('\n🔗 步骤2: 测试数据库连接...');

    let connection = null;
    try {
        console.log('🔄 尝试连接数据库...');

        const poolConfig = {
            ...config.database,
            acquireTimeout: 10000, // 10秒超时
            timeout: 10000,
            connectTimeout: 10000
        };

        const pool = mysql.createPool(poolConfig);
        connection = await pool.getConnection();

        console.log('✅ 数据库连接成功');

        // 测试简单查询
        const [result] = await connection.query('SELECT 1 as test');
        console.log('✅ 数据库查询测试成功');

        // 检查数据库是否存在
        const [databases] = await connection.query('SHOW DATABASES');
        const dbExists = databases.some(db => db.Database === config.database.database);

        if (dbExists) {
            console.log('✅ 目标数据库存在');
        } else {
            console.log('❌ 目标数据库不存在');
        }

        return true;
    } catch (error) {
        console.log('❌ 数据库连接失败:', error.message);
        console.log('💡 可能的原因:');
        console.log('   - 网络连接问题');
        console.log('   - 数据库服务器未启动');
        console.log('   - 用户名或密码错误');
        console.log('   - 防火墙阻止连接');
        return false;
    } finally {
        if (connection) {
            try {
                await connection.release();
                await connection.pool.end();
            } catch (e) {
                console.log('⚠️ 释放连接时出错:', e.message);
            }
        }
    }
}

// 诊断步骤3：检查文件路径
async function diagnoseFilePaths() {
    console.log('\n📁 步骤3: 检查文件路径...');

    let validPaths = 0;
    let invalidPaths = 0;

    // 检查文件夹路径
    for (const folder of config.folders) {
        try {
            console.log(`🔍 检查文件夹: ${folder.path}`);

            // 使用同步方法快速检查
            const exists = fs.existsSync(folder.path);

            if (exists) {
                console.log(`✅ 文件夹存在: ${folder.path}`);
                validPaths++;

                // 检查文件夹内容
                try {
                    const files = fs.readdirSync(folder.path);
                    const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));
                    console.log(`📊 找到 ${excelFiles.length} 个Excel文件`);
                } catch (readError) {
                    console.log(`⚠️ 无法读取文件夹内容: ${readError.message}`);
                }
            } else {
                console.log(`❌ 文件夹不存在: ${folder.path}`);
                invalidPaths++;
            }
        } catch (error) {
            console.log(`❌ 检查文件夹失败: ${folder.path} - ${error.message}`);
            invalidPaths++;
        }
    }

    // 检查单文件路径
    for (const singleFile of config.singleFiles) {
        try {
            console.log(`🔍 检查文件: ${singleFile.filePath}`);

            const exists = fs.existsSync(singleFile.filePath);

            if (exists) {
                console.log(`✅ 文件存在: ${singleFile.filePath}`);
                validPaths++;

                // 检查文件大小
                const stats = fs.statSync(singleFile.filePath);
                const sizeMB = (stats.size / 1024 / 1024).toFixed(2);
                console.log(`📊 文件大小: ${sizeMB}MB`);
            } else {
                console.log(`❌ 文件不存在: ${singleFile.filePath}`);
                invalidPaths++;
            }
        } catch (error) {
            console.log(`❌ 检查文件失败: ${singleFile.filePath} - ${error.message}`);
            invalidPaths++;
        }
    }

    console.log(`\n📊 路径检查结果: ${validPaths} 个有效, ${invalidPaths} 个无效`);
    return validPaths > 0;
}

// 诊断步骤4：测试Excel文件读取
async function diagnoseExcelReading() {
    console.log('\n📊 步骤4: 测试Excel文件读取...');

    const xlsx = require('xlsx');

    // 找到第一个存在的Excel文件进行测试
    let testFile = null;

    for (const folder of config.folders) {
        if (fs.existsSync(folder.path)) {
            try {
                const files = fs.readdirSync(folder.path);
                const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));

                if (excelFiles.length > 0) {
                    testFile = path.join(folder.path, excelFiles[0]);
                    break;
                }
            } catch (error) {
                console.log(`⚠️ 无法读取文件夹: ${folder.path}`);
            }
        }
    }

    if (!testFile) {
        console.log('❌ 没有找到可测试的Excel文件');
        return false;
    }

    try {
        console.log(`🔍 测试读取文件: ${testFile}`);

        const startTime = Date.now();
        const workbook = xlsx.readFile(testFile);
        const readTime = Date.now() - startTime;

        console.log(`✅ Excel文件读取成功 (耗时: ${readTime}ms)`);

        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];

        const data = xlsx.utils.sheet_to_json(worksheet, { defval: null });
        console.log(`📊 数据行数: ${data.length}`);

        if (data.length > 0) {
            console.log(`📋 列名: ${Object.keys(data[0]).join(', ')}`);
        }

        return true;
    } catch (error) {
        console.log('❌ Excel文件读取失败:', error.message);
        console.log('💡 可能的原因:');
        console.log('   - 文件被其他程序占用');
        console.log('   - 文件损坏');
        console.log('   - 内存不足');
        return false;
    }
}

// 诊断步骤5：测试数据库表操作
async function diagnoseDatabaseOperations() {
    console.log('\n🗄️ 步骤5: 测试数据库表操作...');

    let connection = null;
    try {
        const pool = mysql.createPool(config.database);
        connection = await pool.getConnection();

        // 测试创建表
        const testTableName = 'diagnose_test_table';
        console.log(`🔧 测试创建表: ${testTableName}`);

        await connection.query(`
            CREATE TABLE IF NOT EXISTS \`${testTableName}\` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                test_column VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `);

        console.log('✅ 表创建成功');

        // 测试插入数据
        console.log('📝 测试插入数据...');
        await connection.query(
            `INSERT INTO \`${testTableName}\` (test_column) VALUES (?)`,
            ['诊断测试数据']
        );

        console.log('✅ 数据插入成功');

        // 测试查询数据
        const [rows] = await connection.query(`SELECT * FROM \`${testTableName}\``);
        console.log(`✅ 数据查询成功，找到 ${rows.length} 条记录`);

        // 清理测试表
        await connection.query(`DROP TABLE \`${testTableName}\``);
        console.log('🧹 测试表已清理');

        return true;
    } catch (error) {
        console.log('❌ 数据库操作测试失败:', error.message);
        return false;
    } finally {
        if (connection) {
            try {
                await connection.release();
                await connection.pool.end();
            } catch (e) {
                console.log('⚠️ 释放连接时出错:', e.message);
            }
        }
    }
}

// 主诊断函数
async function runDiagnosis() {
    console.log('🚀 开始Windows环境诊断...\n');

    const results = {
        config: false,
        database: false,
        filePaths: false,
        excelReading: false,
        dbOperations: false
    };

    try {
        // 步骤1: 检查配置
        results.config = await diagnoseConfig();

        // 步骤2: 测试数据库连接
        results.database = await diagnoseDatabase();

        // 步骤3: 检查文件路径
        results.filePaths = await diagnoseFilePaths();

        // 步骤4: 测试Excel读取
        if (results.filePaths) {
            results.excelReading = await diagnoseExcelReading();
        }

        // 步骤5: 测试数据库操作
        if (results.database) {
            results.dbOperations = await diagnoseDatabaseOperations();
        }

    } catch (error) {
        console.log('💥 诊断过程中发生错误:', error.message);
    }

    // 输出诊断结果
    console.log('\n📊 诊断结果汇总:');
    console.log('=' * 50);
    console.log(`📋 配置文件: ${results.config ? '✅ 正常' : '❌ 异常'}`);
    console.log(`🔗 数据库连接: ${results.database ? '✅ 正常' : '❌ 异常'}`);
    console.log(`📁 文件路径: ${results.filePaths ? '✅ 正常' : '❌ 异常'}`);
    console.log(`📊 Excel读取: ${results.excelReading ? '✅ 正常' : '❌ 异常'}`);
    console.log(`🗄️ 数据库操作: ${results.dbOperations ? '✅ 正常' : '❌ 异常'}`);

    // 提供建议
    console.log('\n💡 建议:');
    if (!results.database) {
        console.log('🔧 请检查数据库连接配置和网络连接');
    }
    if (!results.filePaths) {
        console.log('🔧 请检查文件路径是否正确，确保文件存在');
    }
    if (!results.excelReading) {
        console.log('🔧 请检查Excel文件是否被其他程序占用');
    }
    if (!results.dbOperations) {
        console.log('🔧 请检查数据库权限和表结构');
    }

    if (results.config && results.database && results.filePaths && results.excelReading && results.dbOperations) {
        console.log('🎉 所有检查都通过，可以尝试运行完整的上传脚本');
    } else {
        console.log('⚠️ 发现问题，请先解决上述问题再运行上传脚本');
    }
}

// 运行诊断
if (require.main === module) {
    runDiagnosis()
        .then(() => {
            console.log('\n✅ 诊断完成');
            process.exit(0);
        })
        .catch((error) => {
            console.error('💥 诊断失败:', error.message);
            process.exit(1);
        });
}

module.exports = { runDiagnosis }; 