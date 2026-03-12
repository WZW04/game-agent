import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ.get("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# 一段有问题的Unity C#代码
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


"""
# 直接丢给模型，不给任何引导
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "user", "content": f"审查这段代码：\n{buggy_code}"}
    ]
)

print(response.choices[0].message.content)
"""


# 接着上面的代码继续加

response2 = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": """你是一个资深游戏开发工程师，专门做Unity C#代码审查。

            审查代码时必须按以下格式输出，不要多说废话：

            【严重问题】（影响性能或导致崩溃）
            - 问题描述：xxx
            - 问题位置：第x行
            - 修改建议：xxx

            【一般问题】（代码规范或潜在隐患）
            - 问题描述：xxx
            - 修改建议：xxx

            【总体评分】x/10
            【一句话总结】xxx"""
        },
        {
            "role": "user",
            "content": f"审查这段代码：\n{buggy_code}"
        }
    ]
)

print(response2.choices[0].message.content)
