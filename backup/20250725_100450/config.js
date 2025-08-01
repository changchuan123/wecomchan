module.exports = {
    // 数据库配置
    database: {
        host: 'localhost',
        user: 'root',
        password: 'your_password',
        database: 'your_database',
        port: 3306,
        // 连接超时设置
        connectTimeout: 60000,        // 连接超时时间（毫秒）
        acquireTimeout: 60000,        // 获取连接超时时间
        timeout: 60000,               // 查询超时时间
        reconnect: true,              // 启用自动重连
        // 连接池设置
        connectionLimit: 10,          // 连接池大小
        queueLimit: 0,                // 队列限制
        // 重连设置
        maxReconnectAttempts: 3,      // 最大重连次数
        reconnectDelay: 2000          // 重连延迟时间
    },

    // 文件夹映射配置
    folders: [
        {
            path: './data/orders',
            tableName: 'BS_jddingdan'
        },
        {
            path: './data/products',
            tableName: 'BS_jdshangpin'
        },
        {
            path: './data/promotion',
            tableName: 'BS_jdkuaiche'
        }
    ],

    // 性能优化配置
    performance: {
        // 批量插入大小（建议：100-1000）
        batchSize: 500,
        // 是否启用性能监控
        enablePerformanceMonitoring: true,
        // 是否启用详细日志
        enableDetailedLogging: true,
        // 并行处理文件数量（0表示不并行）
        parallelFileProcessing: 0
    },

    // 校验配置
    validation: {
        // 是否启用随机抽样校验
        enableSamplingCheck: true,
        // 默认抽样数量
        defaultSampleSize: 10,
        // 抽样比例（1%）
        samplePercentage: 0.01,
        // 最小数据量才进行抽样校验
        minDataSizeForSampling: 5,
        // 关键字段列表（用于校验）
        keyFields: [
            '订单号', '订单编号', '商品ID', '商品编号',
            '交易时间', '下单时间', '日期', '店铺', '店铺名称'
        ]
    },

    // 企业微信配置
    wecom: {
        // 是否启用企业微信通知
        enable_notification: true,
        // 企业微信机器人webhook地址
        webhook_url: 'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=02d1441f-aa5b-44cb-aeab-b934fe78f8cb',
        // 消息发送超时时间（毫秒）
        timeout: 10000
    },

    // 重试配置
    retry: {
        // 最大重试次数
        maxRetries: 3,
        // 重试间隔时间（毫秒）
        retryDelay: 2000,
        // 是否启用重试功能
        enableRetry: true,
        // 重试时是否增加延迟时间
        exponentialBackoff: true
    },

    // 日志配置
    logging: {
        // 是否记录详细日志
        enableDetailedLogging: true,
        // 错误日志文件
        errorLogFile: 'import_error.log',
        // 是否记录校验结果
        logValidationResults: true
    }
}; 