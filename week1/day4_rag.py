import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 模拟你们游戏的内部文档库
game_docs = [
    "影魂法师是暗系远程职业，擅长控制和爆发伤害。觉醒技能为【噬魂裂空】，召唤暗影裂缝对范围内敌人造成300%魔法伤害并沉默2秒。",
    "烈焰战士是火系近战职业，擅长单体高伤害。觉醒技能为【炎帝降临】，进入狂热状态15秒，攻击力提升50%，每次攻击附带灼烧效果。",
    "疾风弓手是风系远程职业，擅长高移速游走。觉醒技能为【风神领域】，在范围内创造风暴领域，己方移速提升30%，敌方移速降低30%，持续10秒。",
]

def retrieve(query: str, docs: list) -> str:
    """简单关键词检索，找到最相关的文档片段"""
    for doc in docs:
        # 把用户问题里的词，逐个去文档里找
        for word in query:
            if word in doc:
                return doc  # 找到第一个相关的就返回
    return "未找到相关文档"

# 用户提问
question = "哪个职业适合喜欢控制敌人的玩家？"

# 先检索
context = retrieve(question, game_docs)
print("检索到的文档片段：")
print(context)
print("\n" + "="*50 + "\n")

# 把检索结果塞进prompt
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "你是游戏客服助手，只根据提供的游戏文档回答问题，不要编造信息。"},
        {"role": "user", "content": f"参考文档：\n{context}\n\n问题：{question}"}
    ]
)

print("有RAG的回答：")
print(response.choices[0].message.content)