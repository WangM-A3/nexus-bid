# -*- coding: utf-8 -*-
"""
规则引擎模块 —— 招标文件合规检测
包含：排斥性条款关键词库、保证金/工期等数值检测规则、错敏词检测库
"""

import re

# ============================================================
# 一、排斥限制竞争 —— 关键词模式库
# ============================================================

# 排斥性条款的正则模式列表，每项格式: (模式, 问题描述, 法规依据, 修改建议, 风险等级)
EXCLUSION_PATTERNS = [
    # —— 地域歧视 ——
    (
        r'(?:投标人|供应商|中标人).{0,10}(?:须|应|必须|要求).{0,5}(?:本地|本省|本市|本市注册|本地注册|本地企业)',
        '存在地域歧视条款，要求投标人为本地企业',
        '《招标投标法实施条例》第三十二条第六项：以特定行政区域或者特定行业的业绩、奖项作为加分条件或者中标条件',
        '删除地域限制要求，不得以地域作为资格条件或加分条件',
        '高'
    ),
    (
        r'(?:仅限|优先考虑|优先选择).{0,5}(?:本地|本省|本市|本区).{0,5}(?:企业|供应商|公司|单位)',
        '存在地域歧视条款，优先选择本地企业',
        '《招标投标法》第五条：招标投标活动应当遵循公开、公平、公正和诚实信用的原则',
        '删除地域优先条款，对所有投标人一视同仁',
        '高'
    ),
    # —— 规模歧视 ——
    (
        r'(?:注册资本|注册资金).{0,5}(?:不低于|不少于|≥|大于|超过).{0,5}(\d+(?:\.\d+)?)\s*(?:万|亿元)',
        '设置注册资本门槛，涉嫌规模歧视',
        '《政府采购法实施条例》第十七条：采购人、采购代理机构不得将注册资本、资产总额、营业收入、从业人员、利润、纳税额等规模条件作为资格要求或者评审因素',
        '删除注册资本要求，不得将企业规模作为资格条件',
        '高'
    ),
    (
        r'(?:营业收入|年营业额|年销售额|营业收入).{0,5}(?:不低于|不少于|≥|大于|超过).{0,5}(\d+(?:\.\d+)?)\s*(?:万|亿元)',
        '设置营业收入门槛，涉嫌规模歧视',
        '《政府采购法实施条例》第十七条',
        '删除营业收入要求，不得将经营规模作为资格条件',
        '高'
    ),
    # —— 品牌指定 ——
    (
        r'(?:须|应|必须|要求).{0,10}(?:采用|使用|选用|配备).{0,5}(?:指定品牌|特定品牌|某某品牌|指定厂家)',
        '存在指定品牌条款，限制竞争',
        '《招标投标法实施条例》第三十二条第三项：指定特定的专利、商标、品牌、原产地或者供应商',
        '修改为"同等或优于XX品牌"的开放式技术要求，不得指定具体品牌',
        '高'
    ),
    (
        r'(?:仅接受|仅限|必须是|必须为)\s*[A-Za-z\u4e00-\u9fa5]+\s*(?:品牌|牌|型号)',
        '直接指定品牌或型号，限制竞争',
        '《招标投标法实施条例》第三十二条第三项',
        '删除品牌/型号指定，改为技术参数要求',
        '高'
    ),
    # —— 业绩歧视 ——
    (
        r'(?:业绩|经验|合同).{0,5}(?:要求|不低于|不少于|≥).{0,5}(\d+)\s*(?:个|项|份|年以上)',
        '设置过高业绩门槛，涉嫌排斥潜在投标人',
        '《招标投标法实施条例》第三十二条第四项：以特定行业的业绩、奖项作为加分条件或者中标条件',
        '合理设置业绩要求，不得设置与项目无关或过高的业绩门槛',
        '中'
    ),
    # —— 资质歧视 ——
    (
        r'(?:须|应|必须).{0,5}(?:同时具备|兼具|具有).{0,5}(?:两项|两个|多个|多项).{0,5}(?:资质|资格|证书)',
        '设置多重资质要求，可能过度限制竞争',
        '《招标投标法实施条例》第三十二条：以不合理的条件限制或者排斥潜在投标人',
        '根据项目实际需要合理设置资质要求，不得要求与项目无关的资质',
        '中'
    ),
    # —— 不合理条件 ——
    (
        r'(?:投标人|供应商).{0,10}(?:须|应|必须).{0,5}(?:在当地|在本地|在本市|在本省).{0,5}(?:设立|成立|注册|登记).{0,5}(?:分支机构|分公司|办事处)',
        '要求投标人在本地设立分支机构，涉嫌排斥外地企业',
        '《招标投标法实施条例》第三十二条第五项：以要求设立分支机构为条件限制或者排斥潜在投标人',
        '删除设立分支机构的要求',
        '高'
    ),
    (
        r'(?:投标保证金|履约保证金|保证金).{0,5}(?:必须|须|应).{0,5}(?:现金|银行转账|电汇).{0,10}(?:形式|方式|缴纳)',
        '限定保证金缴纳方式，排斥其他担保方式',
        '《招标投标法实施条例》第二十六条：招标人在招标文件中要求投标人提交投标保证金的，投标保证金不得超过招标项目估算价的2%',
        '接受银行保函、保险保函等多种担保形式',
        '中'
    ),
]

