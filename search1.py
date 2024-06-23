import json
import os
from neo4j import GraphDatabase
from langchain_core.output_parsers import StrOutputParser
from templates2 import   template_entity,template_grade
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.output_parsers import StrOutputParser
from transformers import GPT2Tokenizer
from loguru import logger 
from sqlalchemy import create_engine
from config import(
    NEO4J_URI,
    NEO4J_PASSWORD,
    NEO4J_USERNAME,
    OPENAI_API_BASE,
    OPENAI_API_KEY,
    DATABASE,
)
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
from langchain_openai import ChatOpenAI
from typing import List
from langchain.pydantic_v1 import Field, BaseModel
from langchain_community.graphs import Neo4jGraph
from langchain_core.retrievers import BaseRetriever
from langchain.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_community.graphs import Neo4jGraph
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


class Retriever(BaseRetriever):
        def structured_retriever(self, question: str) -> str:
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
            prompt_entity = ChatPromptTemplate.from_messages(template_entity)
            entity_chain = prompt_entity | llm.with_structured_output(Entities)
            result = ""
            seen_neighbors = set()  
            entities = entity_chain.invoke({"question": question})
            logger.error(entities)
            for entity in entities.names:
                response = graph.query(
                        """CALL db.index.fulltext.queryNodes('entity', $query, {limit:2})
                        YIELD node
                        RETURN node""",
                        {"query": entity
                         }, 
                    )
                for row in response:
                        neighbor_response = graph.query(
                            """MATCH (node)-[r]-(neighbor:Document) 
                            WHERE node.id = $node_id
                            RETURN neighbor, r""", 
                            {"node_id": row['node']['id']},
                        )
                        for neighbor_row in neighbor_response:
                            neighbor_id = neighbor_row['neighbor']['id']
                            if neighbor_id not in seen_neighbors:  
                                result += f"coll_back_content:{neighbor_row['neighbor']}"
                                seen_neighbors.add(neighbor_id)  
                logger.warning(result)  
                return result


        def _get_relevant_documents(self, question: str) -> dict:
            structured_data = self.structured_retriever(question)
            return {
                "structured_data": structured_data,
            }
        
        def prompt_grade(self, expected_result, question):
            prompt_grade = ChatPromptTemplate.from_template(template_grade)
            chain_grade = prompt_grade| llm | StrOutputParser()
            n=self.text_retriever(question)
            t=self.structured_retriever(question)
            combined_item = {
                    "node's relationship": t,
                    "coll_text": n,
                }
            result=chain_grade.invoke({"expected_result": expected_result, "coll_result": combined_item})
            return result
        
        def test(self):
            graph.query(
    "CREATE FULLTEXT INDEX entity IF NOT EXISTS FOR (e:__Entity__) ON EACH [e.id]")
            all_results = []
            file_path="fibona-drop rag测试集.json"
            # try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            for item in data:
                question = item["question"]
                logger.info("question{}",question)
                expected_result = item["expected_result"]
                logger.info("expected_result{}",expected_result)
                # retrieved_result=self.structured_retriever(question)
                result=self.prompt_grade(expected_result,question)
                combined_item = {
                    "question": question,
                    "expected_result": expected_result,
                    "score": result
                }
                all_results.append(combined_item)
            with open("/xxx/score.json", 'w', encoding='utf-8') as json_file:
                json.dump(all_results, json_file, ensure_ascii=False, indent=2)   
               
instance = Retriever
instance.test()
