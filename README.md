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
参数解释（content_ids）为数据库中文章代表id

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

#### 2种检索的不同选择

##### search1
利用问题抽取通过以下对所有实体节点进行检索得出相似度最高的两个节点后抽出后进行图结构检索
```bash
CALL db.index.fulltext.queryNodes('entity', $query, {limit:2}
```
运行获得测试集评分和结果
```bash
instance = Retriever
instance.test()
```


##### search2
利用问题抽取通过以下对所有实体节点进行检索得出相似度最高的两个节点后抽出后通过document中心节点进行拓扑结构抽取该节点代表的中心节点所组成小型整图
```bash
CALL db.index.fulltext.queryNodes('entity', $query, {limit:2}
```
可运行test直接得到测试集生成的cypher语句

```bash
instance = Retriever()
instance.test()
```

为适配qachain可使用schema_count获得相关token数量
```bash
instance = Retriever()
chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0), graph=graph, verbose=True, return_intermediate_steps=True
)
graph_schema=chain.graph_schema
instance.schema_count(graph_schema)
```



