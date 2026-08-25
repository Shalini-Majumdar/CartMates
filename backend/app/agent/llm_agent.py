# agent/llm_agent.py
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from agent.tools import tools
from agent.prompt_templates import SYSTEM_PROMPT

load_dotenv()

# Step 1: Create Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.5
)

# Step 2: Create a proper ReAct prompt template that uses your system prompt
react_prompt = PromptTemplate.from_template(
    SYSTEM_PROMPT + """

You have access to the following tools:
{tools}

Use the following format:

Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat 3 times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question

Begin!

Question: {input}
Thought: {agent_scratchpad}"""
)

# Step 3: Create the ReAct agent using create_react_agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=react_prompt
)

# Step 4: Create agent executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# Step 5: Final callable function
def recommend_products(user_prompt: str, cart_id: int):
    response = agent_executor.invoke({
        "input": f"{user_prompt} (cart_id: {cart_id})"
    })
    return response["output"]