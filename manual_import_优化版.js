const xlsx = require('xlsx');
const mysql = require('mysql2/promise');
const fs = require('fs');
const path = require('path');
const config = require('./config');
const https = require('https');

console.log('🚀 优化版数据库上传脚本启动...');
console.log('开始批量导入Excel数据到数据库...');
console.log('开始时间:', new Date().toLocaleString('zh-CN'));

// 简化的配置检查
async function checkConfig() {
    console.log('🔍 跳过路径检查，直接处理...');
    return config;
}

// 获取数据库连接池
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
    report += `📁 处理文件夹数: ${uploadResults.totalFolders || 0} 个\n`;
    report += `📄 处理文件数: ${uploadResults.totalFiles || 0} 个\n`;
    report += `📈 总记录数: ${uploadResults.totalRecords || 0} 条\n`;
    report += `✅ 成功: ${uploadResults.successRecords || 0} 条\n`;
    report += `❌ 失败: ${uploadResults.failedRecords || 0} 条\n`;
    report += `⏱️ 总耗时: ${uploadResults.totalTime || 0}ms\n\n`;

    if (uploadResults.folderResults && uploadResults.folderResults.length > 0) {
        report += `📋 文件夹处理详情:\n`;
        uploadResults.folderResults.forEach(result => {
            report += `• ${result.folderName}: ${result.successFiles} 个文件成功, ${result.failFiles} 个文件失败\n`;
        });
        report += '\n';
    }

    // 添加库存处理结果
    if (uploadResults.inventoryResults) {
        const inventory = uploadResults.inventoryResults;
        report += `📦 库存数据处理结果:\n`;
        report += `📊 库存类型: ${inventory.totalTypes} 个\n`;
        report += `✅ 成功类型: ${inventory.successTypes} 个\n`;
        report += `❌ 失败类型: ${inventory.failTypes} 个\n`;
        report += `📄 处理文件: ${inventory.totalFiles} 个\n`;
        report += `📈 库存记录: ${inventory.totalRecords} 条\n`;
        report += `✅ 成功记录: ${inventory.successRecords} 条\n\n`;

        if (inventory.typeResults && inventory.typeResults.length > 0) {
            report += `📋 库存类型处理详情:\n`;
            inventory.typeResults.forEach(result => {
                report += `• ${result.type} (${result.tableName}): ${result.files.length} 个文件, ${result.records} 条记录\n`;
            });
            report += '\n';
        }

        if (inventory.errors && inventory.errors.length > 0) {
            report += `❌ 库存处理错误:\n`;
            inventory.errors.forEach((error, index) => {
                report += `${index + 1}. ${error}\n`;
            });
            report += '\n';
        }
    }

    if (uploadResults.errors && uploadResults.errors.length > 0) {
        report += `❌ 错误信息:\n`;
        uploadResults.errors.forEach((error, index) => {
            report += `${index + 1}. ${error}\n`;
        });
    }

    return report;
}

// 转换Excel日期序列号为标准日期格式
function convertExcelDate(excelDate) {
    if (!excelDate || excelDate === '') return null;

    // 如果已经是标准日期格式，直接返回
    if (typeof excelDate === 'string' && /^\d{4}-\d{2}-\d{2}/.test(excelDate)) {
        return excelDate;
    }

    // 处理日期范围格式 (如: '20250521~20250521')
    if (typeof excelDate === 'string' && excelDate.includes('~')) {
        const parts = excelDate.split('~');
        if (parts.length >= 1) {
            const startDate = parts[0].trim();
            // 处理8位数字格式 (如: 20250521)
            if (/^\d{8}$/.test(startDate)) {
                const year = startDate.substring(0, 4);
                const month = startDate.substring(4, 6);
                const day = startDate.substring(6, 8);
                return `${year}-${month}-${day}`;
            }
        }
    }

    // 处理字符串格式的Excel日期序列号
    if (typeof excelDate === 'string' && /^\d+$/.test(excelDate)) {
        const numericDate = parseFloat(excelDate);
        if (numericDate > 1 && numericDate < 100000) {
            excelDate = numericDate;
        }
    }

    // 如果是数字（Excel序列号），转换为日期
    if (typeof excelDate === 'number' && excelDate > 1 && excelDate < 100000) {
        // Excel日期序列号转JS日期
        const excelEpoch = new Date(1900, 0, 1);
        const daysSinceEpoch = Math.floor(excelDate) - 1;

        // 处理Excel的1900年闰年bug
        const adjustedDays = daysSinceEpoch - (excelDate > 59 ? 1 : 0);

        const date = new Date(excelEpoch.getTime() + adjustedDays * 24 * 60 * 60 * 1000);

        // 格式化为yyyy-mm-dd
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');

        return `${year}-${month}-${day}`;
    }

    return excelDate;
}

