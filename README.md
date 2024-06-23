# graph_rag:2024腾讯校内实习项目

## 项目简介
利用web-clawer爬取数据进行图形生成
通过使用实验性LLMGraphTransformer生成知识图谱，并设有两种混合检索方式。

## 项目成员

- 宋凯帆、蔡锦浩

## 快速开始

### 环境变量
参考[env_template.env]
配置好Mysql，openai，neo4j相关的环境变量。
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
可供选择的有neo2.py中使用数据库中输入的文章代码
//content_ids = input("Input the IDs of the content (separate IDs by space): ").strip().split()
```bash
python neo2.py
```
构建知识图谱后的检索：
1，
```bash
python search1.py
```
2，
```bash
python search2.py
```

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
