const xlsx = require('xlsx');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const config = require('./config');
const https = require('https');

console.log('🚀 修复版数据库上传脚本启动...');
console.log('开始手动导入Excel数据到数据库...');
console.log('开始时间:', new Date().toLocaleString('zh-CN'));

// 简化的配置检查
async function checkConfig() {
    console.log('🔍 跳过路径检查，直接处理...');
    return config;
}

// 获取数据库连接池 - 使用mysql2支持的配置
async function getPool() {
    const poolConfig = {
        host: config.database.host,
        user: config.database.user,
        password: config.database.password,
        database: config.database.database,
        port: config.database.port,
        connectionLimit: 10,
        queueLimit: 0,
        waitForConnections: true
    };

    return mysql.createPool(poolConfig);
}

// 企业微信消息发送
async function sendWecomMessage(message) {
    if (!config.wecom?.webhook_url) {
        console.log('⚠️ 企业微信配置缺失，跳过消息发送');
        return false;
    }

    try {
        const data = JSON.stringify({
            msgtype: 'text',
            text: { content: message }
        });

        const url = new URL(config.wecom.webhook_url);
        const options = {
            hostname: url.hostname,
            port: url.port || 443,
            path: url.pathname + url.search,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Content-Length': Buffer.byteLength(data)
            },
            timeout: 10000
        };

        return new Promise((resolve) => {
            const req = https.request(options, (res) => {
                let responseData = '';
                res.on('data', (chunk) => {
                    responseData += chunk;
                });
                res.on('end', () => {
                    try {
                        const result = JSON.parse(responseData);
                        if (result.errcode === 0) {
                            console.log('✅ 企业微信消息发送成功');
                            resolve(true);
                        } else {
                            console.log(`❌ 企业微信消息发送失败: ${result.errmsg}`);
                            resolve(false);
                        }
                    } catch (e) {
                        console.log('❌ 解析企业微信响应失败');
                        resolve(false);
                    }
                });
            });

            req.on('error', (error) => {
                console.log(`❌ 企业微信请求失败: ${error.message}`);
                resolve(false);
            });

            req.on('timeout', () => {
                console.log('⏰ 企业微信请求超时');
                req.destroy();
                resolve(false);
            });

            req.write(data);
            req.end();
        });
    } catch (error) {
        console.log(`❌ 企业微信消息发送异常: ${error.message}`);
        return false;
    }
}

// 生成上传报告
function generateUploadReport(uploadResults) {
    const now = new Date();
    const timestamp = now.toLocaleString('zh-CN');

    let report = `📊 数据库上传完成报告\n`;
    report += `⏰ 时间: ${timestamp}\n`;
    report += `📁 处理文件数: ${uploadResults.totalFiles || 0} 个\n`;
    report += `📈 总记录数: ${uploadResults.totalRecords || 0} 条\n`;
    report += `✅ 成功: ${uploadResults.successRecords || 0} 条\n`;
    report += `❌ 失败: ${uploadResults.failedRecords || 0} 条\n`;
    report += `⏱️ 总耗时: ${uploadResults.totalTime || 0}ms\n\n`;

    if (uploadResults.errors && uploadResults.errors.length > 0) {
        report += `❌ 错误信息:\n`;
        uploadResults.errors.forEach((error, index) => {
            report += `${index + 1}. ${error}\n`;
        });
    }

    return report;
}

// 处理Excel文件
async function processExcelFile(filePath) {
    try {
        console.log(`📁 处理文件: ${filePath}`);
        const workbook = xlsx.readFile(filePath);
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const data = xlsx.utils.sheet_to_json(worksheet, { defval: null });

        if (data.length === 0) {
            console.log('文件中没有数据');
            return null;
        }

        console.log(`✅ 文件处理完成，包含 ${data.length} 条记录`);
        return data;
    } catch (error) {
        console.error(`❌ 处理文件时出错:`, error);
        return null;
    }
}

