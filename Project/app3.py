import streamlit as st
from langchain_aws.agents.base import BedrockAgentsRunnable
from langchain_community.tools import DuckDuckGoSearchResults
from langchain.agents import Tool
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent
from langsmith import traceable
import boto3
import config as conf

# Initialize the Streamlit app
st.title("Coding Interview Preparation Agent")

# Set up Bedrock agent
region_name = 'us-east-1'
bedrock_agent = boto3.client(service_name='bedrock-agent-runtime', region_name=region_name)

bedrock_agent = BedrockAgentsRunnable(
    agent_id="JQNNUTIFGE", 
    agent_alias_id="ADSXXXOCVK",
    client=bedrock_agent
)

search = DuckDuckGoSearchResults()

# Define the tools
@tool
@traceable
def interact_with_agent(input_query, chat_history):
    """Interact with the agent and store chat history. Return the response."""
    result = bedrock_agent.invoke(
        {
            "input": input_query,
            "chat_history": chat_history,
        }
    )
    chat_history.append(input_query)
    chat_history.append("Assistant: " + result.return_values['output'])
    return result

@tool
@traceable
def search_tool(input_data):
    """Searches for the YouTube videos explaining the problem."""
    return search.run(input_data)

# System message for the agent
system_message = """You are a Teacher of preparation for the coding interview. You are preparing a student for the coding interview. 
When the student is communicating with you always call the interact_with_agent_tool with only one exception - when the student wants to find a video
with the explanation of the problem. In this case, call the search_tool.
When the user asks you to give the problem in specific topic - call interact_with_agent_tool with the user request as an input.
If the user asks you for a video - call the search_tool with the user request and problem as an input."""

# Initialize the chat model and app
model = ChatOpenAI(model="gpt-4o", openai_api_key=conf.open_ai_key)
app = create_react_agent(model, [interact_with_agent, search_tool], state_modifier=system_message)

# Streamlit input and buttons
query = st.text_input("You: ", placeholder="Ask a question about coding interviews...")

if 'message_history' not in st.session_state or 'internal_history' not in st.session_state:
    st.session_state.message_history = []
    st.session_state.internal_history = []

if st.button("Send"):
    if query:
        # Prepare the history
        if len(st.session_state.internal_history) > 1:
            history = [message['messages'] for message in st.session_state.internal_history[-1:]]
        elif st.session_state.internal_history == []:
            history = []
        else:
            history = st.session_state.internal_history['messages']

        # Invoke the agent
        messages = app.invoke({"messages": history + [("human", query)]})

        # Update the message history
        # if st.session_state.message_history == []:
        #     st.session_state.message_history = [messages]
        # else:
        #     st.session_state.message_history.append(messages)

        if st.session_state.internal_history == []:
            st.session_state.internal_history = messages
        else:
            st.session_state.internal_history += messages
        
        # Display the chat history
        st.session_state.message_history.append({"role": "human", "content": query})
        st.session_state.message_history.append({"role": "AI", "content": messages['messages'][-1].content})
        
        for msg in st.session_state.message_history:
            if msg.get('role'):  # It's a dictionary (our message format)
                role = "User" if msg['role'] == "human" else "Assistant"
                st.write(f"**{role}:** {msg['content']}")
            elif isinstance(msg, str):  # It's a string (legacy format or incorrect format)
                st.write(f"**{msg}**")

if st.button("Reset"):
    st.session_state.message_history = []
    st.session_state.internal_history = []
    st.write("Conversation history cleared.")