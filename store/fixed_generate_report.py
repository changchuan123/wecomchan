    def generate_new_format_report(self, df: pd.DataFrame) -> str:
        """生成新格式的报告"""
        try:
            if df.empty:
                return "暂无库存数据"
            
            # 确保所有必要列存在
            required_columns = ['标准化品类', '规格名称', '库存量', '品牌', '渠道类型']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"缺少必要列: {missing_columns}")
                return f"报告生成失败：缺少列 {missing_columns}"
            
            # 获取匹配失败的数据
            failed_df = df[df['标准化品类'] == '其他']
            failed_matches = failed_df['规格名称'].dropna().unique() if '规格名称' in failed_df.columns else []
            
            # 总体概况
            total_inventory = df['库存量'].sum()
            total_categories = df['标准化品类'].nunique()
            total_brands = df['品牌'].nunique()
            
            # 按品类汇总
            category_summary = df.groupby('标准化品类').agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False)
            
            # 按渠道汇总
            channel_summary = df.groupby('渠道类型').agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False)
            
            # TOP10型号（按库存量排序）
            top_models = df.groupby(['标准化品类', '规格名称']).agg({
                '库存量': 'sum'
            }).reset_index().sort_values('库存量', ascending=False).head(10)
            
            html_content = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>库存分析报告 - 新格式</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                h1, h2 {{ color: #333; text-align: center; }}
                .summary-card {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin: 20px 0; }}
                .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 15px; }}
                .summary-item {{ text-align: center; }}
                .summary-item h3 {{ margin: 0; font-size: 2em; }}
                .summary-item p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f2f2f2; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .number {{ text-align: right; font-family: monospace; }}
                .warning {{ background-color: #fff3cd; color: #856404; padding: 10px; border-radius: 4px; margin: 10px 0; }}
                .timestamp {{ text-align: center; color: #666; margin-top: 20px; font-style: italic; }}
                .category-section {{ margin: 20px 0; }}
                .channel-section {{ margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>📦 库存分析报告 - 新格式</h1>
                
                <!-- 总体概况 -->
                <div class="summary-card">
                    <h2>📊 总体概况</h2>
                    <div class="summary-grid">
                        <div class="summary-item">
                            <h3>{total_inventory:,}</h3>
                            <p>总库存量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_categories}</h3>
                            <p>品类数量</p>
                        </div>
                        <div class="summary-item">
                            <h3>{total_brands}</h3>
                            <p>品牌数量</p>
                        </div>
                    </div>
                </div>
                
                <!-- 品类分类 -->
                <div class="category-section">
                    <h2>🏆 品类分类汇总</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>品类</th>
                                <th>库存量</th>
                                <th>占比</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in category_summary.iterrows():
            category = row['标准化品类']
            inventory = row['库存量']
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            
            html_content += f"""
                        <tr>
                            <td>{category}</td>
                            <td class="number">{inventory:,}</td>
                            <td class="number">{percentage:.1f}%</td>
                        </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
                
                <!-- 渠道分析 -->
                <div class="channel-section">
                    <h2>📊 线上线下渠道分析</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>渠道类型</th>
                                <th>库存量</th>
                                <th>占比</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for _, row in channel_summary.iterrows():
            channel = row['渠道类型']
            inventory = row['库存量']
            percentage = (inventory / total_inventory * 100) if total_inventory > 0 else 0
            
            html_content += f"""
                        <tr>
                            <td>{channel}</td>
                            <td class="number">{inventory:,}</td>
                            <td class="number">{percentage:.1f}%</td>
                        </tr>
            """
        
        html_content += f"""
                        </tbody>
                    </table>
                </div>
                
                <!-- TOP型号 -->
                <div class="category-section">
                    <h2>💎 TOP10型号</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>品类</th>
                                <th>规格名称</th>
                                <th>库存量</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        for idx, (_, row) in enumerate(top_models.iterrows(), 1):
            category = row['标准化品类']
            model = row['规格名称']
            inventory = row['库存量']
            
            html_content += f"""
                        <tr>
                            <td>{category}</td>
                            <td>{model}</td>
                            <td class="number">{inventory:,}</td>
                        </tr>
            """
        
        # 匹配失败预警
        if len(failed_matches) > 0:
            html_content += f"""
                        </tbody>
                    </table>
                </div>
                
                <div class="warning">
                    <h3>⚠️ 匹配失败预警</h3>
                    <p>以下规格名称未能成功匹配到标准化品类：</p>
                    <ul>
            """
            
            for match in failed_matches[:10]:  # 显示前10个
                html_content += f"<li>{match}</li>"
            
            if len(failed_matches) > 10:
                html_content += f"<li>... 共{len(failed_matches)}个未匹配项</li>"
            
            html_content += """
                    </ul>
                </div>
            """
        
        html_content += f"""
                <div class="timestamp">
                    📅 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
        except Exception as e:
            logger.error(f"生成HTML报告失败: {e}")
            return f"<html><body><h1>报告生成失败</h1><p>错误: {str(e)}</p></body></html>"