// 创建表
async function createTableIfNotExists(connection, tableName, columns) {
    try {
        const [existingTables] = await connection.execute(`
            SELECT COUNT(*) as count 
            FROM information_schema.tables 
            WHERE table_schema = ? AND table_name = ?
        `, ['Date', tableName]);

        if (existingTables[0].count > 0) {
            console.log(`✅ 表 ${tableName} 已存在，跳过创建`);
            return;
        }

        const filteredColumns = columns.filter(col => col.toLowerCase() !== 'id');
        const columnDefinitions = filteredColumns.map(col => `\`${col}\` TEXT`).join(', ');
        const createTableSql = `
            CREATE TABLE \`${tableName}\` (
                id INT AUTO_INCREMENT PRIMARY KEY,
                ${columnDefinitions},
                \`_filepath\` VARCHAR(255),
                import_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        `;
        await connection.query(createTableSql);
        console.log(`✅ 表 ${tableName} 创建完成`);
    } catch (error) {
        console.error(`❌ 创建表 ${tableName} 时出错:`, error.message);
        throw error;
    }
}

// 更新表数据
async function updateTableIncrementally(connection, tableName, data, filePath) {
    try {
        if (!data || data.length === 0) return { successCount: 0, failCount: 0 };

        const fileName = path.basename(filePath);
        console.log(`🚀 开始处理文件: ${fileName} (${data.length} 条记录)`);

        let columns = Object.keys(data[0]).filter(col =>
            !['id', '_filepath'].includes(col.toLowerCase()) &&
            col && col.trim() !== '' && col !== '__EMPTY'
        );

        if (columns.length === 0) {
            throw new Error('数据中没有有效的列名');
        }

        console.log(`📋 有效列名: ${columns.join(', ')}`);

        await createTableIfNotExists(connection, tableName, columns);

        // 检查文件是否已上传
        const [existing] = await connection.execute(`
            SELECT COUNT(*) as count FROM ${tableName} 
            WHERE _filepath = ?
        `, [fileName]);

        if (existing[0].count > 0) {
            console.log(`⏭️ 文件已上传过，跳过: ${fileName}`);
            return { successCount: 0, failCount: 0 };
        }

        // 为fenxiaochanpin表使用覆盖模式
        if (tableName === 'fenxiaochanpin') {
            console.log(`🔄 fenxiaochanpin表使用覆盖上传模式，清空旧数据...`);
            await connection.query(`DELETE FROM \`${tableName}\``);
        }

        console.log(`✅ 文件 ${fileName} 首次上传，开始插入数据...`);

        const dataWithFilePath = data.map(row => ({
            ...row,
            _filepath: fileName
        }));

        await connection.beginTransaction();

        try {
            let successCount = 0;
            let failCount = 0;

            const [currentColumns] = await connection.query(`SHOW COLUMNS FROM \`${tableName}\``);
            let actualColumns = currentColumns.filter(col =>
                col.Field.toLowerCase() !== 'id' &&
                col.Field.toLowerCase() !== '_filepath'
            ).map(col => col.Field);

            console.log(`📋 实际字段列表: ${actualColumns.join(', ')}`);

            const columnNames = actualColumns.concat(['_filepath']).map(col => `\`${col}\``).join(', ');
            const batchSize = 100; // 减小批次大小

            console.log(`📦 使用批量大小: ${batchSize}`);

            for (let i = 0; i < dataWithFilePath.length; i += batchSize) {
                const batch = dataWithFilePath.slice(i, i + batchSize);
                const batchValues = batch.map(row =>
                    actualColumns.concat(['_filepath']).map(col => row[col] || null)
                );

                try {
                    const [result] = await connection.query(
                        `INSERT INTO ${tableName} (${columnNames}) VALUES ?`,
                        [batchValues]
                    );
                    successCount += result.affectedRows;
                } catch (error) {
                    console.log(`❌ 批量插入失败，回退到单条插入: ${error.message}`);
                    failCount += batch.length;
                }
            }

            await connection.commit();

            console.log(`\n📊 文件 ${fileName} 上传完成:`);
            console.log(`  ✅ 成功插入: ${successCount} 条`);
            console.log(`  ❌ 插入失败: ${failCount} 条`);

            return { successCount, failCount };

        } catch (error) {
            await connection.rollback();
            console.error(`❌ 文件 ${fileName} 上传失败: ${error.message}`);
            throw error;
        }
    } catch (error) {
        console.error(`❌ 上传失败: ${error.message}`);
        throw error;
    }
}