// 处理Excel文件
async function processExcelFile(filePath) {
    try {
        console.log(`📁 处理文件: ${path.basename(filePath)}`);
        const workbook = xlsx.readFile(filePath);
        const sheetName = workbook.SheetNames[0];
        const worksheet = workbook.Sheets[sheetName];
        const data = xlsx.utils.sheet_to_json(worksheet, { defval: null });

        if (data.length === 0) {
            console.log('文件中没有数据');
            return null;
        }

        // 智能选择日期字段
        const processedData = data.map(row => {
            const processedRow = { ...row };

            // 查找所有日期相关字段
            const dateFields = [];
            Object.keys(processedRow).forEach(field => {
                if (field && (field.includes('日期') || field.includes('时间'))) {
                    dateFields.push(field);
                }
            });

            // 智能选择最佳日期字段
            if (dateFields.length > 1) {
                console.log(`📅 发现多个日期字段: ${dateFields.join(', ')}`);

                // 优先选择标准格式的日期字段
                let bestDateField = null;
                let bestDateValue = null;

                for (const field of dateFields) {
                    const value = processedRow[field];
                    if (value) {
                        // 检查是否为标准日期格式
                        if (typeof value === 'string' && /^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}/.test(value)) {
                            bestDateField = field;
                            bestDateValue = value;
                            console.log(`✅ 选择标准格式日期字段: ${field} = ${value}`);
                            break;
                        }
                    }
                }

                // 如果没有标准格式，选择第一个非空日期字段
                if (!bestDateField) {
                    for (const field of dateFields) {
                        const value = processedRow[field];
                        if (value && value !== '') {
                            bestDateField = field;
                            bestDateValue = value;
                            console.log(`📅 选择日期字段: ${field} = ${value}`);
                            break;
                        }
                    }
                }

                // 处理选中的日期字段
                if (bestDateField && bestDateValue) {
                    processedRow[bestDateField] = convertExcelDate(bestDateValue);

                    // 移除其他日期字段，避免冲突
                    dateFields.forEach(field => {
                        if (field !== bestDateField) {
                            delete processedRow[field];
                        }
                    });
                }
            } else if (dateFields.length === 1) {
                // 只有一个日期字段，直接处理
                const field = dateFields[0];
                const value = processedRow[field];
                if (value) {
                    processedRow[field] = convertExcelDate(value);
                }
            }

            return processedRow;
        });

        console.log(`✅ 文件处理完成，包含 ${processedData.length} 条记录`);
        return processedData;
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

// 文件夹级别批量去重和上传
async function processFolderBatch(connection, folderPath, tableName) {
    console.log(`\n📁 开始处理文件夹: ${folderPath} -> 表: ${tableName}`);

    try {
        // 获取文件夹中的所有Excel文件
        const files = fs.readdirSync(folderPath);
        const excelFiles = files.filter(f => f.endsWith('.xlsx') || f.endsWith('.xls'));

        if (excelFiles.length === 0) {
            console.log(`⚠️ 文件夹中没有Excel文件: ${folderPath}`);
            return { successFiles: 0, failFiles: 0, totalRecords: 0, successRecords: 0, failRecords: 0 };
        }

        console.log(`📊 找到 ${excelFiles.length} 个Excel文件`);

        // 检查数据库中是否存在重复数据
        const fileNames = excelFiles.map(f => f);

        // 分批查询已上传的文件，避免IN查询参数过多
        const existingFileSet = new Set();
        const batchSize = 100; // 每批查询100个文件

        for (let i = 0; i < fileNames.length; i += batchSize) {
            const batch = fileNames.slice(i, i + batchSize);
            const placeholders = batch.map(() => '?').join(',');

            try {
                const [existingFilesBatch] = await connection.execute(`
                    SELECT DISTINCT _filepath FROM ${tableName} 
                    WHERE _filepath IN (${placeholders})
                `, batch);

                existingFilesBatch.forEach(row => {
                    existingFileSet.add(row._filepath);
                });
            } catch (error) {
                console.log(`⚠️ 批量查询失败，跳过此批次: ${error.message}`);
            }
        }

        const newFiles = excelFiles.filter(file => !existingFileSet.has(file));

        console.log(`📋 已上传文件: ${existingFileSet.size} 个`);
        console.log(`📋 新文件: ${newFiles.length} 个`);

        if (newFiles.length === 0) {
            console.log(`⏭️ 所有文件都已上传，跳过处理`);
            return { successFiles: 0, failFiles: 0, totalRecords: 0, successRecords: 0, failRecords: 0 };
        }

        // 处理新文件
        let totalRecords = 0;
        let successRecords = 0;
        let failRecords = 0;
        let successFiles = 0;
        let failFiles = 0;

        for (const file of newFiles) {
            try {
                const filePath = path.join(folderPath, file);
                console.log(`\n📄 处理新文件: ${file}`);

                const data = await processExcelFile(filePath);
                if (!data || data.length === 0) {
                    console.log(`⚠️ 文件 ${file} 没有数据，跳过`);
                    continue;
                }

                // 获取列名
                let columns = Object.keys(data[0]).filter(col =>
                    !['id', '_filepath'].includes(col.toLowerCase()) &&
                    col && col.trim() !== '' && col !== '__EMPTY'
                );

                if (columns.length === 0) {
                    console.log(`❌ 文件 ${file} 没有有效的列名`);
                    failFiles++;
                    continue;
                }

                // 创建表（如果不存在）
                await createTableIfNotExists(connection, tableName, columns);

                // 为fenxiaochanpin表使用覆盖模式
                if (tableName === 'fenxiaochanpin') {
                    console.log(`🔄 fenxiaochanpin表使用覆盖上传模式，清空旧数据...`);
                    await connection.query(`DELETE FROM \`${tableName}\``);
                }

                // 准备数据
                const dataWithFilePath = data.map(row => ({
                    ...row,
                    _filepath: file
                }));

                await connection.beginTransaction();

                try {
                    const [currentColumns] = await connection.query(`SHOW COLUMNS FROM \`${tableName}\``);
                    let actualColumns = currentColumns.filter(col =>
                        col.Field.toLowerCase() !== 'id' &&
                        col.Field.toLowerCase() !== '_filepath'
                    ).map(col => col.Field);

                    const columnNames = actualColumns.concat(['_filepath']).map(col => `\`${col}\``).join(', ');
                    const batchSize = 100;

                    let fileSuccessCount = 0;
                    let fileFailCount = 0;

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
                            fileSuccessCount += result.affectedRows;
                        } catch (error) {
                            console.log(`❌ 批量插入失败: ${error.message}`);
                            fileFailCount += batch.length;
                        }
                    }

                    await connection.commit();

                    console.log(`✅ 文件 ${file} 上传完成: ${fileSuccessCount} 成功, ${fileFailCount} 失败`);

                    totalRecords += data.length;
                    successRecords += fileSuccessCount;
                    failRecords += fileFailCount;
                    successFiles++;

                } catch (error) {
                    await connection.rollback();
                    console.log(`❌ 文件 ${file} 上传失败: ${error.message}`);
                    failFiles++;
                }

            } catch (error) {
                console.log(`❌ 处理文件 ${file} 失败: ${error.message}`);
                failFiles++;
            }
        }

        console.log(`\n📊 文件夹 ${folderPath} 处理完成:`);
        console.log(`  📄 成功文件: ${successFiles} 个`);
        console.log(`  📄 失败文件: ${failFiles} 个`);
        console.log(`  📈 总记录: ${totalRecords} 条`);
        console.log(`  ✅ 成功记录: ${successRecords} 条`);
        console.log(`  ❌ 失败记录: ${failRecords} 条`);

        return { successFiles, failFiles, totalRecords, successRecords, failRecords };

    } catch (error) {
        console.log(`❌ 处理文件夹 ${folderPath} 失败: ${error.message}`);
        return { successFiles: 0, failFiles: 1, totalRecords: 0, successRecords: 0, failRecords: 0 };
    }
}

