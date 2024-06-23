
from config import(
    NEO4J_URI,
    NEO4J_PASSWORD,
    NEO4J_USERNAME,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    DATABASE,
)
from sqlalchemy.orm import sessionmaker
from langchain_core.documents import Document
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
import re
from loguru import logger
from neo4j import GraphDatabase
from sqlalchemy import create_engine
from contextlib import contextmanager
from models.passage import Passage
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_community.graphs import Neo4jGraph
from langchain_text_splitters import CharacterTextSplitter

api_key=OPENAI_API_KEY
api_url=OPENAI_API_BASE

graph=Neo4jGraph()

engine = create_engine(DATABASE, echo=True)
Session = sessionmaker(bind=engine)

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

def delete_all_nodes():
    with neo4j_driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")
        

llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)


@contextmanager
def scoped_session():
        db_session = Session()
        try:
            yield db_session
        finally:
            db_session.close() 

content_ids = input("Input the IDs of the content (separate IDs by space): ").strip().split()
print(content_ids)
contents = []
with scoped_session() as conn:
    for content_id in content_ids:
        result = conn.query(Passage.content).offset(int(content_id) - 1).limit(1).all()
        content = result[0][0] if result else None
        if content:
            contents.append(content)
contents_str="\n".join(contents)


llm_transformer_filtered = LLMGraphTransformer(   
    llm=llm,
    node_properties=["Description"]
)
# 设置抽取模型


def extract_code_blocks(markdown_text):
    code_blocks = re.findall(r'```(.*?)```', markdown_text, re.DOTALL)
    return code_blocks

# 分割markdown格式的代码

contents_str="\n".join(contents)
contents=contents+extract_code_blocks(contents_str)
logger.debug(contents)
text_splitter = CharacterTextSplitter.from_tiktoken_encoder(chunk_size=800, chunk_overlap=24)
# 汉字分割成块
logger.info(text_splitter)
# delete_all_nodes()
documents_text_chunks = []
for content in contents:
    documents_text_chunks.extend(text_splitter.split_text(content))
documents = [Document(page_content=chunk) for chunk in documents_text_chunks]


graph_documents_filtered = llm_transformer_filtered.convert_to_graph_documents(documents)
logger.warning(graph_documents_filtered)
graph.add_graph_documents(graph_documents_filtered, baseEntityLabel=True, include_source=False)
# 生成图同时设置形成节点标签
