# 假新闻检测系统

基于LangChain和DeepSeek API的假新闻检测后端系统，支持PDF和TXT文件处理，以及网络搜索和RAG增强功能。

## 功能特点

- 使用DeepSeek API进行高质量的假新闻检测
- 支持PDF和TXT文件上传和处理
- 支持网络搜索功能，查找相关信息
- 内置RAG（检索增强生成）技术，提高检测准确性
- 提供RESTful API接口，便于集成
- 支持命令行和交互式运行模式

## 环境准备

### 依赖安装

```bash
pip install -r requirements.txt
```

### 环境变量配置

复制`.env.example`为`.env`，并配置必要的环境变量：

```bash
cp .env.example .env
```

编辑`.env`文件，设置DeepSeek API密钥：

```
DEEPSEEK_API_KEY=your_deepseek_api_key_here
```

## 使用方式

本系统提供了多种使用方式，您可以根据需要选择最适合的方式。

### 1. 直接运行交互式控制台

最简单的使用方式是通过交互式控制台运行：

```bash
python run_interactive.py
```

这将启动一个交互式界面，您可以在其中选择输入文本或提供文件路径，并设置是否使用RAG和网络搜索功能。

### 2. 使用命令行参数运行

如果您需要在脚本或命令行中使用，可以使用`run_detector.py`：

```bash
# 检测文本
python run_detector.py --text "这是一篇需要检测的新闻文本..." --web-search --rag

# 检测文件
python run_detector.py --file path/to/news.pdf --web-search

# 保存结果到文件
python run_detector.py --text "新闻文本..." --output results.json
```

命令行参数说明：
- `--text`: 指定要检测的文本内容
- `--file`: 指定要检测的文件路径（PDF或TXT）
- `--rag`: 启用RAG增强
- `--web-search`: 启用网络搜索
- `--output`: 将结果保存到指定文件

### 3. 运行示例

我们提供了一个示例脚本，用于展示系统的基本功能：

```bash
python run_example.py
```

该脚本包含一个假新闻示例和一个真实新闻示例，会分别使用基础模式和网络搜索模式进行检测。

### 4. 启动Web服务器

如果您需要以Web服务方式使用，可以启动Flask服务器：

```bash
python app.py
```

服务默认将在`http://localhost:5001`上运行。

## API接口

### 健康检查

```
GET /health
```

返回服务健康状态。

### 假新闻检测

```
POST /detect
```

参数:
- `text` (可选): 直接输入的新闻文本
- `file` (可选): 上传的PDF或TXT文件
- `use_rag` (可选): 是否使用RAG增强 (true/false)
- `use_web_search` (可选): 是否使用网络搜索 (true/false)

至少需要提供`text`或`file`中的一个。

示例响应:
```json
{
  "is_fake": true,
  "confidence": 85,
  "reasoning": "这篇文章包含多处不一致的信息和无法验证的来源...",
  "evidence": [
    "文中提到的专家不存在或其陈述被篡改",
    "数据与官方公布的统计数据不符"
  ],
  "processing_time": 2.45,
  "web_search_results": [...],
  "rag_contexts": [...]
}
```

### 网络搜索

```
POST /web-search
```

参数:
- `query`: 搜索查询

返回与查询相关的搜索结果列表。

## 使用示例

### 使用curl检测文本

```bash
curl -X POST http://localhost:5001/detect \
  -F "text=这是一篇需要检测的新闻..." \
  -F "use_web_search=true"
```

### 使用curl上传文件

```bash
curl -X POST http://localhost:5001/detect \
  -F "file=@/path/to/news.pdf" \
  -F "use_rag=true" \
  -F "use_web_search=true"
```

## 性能与限制

- 较长文档的处理可能需要较长时间
- API调用受DeepSeek API限制影响
- 网络搜索功能依赖于网络连接和第三方服务

## 技术架构

- Flask: Web框架
- LangChain: LLM应用框架
- DeepSeek API: 大型语言模型服务
- FAISS: 高效向量检索库
- HuggingFace Transformers: 本地嵌入模型 