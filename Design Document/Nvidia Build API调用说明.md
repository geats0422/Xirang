# 1 API

## 1.1 基础信息

**Base URL**： https://integrate.api.nvidia.com/v1

**认证方式**：Bearer Token（即你的 API Key）

**接口格式**：兼容 OpenAI API 格式

## 1.2 python调用示例

```python
import openai
	client = openai.OpenAI(
	base_url="https://integrate.api.nvidia.com/v1",
	api_key="your-api-key-here" # 替换为你的 API Key
	)
response = client.chat.completions.create(
	model="nvidia/nemotron-3-nano-30b-a3b", # 模型名称
	messages=[
		{"role": "user", "content": "你好，请介绍一下自己"}
	],
	temperature=0.7,
	max_tokens=1024
)
print(response.choices[0].message.content)
```