# ============================================================
# 二、违法违规条款 —— 关键词模式库
# ============================================================

ILLEGAL_PATTERNS = [
    # —— 规避招标 ——
    (
        r'(?:肢解|拆分|化整为零).{0,5}(?:项目|工程|采购|招标)',
        '存在肢解项目规避招标的表述',
        '《招标投标法》第四条：任何单位和个人不得将依照本法规定必须进行招标的项目化整为零或者以其他任何方式规避招标',
        '不得将必须招标的项目肢解以规避招标',
        '高'
    ),
    # —— 串通招标 ——
    (
        r'(?:围标|串标|陪标|串通投标|事先约定)',
        '存在串通投标相关表述',
        '《招标投标法》第三十二条：投标人不得相互串通投标报价，不得排挤其他投标人的公平竞争',
        '删除任何涉及串通投标的条款或表述',
        '高'
    ),
    # —— 评标歧视 ——
    (
        r'(?:评标|评审|打分).{0,10}(?:倾向|偏向|照顾|优先).{0,5}(?:特定|某|部分).{0,5}(?:投标人|供应商|企业)',
        '评标条款存在倾向性表述',
        '《招标投标法实施条例》第四十九条：评标委员会成员应当客观、公正地履行职务',
        '评标标准应客观、公正，不得有倾向性条款',
        '高'
    ),
    # —— 违规分包 ——
    (
        r'(?:允许|可以|可).{0,5}(?:整体|全部).{0,5}(?:分包|转包|转包)',
        '允许整体分包/转包，违反法律规定',
        '《招标投标法》第四十八条：中标人不得向他人转让中标项目，也不得将中标项目肢解后分别向他人转让',
        '禁止整体转包，分包需符合法定条件',
        '高'
    ),
    # —— 不合理收费 ——
    (
        r'(?:收取|缴纳|支付).{0,5}(?:报名费|投标报名费|资料费|标书费).{0,5}(\d+(?:\.\d+)?)\s*(?:元|万元)',
        '收取投标报名费/标书费可能不合规',
        '《政府采购法实施条例》第十七条第五款：不得收取没有法律法规依据的保证金和费用',
        '核实收费依据，无法律法规依据的不得收费',
        '中'
    ),
]

# ============================================================
# 三、错敏词检测库
# ============================================================

# 政治敏感词/不规范表述 (错误表述 -> 正确表述)
SENSITIVE_WORDS = {
    '国家主席': '应使用"国家主席"的完整称谓',
    '总书记': '应使用"习近平总书记"等完整称谓',
    '两会代表': '应为"全国人大代表"或"全国政协委员"',
    '人大代表': '应注明"全国人大代表"或"地方各级人大代表"',
    '人民政府': '应使用完整称谓，如"XX省人民政府"',
    '法院': '应为"人民法院"',
    '检察院': '应为"人民检察院"',
    '公安': '应为"公安机关"',
    '一带一路战略': '应为"一带一路倡议"',
    '战略': '注意上下文，涉及国家层面应使用"倡议"而非"战略"',
    '中华民族伟大复兴的中国梦': '应完整表述',
}