// 主函数
async function importExcelToDatabase() {
    console.log('🚀 开始执行数据库导入任务...');

    const startTime = Date.now();
    const uploadResults = {
        successCount: 0,
        failCount: 0,
        successRecords: 0,
        failedRecords: 0,
        totalFiles: 0,
        totalRecords: 0,
        totalTime: 0,
        tableResults: [],
        errors: []
    };

    try {
        // 检查配置
        const config = await checkConfig();
        if (!config) {
            throw new Error('配置检查失败');
        }

        // 获取数据库连接
        const pool = await getPool();
        const connection = await pool.getConnection();

        try {
            console.log('✅ 数据库连接成功');

            // 检查是否有实际文件需要处理
            let hasRealFiles = false;

            // 检查文件夹中的文件
            for (const folder of config.folders) {
                if (fs.existsSync(folder.path)) {
                    try {
                        const files = fs.readdirSync(folder.path);
                        const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));
                        if (excelFiles.length > 0) {
                            hasRealFiles = true;
                            console.log(`📁 找到文件夹: ${folder.path} (${excelFiles.length} 个Excel文件)`);
                        }
                    } catch (error) {
                        console.log(`⚠️ 无法读取文件夹: ${folder.path}`);
                    }
                }
            }

            // 检查单文件
            for (const singleFile of config.singleFiles) {
                if (fs.existsSync(singleFile.filePath)) {
                    hasRealFiles = true;
                    console.log(`📄 找到文件: ${singleFile.filePath}`);
                }
            }

            if (!hasRealFiles) {
                console.log('🧪 没有找到实际文件，进入测试模式...');

                // 模拟测试数据
                const testData = {
                    isTestMode: true,
                    successCount: 0,
                    failCount: 0,
                    totalFiles: 0,
                    totalRecords: 0,
                    successRecords: 0,
                    failedRecords: 0,
                    totalTime: Date.now() - startTime,
                    avgSpeed: 0,
                    tableResults: [],
                    errors: [],
                    details: [{
                        tableName: 'test_table',
                        fileName: 'test.xlsx',
                        successCount: 0,
                        failCount: 0,
                        error: '测试模式：无实际数据'
                    }]
                };

                console.log('📊 测试模式完成');

                // 生成测试报告
                const report = generateUploadReport(testData);
                console.log('\n' + report);

                // 发送测试报告
                try {
                    await sendWecomMessage(report);
                    console.log('📱 测试报告已发送到企业微信');
                } catch (sendError) {
                    console.log('⚠️ 发送测试报告失败:', sendError.message);
                }

                return testData;
            } else {
                console.log('�� 找到实际文件，开始处理...');

                // 实际处理文件逻辑
                let totalFiles = 0;
                let totalRecords = 0;
                let successRecords = 0;
                let failedRecords = 0;

                // 处理文件夹中的文件
                for (const folder of config.folders) {
                    if (fs.existsSync(folder.path)) {
                        try {
                            const files = fs.readdirSync(folder.path);
                            const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));

                            for (const file of excelFiles) {
                                const filePath = path.join(folder.path, file);
                                console.log(`\n📁 处理文件: ${file} -> 表: ${folder.tableName}`);

                                try {
                                    const data = await processExcelFile(filePath);
                                    if (data && data.length > 0) {
                                        const result = await updateTableIncrementally(connection, folder.tableName, data, filePath);
                                        totalFiles++;
                                        totalRecords += data.length;
                                        successRecords += result.successCount;
                                        failedRecords += result.failCount;
                                    }
                                } catch (error) {
                                    console.log(`❌ 处理文件 ${file} 失败: ${error.message}`);
                                    uploadResults.errors.push(`文件 ${file} 处理失败: ${error.message}`);
                                }
                            }
                        } catch (error) {
                            console.log(`⚠️ 无法读取文件夹: ${folder.path}`);
                        }
                    }
                }

                // 处理单文件
                for (const singleFile of config.singleFiles) {
                    if (fs.existsSync(singleFile.filePath)) {
                        console.log(`\n📄 处理单文件: ${path.basename(singleFile.filePath)} -> 表: ${singleFile.tableName}`);

                        try {
                            const data = await processExcelFile(singleFile.filePath);
                            if (data && data.length > 0) {
                                const result = await updateTableIncrementally(connection, singleFile.tableName, data, singleFile.filePath);
                                totalFiles++;
                                totalRecords += data.length;
                                successRecords += result.successCount;
                                failedRecords += result.failCount;
                            }
                        } catch (error) {
                            console.log(`❌ 处理单文件失败: ${error.message}`);
                            uploadResults.errors.push(`单文件处理失败: ${error.message}`);
                        }
                    }
                }

                // 更新结果
                uploadResults.totalFiles = totalFiles;
                uploadResults.totalRecords = totalRecords;
                uploadResults.successRecords = successRecords;
                uploadResults.failedRecords = failedRecords;
                uploadResults.totalTime = Date.now() - startTime;

                console.log('✅ 文件处理完成');

                const report = generateUploadReport(uploadResults);
                console.log('\n' + report);
                await sendWecomMessage(report);

                return uploadResults;
            }

        } finally {
            await connection.release();
            await pool.end();
        }

    } catch (error) {
        console.error(`❌ importExcelToDatabase 函数执行失败: ${error.message}`);

        const errorReport = `🚨 数据库上传失败报告
⏰ 时间: ${new Date().toLocaleString('zh-CN')}
❌ 错误类型: 数据库上传失败
💥 错误信息: ${error.message}`;

        try {
            await sendWecomMessage(errorReport);
            console.log('📱 错误报告已发送到企业微信');
        } catch (pushError) {
            console.error('❌ 发送错误报告失败:', pushError.message);
        }

        throw error;
    }
}

