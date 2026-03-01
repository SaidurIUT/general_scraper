# LLM Tool Calling Explained

A simple guide to understanding how `rag_query_tool_calling.py` works.

---

## What is Tool Calling?

**Without tool calling:** You ask LLM a question → LLM makes up an answer from memory

**With tool calling:** You ask LLM a question → LLM picks a tool → Tool fetches real data → LLM answers using that data

```
┌─────────────────────────────────────────────────────────────┐
│  "What is the latest iPhone?"                               │
│                    │                                        │
│                    ▼                                        │
│  LLM thinks: "This is about products → I'll use web_search" │
│                    │                                        │
│                    ▼                                        │
│  web_search("latest iPhone") → Returns real search results  │
│                    │                                        │
│                    ▼                                        │
│  LLM reads results → "The iPhone 17 is the latest model..." │
└─────────────────────────────────────────────────────────────┘
```

---

## The Two Tools

We have two tools. The LLM reads their descriptions to decide which one to use.

### Tool 1: `search_policy_documents`

```python
@tool
def search_policy_documents(query: str) -> str:
    """
    Search company privacy policies, terms of service, and data handling documents.
    Use for: privacy, GDPR, cookies, data collection, terms of service, compliance.
    """
```

**When LLM uses it:** Privacy, terms, cookies, GDPR, data questions

**What it does:** Searches our PostgreSQL vector database for policy documents

---

### Tool 2: `web_search`

```python
@tool
def web_search(query: str) -> str:
    """
    Search the web for general information.
    Use for: products, news, features, pricing, company info (NOT privacy/legal).
    """
```

**When LLM uses it:** Products, news, general questions

**What it does:** Searches DuckDuckGo (free, no API key)

---

## How the LLM Chooses

The `@tool` decorator turns a function into a tool with a **description**. The LLM reads this description.

```
User: "What data do you collect?"
                │
                ▼
LLM sees two options:
┌────────────────────────────────────────────────────────┐
│ search_policy_documents: "privacy, GDPR, cookies..."   │ ✅ Match!
│ web_search: "products, news, features..."              │ ❌ Nope
└────────────────────────────────────────────────────────┘
                │
                ▼
LLM outputs: {"tool": "search_policy_documents", "query": "data collection"}
```

```
User: "What is the latest iPhone?"
                │
                ▼
LLM sees two options:
┌────────────────────────────────────────────────────────┐
│ search_policy_documents: "privacy, GDPR, cookies..."   │ ❌ Nope
│ web_search: "products, news, features..."              │ ✅ Match!
└────────────────────────────────────────────────────────┘
                │
                ▼
LLM outputs: {"tool": "web_search", "query": "latest iPhone"}
```

---

## The Magic Line

```python
llm_with_tools = llm.bind_tools(tools)
```

This one line enables tool calling. It attaches tool definitions to every LLM request.

| Without `bind_tools()` | With `bind_tools()` |
|------------------------|---------------------|
| LLM only outputs text | LLM can output tool calls |
| No tool awareness | Knows what tools exist |
| Guesses answers | Uses real data |

---

## The Graph Flow

```
┌─────────┐         ┌─────────┐         ┌─────────┐
│  agent  │────────▶│  tools  │────────▶│  agent  │────────▶ END
└─────────┘         └─────────┘         └─────────┘
     │                                       │
     │ (no tool call)                        │ (has answer)
     ▼                                       ▼
┌─────────┐                             ┌─────────┐
│ format  │────────────────────────────▶│   END   │
└─────────┘                             └─────────┘
```

**Step by step:**

1. **agent** → LLM decides: call a tool or answer directly
2. **tools** → If tool called, execute it and get results
3. **agent** → LLM reads results and generates final answer
4. **format** → Extract the answer text
5. **END** → Done!

---

## Code Walkthrough

### 1. State (What flows through the graph)

```python
class GraphState(TypedDict):
    question: str    # User's question
    messages: List   # Conversation history
    answer: str      # Final answer
    verbose: bool    # Debug mode
```

---

### 2. Agent Node (LLM decides)

```python
def call_agent(state: GraphState) -> GraphState:
    messages = state.get("messages", [])
    
    # First call: set up the conversation
    if not messages:
        messages = [
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=state["question"])
        ]
    
    # Ask LLM (with tools available)
    response = llm_with_tools.invoke(messages)
    
    return {"messages": messages + [response]}
```

**What happens:**

```
Input:  question = "What is the latest iPhone?"
        messages = []

Output: messages = [
          SystemMessage("You are a factual assistant..."),
          HumanMessage("What is the latest iPhone?"),
          AIMessage(tool_calls=[{name: "web_search", args: {...}}])
        ]
```