# 常见错别字 (错别字 -> 正确字)
COMMON_TYPOS = {
    '招投标': None,  # 正确，跳过
    '投标': None,    # 正确，跳过
    '评标': None,    # 正确，跳过
    '按装': '安装',
    '帐户': '账户',
    '帐号': '账号',
    '帐目': '账目',
    '帐面': '账面',
    '登陆': '登录',
    '复议': '复核',
    '签定': '签订',
    '签暑': '签署',
    '做为': '作为',
    '按排': '安排',
    '布暑': '部署',
    '部暑': '部署',
    '既使': '即使',
    '截止到': '截至',
    '制定': None,  # 视上下文，"制定"和"制订"均可
    '唯ㄧ': '唯一',
    '叁考': '参考',
    '按照': None,
    '其它': '其他',
    '帐': '账',
    '泊位': None,  # 港口术语，正确
    '泊': None,
    '象': '像',  # "好象"应为"好像"
    '候': None,  # 视上下文
    '以经': '已经',
    '在次': '再次',
    '必需': None,  # 视上下文，"必需"和"必须"含义不同
    '重未': '从未',
    '截止至今': '截至目前',
    '通过后': None,
    '合同仹': '合同价',
    '提交': None,
    '申清': '申请',
    '申清书': '申请书',
}

# ============================================================
# 四、数值检测规则
# ============================================================

