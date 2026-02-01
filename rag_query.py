#!/usr/bin/env python3
"""
RAG (Retrieval-Augmented Generation) Query System using LangChain
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


def ask_question(question: str, threshold: float = 0.5, limit: int = 5, verbose: bool = False):
    """
    Ask a question and get an AI-generated answer using RAG.

    Args:
        question: The question to ask
        threshold: Minimum similarity score for retrieval (0-1)
        limit: Maximum number of documents to retrieve
        verbose: Show retrieved documents and sources
    """
    print("=" * 80)
    print("RAG QUERY SYSTEM (LangChain)")
    print("=" * 80)
    print(f"Question: {question}")
    print("=" * 80)
    print()

    try:
        # Create RAG chain
        print("Initializing RAG chain...")
        rag_chain, retriever = create_rag_chain(threshold=threshold, k=limit)

        # Retrieve documents (for verbose mode)
        print("Retrieving relevant documents...")
        docs = retriever.invoke(question)

        if not docs:
            print("No relevant documents found")
            print("\nTips:")
            print("- Try lowering the threshold (--threshold 0.3)")
            print("- Make sure data has been scraped to the database")
            print("- Try rephrasing your question")
            return

        print(f"Retrieved {len(docs)} relevant documents\n")

        if verbose:
            print("Retrieved Documents:")
            for idx, doc in enumerate(docs, 1):
                print(f"\n{idx}. {doc.metadata['title']} (Similarity: {doc.metadata['similarity']:.2%})")
                print(f"   URL: {doc.metadata['url']}")
                print(f"   Type: {doc.metadata['page_type']}")
                print(f"   Preview: {doc.page_content[:200]}...")
            print("\n" + "=" * 80 + "\n")

        # Generate answer
        print("Generating answer with LLM...\n")
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
            print(f"{idx}. {doc.metadata['title']} (Similarity: {doc.metadata['similarity']:.2%})")
            print(f"   {doc.metadata['url']}")
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
        description='Ask questions about scraped policies using RAG with LangChain',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python rag_query.py "How do companies handle GDPR compliance?"
  python rag_query.py "What is the data retention policy?" --threshold 0.6
  python rag_query.py "Do companies share data with third parties?" --limit 3 --verbose
        """
    )

    parser.add_argument(
        'question',
        help='Your question about the policies'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.5,
        help='Minimum similarity threshold for retrieval (0-1, default: 0.5)'
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
        help='Show retrieved documents before answer'
    )

    args = parser.parse_args()

    if not args.question:
        parser.print_help()
        return

    ask_question(args.question, args.threshold, args.limit, args.verbose)


if __name__ == "__main__":
    main()
