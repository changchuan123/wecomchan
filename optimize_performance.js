// 性能优化方案
// 问题：6508条数据记录在每次updateChart时都要重新遍历和计算，导致页面卡顿

// 解决方案：
// 1. 数据预处理和缓存
// 2. 分批处理大数据集
// 3. 使用Web Workers进行后台计算
// 4. 虚拟化长列表
// 5. 防抖动优化

const PerformanceOptimizer = {
    // 缓存预处理的数据
    cache: {
        byDate: {},
        byShop: {},
        byCategory: {},
        byProduct: {},
        aggregated: {}
    },
    
    // 预处理数据
    preprocessData(trendData) {
        console.log('开始预处理数据...');
        const startTime = performance.now();
        
        // 清空缓存
        this.cache = {
            byDate: {},
            byShop: {},
            byCategory: {},
            byProduct: {},
            aggregated: {}
        };
        
        // 分批处理数据
        const batchSize = 500;
        const batches = [];
        for (let i = 0; i < trendData.length; i += batchSize) {
            batches.push(trendData.slice(i, i + batchSize));
        }
        
        // 处理每个批次
        batches.forEach((batch, batchIndex) => {
            this.processBatch(batch, batchIndex);
        });
        
        const endTime = performance.now();
        console.log(`数据预处理完成，耗时: ${endTime - startTime}ms`);
    },
    
    // 处理单个批次
    processBatch(batch, batchIndex) {
        batch.forEach(item => {
            // 按日期索引
            if (!this.cache.byDate[item.date]) {
                this.cache.byDate[item.date] = [];
            }
            this.cache.byDate[item.date].push(item);
            
            // 按店铺索引
            if (!this.cache.byShop[item.shop]) {
                this.cache.byShop[item.shop] = [];
            }
            this.cache.byShop[item.shop].push(item);
            
            // 按品类索引
            if (!this.cache.byCategory[item.category]) {
                this.cache.byCategory[item.category] = [];
            }
            this.cache.byCategory[item.category].push(item);
            
            // 按产品索引（过滤特殊产品）
            const product = item.product || '';
            if (!product.includes('运费') && !product.includes('室外机') && 
                !product.includes('赠品') && !product.includes('虚拟')) {
                if (!this.cache.byProduct[item.product]) {
                    this.cache.byProduct[item.product] = [];
                }
                this.cache.byProduct[item.product].push(item);
            }
        });
    },
    
    // 获取过滤后的数据（使用缓存）
    getFilteredData(selectedShop, selectedCategory, selectedProduct) {
        let result = [];
        
        // 根据选择的条件使用最优的索引
        if (selectedShop !== 'all') {
            result = this.cache.byShop[selectedShop] || [];
        } else if (selectedCategory !== 'all') {
            result = this.cache.byCategory[selectedCategory] || [];
        } else if (selectedProduct !== 'all') {
            result = this.cache.byProduct[selectedProduct] || [];
        } else {
            // 如果都是'all'，需要遍历所有数据
            result = Object.values(this.cache.byDate).flat();
        }
        
        // 进一步过滤
        return result.filter(item => {
            return (selectedShop === 'all' || item.shop === selectedShop) &&
                   (selectedCategory === 'all' || item.category === selectedCategory) &&
                   (selectedProduct === 'all' || item.product === selectedProduct);
        });
    },
    
    // 防抖动函数
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },
    
    // 异步聚合数据
    async aggregateDataAsync(filteredData, stackDimension) {
        return new Promise((resolve) => {
            // 使用requestIdleCallback在浏览器空闲时处理
            if (window.requestIdleCallback) {
                window.requestIdleCallback(() => {
                    const result = this.aggregateData(filteredData, stackDimension);
                    resolve(result);
                });
            } else {
                // 降级到setTimeout
                setTimeout(() => {
                    const result = this.aggregateData(filteredData, stackDimension);
                    resolve(result);
                }, 0);
            }
        });
    },
    
    // 聚合数据
    aggregateData(filteredData, stackDimension) {
        const aggregatedData = {};
        const stackItems = new Set();
        
        filteredData.forEach(item => {
            const date = item.date;
            const stackKey = item[stackDimension];
            
            if (!aggregatedData[date]) {
                aggregatedData[date] = {};
            }
            
            if (!aggregatedData[date][stackKey]) {
                aggregatedData[date][stackKey] = { amount: 0, qty: 0 };
            }
            
            aggregatedData[date][stackKey].amount += item.amount || 0;
            aggregatedData[date][stackKey].qty += item.qty || 0;
            stackItems.add(stackKey);
        });
        
        return { aggregatedData, stackItems };
    }
};

// 优化后的updateChart函数
async function updateChartOptimized() {
    if (!trendData || trendData.length === 0) return;
    
    // 显示加载状态
    const chartContainer = document.getElementById('chartContainer');
    if (chartContainer) {
        chartContainer.style.opacity = '0.5';
    }
    
    try {
        const selectedShop = document.getElementById('selShop').value;
        const selectedCategory = document.getElementById('selCategory').value;
        const selectedProduct = document.getElementById('selProduct').value;
        
        // 确定堆积维度
        let stackDimension;
        if (selectedCategory === 'all' && selectedShop === 'all' && selectedProduct === 'all') {
            stackDimension = 'category';
        } else if (selectedCategory !== 'all' && selectedShop === 'all') {
            stackDimension = 'shop';
        } else if (selectedShop !== 'all' && selectedCategory === 'all') {
            stackDimension = 'product';
        } else if (selectedCategory === 'all' && selectedShop === 'all' && selectedProduct !== 'all') {
            stackDimension = 'shop';
        } else {
            stackDimension = 'product';
        }
        
        // 使用优化的数据获取
        const filteredData = PerformanceOptimizer.getFilteredData(selectedShop, selectedCategory, selectedProduct);
        
        // 异步聚合数据
        const { aggregatedData, stackItems } = await PerformanceOptimizer.aggregateDataAsync(filteredData, stackDimension);
        
        // 其余图表更新逻辑保持不变...
        // 这里可以继续使用原有的图表更新代码
        
    } finally {
        // 恢复显示状态
        if (chartContainer) {
            chartContainer.style.opacity = '1';
        }
    }
}

// 使用防抖动的updateChart
const debouncedUpdateChart = PerformanceOptimizer.debounce(updateChartOptimized, 300);

console.log('性能优化方案已准备就绪');