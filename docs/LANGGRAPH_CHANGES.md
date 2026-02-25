# LangGraph Conversion - What Changed

## Overview
Converted `rag_query.py` to `rag_query_langgraph.py` by introducing a state graph to manage the query routing workflow.

## Key Changes

### 1. **State Definition** (NEW)
```python
class GraphState(TypedDict):
    """State for the routing graph."""
    question: str
    documents: List[Document]
    highest_similarity: float
    answer: str
    route_decision: str
    threshold: float
    routing_threshold: float
    verbose: bool
    limit: int
```
- **Why**: LangGraph requires explicit state management. This TypedDict defines all data that flows through the graph.
- **Original**: State was implicitly managed through local variables in `ask_question()`

### 2. **Workflow Split into Nodes** (REFACTORED)
The monolithic `ask_question()` function was split into discrete nodes:

#### Node 1: `retrieve_documents(state: GraphState)`
- **Lines**: 79-108
- **Purpose**: Retrieve documents and compute similarity scores
- **Original code**: Lines 164-183 in rag_query.py
- **Change**: Extracted into reusable node that updates state

#### Node 2: `route_query(state: GraphState)`
- **Lines**: 111-124
- **Purpose**: Make routing decision based on similarity threshold
- **Original code**: Lines 185-208 in rag_query.py (if condition)
- **Change**: Isolated decision logic into separate node

#### Node 3: `handle_google_search(state: GraphState)`
- **Lines**: 127-156
- **Purpose**: Handle Google search path
- **Original code**: Lines 185-208 in rag_query.py
- **Change**: Extracted into dedicated node

#### Node 4: `handle_rag(state: GraphState)`
- **Lines**: 159-228
- **Purpose**: Generate answer using RAG
- **Original code**: Lines 210-260 in rag_query.py
- **Change**: Extracted into dedicated node, removed chain caching

### 3. **Conditional Routing Function** (NEW)
```python
def should_continue(state: GraphState) -> str:
    """Conditional edge: Determine which path to take."""
    route_decision = state.get("route_decision", "")

    if route_decision == "no_documents":
        return END
    elif route_decision == "google_search":
        return "google_search"
    elif route_decision == "rag":
        return "rag"
```
- **Why**: LangGraph uses conditional edges to route between nodes
- **Original**: Used simple if/else logic in procedural code

### 4. **Graph Creation** (NEW)
```python
def create_routing_graph():
    """Create the LangGraph workflow for query routing."""
    workflow = StateGraph(GraphState)

    # Add nodes
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("route", route_query)
    workflow.add_node("google_search", handle_google_search)
    workflow.add_node("rag", handle_rag)

    # Add edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "route")

    # Conditional routing
    workflow.add_conditional_edges(
        "route",
        should_continue,
        {
            "google_search": "google_search",
            "rag": "rag",
            END: END
        }
    )

    workflow.add_edge("google_search", END)
    workflow.add_edge("rag", END)

    return workflow.compile()
```
- **Why**: Defines the workflow graph structure
- **Original**: No explicit graph, just procedural execution

### 5. **Updated `ask_question()` Function** (REFACTORED)
```python
def ask_question(...):
    # Create the routing graph
    app = create_routing_graph()

    # Initialize state
    initial_state = {...}

    # Execute the graph
    final_state = app.invoke(initial_state)
```
- **Change**: Now creates and invokes the graph instead of executing logic directly
- **Original**: Lines 136-271 contained all logic inline

## What Stayed the Same

1. **PgVectorRetriever class**: No changes (lines 30-68)
2. **CLI arguments**: No changes (main function)
3. **Business logic**: All routing logic, similarity calculations, and RAG generation remain identical
4. **Dependencies**: Uses same LangChain components (OllamaLLM, ChatPromptTemplate, etc.)

## Visual Workflow

```
                    START
                      |
                      v
            [retrieve_documents]
                      |
                      v
               [route_query]
                      |
                      v
            {should_continue?}
                    /   \
                   /     \
                  v       v
        [google_search] [handle_rag]
                  \       /
                   \     /
                    v   v
                     END
```

## Benefits of LangGraph Version

1. **Explicit State Flow**: State transitions are clear and trackable
2. **Modularity**: Each node can be tested independently
3. **Extensibility**: Easy to add new nodes (e.g., actual Google Search implementation)
4. **Visualization**: Can generate graph visualizations with `app.get_graph().draw_mermaid()`
5. **Debugging**: Better introspection of workflow execution
6. **Composability**: Nodes can be reused in different graphs

## How to Use

Both versions have identical CLI interfaces:

```bash
# Original version
python rag_query.py "Your question here" --verbose

# LangGraph version
python rag_query_langgraph.py "Your question here" --verbose
```

## Migration Path

The LangGraph version is a drop-in replacement. To migrate:
1. Install langgraph: `pip install langgraph` (already in requirements.txt)
2. Use `rag_query_langgraph.py` instead of `rag_query.py`
3. All CLI arguments work identically

## Future Enhancements (Easy with LangGraph)

1. Add actual Google Search node
2. Add a "confidence check" node after RAG answer
3. Add a "source verification" node
4. Add multi-step reasoning with feedback loops
5. Add human-in-the-loop approval nodes
