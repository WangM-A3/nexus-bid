# -*- coding: utf-8 -*-
"""
投标文件模板库 —— LLM Prompt + 标书章节模板 + 佐证材料定义
包含：招标文件解析Prompt、投标内容生成Prompt、标书各章节模板、材料分类定义
"""

# ============================================================
# 一、佐证材料标准分类
# ============================================================

# 佐证材料分类定义：key -> {名称, 类别(必须/可选), 说明}
MATERIAL_CATEGORIES = {
    'business_license': {
        'name': '营业执照',
        'type': 'must',
        'desc': '有效营业执照副本复印件（三证合一）'
    },
    'tax_cert': {
        'name': '税务登记证明',
        'type': 'must',
        'desc': '税务登记证或完税证明'
    },
    'org_code': {
        'name': '组织机构代码证',
        'type': 'optional',
        'desc': '组织机构代码证（未三证合一时需提供）'
    },
    'legal_rep_id': {
        'name': '法定代表人身份证',
        'type': 'must',
        'desc': '法定代表人身份证复印件'
    },
    'auth_letter': {
        'name': '授权委托书',
        'type': 'must',
        'desc': '法定代表人授权委托书'
    },
    'iso9001': {
        'name': 'ISO9001质量管理体系认证',
        'type': 'optional',
        'desc': 'ISO9001质量管理体系认证证书'
    },
    'iso14001': {
        'name': 'ISO14001环境管理体系认证',
        'type': 'optional',
        'desc': 'ISO14001环境管理体系认证证书'
    },
    'iso45001': {
        'name': 'ISO45001职业健康安全管理体系认证',
        'type': 'optional',
        'desc': 'ISO45001职业健康安全管理体系认证证书'
    },
    'industry_qualification': {
        'name': '行业资质证书',
        'type': 'optional',
        'desc': '与项目相关的行业资质/许可证（如建筑业资质、安全生产许可证等）'
    },
    'performance_contract': {
        'name': '业绩合同',
        'type': 'must',
        'desc': '同类项目业绩合同复印件（附验收证明）'
    },
    'financial_report': {
        'name': '财务报表/审计报告',
        'type': 'must',
        'desc': '近三年财务报表或审计报告'
    },
    'social_security': {
        'name': '社保缴纳证明',
        'type': 'must',
        'desc': '近6个月社保缴纳证明'
    },
    'tax_payment': {
        'name': '纳税证明',
        'type': 'optional',
        'desc': '近一年纳税证明'
    },
    'bank_credit': {
        'name': '银行资信证明',
        'type': 'optional',
        'desc': '银行出具的资信证明'
    },
    'team_cert': {
        'name': '项目团队资质证书',
        'type': 'must',
        'desc': '项目经理及关键岗位人员资质证书'
    },
    'credit_report': {
        'name': '信用查询结果',
        'type': 'optional',
        'desc': '信用中国网站查询结果截图'
    },
    'product_cert': {
        'name': '产品认证/检测报告',
        'type': 'optional',
        'desc': '投标产品的认证证书或检测报告'
    },
    'case_video': {
        'name': '项目案例视频',
        'type': 'optional',
        'desc': '同类项目案例视频资料'
    },
    'other': {
        'name': '其他材料',
        'type': 'optional',
        'desc': '招标文件要求的其他佐证材料'
    },
}

# 上传文件允许的扩展名（按类型分组）
ALLOWED_EXTENSIONS_BID = {
    'document': {'docx', 'pdf', 'xls', 'xlsx', 'pptx', 'txt'},
    'image': {'jpg', 'jpeg', 'png', 'bmp', 'webp'},
    'video': {'mp4', 'avi', 'mov'},
    'archive': {'zip', 'rar'},
}

# 各类型文件大小限制（字节）
FILE_SIZE_LIMITS = {
    'document': 20 * 1024 * 1024,   # 20MB
    'image': 10 * 1024 * 1024,      # 10MB
    'video': 100 * 1024 * 1024,     # 100MB
    'archive': 50 * 1024 * 1024,    # 50MB
}

# 文件类型中文映射
FILE_TYPE_LABELS = {
    'document': '文档',
    'image': '图片',
    'video': '视频',
    'archive': '压缩包',
}


def get_file_type(filename):
    """根据文件扩展名判断文件类型（document/image/video/archive）"""
    ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    for ftype, exts in ALLOWED_EXTENSIONS_BID.items():
        if ext in exts:
            return ftype
    return None