---

### 3. Should Continue? (Router)

```python
def should_continue(state: GraphState) -> Literal["tools", "format"]:
    last_msg = state["messages"][-1]
    if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
        return "tools"    # LLM wants to use a tool
    return "format"       # LLM gave direct answer
```

**Simple logic:**

```
Last message has tool_calls? 
  → Yes: Go to "tools" node
  → No:  Go to "format" node (we have the answer)
```

---

### 4. Tools Node (Execute the tool)

```python
def execute_tools(state: GraphState) -> GraphState:
    last_msg = state["messages"][-1]
    
    tool_results = []
    for tc in last_msg.tool_calls:
        # Execute the right tool
        if tc["name"] == "search_policy_documents":
            result = search_policy_documents.invoke(tc["args"])
        else:
            result = web_search.invoke(tc["args"])
        
        # Store result
        tool_results.append(ToolMessage(content=result, tool_call_id=tc["id"]))
    
    # Tell LLM to answer directly
    tool_results.append(HumanMessage(
        content="Based on these search results, give a direct answer."
    ))
    
    return {"messages": tool_results}
```

**What happens:**

```
Input:  AIMessage(tool_calls=[{name: "web_search", query: "latest iPhone"}])

Executes: web_search("latest iPhone")
Returns:  "The iPhone 17 is Apple's latest smartphone..."

Output: [
          ToolMessage("The iPhone 17 is Apple's latest..."),
          HumanMessage("Based on these search results, give a direct answer.")
        ]
```

---

### 5. Format Node (Extract answer)

```python
def format_answer(state: GraphState) -> GraphState:
    for msg in reversed(state["messages"]):
        if isinstance(msg, AIMessage) and not msg.tool_calls:
            return {"answer": msg.content}
    return {"answer": "Could not generate an answer."}
```

**What it does:** Finds the last AI message that doesn't have tool calls (that's the final answer).

---

### 6. Build the Graph

```python
def create_graph():
    workflow = StateGraph(GraphState)
    
    # Add nodes
    workflow.add_node("agent", call_agent)
    workflow.add_node("tools", execute_tools)
    workflow.add_node("format", format_answer)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_continue, {
        "tools": "tools", 
        "format": "format"
    })
    workflow.add_edge("tools", "agent")  # Loop back!
    workflow.add_edge("format", END)
    
    return workflow.compile()
```

---

## Complete Example

**Question:** "What data do you collect from users?"

```
Step 1: call_agent
        ├── Creates: [SystemMessage, HumanMessage("What data...")]
        ├── Calls: llm_with_tools.invoke()
        └── LLM returns: AIMessage(tool_calls=[{name: "search_policy_documents"}])

Step 2: should_continue
        ├── Checks: Does AIMessage have tool_calls?
        └── Returns: "tools" (yes it does)

Step 3: execute_tools
        ├── Runs: search_policy_documents("data collection")
        ├── Gets: "[Privacy Policy] We collect email, name..."
        └── Returns: [ToolMessage(results), HumanMessage("give direct answer")]

Step 4: call_agent (again)
        ├── Messages now include tool results
        ├── Calls: llm_with_tools.invoke()
        └── LLM returns: AIMessage("Based on the privacy policy, we collect...")

Step 5: should_continue
        ├── Checks: Does AIMessage have tool_calls?
        └── Returns: "format" (no, it's the final answer)

Step 6: format_answer
        └── Extracts: "Based on the privacy policy, we collect..."

Done!
```

---

## Key Concepts Summary

| Concept | What it does |
|---------|--------------|
| `@tool` | Converts function to LLM-usable tool |
| `bind_tools()` | Attaches tool schemas to LLM |
| `tool_calls` | LLM's structured output saying "use this tool" |
| `ToolMessage` | Contains tool execution results |
| `should_continue` | Routes graph based on LLM's decision |

---

## Manual Routing vs Tool Calling

| Manual (rag_query_langgraph.py) | Tool Calling (rag_query_tool_calling.py) |
|---------------------------------|------------------------------------------|
| Code checks similarity score | LLM reads question |
| `if score < 0.75: web_search()` | LLM decides based on intent |
| Fixed rules | Flexible understanding |
| Can't handle edge cases | LLM interprets context |

---

## Running the Code

```bash
# Policy question → uses search_policy_documents
python rag_query_tool_calling.py "What data do you collect?" -v

# General question → uses web_search  
python rag_query_tool_calling.py "What is the latest iPhone?" -v
```