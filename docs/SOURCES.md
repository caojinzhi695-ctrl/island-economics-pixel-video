# 来源、复用与使用说明

## 本项目内容

故事依据作者提供的《小岛经济学》读书笔记改编，不附带书中原文和插画。背景与六姿态人物由 AI 生成；不是抖音视频截图。人物动画由 Python/Pillow 绘制与变换，使用 FFmpeg 编码。

故事参考：Peter D. Schiff / Andrew J. Schiff, *How an Economy Grows and Why It Crashes*。
概念核对： [CORE Econ](https://books.core-econ.org/the-economy-v1/book/text/10.html)、[OpenStax](https://openstax.org/books/principles-macroeconomics-2e/pages/2-1-how-individuals-make-choices-based-on-their-budget-constraint)。

储蓄是当期产出未消费的部分；口粮支持生产期间生活，渔网是生产性资本品；投资有失败风险。物质财富可用资产减负债衡量，技能属于人力资本，并不等于随时可出售的资产。

## 工具与调查

- [edge-tts](https://github.com/rany2/edge-tts)，本地实际采用 7.3.1，源码调查固定提交 bd44c1d1aaebdc1db7f47456ee12431b42ec7cac。原生支持中文、语速等配置；本项目增加逐句时长与镜头匹配。上游代码 LGPLv3，srt_composer.py 为 MIT；通过 pip 安装，未把上游源码改换许可证。它是微软在线语音服务客户端，代码许可与服务使用条件独立。
- [CosyVoice](https://github.com/QwenAudio/CosyVoice)：比较过官方文档，需下载模型和推理环境，本次未安装、未实测。
- [vibe-knowledge-film](https://github.com/HeyChengC/vibe-knowledge-film)：参考分镜流程，未复制其视频素材。
- [vibe-knowledge-video-skill](https://github.com/LuZhong-Li/vibe-knowledge-video-skill)：调查过规范，未作为本项目引擎。
- [vibe-knowledge](https://github.com/worlds3/vibe-knowledge)：本地初稿曾使用示例音源做节奏研究；未确认音乐授权，因此本仓库不包含原音乐、混音 WAV 或带该音乐的视频。仅保留时间点检测数据。

本次优先复用已有本地渲染管线，未引入大型视频框架或本地 TTS 模型。依赖版本见 requirements.txt；未上传任何登录凭据、字体文件或全局配置。

本仓库未新设整体开源许可证。公开访问和下载不自动等同于获得所有素材的再分发、商用或衍生授权；如需相关授权，请联系仓库维护者。各第三方工具继续遵循自身许可。
