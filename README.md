# Web-Crawler:2024腾讯校内实习项目

## 项目简介

通过爬虫快速爬取互联网上的性能优化相关文章，为中心快速沉淀性能优化数据，为后续训练私有LLM提供数据支持。

## 项目成员

- 宋凯帆、蔡锦浩

## 快速开始

### 环境变量

参考[wc.env.template](wc.env.template)，配置好Mysql相关的环境变量。
连接数据库后可输入id导入该文档后输入模型

### 运行项目

#### 本地运行

##### 环境准备

- Python 3.11

##### 安装依赖

```bash
pip install poetry
poetry install
playwright install
```

##### 运行代码
可供选择的有neo2.py中使用数据库中输入的
```bash
python main.py
```

参数说明:

- `init_page_id`: 可选，指定文章id开始爬取，在数据库为空的情况下进行指定，数据库不为空则不需要指定
- `max_page`: 可选，最大爬取文章数，默认不进行限制

#### Docker运行(推荐)

##### 拉取基础镜像

前往[Coding制品库](https://sztubdi.coding.net/p/ai-assistant/artifacts/23947142/docker/packages?hash=9ec50f4b491e46d59ba305cf9d2939fa)按照指引配置docker密钥

```bash
docker pull sztubdi-docker.pkg.coding.net/ai-assistant/web-crawler/web-crawler-base:v20240320
```

##### 构建镜像

```bash
docker build -f docker/Dockerfile -t web-crawler:latest .
```

##### 运行容器

```bash
docker run --env-file wc.env --network host web-crawler:latest  python main.py --_type "'keyword'" --max_keywords 1 --max_links_per_keyword 20 --indicated_keyword "'cpu性能'"
```

参数同上
