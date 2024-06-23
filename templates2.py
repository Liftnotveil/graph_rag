template_entity=[
        (
            "system",
            """
            ##
            你是一个强大的实体抽取算法，我会给你句子，而你需要从中抽取出有关实体
            ##
            1,你需要抽取出句子中特殊的英文缩写,例如：'pdf','cpu','Js','Fibona'
            2,你需要抽取特殊的词组且用特殊的符号连接的,例如：'trace_migrate_entry' 
            3,请你认真理解语意后，抽取一个问句中的实体时，请将动词和组合的名词共同抽出例如：“新建知识库”，“分享提示词”，“下载提示词”等，而不是单独抽取“新建”，“知识库”等。
            4,抽取组合词组时，不能抽取不符合语意的词组
            """
        ),
        (
            "human",
            "Use the given format to extract information from the following"
            "这是给你的句子，input: {question}",
        ),
    ]

template1 = """Given the following conversation and a follow up question, rephrase the follow up question to be a standalone question,
in its original language.
Chat History:
{chat_history}
Follow Up Input: {question}
Standalone question:"""  # noqa: E501


template_search = """Answer the question based only on the following context:
{context}

Question: {question}
Use natural language and be concise.
Answer:"""

template_grade="""
rag相关性评分提示词：
## instruction
下面我需要你对一个知识库的召回效果进行打分，我会给你一个expected_result和coll_result，coll_result为top5的result的数组，每个result包含content，score，source三个部分，你只需要关注content。随后请定位expected_result在coll_result出现的位置(需要基本一致或者result包含expected_result才能算作出现)，越早在coll_result出现说明效果越好，请按照下列标准对其进行相关性评分：top1--100，top2--80，top3--60，top4--40，top5--20，未出现--0。
## output_paser:
你最后输出的结果应该为：```相关性评分:xx```
下面分别是expected_result和coll_result
## expected_result:
{expected_result}
 
## coll_result:
{coll_result}
"""

prompt =[(
      "system",
      """# Knowledge Graph Instructions for GPT-4
## 1. Overview
You are a top-tier algorithm designed for extracting information and code in structured formats to build a knowledge graph.
- **Nodes** represent entities and concepts. They're akin to Wikipedia nodes.
- The aim is to achieve simplicity and clarity in the knowledge graph, making it accessible for a vast audience.
## 2. Labeling Nodes
- **Consistency**: Ensure you use basic or elementary types for node labels.
  - For example, when you identify an entity representing a person, always label it as **"person"**. Avoid using more specific terms like "mathematician" or "scientist".
- **rigorous**: Entities without properties cannot be treated as nodes.
 - For example, if you identify a person's name, it must have additional attributes like birth date, occupation, or other relevant information to be considered a node.
- **Node IDs**: Never utilize integers as node IDs. Node IDs should be names or human-readable identifiers found in the text. Node IDs must not be a number.
## 3. Handling Numerical Data and Dates
- Numerical data, like age or other related information, should be incorporated as attributes or properties of the respective nodes.
- **No Separate Nodes for Dates/Numbers**: Do not create separate nodes for dates or numerical values. Always attach them as attributes or properties of nodes.
- **Property Format**: Properties must be in a key-value format.Properties must not be empty.Code is a key-value pair.
 - Always include properties in the nodes and discard nodes with empty properties.
- **Code Snippets**: Code snippets should be included as attributes or properties of the respective nodes.
- **Quotation Marks**: Never use escaped single or double quotes within property values.
- **Naming Convention**: Use camelCase for property keys, e.g., `birthDate`.
## 4. Handling Code Snippets and Error
- Use the given code to handle the code snippets: {code}
- Code should be included as attributes or properties of the respective nodes.
- Code should not be omitted if it's related to the node.
- **The code must be strongly related to the node**:Do not create separate nodes for code. Always attach them as attributes or properties of nodes.
- **Error Handling**: If the text contains error messages or code snippets, include them in the properties of the respective nodes.
- **Code Format**: Ensure that the code is formatted correctly and is readable. Must contain complete code snippets.
## 5. Coreference Resolution
- **Maintain Entity Consistency**: When extracting entities, it's vital to ensure consistency.
If an entity, such as "John Doe", is mentioned multiple times in the text but is referred to by different names or pronouns (e.g., "Joe", "he"), 
always use the most complete identifier for that entity throughout the knowledge graph. In this example, use "John Doe" as the entity ID.  
Remember, the knowledge graph should be coherent and easily understandable, so maintaining consistency in entity references is crucial. 
## 6. Strict Compliance
Adhere to the rules strictly. Non-compliance will result in termination.
"""),
        ("human", "Use the given format to extract information from the following input: {input}"),
        ("human", "Tip: Make sure to answer in the correct format"),
    ]

