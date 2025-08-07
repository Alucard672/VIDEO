视频搬运矩阵自动化系统 —— 文件结构与开发任务清单
一、项目目录结构
bash
复制
编辑
video-auto-pipeline/
│
├── 01_content_fetch/         # 内容采集模块
│    └── fetch_news.py
│    └── fetch_videos.py
│
├── 02_script_gen/            # 脚本生成模块
│    └── generate_script.py
│
├── 03_tts/                   # AI配音模块
│    └── tts_generate.py
│
├── 04_video_edit/            # 视频剪辑与合成模块
│    └── edit_merge.py
│
├── 05_thumbnail/             # 封面生成模块
│    └── thumbnail_gen.py
│
├── 06_account_manager/       # 账号管理模块
│    └── account_db.py
│    └── login_handler.py
│    └── account_monitor.py
│
├── 07_uploader/              # 自动上传模块
│    └── upload_douyin.py
│    └── upload_bilibili.py
│
├── 08_content_review/        # 内容审核模块
│    └── content_review.py
│
├── 09_scheduler/             # 发布调度与轮播模块
│    └── scheduler.py
│
├── config.py                 # 项目配置文件
├── requirements.txt          # Python依赖
└── run_pipeline.py           # 一键执行主程序
二、模块开发任务清单
01_content_fetch（内容采集）
脚本	功能	开发任务
fetch_news.py	爬取/调用新闻API获取实时资讯	- 网易/新浪/凤凰网API调用或爬虫编写
- 支持按关键词筛选、时间过滤
fetch_videos.py	YouTube/TikTok热点视频采集	- yt-dlp命令封装
- 视频时长、标题关键词过滤下载

02_script_gen（脚本生成）
脚本	功能	开发任务
generate_script.py	生成中文解说文案	- 调用OpenAI API生成文案
- 支持自动插入“个人观点”模板
- 文案存储成txt/json格式

03_tts（AI配音）
脚本	功能	开发任务
tts_generate.py	文案转AI配音	- 接入Fliki/Heygen API生成mp3
- 支持不同音色选择
- 音频文件输出到/audio目录

04_video_edit（视频剪辑合成）
脚本	功能	开发任务
edit_merge.py	视频剪辑、合成配音、加字幕	- 封装FFmpeg裁剪、合成音轨
- 自动添加字幕（可调用自动识别API）
- 添加开头LOGO、转场特效

05_thumbnail（封面生成）
脚本	功能	开发任务
thumbnail_gen.py	生成视频封面	- DALL·E或Midjourney生成插画背景
- Canva API或Pillow批量添加标题、LOGO

06_account_manager（账号管理）
脚本	功能	开发任务
account_db.py	账号信息加密存储与管理	- 使用SQLite数据库存储账号信息
- 加密账号密码、Token/Cookie
- 提供增删改查接口
login_handler.py	自动登录与Cookie加载	- 用Selenium加载账号Cookie快速登录
- 模拟人工登录（可选）
account_monitor.py	账号状态监控与异常提醒	- 登录状态检测（抓取主页检查）
- 异常推送微信/邮箱提醒

07_uploader（自动上传）
脚本	功能	开发任务
upload_douyin.py	自动上传到抖音/西瓜	- 接入巨量百应API或用Selenium自动上传
- 自动填写标题、封面、标签
upload_bilibili.py	自动上传到B站	- 模拟登录或调用B站CMS接口
- 支持多账号轮播上传

08_content_review（内容审核）
脚本	功能	开发任务
content_review.py	文案与视频内容审核	- 接入腾讯云/阿里云内容安全API
- 文案敏感词检测，视频画面合规检测

09_scheduler（发布调度与轮播）
脚本	功能	开发任务
scheduler.py	多账号发布调度	- 账号轮播发布策略（发布间隔、冷却时间）
- 定时发布（schedule库实现）

run_pipeline.py（一键启动主程序）
功能	开发任务
串联所有模块流程	- 按顺序执行采集 → 文案 → 配音 → 剪辑 → 审核 → 上传
- 加入命令行参数，支持选择执行哪些模块
- 运行日志输出

三、加分项（后续可做）
模块	功能
Web管理后台	使用Flask+Vue做一个账号、任务、数据监控后台
内容爆款分析	自动统计视频效果数据，输出爆款选题推荐
账号风控模块	加入IP代理、设备指纹、自动化行为优化策略

四、开发优先级建议
内容采集 → 脚本生成 → 配音 → 剪辑合成（核心流水线）

账号管理 → 自动上传 → 发布调度（矩阵管理）

内容审核模块（上线前确保合规）

数据监控/爆款分析（后期优化）

Web后台与风控模块（进阶扩展）