def get_file_size_limit(file_type):
    """获取文件类型对应的大小限制"""
    return FILE_SIZE_LIMITS.get(file_type, 10 * 1024 * 1024)


# ============================================================
# 二、招标文件解析 LLM Prompt
# ============================================================

def build_tender_parse_prompt(text):
    """
    构建招标文件解析的LLM Prompt
    输入: 招标文件全文
    输出: 系统提示 + 用户消息
    """
    system_prompt = """你是一名资深的招投标分析师，精通政府采购和工程招标文件的解析。

你的任务是：仔细阅读招标文件，提取以下结构化信息：
1. 项目基本信息：项目名称、预算金额、投标截止日期
2. 资质要求：投标人需具备的资质条件
3. 技术要求：招标文件中列明的技术规格、功能要求（逐条提取，保留原文要点）
4. 商务要求：付款方式、质保期、交货期/工期等商务条件
5. 评分标准：各评分项及分值
6. 关键时间节点：投标截止时间、开标时间等
7. 佐证材料清单：招标文件要求投标人提交的所有证明材料，分为"必须提供"和"可选提供"

请严格按照以下JSON格式输出，不要输出任何其他内容：
```json
{
  "project_name": "项目名称",
  "project_budget": "预算金额（如100万元）",
  "deadline": "投标截止日期（YYYY-MM-DD格式，如无法确定则留空）",
  "qualifications": ["资质要求1", "资质要求2"],
  "technical_requirements": ["技术要求1（保留原文要点）", "技术要求2"],
  "commercial_requirements": ["商务要求1", "商务要求2"],
  "evaluation_criteria": {"评分项1": 分值, "评分项2": 分值},
  "key_dates": {"投标截止": "日期", "开标时间": "日期"},
  "required_materials": [
    {"name": "材料名称", "type": "must", "desc": "材料说明"},
    {"name": "材料名称", "type": "optional", "desc": "材料说明"}
  ]
}
```

注意：
- type字段只能是"must"（必须提供）或"optional"（可选提供）
- 技术要求必须逐条提取，保留原文要点，不能泛泛概括
- 佐证材料要全面，包括但不限于：营业执照、资质证书、业绩证明、财务报表、社保证明等
- 如果某项信息在招标文件中未提及，对应字段留空或返回空列表
- 只返回JSON，不要有任何其他文字"""

    # 截取前8000字，控制Token消耗
    truncated_text = text[:8000] if len(text) > 8000 else text

    user_prompt = f"""请解析以下招标文件内容，提取结构化信息：

{truncated_text}

请严格按照要求的JSON格式输出。"""

    return system_prompt, user_prompt


# ============================================================
# 三、投标文件内容生成 LLM Prompt
# ============================================================

def build_bid_generation_prompt(tender_req, company_info):
    """
    构建投标文件内容生成的LLM Prompt
    输入: 招标需求JSON + 企业信息
    输出: 系统提示 + 用户消息
    """
    system_prompt = """你是一名资深的投标文件撰写专家，精通政府采购和工程招标投标文件的编写。

你的任务是：根据招标要求和投标人企业信息，生成投标文件的核心章节内容。

生成要求：
1. 技术方案：必须逐条响应招标技术要求，每条要求对应一个"响应"段落，说明我方如何满足该要求，不能遗漏任何一条
2. 商务方案：包括报价说明、付款方式响应、售后服务承诺等
3. 投标函：正式的投标函文本，格式规范

请严格按照以下JSON格式输出，不要输出任何其他内容：
```json
{
  "bid_letter": "投标函正文内容（完整的投标函文本）",
  "technical_responses": [
    {"requirement": "招标技术要求原文", "response": "我方响应：详细说明如何满足该要求"},
    {"requirement": "招标技术要求原文", "response": "我方响应：详细说明如何满足该要求"}
  ],
  "commercial_response": "商务方案正文（包括报价说明、付款方式响应、售后服务承诺等）"
}
```

注意：
- 技术方案必须逐条响应，technical_responses数组的长度应等于技术要求的条数
- 每条响应要具体、专业，不能泛泛而谈，要结合企业实际情况
- 投标函要包含：致采购人的称谓、投标项目名称、投标报价、工期/交货期承诺、质量承诺、有效期承诺、落款
- 语气正式、专业，符合政府采购投标文件规范
- 只返回JSON，不要有任何其他文字"""

    # 构建用户消息，包含招标需求和企业信息
    user_prompt = f"""请根据以下信息生成投标文件内容：

【招标要求】
项目名称：{tender_req.get('project_name', '')}
预算金额：{tender_req.get('project_budget', '')}
资质要求：{', '.join(tender_req.get('qualifications', []))}
技术要求：
{chr(10).join(f'  {i+1}. {req}' for i, req in enumerate(tender_req.get('technical_requirements', [])))}
商务要求：
{chr(10).join(f'  {i+1}. {req}' for i, req in enumerate(tender_req.get('commercial_requirements', [])))}
评分标准：{tender_req.get('evaluation_criteria', {})}

【投标人企业信息】
企业名称：{company_info.get('company_name', '')}
统一社会信用代码：{company_info.get('credit_code', '')}
企业地址：{company_info.get('address', '')}
联系电话：{company_info.get('phone', '')}
联系人：{company_info.get('contact_person', '')}
资质证书：{', '.join(company_info.get('qualifications', []))}
投标报价：{company_info.get('bid_price', '（后续填写）')}
工期/交货期：{company_info.get('delivery_period', '（后续填写）')}
项目团队：
{chr(10).join(f'  - {member}' for member in company_info.get('team_members', []))}
同类项目业绩：
{chr(10).join(f'  - {perf}' for perf in company_info.get('performances', []))}

请严格按照要求的JSON格式生成投标文件内容。"""

    return system_prompt, user_prompt


