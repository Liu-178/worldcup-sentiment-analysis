# 世界杯多行业舆情热度分析项目

> 本科计算机课程期末大作业 | 2022卡塔尔 vs 2026美加墨世界杯五大行业舆情对比分析

---

## 📦 项目收到后的操作步骤

### 第一步：环境准备

```bash
# 1. 确保已安装 Python 3.8+ 和 pip
python --version

# 2. 进入项目目录
cd worldcup-sentiment-analysis

# 3. 安装依赖
pip install -r requirements.txt

# 4. 安装 SQL Server ODBC 驱动（如需使用数据库功能）
# Windows 通常已自带，如没有请从微软官网下载 ODBC Driver 17 for SQL Server
```

### 第二步：运行 Web 应用（查看数据）

```bash
# 进入 web 目录
cd web

# 启动 Flask 应用
python app.py
```

访问 **http://127.0.0.1:5000** 查看数据可视化结果。

### 第三步：（可选）更新数据

```bash
# 回到项目根目录
cd ..

# 运行一键更新脚本（爬虫 + 数据转换 + SQL导入）
python update_all.py
```

### 第四步：（可选）导入 SQL Server 数据库

```bash
# 1. 先在 SQL Server 中创建数据库
# 打开 SQL Server Management Studio，执行：
CREATE DATABASE worldcup_db;

# 2. 运行导入脚本
python analysis/import_to_sqlserver.py
```

---

## 📂 项目目录结构

```
worldcup-sentiment-analysis/
├── spider/                     # 爬虫代码目录
│   └── world_cup_spider.py     # 百度新闻爬虫
│
├── data/                       # 数据文件目录
│   ├── world_cup_news.csv      # 原始爬取数据（累积）
│   ├── merged_all.csv          # 转换后数据（供系统使用）
│   ├── industry_stats.csv      # 行业统计结果
│   ├── industry_comparison.csv # 两届对比数据
│   ├── timeline_stats.csv      # 时间序列统计
│   ├── daily_total.csv         # 每日热度汇总
│   └── word_freq_*.csv         # 词频数据
│
├── analysis/                   # 数据分析目录
│   ├── data_converter.py       # 数据转换模块
│   ├── industry_analysis.py    # 行业热度分析
│   ├── wordcloud_generator.py  # 词云生成模块
│   ├── word_freq_simple.py     # 词频统计
│   └── import_to_sqlserver.py  # SQL Server导入
│
├── web/                        # Web应用目录
│   ├── app.py                  # Flask主程序
│   ├── chat_api.py             # AI对话API
│   ├── static/                 # 静态资源
│   │   ├── css/                # 样式文件
│   │   ├── js/                 # ECharts脚本
│   │   └── images/             # 词云图片
│   └── templates/              # HTML模板
│       ├── index.html          # 首页
│       ├── compare.html        # 对比分析页
│       └── wordcloud.html      # 词云展示页
│
├── sql/                        # SQL脚本目录
│   ├── create_table.sql        # 建表语句
│   └── clean_duplicates.sql    # 清理重复数据
│
├── requirements.txt            # 依赖配置
├── update_all.py               # 一键更新脚本
└── readme.md                   # 项目说明
```

---

## 🚀 快速开始

### 1. 环境准备

```bash
# 创建虚拟环境（可选）
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 启动Web应用

```bash
cd web
python app.py
```

访问 http://127.0.0.1:5000 查看可视化结果。

---

## 📊 当前数据统计（截至2026/07/09）

### 总量统计
- 总数据量: **1593 条**
- 2022卡塔尔: **533 条**
- 2026美加墨: **1060 条**

### 各行业数据
| 行业 | 2022数量 | 2022占比 | 2026数量 | 2026占比 |
|------|----------|----------|----------|----------|
| 餐饮 | 136 | 25.52% | 283 | 26.7% |
| 旅游 | 102 | 19.14% | 236 | 22.26% |
| 体彩 | 113 | 21.2% | 218 | 20.57% |
| 零售 | 102 | 19.14% | 199 | 18.77% |
| 财经 | 80 | 15.01% | 124 | 11.7% |

---

## 🔧 技术栈

| 类别 | 技术 |
|:----:|:----:|
| 爬虫 | requests + BeautifulSoup |
| 数据处理 | pandas |
| 中文分词 | jieba |
| 词云生成 | wordcloud |
| Web框架 | Flask |
| 可视化 | ECharts |
| 数据库 | SQL Server（可选）|

---

## 💡 常见问题

### Q: 如何更新数据？
```bash
python update_all.py
```
脚本会自动执行：爬虫 → 数据转换 → SQL导入

### Q: 数据存在哪里？
- **CSV文件**: `data/` 目录下
- **SQL Server**: 本地实例的 `worldcup_db` 数据库（连接串见 `analysis/import_to_sqlserver.py`，按自己的实例名修改）

### Q: 如何只查看数据不运行爬虫？
直接运行 `python web/app.py` 启动Web应用即可查看现有数据。

### Q: 词频统计有省略号怎么办？
重新运行词频统计：
```bash
python analysis/word_freq_simple.py
```

---

## 作者信息

- 课程名称：计算机本科课程期末大作业
- 项目主题：世界杯多行业舆情热度分析
- 开发时间：2026年7月
