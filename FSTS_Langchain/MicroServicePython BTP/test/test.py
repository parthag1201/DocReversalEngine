from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Point LangChain to your LM Studio server
llm_model = ChatOpenAI(
    model="meta-llama-3.1-8b-instruct",  # model name from LM Studio
    openai_api_base="http://localhost:1234/v1",
    openai_api_key="none",  # LM Studio runs locally, no key needed
)

# Example prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant."),
    ("human", "{question}")
])

response = (prompt | llm_model).invoke({"question": "What is the capital of India?"})
print(response)
