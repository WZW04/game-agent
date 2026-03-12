import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============ 游戏开发规范文档库 ============
# 真实项目里这些从公司内部文档读取
code_standards = [
    "Unity性能规范：禁止在Update()中调用FindObjectsOfType、FindGameObjectsWithTag等查找函数，所有场景对象引用必须在Start()或Awake()中缓存。",
    "Unity性能规范：禁止在Update()中调用GetComponent，组件引用必须在初始化阶段缓存到成员变量。",
    "Unity内存规范：修改材质颜色必须使用MaterialPropertyBlock，禁止直接修改material.color，否则会产生多余的材质实例导致内存泄漏。",
    "Unity安全规范：所有GetComponent调用必须做空值检查，推荐使用TryGetComponent替代GetComponent。",
    "Unity对象规范：动态创建销毁对象必须使用对象池，禁止在游戏循环中直接调用Instantiate和Destroy。",
    "代码规范：所有公共方法必须添加XML注释，私有成员变量以下划线开头命名。",
]

def retrieve_standards(issue_type: str) -> str:
    """根据问题类型检索相关规范"""
    keywords = {
        "performance": ["性能", "Update", "Find", "GetComponent"],
        "memory": ["内存", "材质", "material", "实例"],
        "safety": ["安全", "空值", "null", "异常"],
        "object": ["对象", "Instantiate", "Destroy", "对象池"],
    }

    relevant = []
    search_words = keywords.get(issue_type, [issue_type])

    for standard in code_standards:
        if any(word in standard for word in search_words):
            relevant.append(standard)

    return "\n".join(relevant) if relevant else "未找到相关规范"

# ============ 工具定义 ============
tools = [
    {
        "type": "function",
        "function": {
            "name": "detect_language",
            "description": "检测代码的编程语言和游戏引擎类型",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "需要检测的代码"}
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_standards",
            "description": "检索公司游戏开发规范文档，获取相关编码标准",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_type": {
                        "type": "string",
                        "description": "问题类型：performance/memory/safety/object"
                    }
                },
                "required": ["issue_type"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_code",
            "description": "对代码进行全面检查，发现问题清单",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "需要检查的代码"},
                    "engine": {"type": "string", "description": "游戏引擎：unity/unreal/other"}
                },
                "required": ["code", "engine"]
            }
        }
    }
]

# ============ 工具函数 ============
def detect_language(code: str) -> str:
    result = {"language": "unknown", "engine": "other"}
    unity_keywords = ["MonoBehaviour", "GameObject", "Update()", "Start()", "GetComponent"]
    if any(kw in code for kw in unity_keywords):
        result["language"] = "csharp"
        result["engine"] = "unity"
    return json.dumps(result, ensure_ascii=False)

def check_code(code: str, engine: str) -> str:
    issues = []
    if engine == "unity":
        if "FindObjectsOfType" in code:
            issues.append({"type": "performance", "desc": "Update中使用FindObjectsOfType", "severity": "严重"})
        if "GetComponent" in code and "Update" in code:
            issues.append({"type": "performance", "desc": "Update中调用GetComponent未缓存", "severity": "严重"})
        if ".material.color" in code:
            issues.append({"type": "memory", "desc": "直接修改material.color导致内存泄漏", "severity": "一般"})
        if "GetComponent" in code and "!= null" not in code:
            issues.append({"type": "safety", "desc": "GetComponent未做空值检查", "severity": "一般"})
    return json.dumps(issues, ensure_ascii=False)

fn_map = {
    "detect_language": detect_language,
    "retrieve_standards": retrieve_standards,
    "check_code": check_code
}

# ============ Agent主循环 ============
def run_review_agent(code: str):
    print("开始审查代码...\n")

    messages = [
        {
            "role": "system",
            "content": """你是游戏代码审查Agent，按以下步骤工作：
            1. detect_language：检测语言和引擎
            2. check_code：检查代码问题，得到问题清单
            3. 针对每个问题的type，调用retrieve_standards检索对应规范
            4. 整合所有结果，输出审查报告

            报告格式：
            【语言/引擎】xxx
            【问题清单】
            - [严重/一般] 问题描述
            违反规范：xxx
            修改建议：xxx
            【总体评分】x/10
            【修改优先级】xxx"""
        },
        {"role": "user", "content": f"请审查这段代码：\n{code}"}
    ]

    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        finish = response.choices[0].finish_reason

        if finish == "stop":
            print("📋 审查报告：")
            print(msg.content)
            break

        if finish == "tool_calls":
            messages.append(msg)
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                fn_name = tool_call.function.name
                print(f"🔧 调用工具：{fn_name}，参数：{args}")
                result = fn_map[fn_name](**args)
                print(f"   结果：{result}\n")
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

# ============ 测试 ============
buggy_code = """
void Update() {
    GameObject[] enemies = GameObject.FindObjectsOfType<GameObject>();
    foreach(var enemy in enemies) {
        if(enemy.tag == "Enemy") {
            enemy.GetComponent<Renderer>().material.color = Color.red;
        }
    }
}
"""

run_review_agent(buggy_code)