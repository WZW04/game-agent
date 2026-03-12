# 游戏代码审查 Agent

基于 DeepSeek API 实现的游戏研发场景 AI Agent，能够自动审查 Unity C# 代码，
识别性能、内存、安全问题，并对照开发规范给出具体修改建议。

## 演示效果

输入一段 Unity C# 代码：
```csharp
void Update() {
    GameObject[] enemies = GameObject.FindObjectsOfType<GameObject>();
    foreach(var enemy in enemies) {
        if(enemy.tag == "Enemy") {
            enemy.GetComponent<Renderer>().material.color = Color.red;
        }
    }
}
```

Agent 自动输出：
```
【语言/引擎】C# / Unity
【问题清单】
- [严重] Update中使用FindObjectsOfType
  违反规范：禁止在Update()中调用查找函数，必须在Start()中缓存
  修改建议：将对象查找移到Start()中缓存到成员变量

- [严重] Update中调用GetComponent未缓存
  违反规范：禁止在Update()中调用GetComponent
  修改建议：在Start()中缓存Renderer组件引用

- [一般] 直接修改material.color导致内存泄漏
  违反规范：必须使用MaterialPropertyBlock修改材质颜色
  修改建议：改用MaterialPropertyBlock

【总体评分】3/10
【修改优先级】先改性能问题，再改内存问题，最后加空值检查
```

## 技术架构
```
用户输入代码
     ↓
detect_language()    ← 识别语言和引擎类型
     ↓
check_code()         ← 检测问题清单
     ↓
retrieve_standards() ← RAG检索对应规范条目（可调用多次）
     ↓
整合输出审查报告
```

三个核心技术点：
- **Function Calling**：Agent自主决定调用哪些工具、调用几次，无需人工指定流程
- **RAG**：审查时检索内部规范文档，报告中每个问题都对应具体违规条款
- **System Prompt**：约束输出格式，确保报告结构统一

## 项目结构
```
game-agent/
├── week1/                        # 基础学习
│   ├── day1_api_test.py          # LLM API调用
│   ├── day2_prompt.py            # Prompt Engineering
│   ├── day3_function_calling.py  # Function Calling原理
│   ├── day4_rag.py               # RAG原理
│   └── day5_agent.py            # 综合Agent
├── week2/                        # 游戏代码审查Agent
│   ├── day1_code_review_basic.py # 基础审查
│   ├── day2_code_review_agent.py # 加入Function Calling
│   ├── day3_code_review_rag.py   # 加入RAG
│   └── day4_final_demo.py       # 完整可演示版本
└── README.md
```

## 快速开始

**安装依赖**
```bash
pip install openai
```

**设置环境变量**
```bash
# Windows
set DEEPSEEK_API_KEY=你的Key

# Mac/Linux1
export DEEPSEEK_API_KEY=你的Key
```

**运行演示**
```bash
python week2/day4_final_demo.py
```

## 下一步计划

- [ ] 升级为向量检索RAG，支持语义匹配规范文档
- [ ] 支持读取本地代码文件（.cs/.cpp）直接审查
- [ ] 扩展Unreal C++审查规则
- [ ] 输出JSON格式报告，对接CI/CD流水线