// 处理库存数据
async function processInventory(connection) {
    console.log('📦 开始处理库存数据...');
    const inventoryConfig = config.inventory;
    console.log('🔍 检查库存配置...');
    console.log('📋 配置对象:', JSON.stringify(inventoryConfig, null, 2));

    if (!inventoryConfig) {
        console.log('⚠️ 未找到库存配置，跳过处理');
        return null;
    }

    console.log('✅ 找到库存配置，开始处理...');

    const inventoryResults = {
        totalTypes: 0,
        successTypes: 0,
        failTypes: 0,
        totalFiles: 0,
        totalRecords: 0,
        successRecords: 0,
        failRecords: 0,
        typeResults: [],
        errors: []
    };

    // 处理四种库存类型
    const inventoryTypes = ['jdstore', 'rrsstore', 'tongstore', 'jinrongstore'];
    for (const type of inventoryTypes) {
        const configItem = inventoryConfig[type];
        if (!configItem) {
            console.log(`⚠️ 未找到库存类型配置: ${type}`);
            continue;
        }

        inventoryResults.totalTypes++;

        console.log(`\n📦 处理库存类型: ${type}`);
        console.log(`📁 配置路径: ${configItem.path}`);
        console.log(`📋 文件名模式: ${configItem.fileNamePattern}`);
        console.log(`🔢 是否有账户ID: ${configItem.hasAccountId}`);

        try {
            // 检查文件夹是否存在
            if (!fs.existsSync(configItem.path)) {
                console.log(`❌ 文件夹不存在: ${configItem.path}`);
                inventoryResults.failTypes++;
                inventoryResults.errors.push(`库存类型 ${type} 文件夹不存在: ${configItem.path}`);
                continue;
            }

            console.log(`✅ 文件夹存在: ${configItem.path}`);

            // 获取所有文件
            const allFiles = fs.readdirSync(configItem.path);
            console.log(`📋 文件夹中的所有文件: ${allFiles.join(', ')}`);

            // 将通配符模式转换为正则表达式
            const patternRegex = configItem.pattern.replace(/\*/g, '.*').replace(/\./g, '\\.');
            console.log(`📋 转换后的正则表达式: ${patternRegex}`);

            const files = allFiles.filter(f => f.match(new RegExp(patternRegex)));
            console.log(`📋 符合模式的文件: ${files.join(', ')}`);

            if (files.length === 0) {
                console.log(`⚠️ 未找到符合模式的文件: ${configItem.path}`);
                inventoryResults.failTypes++;
                inventoryResults.errors.push(`库存类型 ${type} 未找到符合模式的文件`);
                continue;
            }

            console.log(`📋 找到 ${files.length} 个文件`);

            // 按账户分组并找到最新文件
            const accountFiles = {};
            files.forEach(file => {
                console.log(`🔍 检查文件: ${file}`);
                const match = file.match(new RegExp(configItem.fileNamePattern));
                if (!match) {
                    console.log(`⚠️ 文件名格式不匹配: ${file}`);
                    return;
                }

                const accountId = configItem.hasAccountId ? match[1] : 'default';
                const dateStr = configItem.hasAccountId ? match[2] : match[1];
                console.log(`📅 提取的账户ID: ${accountId}, 日期: ${dateStr}`);

                const fileDate = new Date(dateStr.replace(/-/g, '/'));
                console.log(`📅 解析的日期: ${fileDate.toISOString()}`);

                if (!accountFiles[accountId] || fileDate > accountFiles[accountId].date) {
                    accountFiles[accountId] = { file, date: fileDate };
                    console.log(`✅ 更新账户 ${accountId} 的最新文件: ${file}`);
                }
            });

            // 处理每个账户的最新文件
            const latestFiles = Object.values(accountFiles).map(item => item.file);
            console.log(`📋 找到最新文件: ${latestFiles.join(', ')}`);

            if (latestFiles.length === 0) {
                console.log(`⚠️ 没有找到有效的最新文件`);
                inventoryResults.failTypes++;
                inventoryResults.errors.push(`库存类型 ${type} 没有找到有效的最新文件`);
                continue;
            }

            let mergedData = [];
            let typeSuccessRecords = 0;
            let typeFailRecords = 0;

            for (const file of latestFiles) {
                const filePath = path.join(configItem.path, file);
                console.log(`📄 处理文件: ${file}`);
                const data = await processExcelFile(filePath);
                if (data && data.length > 0) {
                    // 添加账户ID（如果有）
                    if (configItem.hasAccountId) {
                        const accountId = file.match(new RegExp(configItem.fileNamePattern))[1];
                        data.forEach(row => row['账户ID'] = accountId);
                        console.log(`🔢 添加账户ID: ${accountId}`);
                    }
                    mergedData = mergedData.concat(data);
                    typeSuccessRecords += data.length;
                    console.log(`✅ 文件 ${file} 处理完成，包含 ${data.length} 条记录`);
                } else {
                    console.log(`⚠️ 文件 ${file} 没有有效数据`);
                }
            }

            // 覆盖上传到数据库
            if (mergedData.length > 0) {
                console.log(`🔄 开始覆盖上传 ${mergedData.length} 条记录到表 ${configItem.tableName}`);

                // 创建表（如果不存在）
                const columns = Object.keys(mergedData[0]).filter(col =>
                    !['id', '_filepath'].includes(col.toLowerCase())
                );
                console.log(`📋 数据列: ${columns.join(', ')}`);

                await createTableIfNotExists(connection, configItem.tableName, columns);

                // 清空表
                await connection.query(`TRUNCATE TABLE \`${configItem.tableName}\``);
                console.log(`🗑️ 已清空表 ${configItem.tableName}`);

                const columnNames = columns.map(col => `\`${col}\``).join(', ');
                const values = mergedData.map(row =>
                    columns.map(col => row[col] || null)
                );

                await connection.query(
                    `INSERT INTO \`${configItem.tableName}\` (${columnNames}) VALUES ?`,
                    [values]
                );
                console.log(`✅ ${configItem.tableName} 表更新完成，插入了 ${mergedData.length} 条记录`);

                inventoryResults.successTypes++;
                inventoryResults.totalFiles += latestFiles.length;
                inventoryResults.totalRecords += mergedData.length;
                inventoryResults.successRecords += mergedData.length;

                inventoryResults.typeResults.push({
                    type: type,
                    tableName: configItem.tableName,
                    files: latestFiles,
                    records: mergedData.length,
                    success: true
                });
            } else {
                console.log(`⚠️ 没有有效数据需要上传到 ${configItem.tableName}`);
                inventoryResults.failTypes++;
                inventoryResults.errors.push(`库存类型 ${type} 没有有效数据需要上传`);
            }
        } catch (error) {
            console.error(`❌ 处理库存 ${type} 失败:`, error);
            inventoryResults.failTypes++;
            inventoryResults.errors.push(`库存类型 ${type} 处理失败: ${error.message}`);
        }
    }

    // 处理库存匹配表
    if (inventoryConfig.matchstore) {
        console.log('\n📊 处理库存匹配表...');
        const matchConfig = inventoryConfig.matchstore;
        console.log(`📁 匹配表文件路径: ${matchConfig.filePath}`);

        try {
            if (!fs.existsSync(matchConfig.filePath)) {
                console.log(`❌ 库存匹配表文件不存在: ${matchConfig.filePath}`);
                inventoryResults.errors.push(`库存匹配表文件不存在: ${matchConfig.filePath}`);
                return inventoryResults;
            }

            console.log(`✅ 库存匹配表文件存在`);
            const data = await processExcelFile(matchConfig.filePath);
            if (data && data.length > 0) {
                console.log(`🔄 开始覆盖上传 ${data.length} 条记录到表 ${matchConfig.tableName}`);

                // 创建表（如果不存在）
                const columns = Object.keys(data[0]).filter(col =>
                    !['id', '_filepath'].includes(col.toLowerCase())
                );
                console.log(`📋 匹配表数据列: ${columns.join(', ')}`);

                await createTableIfNotExists(connection, matchConfig.tableName, columns);

                // 清空表
                await connection.query(`TRUNCATE TABLE \`${matchConfig.tableName}\``);
                console.log(`🗑️ 已清空表 ${matchConfig.tableName}`);

                const columnNames = columns.map(col => `\`${col}\``).join(', ');
                const values = data.map(row =>
                    columns.map(col => row[col] || null)
                );

                await connection.query(
                    `INSERT INTO \`${matchConfig.tableName}\` (${columnNames}) VALUES ?`,
                    [values]
                );
                console.log(`✅ ${matchConfig.tableName} 表更新完成，插入了 ${data.length} 条记录`);

                inventoryResults.successTypes++;
                inventoryResults.totalFiles += 1;
                inventoryResults.totalRecords += data.length;
                inventoryResults.successRecords += data.length;

                inventoryResults.typeResults.push({
                    type: 'matchstore',
                    tableName: matchConfig.tableName,
                    files: [path.basename(matchConfig.filePath)],
                    records: data.length,
                    success: true
                });
            } else {
                console.log(`⚠️ 库存匹配表没有有效数据`);
                inventoryResults.errors.push(`库存匹配表没有有效数据`);
            }
        } catch (error) {
            console.error('❌ 处理库存匹配表失败:', error);
            inventoryResults.errors.push(`库存匹配表处理失败: ${error.message}`);
        }
    }

    return inventoryResults;
}

