import os
from pathlib import Path

import faiss
import pandas as pd
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mistralai import Mistral


class Chatbot:

    def __init__(self, faq_csv, website_csv, mistral_api_key):

        # -----------------------------
        # Load FAQ dataset
        # -----------------------------
        faq = pd.read_csv(faq_csv)
        faq.columns = faq.columns.str.strip().str.lower()

        if faq.empty:
            raise ValueError(f"FAQ CSV '{faq_csv}' has no rows")

        if not {'question', 'answer'}.issubset(faq.columns):
            raise ValueError(
                f"FAQ CSV '{faq_csv}' must contain 'question' and 'answer' columns. "
                f"Found columns: {list(faq.columns)}"
            )

        faq_docs = [
            f"Source: FAQ\nQuestion: {row['question']}\nAnswer: {row['answer']}"
            for _, row in faq.iterrows()
        ]

        print(f"[Chatbot] Loaded {len(faq_docs)} FAQ entries from {faq_csv}")

        faq_questions = faq["question"].tolist()

        # -----------------------------
        # Load website dataset
        # -----------------------------
        site = pd.read_csv(website_csv)

        if site.empty:
            raise ValueError(f"Website CSV '{website_csv}' has no rows")

        if 'text' not in site.columns:
            raise ValueError(
                f"Website CSV '{website_csv}' must contain a 'text' column. "
                f"Found columns: {list(site.columns)}"
            )

        site_docs = [
            row['text']
            for _, row in site.iterrows()
        ]

        print(f"[Chatbot] Loaded {len(site_docs)} website chunks from {website_csv}")

        site_questions = site["text"].tolist()

        # -----------------------------
        # Merge knowledge base
        # -----------------------------
        self.documents = faq_docs + site_docs
        self.questions = faq_questions + site_questions

        # -----------------------------
        # Embedding model
        # -----------------------------
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # use cache based on input files to avoid repeating work every run
        faq_key = Path(faq_csv).stem
        website_key = Path(website_csv).stem
        embeddings_cache = f"{faq_key}_{website_key}_embeddings.npy"
        index_cache = f"{faq_key}_{website_key}_faiss.index"

        if os.path.exists(embeddings_cache) and os.path.exists(index_cache):
            print(f"[Chatbot] Loading cached embeddings from {embeddings_cache} and index {index_cache}")
            self.doc_embeddings = np.load(embeddings_cache)
            self.index = faiss.read_index(index_cache)
        else:
            self.doc_embeddings = self.model.encode(
                self.documents,
                convert_to_numpy=True
            ).astype("float32")

            # -----------------------------
            # FAISS index
            # -----------------------------
            dimension = self.doc_embeddings.shape[1]
            self.index = faiss.IndexFlatIP(dimension)

            faiss.normalize_L2(self.doc_embeddings)
            self.index.add(self.doc_embeddings)

            np.save(embeddings_cache, self.doc_embeddings)
            faiss.write_index(self.index, index_cache)
            print(f"[Chatbot] Saved cached embeddings and index")

        # -----------------------------
        # TF-IDF keyword retrieval
        # -----------------------------
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

        # -----------------------------
        # LLM client
        # -----------------------------
        if mistral_api_key:
            self.client = Mistral(api_key=mistral_api_key)
        else:
            self.client = None
            print("[Chatbot] WARNING: MISTRAL_API_KEY is not set. LLM generation will be disabled; responses use context fallback only.")

        # conversation memory
        self.history = []

    # -----------------------------
    # Router using keywords
    # -----------------------------

    def route_query(self, question):
        q_lower = question.lower()
        greeting_keywords = ["hi", "hello", "hey", "good morning", "good afternoon", "good evening", "how are you", "what's up"]
        udst_keywords = ["udst", "university", "college", "program", "admission", "library", "president", "student", "faculty", "campus", "qatar", "doha"]

        if any(kw in q_lower for kw in greeting_keywords):
            return "greeting"

        # Always use RAG for any non-greeting input; improves coverage for questions that may miss keyword triggers.
        if any(kw in q_lower for kw in udst_keywords):
            return "udst_question"

        return "rag_question"  # fallback to retrieval for everything else

    # -----------------------------
    # FAISS search
    # -----------------------------

    def faiss_search(self, query):

        query_embedding = self.model.encode([query]).astype("float32")

        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, len(self.documents))

        return scores[0], indices[0]

    # -----------------------------
    # Hybrid retrieval
    # -----------------------------

    def hybrid_search(self, query, top_k=4):

        semantic_scores, indices = self.faiss_search(query)

        query_vec = self.vectorizer.transform([query])
        keyword_scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        hybrid_scores = 0.6 * semantic_scores + 0.4 * keyword_scores

        top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]

        results = []

        for idx in top_indices:
            results.append({
                "doc": self.documents[idx],
                "score": float(hybrid_scores[idx])
            })

        return results

    # -----------------------------
    # Generate LLM answer
    # -----------------------------

    def generate_answer(self, question, contexts):

        context_text = "\n\n".join(contexts)

        history_text = "\n".join(
            [f"User: {h['user']}\nAssistant: {h['bot']}" for h in self.history]
        )

        system_prompt = """
You are a helpful student support assistant for the University of Doha for Science and Technology (UDST).

Your job is to help students by answering questions clearly and naturally.

Rules:
- Use the provided context as your main knowledge source.
- If the context does not contain the answer, say you are unsure.
- Do NOT invent policies or information.
- Respond in a friendly conversational way.
"""

        if self.client is None:
            short_context = "\n\n".join(contexts[:3])
            return (
                "Mistral API key is not configured, so I cannot generate a language model response. "
                "Here are the highest-relevance retrieved context chunks you can use to answer this question:\n\n"
                f"{short_context}"
            )

        prompt = f"""
Conversation History:
{history_text}

Context:
{context_text}

Student Question:
{question}

Answer:
"""

        response = self.client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
        )

        return response.choices[0].message.content

    # -----------------------------
    # Main RAG response helper
    # -----------------------------

    def get_response_rag(self, q):

        results = self.hybrid_search(q)

        if not results:
            return (
                "Sorry, I couldn't find relevant information in the knowledge base. "
                "Please try rephrasing your question.",
                "RAG",
                0
            )

        contexts = [r["doc"] for r in results]

        answer = self.generate_answer(q, contexts)

        self.history.append({
            "user": q,
            "bot": answer
        })

        if len(self.history) > 3:
            self.history.pop(0)

        return answer, "RAG", results[0]["score"]


    # -----------------------------
    # Main response function
    # -----------------------------

    def get_response(self, question):

        q = question.strip()

        if not q:
            return "Please enter a question.", [], 0

        # -----------------------------
        # Route query
        # -----------------------------
        route = self.route_query(q)

        # Greeting
        if route == "greeting":

            answer = self.generate_answer(
                q,
                ["The user greeted the assistant."]
            )

            return answer, "Greeting", None

        # RAG-based response (udst_question or rag_question)
        if route in ["udst_question", "rag_question"]:
            return self.get_response_rag(q)

        # Never reach here, but fallback
        return (
            "I'm designed to help with questions related to UDST. "
            "Please ask something about the university.",
            "Unrelated",
            None
        )


