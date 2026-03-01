#!/usr/bin/env python3
"""
Intelligent Query Routing System with RAG and Google Search

Routes user questions intelligently:
- Computes similarity with RAG documents
- If similarity >= threshold: Answer with RAG (policy documents)
- If similarity < threshold: Indicate Google search is needed
"""

import sys
import argparse
import os
from typing import List
from dotenv import load_dotenv

from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever
from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_ollama import OllamaLLM
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from utils import DatabaseHandler

load_dotenv()


class PgVectorRetriever(BaseRetriever):
    """Custom retriever that uses our existing pgvector database."""

    threshold: float = 0.5
    k: int = 5

    class Config:
        arbitrary_types_allowed = True

    def __init__(self, threshold: float = 0.5, k: int = 5):
        """Initialize retriever with database handler."""
        super().__init__(threshold=threshold, k=k)
        self._db_handler = DatabaseHandler()

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> List[Document]:
        """Retrieve documents from pgvector database."""
        results = self._db_handler.search_similar(query, self.threshold, self.k)

        documents = []
        for result in results:
            # Create LangChain Document with metadata
            doc = Document(
                page_content=result['content'],
                metadata={
                    'title': result['title'],
                    'url': result['url'],
                    'page_type': result['page_type'],
                    'similarity': result['similarity']
                }
            )
            documents.append(doc)

        return documents


def create_rag_chain(threshold: float = 0.5, k: int = 5):
    """
    Create a RAG chain using LangChain.

    Args:
        threshold: Minimum similarity threshold for retrieval
        k: Number of documents to retrieve

    Returns:
        LangChain RAG chain
    """
    # Initialize retriever
    retriever = PgVectorRetriever(threshold=threshold, k=k)

    # Initialize Ollama LLM
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://10.112.30.10:11434")
    ollama_model = os.getenv("OLLAMA_MODEL", "ollama/phi4-mini-reasoning").replace("ollama/", "")

    llm = OllamaLLM(
        base_url=ollama_base_url,
        model=ollama_model,
        temperature=0.7,
    )

    # Create prompt template
    template = """You are a helpful assistant that answers questions based on company policy documents.

Use the following context from policy documents to answer the question.

Context:
{context}

Question: {question}

Instructions:
- Answer based ONLY on the provided context
- If the context doesn't contain enough information, say so clearly
- Be concise but informative
- Mention which document(s) or company policies you're referencing
- If you find contradictions between documents, point them out

Answer:"""

    prompt = ChatPromptTemplate.from_template(template)

    # Format documents for context
    def format_docs(docs):
        formatted = []
        for i, doc in enumerate(docs, 1):
            formatted.append(
                f"--- Document {i}: {doc.metadata['title']} ---\n"
                f"Source: {doc.metadata['url']}\n"
                f"Type: {doc.metadata['page_type']}\n"
                f"Similarity: {doc.metadata['similarity']:.2%}\n"
                f"Content: {doc.page_content[:1500]}\n"
            )
        return "\n".join(formatted)

    # Create RAG chain
    rag_chain = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | llm
        | StrOutputParser()
    )

    return rag_chain, retriever


