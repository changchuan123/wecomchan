require('dotenv').config();

module.exports = {
    // 数据库配置
    database: {
        host: '212.64.57.87',
        user: 'root',
        password: 'c973ee9b500cc638',
        database: 'Date',
        port: 3306,
        // 只保留mysql2支持的配置选项
        connectionLimit: 10,
        queueLimit: 0,
        waitForConnections: true
    },

    // 文件夹配置 - 每个对象表示一个需要处理的文件夹
    folders: [
        {
            path: 'E:\\电商数据\\佰穗\\订单明细',
            tableName: 'BS_jddingdan',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\商品明细',
            tableName: 'BS_jdshangpin',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\推广数据\\快车',
            tableName: 'BS_jdkuaiche',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\推广数据\\全站',
            tableName: 'BS_jdquanzhan',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\推广数据\\智能投放',
            tableName: 'BS_jdzhineng',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\拼多多推广数据',
            tableName: 'BS_pddtuiguang',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\佰穗\\拼多多销售数据',
            tableName: 'BS_pddxiaoshou',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\订单明细',
            tableName: 'HT_jddingdan',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\商品明细',
            tableName: 'HT_jdshangpin',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\推广数据\\快车',
            tableName: 'HT_jdkuaiche',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\推广数据\\全站',
            tableName: 'HT_jdquanzhan',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\推广数据\\智能投放',
            tableName: 'HT_jdzhineng',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\拼多多推广数据',
            tableName: 'HT_pddtuiguang',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\拼多多销售数据',
            tableName: 'HT_pddxiaoshou',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\天猫推广数据',
            tableName: 'HT_tmtuiguang',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\天猫销售数据',
            tableName: 'HT_tmxiaoshou',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\抖音销售数据',
            tableName: 'HT_dyxiaoshou',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\抖音推广数据',
            tableName: 'HT_dytuiguang',
            pattern: '*.xlsx'
        },
        {
            path: 'E:\\电商数据\\虹图\\供销平台',
            tableName: 'HT_fenxiao',
            pattern: '*.xlsx',
            // 分销表特殊配置
            enableStrictDeduplication: true,
            deduplicationFields: ['分销商店铺名称', '产品名称', '采购单支付时间', '采购数量']
        },
        {
            path: 'E:\\电商数据\\佰穗\\供销平台',
            tableName: 'BS_fenxiao',
            pattern: '*.xlsx',
            // 分销表特殊配置
            enableStrictDeduplication: true,
            deduplicationFields: ['分销商店铺名称', '产品名称', '采购单支付时间', '采购数量']
        },
        {
            path: 'E:\\电商数据\\虹图\\ERP订单明细',
            tableName: 'Daysales',
            pattern: '*.xlsx'
        }
    ],

    // 库存数据配置 - 新增
    inventory: {
        // 京东库存
        jdstore: {
            path: 'E:\\电商数据\\虹图\\库存\\京东库存JDstore',
            tableName: 'jdstore',
            pattern: '*.xlsx',
            // 京东库存文件名格式：京仓库存YYYY-MM-DD.xlsx
            fileNamePattern: '京仓库存(\\d{4}-\\d{2}-\\d{2})\\.xlsx',
            hasAccountId: false
        },
        // 云仓库存
        rrsstore: {
            path: 'E:\\电商数据\\虹图\\库存\\云仓库存',
            tableName: 'rrsstore',
            pattern: '*.xlsx',
            // 云仓库存文件名格式：云仓库存{账户ID}{YYYY-MM-DD}.xlsx
            fileNamePattern: '云仓库存(\\d+)(\\d{4}-\\d{2}-\\d{2})\\.xlsx',
            hasAccountId: true
        },
        // 统仓库存
        tongstore: {
            path: 'E:\\电商数据\\虹图\\库存\\统仓库存',
            tableName: 'tongstore',
            pattern: '*.xlsx',
            // 统仓库存文件名格式：统仓库存{账户ID}{YYYY-MM-DD}.xlsx
            fileNamePattern: '统仓库存(\\d+)(\\d{4}-\\d{2}-\\d{2})\\.xlsx',
            hasAccountId: true
        },
        // 金融仓库存
        jinrongstore: {
            path: 'E:\\电商数据\\虹图\\库存\\金融仓库存',
            tableName: 'jinrongstore',
            pattern: '*.xlsx',
            // 金融仓库存文件名格式：金融仓库存{账户ID}{YYYY-MM-DD}.xlsx
            fileNamePattern: '金融仓库存(\\d+)(\\d{4}-\\d{2}-\\d{2})\\.xlsx',
            hasAccountId: true
        },
        // 库存匹配表
        matchstore: {
            filePath: 'E:\\电商数据\\虹图\\库存\\库存匹配.xlsx',
            tableName: 'matchstore',
            overwriteMode: true,
            clearTableBeforeImport: true
        }
    },

    // 单文件配置 - 用于处理单个Excel文件
    singleFiles: [
        {
            filePath: 'E:\\电商数据\\虹图\\分销产品匹配.xlsx',
            tableName: 'fenxiaochanpin',
            overwriteMode: true,  // 启用覆盖模式
            clearTableBeforeImport: true  // 导入前清空表
        }
    ],

    // 性能优化配置
    performance: {
        // 批量插入大小（降低以避免调用栈溢出）
        batchSize: 100,
        // 最大并发批次数（降低并发）
        maxConcurrentBatches: 2,
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
        timeout: 15000,
        // 重试次数
        retries: 3,
        // 重试间隔（毫秒）
        retryDelay: 2000,
        // 是否启用详细调试日志
        enableDebugLog: true
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
    },

    // 分销表特殊配置
    fenxiao: {
        // 是否启用严格去重
        enableStrictDeduplication: true,
        // 去重字段
        deduplicationFields: ['分销商店铺名称', '产品名称', '采购单支付时间', '采购数量'],
        // 是否跳过空值记录
        skipEmptyRecords: true,
        // 是否启用重复数据检查
        enableDuplicateCheck: true
    }
};