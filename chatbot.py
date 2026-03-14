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

        faq_docs = [
            f"Source: FAQ\nQuestion: {row['question']}\nAnswer: {row['answer']}"
            for _, row in faq.iterrows()
        ]

        faq_questions = faq["question"].tolist()

        # -----------------------------
        # Load website dataset
        # -----------------------------
        site = pd.read_csv(website_csv)

        site_docs = [
            f"Source: Website\nContent: {row['text']}"
            for _, row in site.iterrows()
        ]

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

        # -----------------------------
        # TF-IDF keyword retrieval
        # -----------------------------
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)

        # -----------------------------
        # LLM client
        # -----------------------------
        self.client = Mistral(api_key=mistral_api_key)

        # conversation memory
        self.history = []

    # -----------------------------
    # Router using LLM
    # -----------------------------

    def route_query(self, question):

        router_prompt = f"""
Classify the message into ONE category:

1. greeting
2. udst_question
3. unrelated

Message: "{question}"

Return ONLY the category.
"""

        response = self.client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": router_prompt}],
        )

        return response.choices[0].message.content.strip().lower()

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

            return answer, [], 1

        # Unrelated
        if route == "unrelated":

            return (
                "I'm designed to help with questions related to UDST. "
                "Please ask something about the university.",
                [],
                0
            )

        # -----------------------------
        # UDST question → RAG
        # -----------------------------
        results = self.hybrid_search(q)

        contexts = [r["doc"] for r in results]

        answer = self.generate_answer(q, contexts)

        self.history.append({
            "user": q,
            "bot": answer
        })

        if len(self.history) > 3:
            self.history.pop(0)

        return answer, contexts[:2], results[0]["score"]