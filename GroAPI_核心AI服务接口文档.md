# GroAPI 核心AI服务接口文档

## 概述

GroAPI 是新一代大模型网关与AI资产管理系统，提供统一的AI服务接口，完全兼容 OpenAI API 协议。支持文本、图像、音频、视频等多模态AI服务，聚合30+AI服务商。

### 基础信息
- **基础URL**: `https://your-domain.com/v1`
- **协议**: HTTPS  
- **认证方式**: Bearer Token
- **数据格式**: JSON
- **字符编码**: UTF-8

### 认证方式
所有请求需要在HTTP请求头中包含API密钥：
```http
Authorization: Bearer YOUR_API_KEY
```

---

## 一、模型列表接口

### 1. 获取可用模型列表

**接口地址**: `GET /v1/models`

**请求方法**: GET

**请求参数**: 无

**请求头**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| Authorization | string | 是 | Bearer YOUR_API_KEY |

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "gpt-4o",
      "object": "model", 
      "created": 1626777600,
      "owned_by": "openai"
    },
    {
      "id": "claude-3-opus",
      "object": "model",
      "created": 1626777600, 
      "owned_by": "anthropic"
    },
    {
      "id": "midjourney-v6",
      "object": "model",
      "created": 1626777600,
      "owned_by": "midjourney"
    }
  ]
}
```

**响应参数说明**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| object | string | 固定值 "list" |
| data | array | 模型列表数组 |
| data[].id | string | 模型标识符 |
| data[].object | string | 固定值 "model" |
| data[].created | integer | 创建时间戳 |
| data[].owned_by | string | 模型提供商 |

### 2. 获取特定模型信息

**接口地址**: `GET /v1/models/{model}`

**请求方法**: GET

**路径参数**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| model | string | 是 | 模型ID，如 "gpt-4o" |

**响应示例**:
```json
{
  "id": "gpt-4o",
  "object": "model",
  "created": 1626777600,
  "owned_by": "openai"
}
```

---

## 二、文本生成接口

### 1. 聊天对话接口

**接口地址**: `POST /v1/chat/completions`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | gpt-4o, claude-3-opus, gemini-pro 等 | 要使用的模型名称 |
| messages | array | 是 | - | 消息对象数组 | 对话消息列表 |
| temperature | number | 否 | 0.7 | 0.0-2.0 | 随机性控制，越高越随机 |
| top_p | number | 否 | 1.0 | 0.1-1.0 | 核采样参数 |
| max_tokens | integer | 否 | 4096 | 1-32768 | 最大生成token数 |
| stream | boolean | 否 | false | true/false | 是否流式返回 |
| stop | array/string | 否 | null | 字符串或数组 | 停止序列 |
| presence_penalty | number | 否 | 0 | -2.0-2.0 | 重复惩罚 |
| frequency_penalty | number | 否 | 0 | -2.0-2.0 | 频率惩罚 |
| logit_bias | object | 否 | null | 偏置对象 | token偏置设置 |
| user | string | 否 | null | 用户标识 | 代表最终用户的唯一标识符 |

**messages 参数详情**:
| 参数名 | 类型 | 必选 | 可接受值 | 说明 |
|--------|------|------|----------|------|
| role | string | 是 | system, user, assistant | 消息角色 |
| content | string/array | 是 | 文本或多模态内容 | 消息内容 |
| name | string | 否 | 字符串 | 角色名称 |

**多模态content格式**:
```json
{
  "role": "user",
  "content": [
    {
      "type": "text",
      "text": "这是什么图片？"
    },
    {
      "type": "image_url", 
      "image_url": {
        "url": "https://example.com/image.jpg"
      }
    }
  ]
}
```

**请求示例**:
```json
{
  "model": "gpt-4o",
  "messages": [
    {
      "role": "system",
      "content": "你是一个有用的AI助手。"
    },
    {
      "role": "user", 
      "content": "你好，介绍一下自己"
    }
  ],
  "temperature": 0.7,
  "max_tokens": 1000,
  "stream": false
}
```

**响应示例（非流式）**:
```json
{
  "id": "chatcmpl-unified-123",
  "object": "chat.completion",
  "created": 1699000000,
  "model": "gpt-4o",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "你好！我是一个AI助手，可以帮助你回答问题、处理任务...",
        "tool_calls": null
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 20,
    "completion_tokens": 30,
    "total_tokens": 50
  },
  "system_fingerprint": "fp_xxx"
}
```

**流式响应示例**:
```
data: {"id":"chatcmpl-unified-123","object":"chat.completion.chunk","created":1699000000,"model":"gpt-4o","choices":[{"index":0,"delta":{"content":"你好"},"finish_reason":null}]}

