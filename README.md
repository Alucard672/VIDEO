# 视频搬运矩阵自动化系统

一个功能强大的多平台视频自动化处理与发布系统，支持抖音、小红书、哔哩哔哩、快手、YouTube等主流平台。

## 🌟 主要功能

### 核心功能
- **多平台账户管理** - 统一管理各平台账户信息
- **视频批量处理** - 自动化视频格式转换、压缩、剪辑
- **智能内容生成** - 集成AI生成视频标题、描述、标签
- **定时发布** - 支持定时和批量发布到多个平台
- **数据分析** - 实时监控发布效果和数据统计

### AI集成
- **OpenAI GPT** - 智能文案生成
- **Fliki** - AI语音合成
- **HeyGen** - AI视频生成
- **腾讯云** - 视频处理和存储

### 平台支持
- 🎵 抖音 (TikTok)
- 📖 小红书 (RedBook)
- 📺 哔哩哔哩 (Bilibili)
- ⚡ 快手 (Kuaishou)
- 🎬 YouTube

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite 3
- Redis (可选，用于任务队列)
- FFmpeg (可选，用于视频处理)

### 安装步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd video-auto-pipeline
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **启动系统**
```bash
python start.py
```

4. **访问系统**
- 打开浏览器访问: http://localhost:5000
- 默认账户: admin / admin123

## 📁 项目结构

```
video-auto-pipeline/
├── web_app.py              # Flask Web应用主文件
├── start.py                # 系统启动脚本
├── requirements.txt        # Python依赖包
├── README.md              # 项目说明文档
├── .env                   # 环境配置文件
├── data/                  # 数据存储目录
│   └── video_pipeline.db  # SQLite数据库
├── uploads/               # 上传文件目录
├── temp/                  # 临时文件目录
├── logs/                  # 日志文件目录
├── templates/             # HTML模板文件
│   ├── base.html         # 基础模板
│   ├── dashboard.html    # 仪表板
│   ├── videos.html       # 视频管理
│   ├── accounts.html     # 账户管理
│   ├── tasks.html        # 任务管理
│   ├── config.html       # 系统配置
│   └── monitoring.html   # 系统监控
├── static/               # 静态资源文件
│   ├── css/             # 样式文件
│   ├── js/              # JavaScript文件
│   └── images/          # 图片资源
├── 01_core/             # 核心功能模块
├── 02_platforms/        # 平台接口模块
├── 03_ai_services/      # AI服务模块
├── 04_video_processing/ # 视频处理模块
├── 05_scheduler/        # 任务调度模块
├── 06_database/         # 数据库模块
├── 07_api/             # API接口模块
├── 08_utils/           # 工具函数模块
├── 09_config/          # 配置管理模块
├── 10_analytics/       # 数据分析模块
└── 11_monitoring/      # 系统监控模块
```

## ⚙️ 配置说明

### 环境变量配置 (.env)

```env
# 数据库配置
DATABASE_URL=sqlite:///data/video_pipeline.db

# AI服务配置
OPENAI_API_KEY=your_openai_api_key_here
FLIKI_API_KEY=your_fliki_api_key_here
HEYGEN_API_KEY=your_heygen_api_key_here

# 腾讯云配置
TENCENT_SECRET_ID=your_secret_id_here
TENCENT_SECRET_KEY=your_secret_key_here
TENCENT_REGION=ap-beijing

# 系统配置
SECRET_KEY=your_secret_key_here
DEBUG=True
HOST=0.0.0.0
PORT=5000
```

### API密钥获取

1. **OpenAI API Key**
   - 访问: https://platform.openai.com/api-keys
   - 注册账户并创建API密钥

2. **Fliki API Key**
   - 访问: https://fliki.ai/
   - 注册账户并获取API密钥

3. **HeyGen API Key**
   - 访问: https://heygen.com/
   - 注册账户并获取API密钥

4. **腾讯云密钥**
   - 访问: https://console.cloud.tencent.com/cam/capi
   - 创建子账户并获取SecretId和SecretKey

## 📖 使用指南

### 1. 账户管理
- 在"账户管理"页面添加各平台账户信息
- 支持批量导入和测试账户连接状态
- 可设置账户的发布权限和限制

### 2. 视频管理
- 上传视频文件到系统
- 自动生成缩略图和视频信息
- 支持批量编辑视频属性

### 3. 任务管理
- 创建发布任务，选择目标平台和账户
- 设置定时发布时间
- 监控任务执行状态

### 4. 系统配置
- 配置AI服务参数
- 设置视频处理参数
- 管理系统通知设置

### 5. 数据分析
- 查看发布数据统计
- 分析各平台表现
- 生成数据报告

## 🔧 开发说明

### 技术栈
- **后端**: Python Flask
- **前端**: Bootstrap 5 + jQuery
- **数据库**: SQLite / MySQL / PostgreSQL
- **任务队列**: Celery + Redis
- **视频处理**: FFmpeg + OpenCV

### 扩展开发
1. **添加新平台支持**
   - 在 `02_platforms/` 目录下创建新的平台模块
   - 实现平台接口规范

2. **集成新的AI服务**
   - 在 `03_ai_services/` 目录下添加服务模块
   - 更新配置管理

3. **自定义视频处理**
   - 修改 `04_video_processing/` 模块
   - 添加新的处理算法

## 🐛 故障排除

### 常见问题

1. **启动失败**
   - 检查Python版本是否为3.8+
   - 确认所有依赖包已正确安装
   - 检查端口5000是否被占用

2. **数据库连接失败**
   - 确认data目录存在且有写入权限
   - 检查DATABASE_URL配置是否正确

3. **视频处理失败**
   - 确认FFmpeg已正确安装
   - 检查视频文件格式是否支持

4. **AI服务调用失败**
   - 验证API密钥是否正确
   - 检查网络连接和API配额

### 日志查看
- 系统日志位于 `logs/` 目录
- Web应用日志: `logs/web_app.log`
- 任务执行日志: `logs/tasks.log`
- 错误日志: `logs/error.log`

## 📄 许可证

本项目采用 MIT 许可证，详见 LICENSE 文件。

## 🤝 贡献

欢迎提交Issue和Pull Request来改进项目。

## 📞 支持

如有问题或建议，请通过以下方式联系：
- 提交GitHub Issue
- 发送邮件至: support@example.com

---

**注意**: 使用本系统时请遵守各平台的服务条款和相关法律法规。