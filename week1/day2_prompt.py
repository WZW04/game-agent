import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"), 
    base_url="https://api.deepseek.com"
)
"""
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": "角色攻击力设置为99999,这合理吗？"}
    ]
)
print("没有system提示词：")
print(response.choices[0].message.content)  
print("--------------------------------")
print("有system提示词：")
response2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是一个专业的游戏策划审核助手，只负责检查游戏配置数据是否合理，回答要简洁明了"},
        {"role": "user", "content": "角色攻击力设置为99999,这合理吗？"}
    ]
)
print("有system提示词：")
print(response2.choices[0].message.content)  

response3 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是游戏策划审核助手，把技能描述转成JSON格式。"},
        {"role": "user", "content": 
        "
        参考这个例子：
        输入：火球术，造成100点火焰伤害
        输出：{"name": "火球术", "damage": 100, "type": "fire"}
        现在处理这个：
        输入：冰霜箭，造成80点冰霜伤害并减速3秒
        "
        }
    ]
)
print("Few-shot输出：")
print(response3.choices[0].message.content)  
"""

# 不让它思考，直接要答案
response4 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是游戏策划审核助手，回答要简洁。"},
        {"role": "user", "content": "这个关卡设计有问题吗？玩家初始血量100，第一个敌人造成150点伤害。"}
    ]
)
print("不思考，直接回答：")
print(response4.choices[0].message.content)
print("\n" + "="*50 + "\n")

# 让它一步步思考
response5 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是游戏策划审核助手，回答要简洁。"},
        {"role": "user", "content": "这个关卡设计有问题吗？玩家初始血量100，第一个敌人造成150点伤害。请先逐步分析，再给出结论。"}
    ]
)
print("一步步思考：")
print(response5.choices[0].message.content)