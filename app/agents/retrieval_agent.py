from crewai import Agent, Task
from crewai.tools import tool
from app.schemas import RetrievalOutput
from app.rag.vector_store import chroma_retriever_tool

@tool("ChromaDB Retriever Tool")
def retriever_tool(query: str) -> str:
    """
    Search the knowledge base for policy and FAQ documents relevant to the ticket.
    Input should be a search query string. Returns a string representation of relevant chunks.
    """
    chunks = chroma_retriever_tool(query, top_k=3)
    # We serialize it to string for the LLM to read easily
    if not chunks:
        return "No relevant documents found."
    
    result = []
    for c in chunks:
        result.append(f"Source: {c['source']}\nScore: {c['score']}\nText: {c['text']}\n---")
    return "\n".join(result)

def create_retrieval_agent() -> Agent:
    return Agent(
        role="Knowledge Base Researcher",
        goal="Find the most relevant policy/FAQ passages for a given ticket and category.",
        backstory="You are a meticulous researcher who searches the company knowledge base for answers to customer tickets. You evaluate the relevance of the results and only provide them if they are truly applicable.",
        tools=[retriever_tool],
        verbose=True,
        allow_delegation=False,
    )

def create_retrieval_task(agent: Agent, ticket_subject: str, ticket_body: str, category: str) -> Task:
    return Task(
        description=f"Search the knowledge base for documents relevant to this ticket.\n\nTicket Subject: {ticket_subject}\nTicket Body: {ticket_body}\nCategory: {category}\n\n1. Formulate a search query based on the ticket.\n2. Use the Retriever Tool to find relevant documents.\n3. If the top result's score is below 0.3, return an empty list of chunks and set low_relevance to true.\n4. Otherwise, return the chunks.",
        expected_output="A JSON object conforming to the RetrievalOutput schema.",
        agent=agent,
        output_pydantic=RetrievalOutput
    )