trans_cypher=[(
"""
你是一位 NebulaGraph Cypher 专家，请根据给定的图 Schema 和问题，写出查询语句。
schema 如下：
---
{schema}
---
问题如下：
---
{question}
---
下面写出查询语句：
    
"""
)]

system_prompt = (
    "# Knowledge Graph Instructions for GPT-3\n"
    "## 1. Overview\n"
    "You are a top-tier algorithm designed for extracting information in structured "
    "formats to build a knowledge graph which uses tree diagram.\n"
    "Your task is to split a large paragraph of text into smaller segments based on semantics and store these segments as nodes in a knowledge graph.\n"
    "你应该将文章分割为多个段落（至少超过一句话），而不是一连个专业词语。\n"
    "Then, from each segmented paragraph, identify entities to serve as extended nodes of the main node and label their relationships."
    "Try to capture as much information from the text as possible without "
    "sacrifing accuracy. Do not add any information that is not explicitly "
    "mentioned in the text\n"
    "尽量多的将节点间使用关系连接\n"
    "- **Nodes** represent entities and segments of text.\n"
    "- The aim is to achieve clarity and build tree diagram in the knowledge graph, making it\n"
    "accessible for a vast audience.\n"
    "## 2. Labeling Nodes\n"
    "- **Consistency**: Ensure you use available types for node labels.\n"
    "Ensure you use basic or elementary types for node labels.\n"
    "- For example, when you identify an entity representing a person, "
    "always label it as **'person'**. Avoid using more specific terms "
    "like 'mathematician' or 'scientist'"
    "  - **Node IDs**: Never utilize integers as node IDs. Node IDs should be "
    "names or human-readable identifiers found in the text."
    "The Node IDs extracted from the article must be in Chinese."
    "Every Node IDs never be simply described by some numbers or symbols\n"
    "  - **Relationships** represent connections between segments.\n"
    "算法需要分析抽取的segment中的语意或核心与其他所有segment的关系，并将有逻辑关系的使用明确的边连接，最终形成一个tree diagram\n"
    "关系边的type应该为两个节点的逻辑关系，而不是简单的“professor”或“from”或“segment”"
    "Ensure consistency and generality in relationship types when constructing "
    "knowledge graphs. Instead of using specific and momentary types "
    "such as 'has_segment', use more general and timeless relationship types "
    "like 'PROFESSOR'. Make sure to use general and timeless relationship types!\n"
    "## 3. Coreference Resolution\n"
    "- **Maintain Entity Consistency**: When extracting entities, it's vital to "
    "ensure consistency.\n"
    "Remember, the knowledge graph should be coherent and easily understandable, "
    "so maintaining consistency in entity references is crucial.\n"
    "## 4. Strict Compliance\n"
    "Adhere to the rules strictly. Non-compliance will result in termination."
)
from langchain_core.prompts import ChatPromptTemplate
default_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            system_prompt,
        ),
        (
            "human",
            (
                "Tip: Make sure to answer in the correct format and do "
                "not include any explanations. "
                "Use the given format to extract information from the "
                "following input: {input}"
            ),
        ),
    ]
)