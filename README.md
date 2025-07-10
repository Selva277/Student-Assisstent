---

# 🎓 EduMate AI – Your Personal AI Tutor

## 📌 Overview

**EduMate AI** is a smart virtual tutoring system designed to make learning interactive and accessible for everyone. Using **Gemini API** (Google’s Generative AI) and Python, EduMate explains concepts, answers questions, generates quizzes, and summarizes study material in real time. The system leverages **FAISS** for fast semantic search to find the most relevant content from your uploaded resources.

---

## ✨ Key Features

* ✅ **Conversational Tutoring:** Explains topics naturally and conversationally using Gemini.
* ✅ **Multi-Subject Support:** Covers Math, Science, English, and more.
* ✅ **Semantic Search Engine:** FAISS retrieves relevant study materials quickly.
* ✅ **Quiz Generation:** Builds practice quizzes with instant feedback.
* ✅ **Topic Summarization:** Breaks down complex subjects into simple summaries.
* ✅ **Study Material Upload:** Ingests PDFs and text files to enrich the knowledge base.

---

## ⚙️ Tech Stack

* **Language:** Python 3.x
* **AI Model:** Gemini API (Google Generative AI)
* **Vector Store:** FAISS (Facebook AI Similarity Search)
* **Web Framework:** Streamlit / Flask
* **PDF/Text Parser:** PyMuPDF, pdfplumber
* **Environment Management:** python-dotenv

---

## 🚀 How to Run the Project

1. **Clone the Repository**

   ```bash
   git clone https://github.com/your-username/edumate-ai.git
   cd edumate-ai
   ```

2. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API Keys**
   Create a `.env` file:

   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   ```

4. **Run the Application**

   * For **Streamlit**:

     ```bash
     streamlit run app.py
     ```
   * For **Flask**:

     ```bash
     python app.py
     ```

5. **Access the App**

   ```
   http://localhost:8501 (Streamlit)
   or
   http://localhost:5000 (Flask)
   ```

---

## 📝 How It Works

1. Upload study materials (PDF or text).
2. The content is embedded and indexed using **FAISS**.
3. Ask questions in plain language (e.g., “Explain photosynthesis”).
4. EduMate retrieves relevant snippets with FAISS and uses **Gemini** to craft an answer.
5. You can also:

   * Generate quizzes on any topic
   * Summarize long materials
   * Get follow-up explanations

---

## 🎯 Use Cases

* Personal online tutoring
* Homework assistance
* Exam preparation
* Self-paced learning

---

## 💡 Future Enhancements

* Voice-based Q\&A
* Learning progress tracking
* LMS integrations
* Support for multiple languages

---


