import os
import json
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 第一部分：定义工具（告诉模型有什么工具可以用）
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
                        "description": "职业类型，warrior/mage/archer之一"
                    },
                    "field": {
                        "type": "string",
                        "description": "配置字段名，如attack、hp、speed"
                    },
                    "value": {
                        "type": "number",
                        "description": "配置的数值"
                    }
                },
                "required": ["class_type", "field", "value"]
            }
        }
    }
]

# 第二部分：真实的业务逻辑函数
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
        return f"✅ 合理：{class_type}的{field}={value}，标准范围[{lo}, {hi}]"
    else:
        return f"❌ 不合理：{class_type}的{field}={value}，超出范围[{lo}, {hi}]"

# 第三部分：第一轮对话，让模型决定调用什么工具
messages = [
    {"role": "system", "content": "你是游戏配置审核助手，收到配置数据时必须调用工具验证，不要自己猜。"},
    {"role": "user", "content": "我们游戏里战士的攻击力设置了85，这在合理范围内吗？"}
]

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    tools=tools,
    tool_choice="auto"
)

msg = response.choices[0].message

# 第四部分：执行工具，把结果还给模型
if response.choices[0].finish_reason == "tool_calls":
    messages.append(msg)  # 把模型的决策存入历史
    
    for tool_call in msg.tool_calls:
        # 解析模型传来的参数
        args = json.loads(tool_call.function.arguments)
        print(f"执行工具，参数：{args}")
        
        # 执行真实函数
        result = validate_config(**args)
        print(f"工具结果：{result}")
        
        # 把结果加入对话历史
        messages.append({
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": result
        })
    
    # 第五部分：第二轮对话，模型根据工具结果生成最终回答
    final = client.chat.completions.create(
        model="deepseek-chat",
        messages=messages,
        tools=tools
    )
    print("\n最终回答：", final.choices[0].message.content)