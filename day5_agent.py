import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ============ RAG部分：文档库 + 检索函数 ============
game_docs = [
    "影魂法师是暗系远程职业，擅长控制和爆发伤害。觉醒技能为【噬魂裂空】，召唤暗影裂缝对范围内敌人造成300%魔法伤害并沉默2秒。",
    "烈焰战士是火系近战职业，擅长单体高伤害。觉醒技能为【炎帝降临】，进入狂热状态15秒，攻击力提升50%，每次攻击附带灼烧效果。",
    "疾风弓手是风系远程职业，擅长高移速游走。觉醒技能为【风神领域】，在范围内创造风暴领域，己方移速提升30%，敌方移速降低30%，持续10秒。",
]

def retrieve(query: str, docs: list) -> str:
    for doc in docs:
        for word in query:
            if word in doc:
                return doc
    return "未找到相关文档"

# ============ Function Calling部分：工具定义 + 函数 ============
tools = [
    {
        "type": "function",
        "function": {
            "name": "validate_config",
            "description": "验证游戏职业的数值配置是否在合理范围内",
            "parameters": {
                "type": "object",
                "properties": {
                    "class_type": {
                        "type": "string",
                        "description": "职业类型：warrior/mage/archer"
                    },
                    "field": {
                        "type": "string",
                        "description": "配置字段：attack/hp/speed"
                    },
                    "value": {
                        "type": "number",
                        "description": "配置的数值"
                    }
                },
                "required": ["class_type", "field", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_game_docs",
            "description": "搜索游戏内部文档，回答关于职业、技能、剧情的问题",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索关键词"
                    }
                },
                "required": ["query"]
            }
        }
    }
]

def validate_config(class_type: str, field: str, value: float) -> str:
    standards = {
        "warrior": {"attack": (60, 100), "hp": (150, 300), "speed": (3, 6)},
        "mage":    {"attack": (80, 130), "hp": (80,  150), "speed": (3, 5)},
        "archer":  {"attack": (50, 90),  "hp": (100, 200), "speed": (5, 8)},
    }
    if class_type not in standards:
        return f"未知职业：{class_type}"
    if field not in standards[class_type]:
        return f"未知字段：{field}"
    lo, hi = standards[class_type][field]
    if lo <= value <= hi:
        return f"✅ 合理：{class_type}的{field}={value}，标准范围[{lo},{hi}]"
    else:
        return f"❌ 不合理：{class_type}的{field}={value}，超出范围[{lo},{hi}]"

def search_game_docs(query: str) -> str:
    result = retrieve(query, game_docs)
    return result

# 工具名 → 函数的映射表
fn_map = {
    "validate_config": validate_config,
    "search_game_docs": search_game_docs
}

# ============ Agent主循环 ============
def run_agent(user_input: str):
    print(f"\n用户：{user_input}")
    print("="*50)

    messages = [
        {"role": "system", "content": """
        你是游戏综合助手，有两个工具可以用：
        1. validate_config：验证数值配置是否合理
        2. search_game_docs：查询职业、技能等游戏内容

        收到问题时判断用哪个工具，需要时可以连续调用多个工具。"""},
        {"role": "user", "content": user_input}
    ]

    # 循环，直到模型不再调用工具
    while True:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )

        msg = response.choices[0].message
        finish = response.choices[0].finish_reason

        # 模型回答完了，退出循环
        if finish == "stop":
            print(f"\n🤖 助手：{msg.content}")
            break

        # 模型要调用工具
        if finish == "tool_calls":
            messages.append(msg)

            for tool_call in msg.tool_calls:
                args = json.loads(tool_call.function.arguments)
                fn_name = tool_call.function.name
                print(f"🔧 调用工具：{fn_name}，参数：{args}")

                result = fn_map[fn_name](**args)
                print(f"   结果：{result}")

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

# ============ 测试三个不同问题 ============
run_agent("影魂法师的觉醒技能是什么？")
run_agent("战士攻击力设置了120，合理吗？")
run_agent("影魂法师的觉醒技能伤害够高吗？如果我把战士攻击力调到120来对抗她，合理吗？")