data: {"id":"chatcmpl-unified-123","object":"chat.completion.chunk","created":1699000000,"model":"gpt-4o","choices":[{"index":0,"delta":{},"finish_reason":"stop"}]}

data: [DONE]
```

**响应参数说明**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| id | string | 请求ID |
| object | string | 对象类型 |
| created | integer | 创建时间戳 |
| model | string | 实际使用的模型 |
| choices | array | 生成选择列表 |
| choices[].index | integer | 选择索引 |
| choices[].message | object | 消息对象 |
| choices[].finish_reason | string | 结束原因：stop, length, tool_calls, content_filter |
| usage | object | 使用统计 |
| usage.prompt_tokens | integer | 输入token数 |
| usage.completion_tokens | integer | 生成token数 |
| usage.total_tokens | integer | 总token数 |

### 2. 文本补全接口

**接口地址**: `POST /v1/completions`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | text-davinci-003, gpt-3.5-turbo-instruct 等 | 模型名称 |
| prompt | string/array | 是 | - | 文本或数组 | 输入提示词 |
| max_tokens | integer | 否 | 16 | 1-32768 | 最大生成token数 |
| temperature | number | 否 | 1.0 | 0.0-2.0 | 随机性控制 |
| top_p | number | 否 | 1.0 | 0.1-1.0 | 核采样参数 |
| n | integer | 否 | 1 | 1-20 | 生成选择数量 |
| stream | boolean | 否 | false | true/false | 是否流式返回 |
| logprobs | integer | 否 | null | 0-5 | 返回对数概率 |
| echo | boolean | 否 | false | true/false | 是否回显提示词 |
| stop | array/string | 否 | null | 停止序列 | 停止标记 |
| presence_penalty | number | 否 | 0 | -2.0-2.0 | 重复惩罚 |
| frequency_penalty | number | 否 | 0 | -2.0-2.0 | 频率惩罚 |
| best_of | integer | 否 | 1 | 1-20 | 最佳选择数 |
| logit_bias | object | 否 | null | 偏置对象 | token偏置设置 |
| user | string | 否 | null | 用户标识 | 最终用户标识符 |

**请求示例**:
```json
{
  "model": "text-davinci-003",
  "prompt": "写一首关于春天的诗：",
  "max_tokens": 100,
  "temperature": 0.8
}
```

**响应示例**:
```json
{
  "id": "cmpl-unified-456",
  "object": "text_completion",
  "created": 1699000000,
  "model": "text-davinci-003",
  "choices": [
    {
      "text": "春天来了，万物复苏...",
      "index": 0,
      "logprobs": null,
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 25,
    "total_tokens": 35
  }
}
```

### 3. 文本嵌入接口

**接口地址**: `POST /v1/embeddings`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | text-embedding-3-large, text-embedding-ada-002 等 | 嵌入模型名称 |
| input | string/array | 是 | - | 文本或文本数组 | 要嵌入的文本 |
| encoding_format | string | 否 | float | float, base64 | 编码格式 |
| dimensions | integer | 否 | null | 1-3072 | 输出维度（部分模型支持） |
| user | string | 否 | null | 用户标识 | 最终用户标识符 |

**请求示例**:
```json
{
  "model": "text-embedding-3-large",
  "input": ["Hello world", "How are you?"],
  "encoding_format": "float"
}
```

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "object": "embedding",
      "index": 0,
      "embedding": [0.123, -0.456, 0.789, ...]
    },
    {
      "object": "embedding", 
      "index": 1,
      "embedding": [0.321, -0.654, 0.987, ...]
    }
  ],
  "model": "text-embedding-3-large",
  "usage": {
    "prompt_tokens": 8,
    "total_tokens": 8
  }
}
```

**响应参数说明**:
| 参数名 | 类型 | 说明 |
|--------|------|------|
| object | string | 固定值 "list" |
| data | array | 嵌入结果数组 |
| data[].object | string | 固定值 "embedding" |
| data[].index | integer | 输入文本索引 |
| data[].embedding | array | 嵌入向量（浮点数组） |
| model | string | 实际使用的模型 |
| usage | object | 使用统计 |

### 4. Claude Messages 接口

**接口地址**: `POST /v1/messages`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | claude-3-opus, claude-3-sonnet 等 | Claude模型名称 |
| messages | array | 是 | - | 消息数组 | 对话消息（不支持system role） |
| system | string | 否 | null | 文本 | 系统提示词 |
| max_tokens | integer | 是 | - | 1-200000 | 最大生成token数 |
| temperature | number | 否 | 1.0 | 0.0-1.0 | 随机性控制 |
| top_p | number | 否 | null | 0.0-1.0 | 核采样参数 |
| stream | boolean | 否 | false | true/false | 是否流式返回 |
| stop_sequences | array | 否 | null | 字符串数组 | 停止序列 |

**请求示例**:
```json
{
  "model": "claude-3-opus",
  "max_tokens": 1000,
  "messages": [
    {
      "role": "user",
      "content": "解释一下量子计算的基本原理"
    }
  ],
  "system": "你是一个物理学专家"
}
```

**响应格式**: 与聊天接口相同，但使用Claude原生格式转换为OpenAI兼容格式。

---

## 三、图像生成接口

### 1. 图像生成

**接口地址**: `POST /v1/images/generations`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | dall-e-3, midjourney-v6, flux-pro 等 | 图像生成模型 |
| prompt | string | 是 | - | 文本描述 | 图像描述提示词 |
| n | integer | 否 | 1 | 1-10 | 生成图像数量 |
| size | string | 否 | 1024x1024 | 256x256, 512x512, 1024x1024, 1792x1024, 1024x1792 等 | 图像尺寸 |
| quality | string | 否 | standard | standard, hd | 图像质量 |
| style | string | 否 | vivid | vivid, natural | 图像风格 |
| response_format | string | 否 | url | url, b64_json | 响应格式 |
| model_params | object | 否 | {} | 模型特定参数 | 模型特定配置 |
| callback_url | string | 否 | null | URL | 异步任务回调地址 |

**model_params 参数说明**:

对于 Midjourney 模型:
| 参数名 | 类型 | 可接受值 | 说明 |
|--------|------|----------|------|
| chaos | integer | 0-100 | 随机性程度 |
| stylize | integer | 0-1000 | 风格化程度 |
| weird | integer | 0-3000 | 奇异程度 |
| tile | boolean | true/false | 是否平铺 |
| version | string | 6, 6.1, 7 | Midjourney版本 |

对于 Flux 模型:
| 参数名 | 类型 | 可接受值 | 说明 |
|--------|------|----------|------|
| guidance_scale | number | 1.0-20.0 | 提示词遵循程度 |
| num_inference_steps | integer | 1-100 | 推理步数 |
| seed | integer | 正整数 | 随机种子 |

**请求示例**:
```json
{
  "model": "midjourney-v6",
  "prompt": "一只可爱的猫咪在阳光下睡觉",
  "n": 1,
  "size": "1024x1024",
  "quality": "hd",
  "model_params": {
    "chaos": 20,
    "stylize": 500,
    "version": "6.1"
  }
}
```

**响应示例（同步）**:
```json
{
  "id": "img-unified-123",
  "object": "image.generation",
  "created": 1699000000,
  "model": "midjourney-v6",
  "data": [
    {
      "url": "https://cdn.example.com/generated_image.png",
      "b64_json": null,
      "revised_prompt": "一只可爱的猫咪在阳光下睡觉 --v 6.1 --chaos 20 --stylize 500",
      "size": "1024x1024",
      "format": "png",
      "metadata": {
        "width": 1024,
        "height": 1024,
        "mime_type": "image/png",
        "file_size": 2048576
      }
    }
  ],
  "usage": {
    "images_generated": 1,
    "credits_used": 1,
    "compute_time_ms": 15000
  },
  "provider": {
    "name": "midjourney",
    "task_id": "mj_original_123456",
    "queue_position": null
  }
}
```

**响应示例（异步任务）**:
```json
{
  "id": "task-unified-123",
  "object": "image.generation.task",
  "created": 1699000000,
  "model": "midjourney-v6",
  "status": "pending",
  "progress": 0,
  "data": null,
  "task_info": {
    "type": "generation",
    "estimated_time": 60,
    "queue_position": 5,
    "can_cancel": true
  },
  "usage": {
    "credits_reserved": 1
  }
}
```

### 2. 图像编辑

**接口地址**: `POST /v1/images/edits`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| model | string | 是 | 支持图像编辑的模型 |
| image | file | 是 | 要编辑的图像文件 |
| mask | file | 否 | 蒙版图像文件 |
| prompt | string | 是 | 编辑描述 |
| n | integer | 否 | 生成数量 |
| size | string | 否 | 输出尺寸 |

---

## 四、音频处理接口

### 1. 语音转文字（STT）

**接口地址**: `POST /v1/audio/transcriptions`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | whisper-1, whisper-large-v3 等 | STT模型名称 |
| file | file | 是 | - | 音频文件 | 音频文件（mp3, wav, m4a等） |
| language | string | 否 | auto | ISO 639-1语言代码 | 音频语言 |
| prompt | string | 否 | null | 文本 | 转录指导文本 |
| response_format | string | 否 | json | json, text, srt, verbose_json, vtt | 响应格式 |
| temperature | number | 否 | 0 | 0.0-1.0 | 随机性控制 |

**请求示例**:
```bash
curl -X POST https://your-domain.com/v1/audio/transcriptions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.mp3" \
  -F "model=whisper-1" \
  -F "language=zh"
```

**响应示例**:
```json
{
  "id": "stt-unified-123",
  "object": "audio.transcription",
  "created": 1699000000,
  "model": "whisper-1",
  "text": "这是转录的文本内容",
  "language": "zh",
  "duration": 10.5,
  "segments": [
    {
      "id": 0,
      "text": "这是转录的文本内容",
      "start": 0.0,
      "end": 10.5,
      "confidence": 0.95
    }
  ],
  "usage": {
    "audio_seconds": 10.5,
    "credits_used": 0.1
  }
}
```

### 2. 文字转语音（TTS）

**接口地址**: `POST /v1/audio/speech`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | tts-1, tts-1-hd, elevenlabs-v2 等 | TTS模型名称 |
| input | string | 是 | - | 文本 | 要转换的文本（最大4096字符） |
| voice | string | 是 | - | alloy, echo, fable, onyx, nova, shimmer | 声音选择 |
| response_format | string | 否 | mp3 | mp3, opus, aac, flac | 音频格式 |
| speed | number | 否 | 1.0 | 0.25-4.0 | 播放速度 |

**请求示例**:
```json
{
  "model": "tts-1-hd",
  "input": "今天天气不错，适合出去走走。",
  "voice": "nova",
  "response_format": "mp3",
  "speed": 1.0
}
```

**响应**: 直接返回音频文件流，Content-Type为对应的音频MIME类型。

### 3. 音乐生成

**接口地址**: `POST /v1/audio/generations`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | suno-v3.5, suno-v4, udio-v1 等 | 音乐生成模型 |
| prompt | string | 是 | - | 文本描述 | 音乐描述提示词 |
| duration | integer | 否 | 30 | 15-300 | 音乐时长（秒） |
| format | string | 否 | mp3 | mp3, wav | 输出格式 |
| model_params | object | 否 | {} | 模型特定参数 | 模型配置 |
| callback_url | string | 否 | null | URL | 异步回调地址 |

**model_params 参数（Suno）**:
| 参数名 | 类型 | 可接受值 | 说明 |
|--------|------|----------|------|
| mode | string | inspiration, custom, extend | 生成模式 |
| lyrics | string | 文本 | 歌词内容 |
| title | string | 文本 | 歌曲标题 |
| tags | string | 音乐标签 | 音乐风格标签 |
| instrumental | boolean | true/false | 是否纯音乐 |
| continue_at | integer | 0-duration | 续写起始时间 |

**请求示例**:
```json
{
  "model": "suno-v3.5",
  "prompt": "一首轻松愉快的流行歌曲",
  "duration": 120,
  "model_params": {
    "mode": "custom",
    "lyrics": "阳光照进我的心房...",
    "title": "阳光心情",
    "tags": "pop, upbeat, chinese",
    "instrumental": false
  }
}
```

**响应示例（异步任务）**:
```json
{
  "id": "task-unified-789",
  "object": "audio.music.task",
  "created": 1699000000,
  "model": "suno-v3.5",
  "status": "pending",
  "progress": 0,
  "task_info": {
    "type": "generation",
    "mode": "custom",
    "estimated_time": 180,
    "queue_position": 3
  },
  "usage": {
    "credits_reserved": 2
  }
}
```

---

## 五、视频生成接口

### 1. 视频生成

**接口地址**: `POST /v1/videos/generations`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| model | string | 是 | - | sora, runway-gen3, luma-dream, kling-v2 等 | 视频生成模型 |
| prompt | string | 是 | - | 文本描述 | 视频描述提示词 |
| duration | integer | 否 | 5 | 3-10 | 视频时长（秒） |
| aspect_ratio | string | 否 | 16:9 | 16:9, 9:16, 1:1, 4:3 | 视频宽高比 |
| image | string | 否 | null | 图像URL或base64 | 图生视频的起始图像 |
| image_end | string | 否 | null | 图像URL或base64 | 结束图像（Luma支持） |
| quality | string | 否 | standard | standard, high | 生成质量 |
| fps | integer | 否 | 24 | 12-60 | 帧率 |
| model_params | object | 否 | {} | 模型特定参数 | 模型配置 |
| callback_url | string | 否 | null | URL | 异步回调地址 |

**model_params 参数（Runway）**:
| 参数名 | 类型 | 可接受值 | 说明 |
|--------|------|----------|------|
| style | string | cinematic, realistic, animated | 视频风格 |
| camera_motion | string | static, zoom_in, zoom_out, pan_left, pan_right | 镜头运动 |
| motion_strength | integer | 1-10 | 运动强度 |

**model_params 参数（可灵Kling）**:
| 参数名 | 类型 | 可接受值 | 说明 |
|--------|------|----------|------|
| mode | string | std, pro | 生成模式 |
| camera_control | object | 镜头控制对象 | 镜头运动控制 |

**请求示例**:
```json
{
  "model": "runway-gen3",
  "prompt": "一只猫咪在花园里追蝴蝶",
  "duration": 5,
  "aspect_ratio": "16:9",
  "quality": "high", 
  "model_params": {
    "style": "cinematic",
    "camera_motion": "zoom_in",
    "motion_strength": 7
  }
}
```

**响应示例（异步任务）**:
```json
{
  "id": "task-unified-999",
  "object": "video.generation.task",
  "created": 1699000000,
  "model": "runway-gen3",
  "status": "pending",
  "progress": 0,
  "task_info": {
    "type": "text2video",
    "duration": 5,
    "resolution": "1920x1080",
    "fps": 24,
    "estimated_time": 300,
    "queue_position": 8,
    "can_cancel": true
  },
  "usage": {
    "credits_reserved": 5
  }
}
```

**完成后响应**:
```json
{
  "id": "task-unified-999",
  "object": "video.generation.task",
  "created": 1699000000,
  "model": "runway-gen3",
  "status": "completed",
  "progress": 100,
  "data": [
    {
      "url": "https://cdn.example.com/video.mp4",
      "thumbnail": "https://cdn.example.com/thumb.jpg",
      "format": "mp4",
      "codec": "h264",
      "metadata": {
        "width": 1920,
        "height": 1080,
        "duration": 5.0,
        "fps": 24,
        "bitrate": "10Mbps",
        "file_size": 6291456
      }
    }
  ],
  "usage": {
    "duration_generated": 5,
    "credits_used": 5,
    "compute_time_ms": 295000
  }
}
```

---

## 六、任务管理接口

### 1. 查询任务状态

**接口地址**: `GET /v1/tasks/{task_id}`

**请求方法**: GET

**路径参数**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 任务ID |

**响应示例**:
```json
{
  "id": "task-unified-123",
  "object": "task",
  "created": 1699000000,
  "model": "midjourney-v6",
  "type": "image.generation",
  "status": "processing",
  "progress": 75,
  "data": null,
  "timestamps": {
    "created_at": "2024-01-01T00:00:00Z",
    "started_at": "2024-01-01T00:00:05Z",
    "completed_at": null
  },
  "usage": {
    "credits_reserved": 1
  }
}
```

### 2. 获取任务列表

**接口地址**: `GET /v1/tasks`

**请求方法**: GET

**查询参数**:
| 参数名 | 类型 | 必选 | 默认值 | 可接受值 | 说明 |
|--------|------|------|--------|----------|------|
| status | string | 否 | all | pending, processing, completed, failed, all | 任务状态过滤 |
| type | string | 否 | all | image.generation, video.generation, audio.generation, all | 任务类型过滤 |
| model | string | 否 | all | 模型名称 | 模型过滤 |
| limit | integer | 否 | 20 | 1-100 | 每页数量 |
| offset | integer | 否 | 0 | ≥0 | 偏移量 |
| order_by | string | 否 | created_at | created_at, updated_at, progress | 排序字段 |
| order | string | 否 | desc | asc, desc | 排序方向 |

**响应示例**:
```json
{
  "object": "list",
  "data": [
    {
      "id": "task-unified-123",
      "object": "task",
      "type": "image.generation",
      "status": "completed",
      "model": "midjourney-v6",
      "created": 1699000000
    }
  ],
  "has_more": true,
  "total": 150
}
```

### 3. 取消任务

**接口地址**: `DELETE /v1/tasks/{task_id}`

**请求方法**: DELETE

**路径参数**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| task_id | string | 是 | 要取消的任务ID |

**响应示例**:
```json
{
  "id": "task-unified-123",
  "object": "task.cancelled",
  "status": "cancelled",
  "message": "Task has been cancelled successfully"
}
```

### 4. 批量查询任务

**接口地址**: `POST /v1/tasks/batch`

**请求方法**: POST

**请求参数**:
| 参数名 | 类型 | 必选 | 说明 |
|--------|------|------|------|
| task_ids | array | 是 | 任务ID列表（最多50个） |

**请求示例**:
```json
{
  "task_ids": ["task-unified-123", "task-unified-456", "task-unified-789"]
}
```

**响应示例**:
```json
{
  "object": "batch.tasks",
  "data": [
    {
      "id": "task-unified-123",
      "status": "completed",
      "data": [...] 
    },
    {
      "id": "task-unified-456", 
      "status": "processing",
      "progress": 50
    }
  ],
  "requested": 3,
  "found": 3
}
```

---

## 七、实时通信接口

### 1. WebSocket 实时对话

**接口地址**: `GET /v1/realtime`

**协议**: WebSocket

**查询参数**:
| 参数名 | 类型 | 必选 | 可接受值 | 说明 |
|--------|------|------|----------|------|
| model | string | 是 | gpt-4o-realtime-preview 等 | 支持实时对话的模型 |

**连接示例**:
```
wss://your-domain.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01
```

**认证**: 通过HTTP Header传递Token，WebSocket握手时验证。

---

## 八、错误处理

### 错误响应格式
```json
{
  "error": {
    "code": "model_not_available",
    "message": "The model midjourney-v6 is currently unavailable",
    "type": "invalid_request_error",
    "param": "model",
    "details": {
      "reason": "queue_full",
      "retry_after": 60,
      "fallback_models": ["midjourney-v5", "flux-pro"]
    }
  }
}
```

### 常见错误代码
| 错误代码 | HTTP状态码 | 说明 |
|----------|------------|------|
| authentication_error | 401 | 认证失败 |
| invalid_request | 400 | 请求参数错误 |
| model_not_available | 400 | 模型不可用 |
| insufficient_quota | 402 | 配额不足 |
| rate_limit_exceeded | 429 | 超过速率限制 |
| server_error | 500 | 服务器内部错误 |

---

## 九、支持的模型列表

### 文本模型
- **OpenAI**: gpt-4o, gpt-4-turbo, gpt-3.5-turbo
- **Anthropic**: claude-3-opus, claude-3-sonnet, claude-3-haiku  
- **Google**: gemini-pro, gemini-pro-vision
- **阿里**: qwen-max, qwen-plus, qwen-turbo
- **百度**: ernie-4.0-turbo, ernie-3.5-turbo
- **字节**: doubao-pro, doubao-lite

### 图像模型
- **OpenAI**: dall-e-3, dall-e-2
- **Midjourney**: midjourney-v6, midjourney-v7
- **Flux**: flux-pro, flux-schnell, flux-kontext-pro
- **Stable Diffusion**: stable-diffusion-xl, stable-diffusion-3
- **Ideogram**: ideogram-v2

### 音频模型
- **STT**: whisper-1, whisper-large-v3
- **TTS**: tts-1, tts-1-hd, elevenlabs-v2
- **音乐**: suno-v3.5, suno-v4, udio-v1

### 视频模型
- **OpenAI**: sora
- **Google**: veo3, veo3-fast
- **Runway**: runway-gen2, runway-gen3
- **Luma**: luma-dream
- **可灵**: kling-v1, kling-v2
- **Pika**: pika-1.0

---

## 十、使用限制与计费

### 速率限制
- 默认：60请求/分钟
- 根据用户等级和模型类型动态调整
- 超限时返回429状态码

### 计费说明
- 基于积分制计费
- 不同模型消耗不同积分
- 异步任务创建时预扣费，完成后结算
- 失败任务退还积分

### 文件大小限制
- 音频文件：最大25MB
- 图像文件：最大20MB
- 支持格式详见各接口说明

---

## 十一、SDK示例

### Python (OpenAI库)
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://your-domain.com/v1"
)

# 文本生成
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "你好"}]
)

# 图像生成
response = client.images.generate(
    model="midjourney-v6",
    prompt="一只猫咪",
    size="1024x1024"
)

# 语音转文字
response = client.audio.transcriptions.create(
    model="whisper-1",
    file=open("audio.mp3", "rb")
)
```

### cURL 示例
```bash
# 文本生成
curl -X POST https://your-domain.com/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "你好"}],
    "max_tokens": 1000
  }'

# 图像生成
curl -X POST https://your-domain.com/v1/images/generations \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "midjourney-v6", 
    "prompt": "一只可爱的猫咪",
    "size": "1024x1024"
  }'
```

---

**文档版本**: v1.0  
**最后更新**: 2024-01-01  
**技术支持**: support@your-domain.com