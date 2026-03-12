import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============ 规范文档库 ============
code_standards = [
    "Unity性能规范：禁止在Update()中调用FindObjectsOfType、FindGameObjectsWithTag等查找函数，所有场景对象引用必须在Start()或Awake()中缓存。",
    "Unity性能规范：禁止在Update()中调用GetComponent，组件引用必须在初始化阶段缓存到成员变量。",
    "Unity内存规范：修改材质颜色必须使用MaterialPropertyBlock，禁止直接修改material.color，否则会产生多余的材质实例导致内存泄漏。",
    "Unity安全规范：所有GetComponent调用必须做空值检查，推荐使用TryGetComponent替代GetComponent。",
    "Unity对象规范：动态创建销毁对象必须使用对象池，禁止在游戏循环中直接调用Instantiate和Destroy。",
    "代码规范：所有公共方法必须添加XML注释，私有成员变量以下划线开头命名。",
]

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
            "name": "check_code",
            "description": "检查代码中的性能、内存、安全问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "需要检查的代码"},
                    "engine": {"type": "string", "description": "游戏引擎：unity/unreal/other"}
                },
                "required": ["code", "engine"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve_standards",
            "description": "检索游戏开发规范文档",
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
    }
]

# ============ 工具函数 ============
def detect_language(code: str) -> str:
    result = {"language": "unknown", "engine": "other"}
    unity_keywords = ["MonoBehaviour", "GameObject", "Update()", "Start()", "GetComponent"]
    if any(kw in code for kw in unity_keywords):
        result["language"] = "csharp"
        result["engine"] = "unity"
    elif any(kw in code for kw in ["AActor", "UObject", "UPROPERTY"]):
        result["language"] = "cpp"
        result["engine"] = "unreal"
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
        if "Instantiate" in code and "Update" in code:
            issues.append({"type": "object", "desc": "Update中使用Instantiate，建议用对象池", "severity": "严重"})
    return json.dumps(issues, ensure_ascii=False)

def retrieve_standards(issue_type: str) -> str:
    keywords = {
        "performance": ["性能", "Update", "Find", "GetComponent"],
        "memory": ["内存", "材质", "material"],
        "safety": ["安全", "空值", "null"],
        "object": ["对象", "Instantiate", "对象池"],
    }
    relevant = []
    search_words = keywords.get(issue_type, [issue_type])
    for standard in code_standards:
        if any(word in standard for word in search_words):
            relevant.append(standard)
    return "\n".join(relevant) if relevant else "未找到相关规范"

fn_map = {
    "detect_language": detect_language,
    "check_code": check_code,
    "retrieve_standards": retrieve_standards
}

# ============ Agent核心 ============
def run_review_agent(code: str) -> str:
    messages = [
        {
            "role": "system",
            "content": """你是游戏代码审查Agent，按以下步骤工作：
1. detect_language：检测语言和引擎
2. check_code：检查代码问题
3. 针对每个问题的type调用retrieve_standards检索规范
4. 整合输出审查报告，格式如下：

【语言/引擎】xxx
【问题清单】
- [严重/一般] 问题描述
  违反规范：xxx
  修改建议：xxx
【总体评分】x/10
【修改优先级】先改xxx，再改xxx

不要输出修改后的完整代码。"""
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
            return msg.content

        if finish == "tool_calls":
            messages.append(msg)
            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                fn_name = tool_call.function.name
                print(f"  🔧 {fn_name}...")
                result = fn_map[fn_name](**args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

# ============ 预置测试用例 ============
test_cases = {
    "1": {
        "name": "Update性能问题",
        "code": """
void Update() {
    GameObject[] enemies = GameObject.FindObjectsOfType<GameObject>();
    foreach(var enemy in enemies) {
        if(enemy.tag == "Enemy") {
            enemy.GetComponent<Renderer>().material.color = Color.red;
        }
    }
}"""
    },
    "2": {
        "name": "对象池问题",
        "code": """
void Update() {
    if(Input.GetKeyDown(KeyCode.Space)) {
        GameObject bullet = Instantiate(bulletPrefab, transform.position, Quaternion.identity);
        bullet.GetComponent<Rigidbody>().velocity = transform.forward * 10f;
    }
}"""
    },
    "3": {
        "name": "自定义代码",
        "code": None
    }
}

# ============ 命令行交互入口 ============
def main():
    print("=" * 50)
    print("  游戏代码审查 Agent")
    print("  基于 DeepSeek API + Function Calling + RAG")
    print("=" * 50)

    while True:
        print("\n请选择测试用例：")
        print("  1. Update性能问题（Unity C#）")
        print("  2. 对象池问题（Unity C#）")
        print("  3. 输入自定义代码")
        print("  q. 退出")

        choice = input("\n输入选项：").strip()

        if choice == "q":
            print("退出。")
            break

        if choice not in test_cases:
            print("无效选项，请重新输入。")
            continue

        if choice == "3":
            print("请输入代码（输入END单独一行结束）：")
            lines = []
            while True:
                line = input()
                if line == "END":
                    break
                lines.append(line)
            code = "\n".join(lines)
        else:
            code = test_cases[choice]["code"]
            print(f"\n审查用例：{test_cases[choice]['name']}")

        print("\n正在审查...\n")
        report = run_review_agent(code)
        print("\n📋 审查报告：")
        print(report)
        print("\n" + "=" * 50)

if __name__ == "__main__":
    main()