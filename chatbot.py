import re
import dotenv
import faiss
import pandas as pd
import numpy as np

from sentence_transformers import SentenceTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from mistralai import Mistral

import os




class Chatbot:

    def __init__(self, csv_file,mistral_api_key):

        # load data
        self.data = pd.read_csv(csv_file)
        self.data.columns = self.data.columns.str.strip().str.lower()

        self.questions = self.data["question"].astype(str).tolist()
        self.answers = self.data["answer"].astype(str).tolist()
        self.categories = self.data["category"].astype(str).tolist()

        # embedding model
        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        # encode questions
        self.question_embeddings = self.model.encode(
            self.questions,
            convert_to_numpy=True
        ).astype("float32")

        # -------- FAISS index --------
        dimension = self.question_embeddings.shape[1]

        self.index = faiss.IndexFlatIP(dimension)

        # normalize vectors
        faiss.normalize_L2(self.question_embeddings)

        self.index.add(self.question_embeddings)

        # -------- TFIDF --------
        self.vectorizer = TfidfVectorizer()
        self.tfidf_matrix = self.vectorizer.fit_transform(self.questions)

        # -------- mistral --------
        self.client = Mistral(api_key=mistral_api_key)

        # conversation memory
        self.history = []

        # thresholds
        self.escalation_threshold = 0.35

    # -----------------------------
    # FAISS semantic search
    # -----------------------------

    def faiss_search(self, user_question, top_k=3):

        query_embedding = self.model.encode([user_question]).astype("float32")

        faiss.normalize_L2(query_embedding)

        scores, indices = self.index.search(query_embedding, top_k)

        return scores[0], indices[0]

    # -----------------------------
    # Hybrid retrieval
    # -----------------------------

    def hybrid_search(self, user_question, top_k=3):

        # semantic search
        semantic_scores, indices = self.faiss_search(user_question, top_k=len(self.questions))

        semantic_scores = semantic_scores

        # keyword search
        query_vec = self.vectorizer.transform([user_question])
        keyword_scores = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # combine
        hybrid_scores = 0.6 * semantic_scores + 0.4 * keyword_scores

        top_indices = np.argsort(hybrid_scores)[-top_k:][::-1]

        results = []

        for idx in top_indices:
            results.append({
                "question": self.questions[idx],
                "answer": self.answers[idx],
                "category": self.categories[idx],
                "score": float(hybrid_scores[idx])
            })

        return results

    # -----------------------------
    # Generate answer with Mistral
    # -----------------------------

    def generate_answer(self, question, contexts):

        context_text = "\n".join(contexts)

        history_text = "\n".join(
            [f"User: {h['user']}\nBot: {h['bot']}" for h in self.history]
        )

        prompt = f"""
You are a student support assistant for UDST (University of Doha for Science and Technology).

Use ONLY the information in the context below to answer the question.

Conversation history:
{history_text}

Context:
{context_text}

Student Question:
{question}

Answer clearly and concisely.
"""

        response = self.client.chat.complete(
            model="mistral-small-latest",
            messages=[{"role": "user", "content": prompt}],
        )

        return response.choices[0].message.content

    # -----------------------------
    # Feedback logging
    # -----------------------------

    def save_feedback(self, question, answer, feedback):

        df = pd.DataFrame([{
            "question": question,
            "answer": answer,
            "feedback": feedback
        }])

        df.to_csv("feedback_log.csv", mode="a", header=False, index=False)

    # -----------------------------
    # Escalation message
    # -----------------------------

    def escalate(self):

        return (
            "I'm not confident about this answer.\n\n"
            "Please contact UDST student services for assistance.\n"
            "Website: https://www.udst.edu.qa\n"
            "Or contact the registrar office."
        )

    # -----------------------------
    # Main chatbot response
    # -----------------------------

    def get_response(self, user_question):

        q = user_question.lower().strip()

        if not q:
            return "Please enter a question.", [], 0.0

        # greetings
        greetings = ["hello", "hi", "hey", "thanks", "thank you"]

        if any(g in q for g in greetings):
            return "Hello! How can I help you with UDST information today?", [], 1.0

        # block unrelated
        blocked = ["weather", "restaurant", "news", "football", "pasta"]

        if any(word in q for word in blocked):
            return "Sorry, I can only answer questions related to UDST.", [], 0.0

        # retrieval
        results = self.hybrid_search(user_question)

        contexts = [r["answer"] for r in results]

        confidence = results[0]["score"]

        if confidence < self.escalation_threshold:
            return self.escalate(), [], confidence

        # generate answer
        answer = self.generate_answer(user_question, contexts)

        # update memory
        self.history.append({
            "user": user_question,
            "bot": answer
        })

        if len(self.history) > 3:
            self.history.pop(0)

        sources = [r["question"] for r in results]

        return answer, sources, confidence