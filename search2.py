import json
import os
from neo4j import GraphDatabase
from templates2 import   template_entity,template_grade,trans_cypher
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from transformers import GPT2Tokenizer
output_parser = StrOutputParser()
from loguru import logger 
from config import(
    NEO4J_URI,
    NEO4J_PASSWORD,
    NEO4J_USERNAME,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    DATABASE,
)
from langchain.chains.graph_qa.cypher import GraphCypherQAChain
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from langchain_openai import ChatOpenAI
from typing import List
from langchain.pydantic_v1 import Field, BaseModel
from langchain_community.graphs import Neo4jGraph
from langchain_core.retrievers import BaseRetriever
from langchain_openai import ChatOpenAI

graph = Neo4jGraph()
tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
api_key=OPENAI_API_KEY
api_url=OPENAI_API_BASE

os.environ["OPENAI_API_KEY"] = api_key
os.environ["OPENAI_API_BASE"] = api_url

engine = create_engine(DATABASE, echo=True)
Session = sessionmaker(bind=engine)

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD)
)

llm = ChatOpenAI(model="gpt-3.5-turbo-16k", temperature=0)
 
@contextmanager
def scoped_session():
        db_session = Session()
        try:
            yield db_session
        finally:
            db_session.close() 
class Entities(BaseModel):
    names: List[str] = Field(
        ...,
        description="All the verb, noun or business entities that appear in the text",
    )
class cypher(BaseModel):
    names: List[str] = Field(
        ...,
        description="trans question into cypher query",
    )

class Retriever(BaseRetriever):
        def structured_retriever(self, question: str) -> str:
            # 返回节点
            prompt_entity = ChatPromptTemplate.from_messages(template_entity)
            entity_chain = prompt_entity | llm.with_structured_output(Entities)
            result_list = []   
            seen_neighbors1 = set()
            entities = entity_chain.invoke({"question": question})
            logger.debug(entities)
            for entity in entities.names: 
                response1 = graph.query(   
                    """CALL db.index.fulltext.queryNodes('entity', $query, {limit:5})
                    YIELD node
                    RETURN node""",
                    {"query": entity},  
                )
            for row in response1:
                    node_info = {
                        "节点": row['node'],
                        "关系": [],
                        "邻节点": []
                    }
                    neighbor_response = graph.query(
                        """MATCH (node)-[r]-(neighbor:__Entity__) 
                        WHERE node.id = $node_id
                        RETURN neighbor, r""", 
                        {"node_id": row['node']['id']},
                    )
                    for neighbor_row in neighbor_response:
                        neighbor_id = neighbor_row['neighbor']['id']
                        if neighbor_id not in seen_neighbors1:  
                            node_info["关系"].append(neighbor_row['r'])
                            node_info["邻节点"].append(neighbor_row['neighbor'])
                            seen_neighbors1.add(neighbor_id) 
                    result_list.append(node_info)
                    logger.info(result_list)

            return json.dump(result_list, ensure_ascii=False, indent=2)    

        def text_retriever(self, question: str) -> str:
            #单节点迭代邻节点返回小图
            prompt_entity = ChatPromptTemplate.from_messages(template_entity)
            entity_chain = prompt_entity | llm.with_structured_output(Entities)
            result = ""
            seen_neighbors = set()
            
            entities = entity_chain.invoke({"question": question})
            logger.error(entities)
            for entity in entities.names:
                response = graph.query(
                    """CALL db.index.fulltext.queryNodes('entity', $query, {limit:1})
                    YIELD node
                    RETURN node""",
                    {"query": entity}, 
                )
                logger.info(response)
                for row in response:
                    neighbor_response = graph.query(
                        """MATCH (node)-[r]-(neighbor:Document) 
                        WHERE node.id = $node_id
                        RETURN neighbor, r""", 
                        {"node_id": row['node']['id']},
                    )
                    for neighbor_row in neighbor_response:
                        document_node = neighbor_row['neighbor']
                        document_id = document_node['id']
                        print(document_id)
                        if document_id not in seen_neighbors:
                            seen_neighbors.add(document_id)
                            
                            doc_neighbors_response = graph.query(
                                """MATCH (document)-[r]->(neighbor:__Entity__) 
                                WHERE document.id = $document_id
                                RETURN neighbor, r""",
                                {"document_id": document_id},
                            )
                            logger.debug(doc_neighbors_response)
                            for doc_neighbor_row in doc_neighbors_response:
                                doc_neighbor_node = doc_neighbor_row['neighbor']
                                
                                doc_neighbor_id = doc_neighbor_node['id']
                                if doc_neighbor_id not in seen_neighbors:
                                    seen_neighbors.add(doc_neighbor_id)
                                    
                                    doc_neighbor_neighbors_response = graph.query(
                                        """MATCH (doc_neighbor)-[r2]->(doc_neighbor_neighbor:__Entity__) 
                                        WHERE doc_neighbor.id = $doc_neighbor_id
                                        RETURN doc_neighbor_neighbor, r2""",
                                        {"doc_neighbor_id": doc_neighbor_id},
                                    )
                                    logger.info(doc_neighbor_neighbors_response)
                                    for doc_neighbor_neighbor_row in doc_neighbor_neighbors_response:
                                        doc_neighbor_neighbor_node = doc_neighbor_neighbor_row['doc_neighbor_neighbor']
                                        result += f"({doc_neighbor_neighbor_node})"  
                                        result += f"[{doc_neighbor_neighbor_row['r2']}]->"  
                                        seen_neighbors.add(doc_neighbor_neighbor_node['id'])
            logger.debug(result)
            prompt = ChatPromptTemplate.from_messages(trans_cypher)
            cypher1 = prompt | llm |output_parser
            entiti = cypher1.invoke({"question": question,"schema":result})
            logger.warning(entiti)               
            return result


        def _get_relevant_documents(self, question: str) -> dict:
            structured_data = self.structured_retriever(question)
            return {
                "structured_data": structured_data,
            }
        
        def prompt_grade(self, expected_result, question):
            prompt_grade = ChatPromptTemplate.from_template(template_grade)
            chain_grade = prompt_grade| llm | StrOutputParser()
            i=self.text_retriever(question)
            n=self.structured_retriever(question)
            result=chain_grade.invoke({"expected_result": expected_result, "coll_result": self.text_retriever(question)})
            return result
        
        def test(self):
            #测试检索返回测试集中问题所搜结果
            all_results = []
            graph.query(
    "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
            file_path="fibona-drop rag测试集.json"
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            for item in data:
                question = item["question"]
                logger.info("question{}",question)
                expected_result = item["expected_result"]
                logger.info("expected_result{}",expected_result)
                retrieved_result=self.structured_retriever(question)
                combined_item = {
                    "question": question,
                    "expected_result": expected_result,
                    "retrieved_result ":retrieved_result,
                }
                all_results.append(combined_item)
            with open("/Users/skf/ModelTest/work/all_results.json", 'w', encoding='utf-8') as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=2)
                   
        def schema_count(graph:str):
            # 适用于qachain进行激素哪schema数量与token关系
            tokens = tokenizer.encode(graph)
            token_count = len(tokens)
            schema_str = graph.strip()
            schema_list = schema_str.split(",")
            schema_count = len(schema_list)
            return (f"token: {token_count}\nschema_count: {schema_count}\naverage_token={token_count/schema_count}")

                
        
instance = Retriever()
chain = GraphCypherQAChain.from_llm(
    ChatOpenAI(temperature=0), graph=graph, verbose=True, return_intermediate_steps=True
)
graph_schema=chain.graph_schema

