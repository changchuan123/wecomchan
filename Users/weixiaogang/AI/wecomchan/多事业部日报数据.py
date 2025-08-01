// ... existing code ...
261: def is_online_shop(shop_name):
262:     if not isinstance(shop_name, str):
263:         return False
264:     online_keywords = ['京东','天猫','拼多多','抖音','卡萨帝','小红书','淘宝','苏宁','国美','快手','唯品会','网易严选','得物','蘑菇街','当当']
265:     offline_keywords = ['分销','空气场景','万慧','线下','体验店','专卖店']
266:     shop_name_upper = shop_name.upper()
267:     has_online = any(kw.upper() in shop_name_upper for kw in online_keywords)
268:     has_offline = any(kw.upper() in shop_name_upper for kw in offline_keywords)
269:     return has_online and not has_offline
370: # 只保留五大渠道相关店铺
371: # 新增：线上店铺过滤
372: df = df[df['店铺名称'].apply(is_online_shop)]
373: before_rows_channel = len(df)
374: df['渠道'] = df['店铺名称'].apply(classify_channel)
375: df = df[df['渠道'] != '其他']
376: after_rows_channel = len(df)
377: print(f"五大渠道店铺筛选：{before_rows_channel} -> {after_rows_channel}")
// ... existing code ...