def check_deposit_ratio(text):
    """
    检测保证金比例是否超标
    投标保证金不得超过招标项目估算价的2%
    履约保证金不得超过中标合同金额的10%
    返回检测结果列表
    """
    results = []
    
    # 投标保证金比例检测（使用非贪婪匹配避免截断数字）
    deposit_patterns = [
        r'(?:投标保证金|投标担保).{0,20}?(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in deposit_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                ratio = float(match.group(1))
                # 提取原文上下文
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                if ratio > 2:
                    results.append({
                        'level': '高',
                        'category': '其他风险',
                        'description': f'投标保证金比例为{ratio}%，超过法定上限2%',
                        'original_text': original_text,
                        'legal_basis': '《招标投标法实施条例》第二十六条：投标保证金不得超过招标项目估算价的2%',
                        'suggestion': f'将投标保证金比例降至2%以内（当前为{ratio}%）'
                    })
                elif ratio == 2:
                    results.append({
                        'level': '低',
                        'category': '其他风险',
                        'description': f'投标保证金比例为{ratio}%，已达法定上限',
                        'original_text': original_text,
                        'legal_basis': '《招标投标法实施条例》第二十六条',
                        'suggestion': '建议适当降低保证金比例，减轻投标人负担'
                    })
            except (ValueError, IndexError):
                continue
    
    # 履约保证金比例检测
    performance_deposit_patterns = [
        r'(?:履约保证金|履约担保).{0,20}?(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in performance_deposit_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                ratio = float(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                if ratio > 10:
                    results.append({
                        'level': '高',
                        'category': '其他风险',
                        'description': f'履约保证金比例为{ratio}%，超过法定上限10%',
                        'original_text': original_text,
                        'legal_basis': '《招标投标法实施条例》第五十八条：履约保证金不得超过中标合同金额的10%',
                        'suggestion': f'将履约保证金比例降至10%以内（当前为{ratio}%）'
                    })
            except (ValueError, IndexError):
                continue
    
    return results


def check_construction_period(text):
    """
    检测工期要求是否合理
    主要检测是否设置了不合理的短工期
    返回检测结果列表
    """
    results = []
    
    # 工期模式匹配（使用非贪婪匹配避免截断数字）
    period_patterns = [
        r'(?:工期|施工工期|建设工期|交付周期|交货期).{0,10}?(\d+)\s*(?:个)?(?:天|日|日历天|工作日)',
    ]
    
    for pattern in period_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                days = int(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                # 工期过短提示（一般工程不少于30天）
                if days < 15:
                    results.append({
                        'level': '中',
                        'category': '其他风险',
                        'description': f'工期要求为{days}天，工期过短可能不合理',
                        'original_text': original_text,
                        'legal_basis': '《建设工程质量管理条例》相关工期要求，工期应保证合理施工需要',
                        'suggestion': f'建议根据工程规模和实际需要合理确定工期，当前{days}天可能不足以完成施工'
                    })
            except (ValueError, IndexError):
                continue
    
    return results


def check_payment_terms(text):
    """
    检测付款条件是否苛刻
    主要检测预付款比例过低、质保金比例过高、付款周期过长等
    返回检测结果列表
    """
    results = []
    
    # 质保金比例检测（不得超过3%）
    warranty_patterns = [
        r'(?:质量保证金|质保金|保留金).{0,20}?(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in warranty_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                ratio = float(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                if ratio > 3:
                    results.append({
                        'level': '中',
                        'category': '其他风险',
                        'description': f'质量保证金比例为{ratio}%，超过法定上限3%',
                        'original_text': original_text,
                        'legal_basis': '《建设工程质量保证金管理办法》第七条：保证金总预留比例不得高于工程价款结算总额的3%',
                        'suggestion': f'将质量保证金比例降至3%以内（当前为{ratio}%）'
                    })
            except (ValueError, IndexError):
                continue
    
    # 预付款比例检测（建议不低于10%）
    prepayment_patterns = [
        r'(?:预付款|预付金).{0,20}?(\d+(?:\.\d+)?)\s*%',
    ]
    
    for pattern in prepayment_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                ratio = float(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                if ratio < 10:
                    results.append({
                        'level': '低',
                        'category': '其他风险',
                        'description': f'预付款比例为{ratio}%，比例较低',
                        'original_text': original_text,
                        'legal_basis': '《建设工程价款结算暂行办法》第十二条：包工包料工程的预付款按合同约定拨付，原则上预付比例不低于合同金额的10%',
                        'suggestion': f'建议提高预付款比例至10%以上（当前为{ratio}%），减轻承包人资金压力'
                    })
            except (ValueError, IndexError):
                continue
    
    return results


def check_evaluation_method(text):
    """
    检测评标办法合规性
    主要检测评分标准是否合理、分值设置是否合规
    返回检测结果列表
    """
    results = []
    
    # 检测价格分占比（综合评估法中价格分一般不低于30%）
    price_score_patterns = [
        r'(?:价格分|报价分|商务报价分|投标报价分).{0,20}?(\d+(?:\.\d+)?)\s*(?:分|%)',
    ]
    
    for pattern in price_score_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = float(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                # 如果是百分制且价格分低于30
                if value < 30 and value > 0:
                    results.append({
                        'level': '中',
                        'category': '评标办法合规性',
                        'description': f'价格分占比为{value}分，低于建议下限30分',
                        'original_text': original_text,
                        'legal_basis': '《评标委员会和评标方法暂行规定》第二十九条：综合评估法中，投标报价所占权重不宜过小',
                        'suggestion': f'建议提高价格分权重至30分以上（当前为{value}分），确保价格竞争性'
                    })
            except (ValueError, IndexError):
                continue
    
    # 检测主观分占比是否过高
    subjective_patterns = [
        r'(?:技术方案|施工组织设计|技术标|方案分).{0,20}?(\d+(?:\.\d+)?)\s*(?:分|%)',
    ]
    
    for pattern in subjective_patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            try:
                value = float(match.group(1))
                start = max(0, match.start() - 20)
                end = min(len(text), match.end() + 20)
                original_text = text[start:end].strip()
                
                if value > 70:
                    results.append({
                        'level': '低',
                        'category': '评标办法合规性',
                        'description': f'主观评分项占比为{value}分，占比偏高可能影响评标公正性',
                        'original_text': original_text,
                        'legal_basis': '《评标委员会和评标方法暂行规定》相关条款',
                        'suggestion': '建议适当降低主观评分项权重，增加客观评分项，提高评标公正性'
                    })
            except (ValueError, IndexError):
                continue
    
    return results


# ============================================================
# 五、错敏词检测
# ============================================================

def check_sensitive_words(text):
    """
    检测政治敏感词和错别字
    返回检测结果列表
    """
    results = []
    
    # 政治敏感词检测
    for word, suggestion in SENSITIVE_WORDS.items():
        if word in text:
            # 提取上下文
            idx = text.find(word)
            start = max(0, idx - 20)
            end = min(len(text), idx + len(word) + 20)
            original_text = text[start:end].strip()
            
            results.append({
                'level': '中',
                'category': '错敏词检测',
                'description': f'检测到不规范政治表述："{word}"',
                'original_text': original_text,
                'legal_basis': '《党政机关公文处理工作条例》及国家通用语言文字相关规范',
                'suggestion': suggestion
            })
    
    # 错别字检测
    for wrong, correct in COMMON_TYPOS.items():
        if correct is None:
            continue
        if wrong in text:
            idx = text.find(wrong)
            start = max(0, idx - 20)
            end = min(len(text), idx + len(wrong) + 20)
            original_text = text[start:end].strip()
            
            results.append({
                'level': '低',
                'category': '错敏词检测',
                'description': f'疑似错别字："{wrong}" → 应为"{correct}"',
                'original_text': original_text,
                'legal_basis': '《通用规范汉字表》',
                'suggestion': f'将"{wrong}"修改为"{correct}"'
            })
    
    return results


# ============================================================
# 六、规则引擎主入口
# ============================================================

def run_rule_check(text):
    """
    规则引擎主入口：运行所有规则检测
    参数: text - 招标文件全文
    返回: 检测结果列表
    """
    all_results = []
    
    # 1. 排斥限制竞争检测
    for pattern, desc, legal, suggestion, level in EXCLUSION_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            original_text = text[start:end].strip()
            all_results.append({
                'level': level,
                'category': '排斥限制竞争',
                'description': desc,
                'original_text': original_text,
                'legal_basis': legal,
                'suggestion': suggestion
            })
    
    # 2. 违法违规条款检测
    for pattern, desc, legal, suggestion, level in ILLEGAL_PATTERNS:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            start = max(0, match.start() - 30)
            end = min(len(text), match.end() + 30)
            original_text = text[start:end].strip()
            all_results.append({
                'level': level,
                'category': '违法违规条款',
                'description': desc,
                'original_text': original_text,
                'legal_basis': legal,
                'suggestion': suggestion
            })
    
    # 3. 错敏词检测
    all_results.extend(check_sensitive_words(text))
    
    # 4. 评标办法合规性检测
    all_results.extend(check_evaluation_method(text))
    
    # 5. 数值检测（保证金、工期、付款条件）
    all_results.extend(check_deposit_ratio(text))
    all_results.extend(check_construction_period(text))
    all_results.extend(check_payment_terms(text))
    
    # 去重：相同描述+相同原文的只保留一条
    seen = set()
    unique_results = []
    for item in all_results:
        # 以描述+原文前30字符作为去重键
        dedup_key = (item['description'], item.get('original_text', '')[:30])
        if dedup_key not in seen:
            seen.add(dedup_key)
            unique_results.append(item)
    
    return unique_results


# ============================================================
# 七、LLM检测Prompt构建
# ============================================================

def build_llm_prompt(text):
    """
    构建LLM深度合规分析的Prompt
    参数: text - 招标文件全文（截取前8000字以控制Token消耗）
    返回: 系统提示+用户消息
    """
    system_prompt = """你是一名资深的招标文件合规审查专家，精通《中华人民共和国招标投标法》《招标投标法实施条例》《政府采购法》及其实施条例等相关法律法规。

你的任务是对招标文件进行深度合规性审查，识别以下五类问题：
1. 排斥限制竞争：不合理资格条件、地域歧视、规模歧视、品牌指定、过高业绩门槛等
2. 违法违规条款：违反招投标法及实施条例的条款，如规避招标、串通投标、违规分包等
3. 错敏词：政治敏感词、错别字、不规范表述
4. 评标办法合规性：评分标准是否合理、分值设置是否合规、主观分占比是否过高
5. 其他风险：工期不合理、保证金比例超标、付款条件苛刻、质保金过高等

请严格按照以下JSON格式输出检测结果，不要输出任何其他内容：
```json
{
  "items": [
    {
      "level": "高/中/低",
      "category": "排斥限制竞争/违法违规条款/错敏词检测/评标办法合规性/其他风险",
      "description": "问题描述（简明扼要）",
      "original_text": "原文引用（引用招标文件中的相关段落）",
      "legal_basis": "法规依据（具体到条款）",
      "suggestion": "修改建议（具体可操作）"
    }
  ]
}
```

注意：
- 风险等级判断标准：高=明显违法违规，可能导致招标无效或被处罚；中=存在合规风险，建议修改；低=存在不规范或优化空间
- 法规依据必须具体到法律名称和条款编号
- 修改建议必须具体、可操作
- 如果没有发现问题，返回空items列表
- 只返回JSON，不要有任何其他文字"""

    # 截取前8000字，控制Token消耗
    truncated_text = text[:8000] if len(text) > 8000 else text
    
    user_prompt = f"""请对以下招标文件内容进行合规性审查：

{truncated_text}

请严格按照要求的JSON格式输出检测结果。"""
    
    return system_prompt, user_prompt
