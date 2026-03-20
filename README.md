# PingPong AI

乒乓球击打动作识别系统。上传视频进行识别；
管理员登录后可标注新视频并训练模型。

## 功能
- 识别页 `/`：上传 MP4/AVI，返回动作、置信度、标准度评分、以及改进建议。
- 管理页 `/admin`（需登录）：
  - 管理员登录页 `/admin_login.html` 输入密码后写入 cookie `admin_auth`，登录一次有效 1 小时。
  - 标注 + 立即训练：上传视频选择标签，提取特征后训练并更新模型。
  - 重新全量训练：基于现有标注样本重新训练。
- 日志：启动与运行细节（训练、预测、错误）写入每次启动生成的日志文件。

## 文件目录结构
```
pingpong_ai/
├─ app/
│  ├─ main.py                 # FastAPI 入口、登录校验、配置
│  ├─ services/               # 特征提取、数据集、训练、推理、评分
│  ├─ models/                 # 模型与标签映射
│  ├─ data/                   # 上传临时文件与 user_annotations.json
│  └─ static/                 # 前端页面 index/admin/admin_login 与脚本
├─ logs/                      # 运行日志
├─ start.bat                  # 一键启动，自动生成日志文件
├─ requirements.txt
└─ README.md
```

## 运行环境
- Windows 10/11
- Python 3.11
- 依赖：FastAPI, Uvicorn, MediaPipe, OpenCV, scikit-learn 等（自动安装）

## 启动
```
start.bat
```
流程：
1) 生成时间戳日志文件 `logs/run-YYYYMMDD-HHMMSS.log`。
2) 创建/复用 `.venv`，安装依赖。
3) 启动 Uvicorn（端口 8000），日志写入日志文件。

## 使用步骤
- 使用：浏览器打开 http://127.0.0.1:8000 ，上传视频即可。
- 管理员训练：
  1) 打开 http://127.0.0.1:8000/admin ，先在登录页输入密码（默认 `admin123`，可用环境变量 `ADMIN_PASSWORD` 覆盖）。
  2) 进入训练面板后可上传视频选择标签并立即训练，或点击“重新全量训练”。
  3) 训练状态显示在页面；模型保存到 `app/models/pingpong_model.joblib`。

## 数据与特征
- 训练仅使用管理员标注的视频生成的 MediaPipe 关键点特征（mean+std）。
- 标注数据存储：`app/data/user_annotations.json`；标签映射：`app/models/label_map.json`（初始含常见动作，可随标注扩展）。

## 环境变量
- `ADMIN_PASSWORD`：管理员密码（默认 `admin123`）。
- `LOG_FILE_PATH`：自定义日志文件路径；若未设置，默认写入 `logs/app.log`，但 start.bat 会同时生成 run-*.log 并通过该变量覆盖。
