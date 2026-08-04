[**高级选项**](./introduction.md) > **翻译服务文档** _(当前)_

---

> **范围说明：** 本页是官方 [`pdf2zh-next` 翻译服务文档](https://github.com/PDFMathTranslate-next/PDFMathTranslate-next) 的参考文档，不是 GBabelDocUI Web UI 文档。GBabelDocUI Web UI 请参阅 [`USAGE_webui.md`](../getting-started/USAGE_webui.md) 和 Docker 部署说明。不要把 `pdf2zh_next` 替换为 `gbabeldocui`，因为两者的命令行参数不兼容。

### 通过命令行查看可用的翻译服务

您可以通过在命令行中打印帮助信息来确认可用的翻译服务及其使用方法。

```bash
pdf2zh_next -h
```

optional arguments:
  -h, --help            show this help message and exit
  -t TRANSLATE_SERVICE, --translate-service TRANSLATE_SERVICE
                        Translation service to use. (default: openai)
  -m TRANSLATE_MODEL, --translate-model TRANSLATE_MODEL
                        Model to use for the translation service. (default: gpt-4o)
  -k TRANSLATE_API_KEY, --translate-api-key TRANSLATE_API_KEY
                        API key for the translation service. (default: None)
  -b TRANSLATE_BASE_URL, --translate-base-url TRANSLATE_BASE_URL
                        Base URL for the translation service. (default: None)
  -l TARGET_LANGUAGE, --target-language TARGET_LANGUAGE
                        Target language for translation. (default: zh-CN)
  -s SOURCE_LANGUAGE, --source-language SOURCE_LANGUAGE
                        Source language of the document. If not specified, the language will be auto-detected. (default: None)
  -c, --copy            Copy the translated text to the clipboard. (default: False)
  --no-cache            Disable caching of translation results. (default: False)
  --cache-dir CACHE_DIR
                        Directory to store translation cache. (default: ~/.cache/pdf2zh)
  --no-split            Disable splitting of the document into chunks. (default: False)
  --split-size SPLIT_SIZE
                        Size of each chunk when splitting the document. (default: 4096)
  --split-overlap SPLIT_OVERLAP
                        Overlap size between chunks when splitting the document. (default: 512)
  --split-method {token,char}
                        Method to split the document. (default: token)
  --no-translate        Skip translation and only extract text from the PDF. (default: False)
  --no-save             Do not save the translated document. (default: False)
  --output OUTPUT       Output file path for the translated document. If not specified, the output file will be saved in the same directory as the input file with the suffix '_translated'. (default: None)
  --output-format {markdown,html,pdf}
                        Output format for the translated document. (default: markdown)
  --model MODEL         Model to use for the translation service. (default: gpt-4o)

Translation Services:
  openai                OpenAI API (default)
  gemini                Google Gemini API
  aliyun                Aliyun Tongyi Qianwen API
  siliconflow           SiliconFlow API
  ollama                Ollama API
  groq                  Groq API

For more information on translation services, visit: ./Documentation-of-Translation-Services.md
```

---

### OUTPUT

在帮助信息的末尾，你可以查看关于不同翻译服务的详细信息。

```
可选参数：
  -h, --help            显示此帮助信息并退出
  -t TRANSLATE_SERVICE, --translate-service TRANSLATE_SERVICE
                        要使用的翻译服务。（默认值：openai）
  -m TRANSLATE_MODEL, --translate-model TRANSLATE_MODEL
                        翻译服务要使用的模型。（默认值：gpt-4o）
  -k TRANSLATE_API_KEY, --translate-api-key TRANSLATE_API_KEY
                        翻译服务的 API 密钥。（默认值：None）
  -b TRANSLATE_BASE_URL, --translate-base-url TRANSLATE_BASE_URL
                        翻译服务的基础 URL。（默认值：None）
  -l TARGET_LANGUAGE, --target-language TARGET_LANGUAGE
                        翻译的目标语言。（默认值：zh-CN）
  -s SOURCE_LANGUAGE, --source-language SOURCE_LANGUAGE
                        文档的源语言。如果未指定，将自动检测语言。（默认值：None）
  -c, --copy            将翻译后的文本复制到剪贴板。（默认值：False）
  --no-cache            禁用翻译结果的缓存。（默认值：False）
  --cache-dir CACHE_DIR
                        存储翻译缓存的目录。（默认值：~/.cache/pdf2zh）
  --no-split            禁用将文档分割成块。（默认值：False）
  --split-size SPLIT_SIZE
                        分割文档时每个块的大小。（默认值：4096）
  --split-overlap SPLIT_OVERLAP
                        分割文档时块之间的重叠大小。（默认值：512）
  --split-method {token,char}
                        分割文档的方法。（默认值：token）
  --no-translate        跳过翻译，仅从 PDF 中提取文本。（默认值：False）
  --no-save             不保存翻译后的文档。（默认值：False）
  --output OUTPUT       翻译后文档的输出文件路径。如果未指定，输出文件将保存在与输入文件相同的目录中，并带有 '_translated' 后缀。（默认值：None）
  --output-format {markdown,html,pdf}
                        翻译后文档的输出格式。（默认值：markdown）
  --model MODEL         翻译服务要使用的模型。（默认值：gpt-4o）

翻译服务：
  openai                OpenAI API（默认）
  gemini                Google Gemini API
  aliyun                阿里云通义千问 API
  siliconflow           SiliconFlow API
  ollama                Ollama API
  groq                  Groq API

有关翻译服务的更多信息，请访问：./Documentation-of-Translation-Services.md


---

This project supports multiple translation engines. For detailed information on each engine, please refer to the [Documentation of Translation Services](./Documentation-of-Translation-Services.md).

The following table lists the supported engines and their status:

| Engine | Status | Note |
| ------ | ------ | ---- |
| Aliyun | ✅ | |
| SiliconFlow | ✅ | |
| OpenAI | ✅ | |
| Google | ✅ | |
| Azure | ✅ | |
| Baidu | ✅ | |
| DeepSeek | ✅ | |
| DeepL | ✅ | |
| Youdao | ✅ | |
| Tencent | ✅ | |
| Yandex | ✅ | |
- ✅: Supported
- 🚧: Under Development
- ❌: Unsupported
- ⚠️: Not Recommended

---

### TRANSLATION RESULT

- [**OpenAI**](https://platform.openai.com/docs/guides/vision) - **Recommended** for its superior translation quality. However, it requires an API key and may incur costs.
- [**Gemini**](https://ai.google.dev/gemini-api/docs/vision) - Offers a free tier and is also a good choice.

#### Tier 2 (Community Supported)
- [**Aliyun**](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api) - Supports Chinese and English, with a free tier.
- [**SiliconFlow**](https://siliconflow.cn/) - Supports Chinese and English, with a free tier.

#### Tier 3 (Self-Deployable)
- [**llava**](https://llava-vl.github.io/) - Open-source, can be self-deployed, but requires technical expertise.
- [**qwen-vl**](https://huggingface.co/Qwen/Qwen-VL) - Open-source, can be self-deployed, but requires technical expertise.
- [**InternLM-XComposer**](https://github.com/internlm/InternLM-XComposer) - Open-source, can be self-deployed, but requires technical expertise.

---

### TRANSLATION RESULT

#### 第一梯队（官方支持）
- [**OpenAI**](https://platform.openai.com/docs/guides/vision) - **推荐**，因其卓越的翻译质量。但需要 API 密钥并可能产生费用。
- [**Gemini**](https://ai.google.dev/gemini-api/docs/vision) - 提供免费额度，也是一个不错的选择。

#### 第二梯队（社区支持）
- [**Aliyun**](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api) - 支持中文和英文，提供免费额度。
- [**SiliconFlow**](https://siliconflow.cn/) - 支持中文和英文，提供免费额度。

#### 第三梯队（可自行部署）
- [**llava**](https://llava-vl.github.io/) - 开源，可自行部署，但需要技术专长。
- [**qwen-vl**](https://huggingface.co/Qwen/Qwen-VL) - 开源，可自行部署，但需要技术专长。
- [**InternLM-XComposer**](https://github.com/internlm/InternLM-XComposer) - 开源，可自行部署，但需要技术专长。

- `"openai"`
- `"gemini"`

**Tier 2 translation engines** are engines that the maintainers consider to be of good quality and are willing to fix if they break. However, since the maintainers do not use them regularly, the response time for fixes may be slower compared to Tier 1 engines. Additionally, if an engine frequently breaks and requires excessive maintenance, it may be downgraded to Tier 3 or removed.

Currently supported Tier 2 translation engines include:

- `"aliyun"`
- `"siliconflow"`

**Tier 3 translation engines** are engines that are either deprecated, have limited support, or are not recommended for use. The maintainers do not guarantee their stability and may not fix issues promptly. If you encounter problems with these engines, you are encouraged to submit a pull request to fix them.

Currently supported Tier 3 translation engines include:

- `"ollama"`
- `"groq"`

---

### OUTPUT

**第一梯队翻译引擎**由项目维护者直接维护。尽管维护者**不经常使用此项目**，但他们会依赖 GitHub 问题来识别问题。当这些引擎中的任何一个遇到问题时，维护者会尽快修复它们，以确保稳定性和可靠性。


当前支持的第一梯队翻译引擎包括：

- `"openai"`
- `"gemini"`

**第二梯队翻译引擎**是维护者认为质量良好且愿意在出现问题时修复的引擎。然而，由于维护者不经常使用它们，修复的响应时间可能比第一梯队引擎慢。此外，如果某个引擎频繁出现问题且需要过多维护，它可能会被降级到第三梯队或移除。

当前支持的第二梯队翻译引擎包括：

- `"aliyun"`
- `"siliconflow"`

**第三梯队翻译引擎**是已弃用、支持有限或不推荐使用的引擎。维护者不保证其稳定性，并且可能不会及时修复问题。如果您在使用这些引擎时遇到问题，鼓励您提交拉取请求来修复它们。

当前支持的第三梯队翻译引擎包括：

- `"ollama"`
- `"groq"`
8. Azure
9. Google
10. Baidu
11. DeepL
12. Youdao
13. Tencent
14. Yandex
15. Ollama
16. Groq
17. Sugoi
18. SugoiUniversal
19. M2M100
20. M2M100_1_2B
21. M2M100_418M
22. M2M100_12B
23. M2M100_AVG
24. M2M100_AVG_12B
25. Alibaba
26. Argos
27. Caiyun
28. ModernMT
29. MyMemory
30. Naver
31. Papago
32. QQ
33. Reverso
34. Sogou

---

### OUTPUT

1. SiliconFlowFree
2. OpenAI
3. AliyunDashScope
4. DeepSeek
5. SiliconFlow
6. Zhipu
7. OpenAICompatible
8. Azure
9. Google
10. Baidu
11. DeepL
12. Youdao
13. Tencent
14. Yandex
15. Ollama
16. Groq
17. Sugoi
18. SugoiUniversal
19. M2M100
20. M2M100_1_2B
21. M2M100_418M
22. M2M100_12B
23. M2M100_AVG
24. M2M100_AVG_12B
25. Alibaba
26. Argos
27. Caiyun
28. ModernMT
29. MyMemory
30. Naver
31. Papago
32. QQ
33. Reverso
34. Sogou

- [Aliyun](https://dashscope.aliyun.com/)
- [SiliconFlow](https://siliconflow.cn/)

#### Tier 3 (Limited Support)
- [Ollama](https://ollama.ai/)
- [Groq](https://groq.com/)

---

### OUTPUT LANGUAGE

zh

- #### Tier 1 (Official Support): - [**OpenAI**](https://platform.openai.com/docs/guides/vision) - **Recommended** for its superior translation quality. However, it requires an API key and may incur costs.
- [**Gemini**](https://ai.google.dev/gemini-api/docs/vision) - Offers a free tier and is also a good choice.

#### Tier 2 (Community Supported)
- [**Aliyun**](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api) - Supports Chinese and English, with a free tier.
- [**SiliconFlow**](https://siliconflow.cn/) - Supports Chinese and English, with a free tier.

#### Tier 3 (Self-Deployable)
- [**llava**](https://llava-vl.github.io/) - Open-source, can be self-deployed, but requires technical expertise.
- [**qwen-vl**](https://huggingface.co/Qwen/Qwen-VL) - Open-source, can be self-deployed, but requires technical expertise.
- [**InternLM-XComposer**](https://github.com/internlm/InternLM-XComposer) - Open-source, can be self-deployed, but requires technical expertise.

---

### OUTPUT

**第二梯队翻译引擎**由社区维护和支持。  
当这些引擎遇到问题时，项目维护者不会直接提供修复，而是会将相关问题标记为 `help wanted`，并欢迎贡献者提交拉取请求来帮助解决。

所有程序支持但未明确列在第一梯队下的引擎均被视为第二梯队翻译引擎。
- #### 第一梯队（官方支持）： - [**OpenAI**](https://platform.openai.com/docs/guides/vision) - **推荐**，因其卓越的翻译质量。但需要 API 密钥并可能产生费用。
- [**Gemini**](https://ai.google.dev/gemini-api/docs/vision) - 提供免费额度，也是一个不错的选择。

#### 第二梯队（社区支持）
- [**Aliyun**](https://help.aliyun.com/zh/dashscope/developer-reference/tongyi-qianwen-vl-plus-api) - 支持中文和英文，提供免费额度。
- [**SiliconFlow**](https://siliconflow.cn/) - 支持中文和英文，提供免费额度。

#### 第三梯队（可自行部署）
- [**llava**](https://llava-vl.github.io/) - 开源，可自行部署，但需要技术专长。
- [**qwen-vl**](https://huggingface.co/Qwen/Qwen-VL) - 开源，可自行部署，但需要技术专长。
- [**InternLM-XComposer**](https://github.com/internlm/InternLM-XComposer) - 开源，可自行部署，但需要技术专长。

- `"sugoi"`: Deprecated. Use `"sugoi-universal"` instead.
- `"m2m100"`: Deprecated. Use `"m2m100-1.2b"` instead.
- `"m2m100-418m"`: Deprecated. Use `"m2m100-1.2b"` instead.
- `"m2m100-12b"`: Deprecated. Use `"m2m100-1.2b"` instead.
- `"m2m100-avg"`: Deprecated. Use `"m2m100-1.2b"` instead.
- `"m2m100-avg-12b"`: Deprecated. Use `"m2m100-1.2b"` instead.

#### Removed Engines

These engines have been removed from the repository due to various reasons:

- `"alibaba"`: Removed due to API changes.
- `"argos"`: Removed due to API changes.
- `"baidu"`: Removed due to API changes.
- `"caiyun"`: Removed due to API changes.
- `"deepl"`: Removed due to API changes.
- `"google"`: Removed due to API changes.
- `"microsoft"`: Removed due to API changes.
- `"modernmt"`: Removed due to API changes.
- `"myMemory"`: Removed due to API changes.
- `"naver"`: Removed due to API changes.
- `"papago"`: Removed due to API changes.
- `"qq"`: Removed due to API changes.
- `"reverso"`: Removed due to API changes.
- `"sogou"`: Removed due to API changes.
- `"tencent"`: Removed due to API changes.
- `"yandex"`: Removed due to API changes.
- `"youdao"`: Removed due to API changes.

---

### OUTPUT

#### 已弃用的引擎
- `"sugoi"`: 已弃用。请改用 `"sugoi-universal"`。
- `"m2m100"`: 已弃用。请改用 `"m2m100-1.2b"`。
- `"m2m100-418m"`: 已弃用。请改用 `"m2m100-1.2b"`。
- `"m2m100-12b"`: 已弃用。请改用 `"m2m100-1.2b"`。
- `"m2m100-avg"`: 已弃用。请改用 `"m2m100-1.2b"`。
- `"m2m100-avg-12b"`: 已弃用。请改用 `"m2m100-1.2b"`。

#### 已移除的引擎

这些引擎由于各种原因已从仓库中移除：

- `"alibaba"`: 因 API 变更而移除。
- `"argos"`: 因 API 变更而移除。
- `"baidu"`: 因 API 变更而移除。
- `"caiyun"`: 因 API 变更而移除。
- `"deepl"`: 因 API 变更而移除。
- `"google"`: 因 API 变更而移除。
- `"microsoft"`: 因 API 变更而移除。
- `"modernmt"`: 因 API 变更而移除。
- `"myMemory"`: 因 API 变更而移除。
- `"naver"`: 因 API 变更而移除。
- `"papago"`: 因 API 变更而移除。
- `"qq"`: 因 API 变更而移除。
- `"reverso"`: 因 API 变更而移除。
- `"sogou"`: 因 API 变更而移除。
- `"tencent"`: 因 API 变更而移除。
- `"yandex"`: 因 API 变更而移除。
- `"youdao"`: 因 API 变更而移除。

- [x] `"sugoi"`: Deprecated. Use `"sugoi-universal"` instead.
- [x] `"m2m100"`: Deprecated. Use `"m2m100-1.2b"` instead.
- [x] `"m2m100-418m"`: Deprecated. Use `"m2m100-1.2b"` instead.
- [x] `"m2m100-12b"`: Deprecated. Use `"m2m100-1.2b"` instead.
- [x] `"m2m100-avg"`: Deprecated. Use `"m2m100-1.2b"` instead.
- [x] `"m2m100-avg-12b"`: Deprecated. Use `"m2m100-1.2b"` instead.

The following translation engines have been **removed** from the repository due to various reasons (e.g., API changes, service discontinuation, etc.):
- [x] `"alibaba"`: Removed due to API changes.
- [x] `"argos"`: Removed due to API changes.
- [x] `"baidu"`: Removed due to API changes.
- [x] `"caiyun"`: Removed due to API changes.
- [x] `"deepl"`: Removed due to API changes.
- [x] `"google"`: Removed due to API changes.
- [x] `"microsoft"`: Removed due to API changes.
- [x] `"modernmt"`: Removed due to API changes.
- [x] `"myMemory"`: Removed due to API changes.
- [x] `"naver"`: Removed due to API changes.
- [x] `"papago"`: Removed due to API changes.
- [x] `"qq"`: Removed due to API changes.
- [x] `"reverso"`: Removed due to API changes.
- [x] `"sogou"`: Removed due to API changes.
- [x] `"tencent"`: Removed due to API changes.
- [x] `"yandex"`: Removed due to API changes.
- [x] `"youdao"`: Removed due to API changes.

---

### OUTPUT

以下翻译引擎已被**弃用**，将不再维护或支持：
- [x] `"sugoi"`: 已弃用。请改用 `"sugoi-universal"`。
- [x] `"m2m100"`: 已弃用。请改用 `"m2m100-1.2b"`。
- [x] `"m2m100-418m"`: 已弃用。请改用 `"m2m100-1.2b"`。
- [x] `"m2m100-12b"`: 已弃用。请改用 `"m2m100-1.2b"`。
- [x] `"m2m100-avg"`: 已弃用。请改用 `"m2m100-1.2b"`。
- [x] `"m2m100-avg-12b"`: 已弃用。请改用 `"m2m100-1.2b"`。

以下翻译引擎由于各种原因（例如 API 变更、服务终止等）已从仓库中**移除**：
- [x] `"alibaba"`: 因 API 变更而移除。
- [x] `"argos"`: 因 API 变更而移除。
- [x] `"baidu"`: 因 API 变更而移除。
- [x] `"caiyun"`: 因 API 变更而移除。
- [x] `"deepl"`: 因 API 变更而移除。
- [x] `"google"`: 因 API 变更而移除。
- [x] `"microsoft"`: 因 API 变更而移除。
- [x] `"modernmt"`: 因 API 变更而移除。
- [x] `"myMemory"`: 因 API 变更而移除。
- [x] `"naver"`: 因 API 变更而移除。
- [x] `"papago"`: 因 API 变更而移除。
- [x] `"qq"`: 因 API 变更而移除。
- [x] `"reverso"`: 因 API 变更而移除。
- [x] `"sogou"`: 因 API 变更而移除。
- [x] `"tencent"`: 因 API 变更而移除。
- [x] `"yandex"`: 因 API 变更而移除。
- [x] `"youdao"`: 因 API 变更而移除。

3. DeepL
4. OpenAI
5. Yandex
6. YouDao
7. Baidu
8. Tencent
9. AliYun
10. SiliconFlow
11. Azure
12. DeepSeek
13. Gemini
14. `argos`
15. `m2m100`
16. `m2m100-1.2b`
17. `m2m100-418m`
18. `m2m100-12b`
19. `m2m100-avg`
20. `m2m100-avg-12b`
21. `sugoi`
22. `sugoi-universal`
23. `alibaba`
24. `caiyun`
25. `microsoft`
26. `modernmt`
27. `myMemory`
28. `naver`
29. `papago`
30. `qq`
31. `reverso`
32. `sogou`
33. `yandex`
34. `youdao`
35. `llava`
36. `qwen-vl`
37. `InternLM-XComposer`
38. `ollama`
39. `groq`

---

### TRANSLATION RESULT

1. Bing
2. Google
3. DeepL
4. OpenAI
5. Yandex
6. YouDao
7. Baidu
8. Tencent
9. AliYun
10. SiliconFlow
11. Azure
12. DeepSeek
13. Gemini
14. `argos`
15. `m2m100`
16. `m2m100-1.2b`
17. `m2m100-418m`
18. `m2m100-12b`
19. `m2m100-avg`
20. `m2m100-avg-12b`
21. `sugoi`
22. `sugoi-universal`
23. `alibaba`
24. `caiyun`
25. `microsoft`
26. `modernmt`
27. `myMemory`
28. `naver`
29. `papago`
30. `qq`
31. `reverso`
32. `sogou`
33. `yandex`
34. `youdao`
35. `llava`
36. `qwen-vl`
37. `InternLM-XComposer`
38. `ollama`
39. `groq`

<div align="right"> 
<h6><small>本页面的部分内容由 GPT 翻译，可能包含错误。</small></h6>