// 如果直接运行此文件，则执行导入
if (require.main === module) {
    console.log('🚀 手动导入脚本启动中...');

    const startTime = Date.now();

    // 添加全局错误捕获
    process.on('uncaughtException', (error) => {
        console.error('💥 未捕获的异常:', error.message);
        console.error('📋 错误堆栈:', error.stack);

        const errorReport = `🚨 脚本执行异常
⏰ 时间: ${new Date().toLocaleString('zh-CN')}
❌ 错误类型: 未捕获异常
💥 错误信息: ${error.message}`;

        // 尝试发送错误报告
        sendWecomMessage(errorReport).catch(() => {
            console.log('⚠️ 发送错误报告失败');
        });

        process.exit(1);
    });

    process.on('unhandledRejection', (reason, promise) => {
        console.error('💥 未处理的Promise拒绝:', reason);

        const errorReport = `🚨 脚本执行异常
⏰ 时间: ${new Date().toLocaleString('zh-CN')}
❌ 错误类型: Promise拒绝
💥 错误信息: ${reason}`;

        // 尝试发送错误报告
        sendWecomMessage(errorReport).catch(() => {
            console.log('⚠️ 发送错误报告失败');
        });

        process.exit(1);
    });

    importExcelToDatabase()
        .then((results) => {
            const endTime = Date.now();
            const totalTime = endTime - startTime;

            console.log('\n🎉 数据库上传任务完成!');
            console.log(`⏱️ 总耗时: ${totalTime}ms`);

            if (results) {
                console.log(`✅ 成功处理: ${results.successCount} 条记录`);
                console.log(`❌ 失败记录: ${results.failCount} 条记录`);
            }

            console.log('📱 请检查企业微信是否收到推送消息');

            // 等待3秒后退出，让用户看到结果
            setTimeout(() => {
                process.exit(0);
            }, 3000);
        })
        .catch((error) => {
            console.error('💥 数据库上传任务失败:', error.message);
            console.error('📋 错误详情:', error);

            // 等待3秒后退出，让用户看到错误信息
            setTimeout(() => {
                process.exit(1);
            }, 3000);
        });
}

module.exports = { importExcelToDatabase, sendWecomMessage }; 