def ask_question(
    question: str,
    threshold: float = 0.5,
    limit: int = 5,
    verbose: bool = False,
    routing_threshold: float = 0.75
):
    """
    Ask a question with intelligent routing between RAG and Google search.

    Args:
        question: The question to ask
        threshold: Minimum similarity score for retrieval (0-1)
        limit: Maximum number of documents to retrieve
        verbose: Show retrieved documents and sources
        routing_threshold: Similarity threshold for routing decision (default: 0.75)
                          If highest similarity >= routing_threshold, use RAG
                          If highest similarity < routing_threshold, suggest Google search
    """
    print("=" * 80)
    print("INTELLIGENT QUERY ROUTING SYSTEM")
    print("=" * 80)
    print(f"Question: {question}")
    print("=" * 80)
    print()

    try:
        # Step 1: Get documents with very low threshold to see all similarity scores
        print("Step 1: Computing similarity with RAG documents...")

        # Create retriever with threshold=0 to get all documents with their similarity scores
        retriever_all = PgVectorRetriever(threshold=0.0, k=limit)
        all_docs = retriever_all.invoke(question)

        if not all_docs:
            print("\nNo documents found in knowledge base")
            print("Database might be empty - scrape some data first")
            print("=" * 80)
            return

        # Get highest similarity score
        highest_similarity = max(doc.metadata['similarity'] for doc in all_docs)

        print(f"Retrieved {len(all_docs)} documents")
        print(f"Highest similarity score: {highest_similarity:.4f} ({highest_similarity:.2%})")
        print(f"Routing threshold: {routing_threshold:.4f} ({routing_threshold:.2%})")
        print()

        # ROUTING DECISION
        if highest_similarity < routing_threshold:
            print("=" * 80)
            print("ROUTING DECISION: GOOGLE SEARCH REQUIRED")
            print("=" * 80)
            print(f"Confidence too low: {highest_similarity:.4f} < {routing_threshold:.4f}")
            print("\nThis question appears to be outside the scope of available policy documents.")
            print("A Google search would provide better results.")
            print("\n(Google search integration not yet implemented)")
            print("=" * 80)

            if verbose:
                print("\nTop documents found (but below routing threshold):")
                for idx, doc in enumerate(all_docs[:3], 1):
                    print(f"{idx}. {doc.metadata['title']}")
                    print(f"   Similarity: {doc.metadata['similarity']:.4f} ({doc.metadata['similarity']:.2%})")
                    print(f"   URL: {doc.metadata['url']}")
                    print()
                print("=" * 80)
            else:
                print("\nTop 3 similarity scores:")
                for idx, doc in enumerate(all_docs[:3], 1):
                    print(f"{idx}. {doc.metadata['title']}: {doc.metadata['similarity']:.4f} ({doc.metadata['similarity']:.2%})")
                print("=" * 80)
            return

        # Proceed with RAG - filter documents by retrieval threshold
        docs = [doc for doc in all_docs if doc.metadata['similarity'] >= threshold]

        if not docs:
            print("=" * 80)
            print("WARNING: Similarity above routing threshold but below retrieval threshold")
            print("=" * 80)
            print(f"Highest similarity: {highest_similarity:.4f} >= {routing_threshold:.4f} (routing)")
            print(f"But all documents below retrieval threshold: {threshold:.4f}")
            print("\nConsider lowering the retrieval threshold parameter")
            print("=" * 80)
            return

        print("=" * 80)
        print("ROUTING DECISION: USING RAG SYSTEM")
        print("=" * 80)
        print(f"Confidence sufficient: {highest_similarity:.4f} >= {routing_threshold:.4f}")
        print(f"Answering from {len(docs)} documents...\n")

        if verbose:
            print("Retrieved Documents:")
            for idx, doc in enumerate(docs, 1):
                print(f"\n{idx}. {doc.metadata['title']}")
                print(f"   Similarity: {doc.metadata['similarity']:.4f} ({doc.metadata['similarity']:.2%})")
                print(f"   URL: {doc.metadata['url']}")
                print(f"   Type: {doc.metadata['page_type']}")
                print(f"   Preview: {doc.page_content[:200]}...")
            print("\n" + "=" * 80 + "\n")

        # Generate answer
        print("Generating answer with LLM...\n")

        # Create RAG chain with proper threshold
        rag_chain, _ = create_rag_chain(threshold=threshold, k=limit)
        answer = rag_chain.invoke(question)

        # Display answer
        print("=" * 80)
        print("ANSWER")
        print("=" * 80)
        print(answer)

        # Display sources
        print("\n" + "=" * 80)
        print("SOURCES")
        print("=" * 80)
        for idx, doc in enumerate(docs, 1):
            print(f"{idx}. {doc.metadata['title']}")
            print(f"   Similarity: {doc.metadata['similarity']:.4f} ({doc.metadata['similarity']:.2%})")
            print(f"   URL: {doc.metadata['url']}")
        print("=" * 80)

    except Exception as e:
        print(f"Error: {e}")
        print("\nTroubleshooting:")
        print("- Make sure PostgreSQL is running and database exists")
        print("- Check Ollama is running at the configured URL")
        print(f"- Ollama URL: {os.getenv('OLLAMA_BASE_URL', 'http://10.112.30.10:11434')}")
        import traceback
        if verbose:
            traceback.print_exc()


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Ask questions with intelligent routing between RAG and Google search',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Privacy policy question (likely uses RAG)
  python rag_query.py "How do companies handle GDPR compliance?"

  # Product question (likely uses Google search)
  python rag_query.py "What is the latest iPhone model?"

  # Custom thresholds
  python rag_query.py "What is the data retention policy?" --threshold 0.6 --routing-threshold 0.8

  # Verbose mode to see routing decision details
  python rag_query.py "Do companies share data with third parties?" --limit 3 --verbose

Routing Logic:
  1. Question is converted to embedding
  2. Similarity computed with all policy documents in database
  3. If highest similarity >= routing_threshold (default 0.75): Use RAG
  4. If highest similarity < routing_threshold: Suggest Google search
        """
    )

    parser.add_argument(
        'question',
        help='Your question (can be about policies or anything else)'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum similarity threshold for retrieval (0-1, default: 0.5)'
    )
    parser.add_argument(
        '--routing-threshold',
        type=float,
        default=0.75,
        help='Similarity threshold for routing decision (0-1, default: 0.75). '
             'Questions with similarity >= this value use RAG, otherwise Google search'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='Maximum number of documents to retrieve (default: 5)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show retrieved documents and routing decision details'
    )

    args = parser.parse_args()

    if not args.question:
        parser.print_help()
        return

    ask_question(
        args.question,
        args.threshold,
        args.limit,
        args.verbose,
        args.routing_threshold
    )


if __name__ == "__main__":
    main()
