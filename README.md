# UDST Chatbot – Student Information Assistant

This project is a chatbot designed to answer common questions about the **University of Doha for Science and Technology (UDST)**.  
The chatbot helps new students quickly find information about:

- UDST colleges
- Academic programs
- General university information

The chatbot uses **semantic search with Sentence Transformers** to understand user questions and return the most relevant answer.

---

# Features

The chatbot can answer questions about:

### UDST Colleges
- College of Business
- College of Computing and Information Technology
- College of Engineering and Technology
- College of Health Sciences
- College of General Education

### Programs Offered
Programs from different colleges such as:

**Computing and IT**
- Data Science and Artificial Intelligence
- Software Engineering
- Information Technology
- Information Systems
- Cyber Security

**Business**
- Accounting
- Digital Marketing
- Banking and Financial Technology
- Human Resource Management
- Logistics and Supply Chain Management

**Engineering**
- Construction Engineering
- Aeronautical Engineering
- Telecommunications Engineering
- Chemical Processing Engineering

**Health Sciences**
- Nursing
- Dental Hygiene
- Environmental Health
- Critical Care Paramedicine

### General Information
The chatbot can answer questions such as:

- What is UDST?
- Where is UDST located?
- Who is the president of UDST?
- What student services are available?
- What is the official UDST website?

---

# Technology Used

The project was implemented using the following technologies:

- Python
- Sentence Transformers
- Cosine Similarity
- Pandas
- Streamlit

Model used for semantic search:

---

# How the Chatbot Works

1. The chatbot loads a dataset of frequently asked questions (`udst_faq.csv`).
2. Each question is converted into an **embedding vector** using Sentence Transformers.
3. When a user asks a question:
   - The question is converted to an embedding.
   - Cosine similarity is calculated with all dataset questions.
4. The chatbot returns the **most similar question and its answer**.

This allows the chatbot to understand different variations of the same question.

---

# Running the Chatbot

### Install dependencies

```bash
pip install -r requirements.txt