# ============================================================
# 四、标书章节模板（用于docx生成时的固定文本）
# ============================================================

def get_bid_letter_template(company_name, project_name, bid_price, delivery_period):
    """
    投标函模板（当LLM未生成时的备用模板）
    """
    return f"""致：{project_name}采购人

根据贵方为{project_name}项目的招标公告/邀请，我方{company_name}（统一社会信用代码：________）作为投标人，正式提交投标文件，并作如下承诺：

一、我方愿意按照招标文件的要求，以人民币{bid_price or '（报价详见投标一览表）'}的投标报价，承担{project_name}项目的实施工作，工期/交货期为{delivery_period or '（详见投标一览表）'}。

二、我方保证投标文件中的全部内容真实、准确、完整，不存在虚假陈述。如有虚假，我方愿意承担一切法律责任。

三、我方承诺：
1. 投标有效期为自投标截止日起90个日历天；
2. 如中标，将按照招标文件和投标文件签订合同，并严格履行合同义务；
3. 保证项目质量达到招标文件要求的标准；
4. 不进行转包或违法分包。

四、我方已详细阅读招标文件，完全理解其全部内容，并同意招标文件中的各项条款和条件。

五、有关本投标的一切往来函件，请寄至以下地址：
联系人：________
电话：________
地址：________

投标人（盖章）：{company_name}
法定代表人或授权代表（签字）：________
日期：________年____月____日"""


def get_commitment_templates(company_name):
    """
    承诺函模板（廉政承诺、保密承诺等）
    返回: 承诺函列表 [{title, content}]
    """
    return [
        {
            'title': '廉政承诺书',
            'content': f'''致：采购人

为维护招投标活动的公平、公正，我方{company_name}郑重承诺：

一、严格遵守国家法律法规和招投标相关规定，自觉维护招投标市场秩序。
二、不向采购人、评标委员会成员及其他相关人员行贿或提供其他不正当利益。
三、不与其他投标人相互串通投标报价，不排挤其他投标人的公平竞争。
四、不以他人名义投标或以其他方式弄虚作假，骗取中标。
五、如违反上述承诺，我方愿意承担相应的法律责任，并接受有关部门的处罚。

投标人（盖章）：{company_name}
日期：________年____月____日'''
        },
        {
            'title': '保密承诺书',
            'content': f'''致：采购人

我方{company_name}就参与{project_name_placeholder}项目的投标活动，郑重承诺：

一、对在投标过程中获悉的采购人商业秘密、技术秘密及其他保密信息，严格保密。
二、不将上述保密信息用于本投标以外的任何目的。
三、不向任何第三方披露上述保密信息。
四、如中标，在合同履行期间及合同终止后，继续承担保密义务。
五、如违反上述承诺，我方愿意承担相应的法律责任，并赔偿由此给采购人造成的损失。

投标人（盖章）：{company_name}
日期：________年____月____日'''
        }
    ]


# 日期占位符，在生成docx时替换
project_name_placeholder = '________'
