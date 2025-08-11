const { importExcelToDatabase } = require('./manual_import_优化版.js');

console.log('🧪 开始测试库存表5秒超时强制删除重建机制...');
console.log('📋 测试内容：');
console.log('1. 测试 jdstore 表的5秒超时机制');
console.log('2. 测试 rrsstore 表的5秒超时机制');
console.log('3. 测试 tongstore 表的5秒超时机制');
console.log('4. 测试 jinrongstore 表的5秒超时机制');
console.log('5. 测试 matchstore 表的5秒超时机制');
console.log('');

// 设置测试超时时间
const TEST_TIMEOUT = 300000; // 5分钟

// 创建超时控制
const timeoutPromise = new Promise((resolve, reject) => {
    setTimeout(() => {
        reject(new Error('测试超时，超过5分钟'));
    }, TEST_TIMEOUT);
});

// 执行测试
Promise.race([
    importExcelToDatabase(),
    timeoutPromise
])
    .then((results) => {
        console.log('\n🎉 测试完成！');
        console.log('📊 测试结果：');

        if (results.inventoryResults) {
            const inventory = results.inventoryResults;
            console.log(`📦 库存类型总数: ${inventory.totalTypes}`);
            console.log(`✅ 成功类型: ${inventory.successTypes}`);
            console.log(`❌ 失败类型: ${inventory.failTypes}`);

            if (inventory.typeResults) {
                console.log('\n📋 详细结果：');
                inventory.typeResults.forEach(result => {
                    let status = result.success ? '✅' : '❌';
                    let rebuildInfo = result.forceRebuild ? ' 💥[强制重建]' : '';
                    console.log(`${status} ${result.type} (${result.tableName}): ${result.records} 条记录${rebuildInfo}`);
                });
            }

            if (inventory.errors && inventory.errors.length > 0) {
                console.log('\n❌ 错误信息：');
                inventory.errors.forEach((error, index) => {
                    console.log(`${index + 1}. ${error}`);
                });
            }
        }

        console.log('\n✅ 5秒超时强制删除重建机制测试完成！');
    })
    .catch((error) => {
        console.error('\n💥 测试失败：', error.message);
        console.error('📋 错误详情：', error);
        process.exit(1);
    }); 