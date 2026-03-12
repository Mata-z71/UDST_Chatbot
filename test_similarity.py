from chatbot import Chatbot

bot = Chatbot("udst_faq.csv")

test_questions = [

    # =========================
    # 1) Similar to dataset
    # =========================

    # Colleges
    "How many colleges are there in UDST?",
    "What colleges are in UDST?",
    "Does UDST have a computing college?",
    "Which college offers business programs?",
    "Which college offers engineering programs?",

    # Programs
    "What programs are offered at UDST?",
    "What majors are available at UDST?",
    "What can I study at UDST?",
    "Does UDST offer diploma programs?",
    "Does UDST offer bachelor programs?",
    "Does UDST offer master programs?",
    "What IT programs does UDST have?",
    "Does UDST offer software engineering?",
    "Does UDST offer cyber security?",
    "What business programs are available at UDST?",
    "What engineering programs are available?",
    "What health sciences programs are offered?",
    "Does UDST offer nursing?",

    # About UDST
    "What is UDST?",
    "What does UDST stand for?",
    "Where is UDST located?",
    "Is UDST a public university?",
    "What is the official UDST website?",
    "Who is the president of UDST?",
    "Does UDST have a library?",
    "What student services does UDST offer?",

    # =========================
    # 2) Different wording
    # =========================

    # Colleges
    "What schools are in UDST?",
    "What faculties exist at UDST?",
    "Is there an engineering faculty at UDST?",
    "Does UDST have a health related college?",
    "Which part of UDST has business studies?",

    # Programs
    "What fields can students study at UDST?",
    "Can I get a diploma from UDST?",
    "Is there a software engineering program?",
    "Can I study AI at UDST?",
    "Do they have cybersecurity at UDST?",
    "What can I study in the business college?",
    "What can I study in engineering at UDST?",
    "Are there nursing programs at UDST?",
    "What can I study in computing?",

    # About UDST
    "Tell me about UDST",
    "What kind of university is UDST?",
    "Which country is UDST in?",
    "Why choose UDST?",
    "Does UDST have a campus map?",
    "Where can students get help at UDST?",
    "Is there student support at UDST?",
    "What is student life like at UDST?",

    # =========================
    # 3) Short student queries
    # =========================

    "UDST colleges",
    "UDST programs",
    "business programs",
    "engineering programs",
    "IT programs UDST",
    "AI program UDST",
    "UDST information",
    "UDST website",
    "UDST president",

    # =========================
    # 4) Out of scope
    # =========================

    "What is the weather today?",
    "Tell me about restaurants near UDST",
    "How to cook pasta",
    "Latest football news",
    "What is the price of gold today?"
]

for q in test_questions:
    answer, category, score = bot.get_response(q)

    print("User Question :", q)
    print("Category      :", category)
    print("Score         :", round(score, 3))
    print("Answer        :", answer)
    print("-" * 60)