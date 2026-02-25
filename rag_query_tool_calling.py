#!/usr/bin/env python3
"""
Intelligent Query System with LLM Tool Calling using LangGraph

The LLM decides which tool to use based on the question:
- search_policy_documents: For privacy, terms, data handling questions
- web_search: For general product info, news, and other queries
"""
import os
import argparse
from typing import List, TypedDict, Literal
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage, ToolMessage
from langchain_ollama import ChatOllama
from langchain_community.tools import DuckDuckGoSearchRun

from langgraph.graph import StateGraph, END

from utils import DatabaseHandler

load_dotenv()


# ============================================================================
# RETRIEVER
# ============================================================================

class PgVectorRetriever(BaseRetriever):
    """Custom retriever using pgvector database."""
    
    threshold: float = 0.3
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        db = DatabaseHandler()
        results = db.search_similar(query, self.threshold, self.k)
        return [
            Document(
                page_content=r['content'],
                metadata={'title': r['title'], 'url': r['url'], 'similarity': r['similarity']}
            )
            for r in results
        ]


# ============================================================================
# TOOLS
# ============================================================================

@tool
def search_policy_documents(query: str) -> str:
    """
    Search company privacy policies, terms of service, and data handling documents.
    Use for: privacy, GDPR, cookies, data collection, terms of service, compliance.
    """
    docs = PgVectorRetriever().invoke(query)
    if not docs:
        return "No relevant policy documents found."
    
    return "\n\n".join([
        f"[{doc.metadata['title']}] ({doc.metadata['similarity']:.0%})\n{doc.page_content[:1000]}"
        for doc in docs
    ])


@tool
def web_search(query: str) -> str:
    """
    Search the web for general information.
    Use for: products, news, features, pricing, company info (NOT privacy/legal).
    """
    try:
        return DuckDuckGoSearchRun().run(query)
    except Exception as e:
        return f"Search failed: {str(e)}"


tools = [search_policy_documents, web_search]


# ============================================================================
# STATE
# ============================================================================

class GraphState(TypedDict):
    """State for the agent graph."""
    question: str
    messages: List
    answer: str
    verbose: bool


# ============================================================================
# GRAPH
# ============================================================================

# Initialize LLM
ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
ollama_model = os.getenv("OLLAMA_MODEL", "qwen2.5:14b").replace("ollama/", "")

llm = ChatOllama(base_url=ollama_base_url, model=ollama_model, temperature=0)
llm_with_tools = llm.bind_tools(tools)

SYSTEM_PROMPT = """You are a factual assistant with two tools:
- search_policy_documents: For privacy/terms/GDPR questions
- web_search: For products/news/general info

OUTPUT FORMAT:
1. Use the appropriate tool
2. Read the results
3. Answer in 2-4 sentences with the key facts
4. Stop. No follow-up questions. No offers for more help.

FORBIDDEN:
- "It seems there might be confusion"
- "Would you like more details?"  
- "Can I help with anything else?"
- Speculation disclaimers
- Asking clarifying questions

Just answer with the facts from the search results."""


def call_agent(state: GraphState) -> GraphState:
    """Let LLM decide which tool to call."""
    messages = state.get("messages", [])
    
    # First call: add system prompt and question
    if not messages:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["question"])
        ]
    
    if state.get("verbose"):
        print("\n📤 Sending to LLM...")
    
    response = llm_with_tools.invoke(messages)
    
    if state.get("verbose"):
        if response.tool_calls:
            print(f"📥 LLM calling: {[tc['name'] for tc in response.tool_calls]}")
        else:
            print("📥 LLM responding directly")
    
    return {"messages": messages + [response]}


def execute_tools(state: GraphState) -> GraphState:
    """Execute tools that LLM requested."""
    messages = state["messages"]
    last_msg = messages[-1]
    
    tool_results = []
    for tc in last_msg.tool_calls:
        if state.get("verbose"):
            print(f"\n🔍 Executing: {tc['name']}('{tc['args'].get('query', '')}')")
        
        # Execute tool
        if tc["name"] == "search_policy_documents":
            result = search_policy_documents.invoke(tc["args"])
        else:
            result = web_search.invoke(tc["args"])
        
        tool_results.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    
    # Add instruction to give direct answer
    tool_results.append(HumanMessage(
        content="Based on these search results, give a direct answer. No follow-up questions."
    ))
    
    return {"messages": tool_results}


def format_answer(state: GraphState) -> GraphState:
    """Extract final answer from messages."""
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            return {"answer": msg.content}
    return {"answer": "Could not generate an answer."}


def should_continue(state: GraphState) -> Literal["tools", "format"]:
    """Route based on whether LLM wants to call tools."""
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"
    return "format"


def create_graph():
    """Build the tool-calling graph."""
    workflow = StateGraph(GraphState)
    
    # Nodes
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", execute_tools)
    workflow.add_node("format", format_answer)
    
    # Edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "format": "format"})
    workflow.add_edge("tools", "agent")  # Loop back after tool execution
    workflow.add_edge("format", END)
    
    return workflow.compile()


# ============================================================================
# MAIN
# ============================================================================

def ask_question(question: str, verbose: bool = False):
    """Ask a question using tool calling."""
    print("=" * 70)
    print("INTELLIGENT QUERY SYSTEM (Tool Calling)")
    print("=" * 70)
    print(f"Question: {question}")
    print(f"Model: {ollama_model}")
    print("=" * 70)
    
    graph = create_graph()
    result = graph.invoke({
        "question": question,
        "messages": [],
        "answer": "",
        "verbose": verbose
    })
    
    print("\n" + "=" * 70)
    print("ANSWER")
    print("=" * 70)
    print(result["answer"])
    print("=" * 70)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Query with LLM Tool Calling")
    parser.add_argument("question", help="Question to ask")
    parser.add_argument("-v", "--verbose", action="store_true", help="Show detailed output")
    
    args = parser.parse_args()
    ask_question(args.question, args.verbose)
