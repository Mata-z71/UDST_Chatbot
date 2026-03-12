import re 
import pandas as pd
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


class Chatbot:
    def __init__(self, csv_file: str):
        self.data = pd.read_csv(csv_file)
        self.data.columns = self.data.columns.str.strip().str.lower()

        self.questions = self.data["question"].astype(str).tolist()
        self.answers = self.data["answer"].astype(str).tolist()
        self.categories = self.data["category"].astype(str).tolist()

        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.question_embeddings = self.model.encode(
            self.questions,
            convert_to_numpy=True
        )

        self.threshold = 0.50

    def fallback(self):
        return (
            "Sorry, I cannot answer that question.\n\n"
            "This chatbot currently helps with:\n"
            "UDST colleges\n"
            "UDST programs\n"
            "General information about UDST\n\n"
            "Example questions you can ask:\n"
            "How many colleges are there in UDST?\n"
            "What programs are offered at UDST?\n"
            "What business programs are available at UDST?\n"
            "What engineering programs are available?\n"
            "What is UDST?\n"
            "Who is the president of UDST?\n"
            "Where is UDST located?",
            None,
            0.0,
        )

    def semantic_search(self, user_question: str):
        user_embedding = self.model.encode(
            [user_question],
            convert_to_numpy=True
        )

        similarities = cosine_similarity(user_embedding, self.question_embeddings)
        best_index = similarities.argmax()
        best_score = similarities[0][best_index]

        if best_score < self.threshold:
            return self.fallback()

        return (
            self.answers[best_index],
            self.categories[best_index],
            float(best_score),
        )

    def get_response(self, user_question: str):
        q = user_question.lower().strip()

        if not q:
            return "Please enter a question.", None, 0.0

        # -------- direct rules: programs --------
        if "major" in q or "majors" in q:
            return (
                "UDST offers programs in computing, business, engineering, and health sciences.",
                "programs",
                1.0,
            )

        if "diploma" in q:
            return (
                "Yes. UDST offers diploma programs in computing, business, engineering technology, and health sciences.",
                "programs",
                1.0,
            )

        if "software engineering" in q:
            return (
                "Yes. UDST offers the Software Engineering program.",
                "programs",
                1.0,
            )

        if "business program" in q or "business programs" in q:
            return (
                "The College of Business offers:\n\n"
                "Accounting\n"
                "Digital Marketing\n"
                "Banking and Financial Technology\n"
                "Human Resource Management\n"
                "Logistics and Supply Chain Management",
                "programs",
                1.0,
            )

        if (
            "it programs" in q
            or "information technology programs" in q
            or "computing programs" in q
        ):
            return (
                "The College of Computing and Information Technology offers:\n\n"
                "Data Science and Artificial Intelligence\n"
                "Software Engineering\n"
                "Information Technology\n"
                "Information Systems\n"
                "Cyber Security",
                "programs",
                1.0,
            )

        if "engineering program" in q or "engineering programs" in q:
            return (
                "The College of Engineering and Technology offers:\n\n"
                "Construction Engineering\n"
                "Aeronautical Engineering\n"
                "Telecommunications Engineering\n"
                "Chemical Processing Engineering",
                "programs",
                1.0,
            )

        if "health sciences program" in q or "health program" in q or "health programs" in q:
            return (
                "The College of Health Sciences offers:\n\n"
                "Nursing\n"
                "Dental Hygiene\n"
                "Environmental Health\n"
                "Critical Care Paramedicine",
                "programs",
                1.0,
            )

        if re.search(r"\bai\b", q) or "artificial intelligence" in q:
            return (
                "Yes. UDST offers the Data Science and Artificial Intelligence program.",
                "programs",
                1.0,
            )
            
        # -------- direct rules: about UDST --------
        if "what is udst" in q or "what does udst stand for" in q:
            return (
                "UDST stands for the University of Doha for Science and Technology.",
                "about_udst",
                1.0,
            )

        if "where is udst" in q or "which country is udst in" in q:
            return (
                "The University of Doha for Science and Technology is located in Doha, Qatar.",
                "about_udst",
                1.0,
            )

        if "official website" in q or "udst website" in q:
            return (
                "The official website of the University of Doha for Science and Technology is https://www.udst.edu.qa",
                "about_udst",
                1.0,
            )

        if "president of udst" in q or "who is the president" in q:
            return (
                "The President of the University of Doha for Science and Technology is Dr. Salem Al-Naemi.",
                "about_udst",
                1.0,
            )

        # -------- block clearly unrelated topics --------
        blocked = [
            "weather",
            "restaurant",
            "news",
            "football",
            "salary",
            "cook",
            "pasta",
        ]

        if any(word in q for word in blocked):
            return self.fallback()

        # -------- semantic search for all dataset questions --------
        return self.semantic_search(user_question)