# rag.py -- main RAG pipeline (analyze -> retrieve -> generate + calendar + course)

from config import llm, vector_store, prompt
from langchain_core.documents import Document
from typing_extensions import Annotated, Literal
from typing import TypedDict, List
from langgraph.graph import START, StateGraph
from google_calendar import get_events
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import OllamaEmbeddings

# ---------- Structured schema ----------
class Search(TypedDict):
    query: Annotated[str, ..., "Short semantic query"]
    course: Annotated[str | None, ..., "Course name or None"]
    page_from: Annotated[int | None, ..., "Page start"]
    page_to: Annotated[int | None, ..., "Page end"]
    section: Annotated[Literal["beginning", "middle", "end"] | None, ..., "Optional section"]

# ---------- State ----------
class State(TypedDict):
    question: str
    query: Search | None
    context: List[Document] | None
    answer: str


# ---------- Calendar detection ----------
def check_calendar_query(state: State):
    q = state["question"].lower()
    keywords = [
        "calendrier", "événement", "rendez-vous", "rdv", "agenda",
        "aujourd", "demain",
        "calendar", "event", "appointment", "meeting", "schedule", "plans", "today", "tomorrow"
    ]

    if any(kw in q for kw in keywords):
        events_answer = get_events(state["question"])
        return {"answer": events_answer, "context": []}
    else:
        return {"query": None}


# ---------- Course detection ----------
def check_course_query(state: State):
    q = state["question"].lower()
    course_keywords = [
        "course", "chapter", "lesson", "pdf", "page", "summarize", "summary",
        "explain", "machine learning", "ml", "computer vision", "cv", "data science"
    ]

    if any(word in q for word in course_keywords):
        return {"query_type": "course"}
    else:
        return {"query_type": None}


# ---------- Analyze query ----------
def analyze_query(state: State):
    if state.get("query") is not None:
        return {}

    try:
        structured_llm = llm.with_structured_output(Search)
        query = structured_llm.invoke(state["question"])
    except Exception:
        import re
        qtext = state["question"]
        m = re.search(r'pages?\s*(\d+)\s*(?:-|to)\s*(\d+)', qtext, re.I)
        page_from = int(m.group(1)) if m else None
        page_to = int(m.group(2)) if m else None
        course = None
        qlow = qtext.lower()
        if "machine learning" in qlow or "ml course" in qlow:
            course = "ML"
        elif "computer vision" in qlow or "cv course" in qlow:
            course = "CV"
        query = {
            "query": qtext,
            "course": course,
            "page_from": page_from,
            "page_to": page_to,
            "section": None
        }

    return {"query": query}


# ---------- Retrieve context ----------
def retrieve(state: State):
    if state.get("context") == []:
        return {}

    q = state["query"]
    semantic_q = q.get("query") or state["question"]

    try:
        results = vector_store.similarity_search(semantic_q, k=6)
    except Exception as e:
        print(f"⚠️ Retrieval error: {e}")
        results = []

    return {"context": results}


# ---------- Generate answer ----------
def generate(state: State):
    if state.get("answer"):
        return {}

    docs_content = "\n\n".join(doc.page_content for doc in state["context"])
    prompt_obj = prompt.invoke({"question": state["question"], "context": docs_content})

    try:
        messages = prompt_obj.to_messages()
    except Exception:
        messages = None

    try:
        if messages:
            response = llm.invoke(messages)
            # Handle both string and object responses
            if isinstance(response, str):
                answer = response
            elif hasattr(response, "content"):
                answer = response.content
            else:
                answer = str(response)
        else:
            single_prompt = f"Question: {state['question']}\n\nContext:\n{docs_content}\n\nAnswer:"
            resp = llm.invoke(single_prompt)
            # Handle both string and object responses
            if isinstance(resp, str):
                answer = resp
            elif hasattr(resp, "content"):
                answer = resp.content
            else:
                answer = str(resp)
    except Exception as e:
        answer = f"⚠️ Error generating response: {e}"

    return {"answer": answer}


# ---------- Build graph ----------
graph_builder = StateGraph(State)
graph_builder.add_node("check_calendar_query", check_calendar_query)
graph_builder.add_node("check_course_query", check_course_query)
graph_builder.add_node("analyze_query", analyze_query)
graph_builder.add_node("retrieve", retrieve)
graph_builder.add_node("generate", generate)

# Flow: START → calendar → course → analyze → retrieve → generate
graph_builder.add_edge(START, "check_calendar_query")
graph_builder.add_edge("check_calendar_query", "check_course_query")
graph_builder.add_edge("check_course_query", "analyze_query")
graph_builder.add_edge("analyze_query", "retrieve")
graph_builder.add_edge("retrieve", "generate")

graph = graph_builder.compile()


# ---------- Ask function ----------
def ask_bot(question: str) -> str:
    """Main function to get an answer from the assistant."""
    try:
        result = graph.invoke({"question": question})
        return result.get("answer", "⚠️ Sorry, I couldn't find an answer.")
    except Exception as e:
        return f"❌ Error: {e}"


# ---------- CLI test ----------
if __name__ == "__main__":
    user_question = input("Enter your question: ")
    result = graph.invoke({"question": user_question})
    print("\nAnswer:")
    print(result["answer"])
