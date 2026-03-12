import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

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
                    "code": {
                        "type": "string",
                        "description": "需要检测的代码"
                    }
                },
                "required": ["code"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_performance",
            "description": "检查代码中的性能问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "需要检查的代码"
                    },
                    "engine": {
                        "type": "string",
                        "description": "游戏引擎类型：unity/unreal/other"
                    }
                },
                "required": ["code", "engine"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "check_safety",
            "description": "检查代码中的空引用、异常处理等安全问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "需要检查的代码"
                    }
                },
                "required": ["code"]
            }
        }
    }
]

# ============ 工具函数实现 ============
def detect_language(code: str) -> str:
    """检测语言和引擎"""
    result = {
        "language": "unknown",
        "engine": "other"
    }
    # 检测Unity C#
    unity_keywords = ["MonoBehaviour", "GameObject", "Update()", "Start()", "GetComponent"]
    if any(kw in code for kw in unity_keywords):
        result["language"] = "csharp"
        result["engine"] = "unity"
    # 检测Unreal C++
    elif any(kw in code for kw in ["AActor", "UObject", "UPROPERTY", "UFUNCTION"]):
        result["language"] = "cpp"
        result["engine"] = "unreal"
    # 检测Python
    elif "def " in code or "import " in code:
        result["language"] = "python"
        result["engine"] = "other"

    return json.dumps(result, ensure_ascii=False)

def check_performance(code: str, engine: str) -> str:
    """检查性能问题"""
    issues = []

    if engine == "unity":
        # Unity常见性能陷阱
        if "FindObjectsOfType" in code:
            issues.append("⚠️ 使用了FindObjectsOfType，每帧调用性能开销极大，建议缓存或改用标签查找")
        if "FindGameObjectsWithTag" in code and "Update" in code:
            issues.append("⚠️ 在Update中使用了FindGameObjectsWithTag，建议移到Start中缓存")
        if "GetComponent" in code and "Update" in code:
            issues.append("⚠️ 在Update中频繁调用GetComponent，建议在Start中缓存组件引用")
        if "Instantiate" in code and "Update" in code:
            issues.append("⚠️ 在Update中使用Instantiate，建议使用对象池")

    if not issues:
        issues.append("✅ 未发现明显性能问题")

    return "\n".join(issues)

def check_safety(code: str) -> str:
    """检查安全问题"""
    issues = []

    if "GetComponent" in code:
        # 简单检查GetComponent后是否有空值判断
        if "!= null" not in code and "is null" not in code:
            issues.append("⚠️ GetComponent返回值未做空值检查，可能引发NullReferenceException")

    if ".material.color" in code:
        issues.append("⚠️ 直接修改material.color会创建新的material实例，建议使用MaterialPropertyBlock")

    if not issues:
        issues.append("✅ 未发现明显安全问题")

    return "\n".join(issues)

# 工具映射
fn_map = {
    "detect_language": detect_language,
    "check_performance": check_performance,
    "check_safety": check_safety
}

# ============ 测试代码 ============
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

# ============ Agent主循环 ============
def run_review_agent(code: str):
    print("开始审查代码...\n")

    messages = [
        {
            "role": "system",
            "content": """你是游戏代码审查Agent。
            收到代码后，按这个顺序调用工具：
            1. 先调用detect_language检测语言和引擎
            2. 再调用check_performance检查性能问题
            3. 再调用check_safety检查安全问题
            4. 最后整合所有工具结果，输出结构化审查报告

            报告格式：
            【语言/引擎】xxx
            【性能问题】xxx
            【安全问题】xxx
            【总体评分】x/10
【          修改优先级】先改xxx，再改xxx"""
        },
        {
            "role": "user",
            "content": f"请审查这段代码：\n{code}"
        }
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
                print(f"🔧 调用工具：{fn_name}")

                result = fn_map[fn_name](**args)
                print(f"   结果：{result}\n")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

run_review_agent(buggy_code)