// 主函数
async function importExcelToDatabase() {
    console.log('🚀 开始执行批量数据库导入任务...');

    const startTime = Date.now();
    const uploadResults = {
        totalFolders: 0,
        totalFiles: 0,
        totalRecords: 0,
        successRecords: 0,
        failedRecords: 0,
        totalTime: 0,
        folderResults: [],
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

            // 检查是否有实际文件夹需要处理
            let hasRealFolders = false;
            const validFolders = [];

            for (const folder of config.folders) {
                if (fs.existsSync(folder.path)) {
                    hasRealFolders = true;
                    validFolders.push(folder);
                    console.log(`📁 找到文件夹: ${folder.path} -> 表: ${folder.tableName}`);
                }
            }

            if (!hasRealFolders) {
                console.log('🧪 没有找到实际文件夹，进入测试模式...');

                const testData = {
                    isTestMode: true,
                    totalFolders: 0,
                    totalFiles: 0,
                    totalRecords: 0,
                    successRecords: 0,
                    failedRecords: 0,
                    totalTime: Date.now() - startTime
                };

                console.log('📊 测试模式完成');

                const report = generateUploadReport(testData);
                console.log('\n' + report);
                await sendWecomMessage(report);

                return testData;
            } else {
                console.log(`📁 找到 ${validFolders.length} 个有效文件夹，开始批量处理...`);

                // 批量处理文件夹
                for (const folder of validFolders) {
                    try {
                        const result = await processFolderBatch(connection, folder.path, folder.tableName);

                        uploadResults.folderResults.push({
                            folderName: path.basename(folder.path),
                            tableName: folder.tableName,
                            successFiles: result.successFiles,
                            failFiles: result.failFiles,
                            totalRecords: result.totalRecords,
                            successRecords: result.successRecords,
                            failRecords: result.failRecords
                        });

                        uploadResults.totalFiles += result.successFiles + result.failFiles;
                        uploadResults.totalRecords += result.totalRecords;
                        uploadResults.successRecords += result.successRecords;
                        uploadResults.failedRecords += result.failRecords;

                    } catch (error) {
                        console.log(`❌ 处理文件夹失败: ${folder.path} - ${error.message}`);
                        uploadResults.errors.push(`文件夹 ${folder.path} 处理失败: ${error.message}`);
                    }
                }

                uploadResults.totalFolders = validFolders.length;
                uploadResults.totalTime = Date.now() - startTime;

                console.log('✅ 所有文件夹处理完成');

                // ========== 新增：处理库存数据 ==========
                console.log('\n📦 开始处理库存数据...');
                console.log('🔍 准备调用 processInventory 函数...');
                try {
                    console.log('🚀 正在调用 processInventory 函数...');
                    const inventoryResults = await processInventory(connection);
                    console.log('✅ 库存数据处理完成');

                    // 将库存处理结果添加到报告中
                    if (inventoryResults) {
                        uploadResults.inventoryResults = inventoryResults;
                    }
                } catch (error) {
                    console.error('❌ 库存数据处理失败:', error);
                    uploadResults.errors.push(`库存数据处理失败: ${error.message}`);
                }
                console.log('📦 库存数据处理流程结束');
                // ======================================

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
    console.log('🚀 优化版批量导入脚本启动中...');

    const startTime = Date.now();

    // 添加全局错误捕获
    process.on('uncaughtException', (error) => {
        console.error('💥 未捕获的异常:', error.message);
        console.error('📋 错误堆栈:', error.stack);

        const errorReport = `🚨 脚本执行异常
⏰ 时间: ${new Date().toLocaleString('zh-CN')}
❌ 错误类型: 未捕获异常
💥 错误信息: ${error.message}`;

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

        sendWecomMessage(errorReport).catch(() => {
            console.log('⚠️ 发送错误报告失败');
        });

        process.exit(1);
    });

    importExcelToDatabase()
        .then((results) => {
            const endTime = Date.now();
            const totalTime = endTime - startTime;

            console.log('\n🎉 批量数据库上传任务完成!');
            console.log(`⏱️ 总耗时: ${totalTime}ms`);

            if (results) {
                console.log(`📁 处理文件夹: ${results.totalFolders} 个`);
                console.log(`📄 处理文件: ${results.totalFiles} 个`);
                console.log(`✅ 成功记录: ${results.successRecords} 条`);
                console.log(`❌ 失败记录: ${results.failedRecords} 条`);
            }

            console.log('📱 请检查企业微信是否收到推送消息');

            setTimeout(() => {
                process.exit(0);
            }, 3000);
        })
        .catch((error) => {
            console.error('💥 数据库上传任务失败:', error.message);
            console.error('📋 错误详情:', error);

            setTimeout(() => {
                process.exit(1);
            }, 3000);
        });
}

module.exports = { importExcelToDatabase, sendWecomMessage }; 