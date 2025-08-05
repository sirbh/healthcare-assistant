# Health Care Assistant

This assistant is a multi-agent app that takes user input and provides diagnosis and lifestyle advice.

App is Live At : [https://healthcare-assistant-woad.vercel.app](https://healthcare-assistant-woad.vercel.app)


## System Design

- **Agents Directory:** `backend/app/agents/`
- **Agents Graph File:** `backend/app/graph/health_care_assistant_graph.py`

![System Diagrame](./system_diag.png)

## Agents Workflow



1. **Summarizer Agent (Long Conversation Management)**  
   To maintain long-running conversations, the **Summarizer Agent** sits in front of the **Supervisor Agent**.  
   - It checks if the list of user messages exceeds 40.
   - If it does, it summarizes the previous messages.
   - The summary is then passed to the Supervisor Agent instead of the full message history.

2. **User Input Handling**  
   The **Supervisor Agent** receives input from the user.

3. **Symptom Detection & Document Retrieval**  
   If the input contains any symptoms, the Supervisor retrieves relevant documents based on those symptoms.

4. **Relevance Evaluation**  
   The retrieved documents are passed to the **Evaluator Agent**, which assesses whether the documents are relevant to the identified symptoms.

5. **Follow-up Questioning**  
   - If the Evaluator confirms the documents are relevant, the Supervisor asks the user follow-up questions based on the document content.
   - Once the user responds, the Supervisor compiles:
     - The user’s answers  
     - Identified symptoms  
     - User profile (including age, sex, and known conditions)

6. **Diagnosis**  
   The compiled information is sent to the **Diagnostic Agent**, which returns a diagnostic outcome.  
   The Supervisor then shares this outcome with the user.

7. **Recommendations and Explanations**  
   - The **Supervisor Agent** has access to:
     - The **Recommendation Agent** (for treatment or next steps)  
     - The **Explanation Agent** (for detailed clarification)
   - If the user asks for recommendations or explanations, the Supervisor consults the appropriate agent and returns the response.

8. **Memory Update**  
   After each interaction, the **Memory Writer Agent** updates the user profile based on the latest conversation.

## Symptom-Based FAISS Retriever

## Symptom-Based FAISS Retriever

This retriever loads symptom data from a CSV file and creates a FAISS vector store using OpenAI embeddings with cosine similarity. Each symptom is embedded and stored along with metadata like associated conditions and follow-up questions.

- **Embedding Field:** Only the `symptom` field is embedded.
- **Reason:** Since users initially provide only symptoms, embedding additional fields like conditions or questions may introduce noise and reduce retrieval accuracy.
- **Metadata:** Includes `conditions` and `follow_up_questions`, which are not embedded but are stored for use after retrieval.
- **Indexing:** Uses a normalized inner product (`IndexFlatIP`) to approximate cosine similarity.
- **Persistence:** If a saved index exists, it is loaded; otherwise, a new index is created and saved.

After the relevant documents are fetched based on symptom similarity, they are passed to a **Relevance Evaluator Agent**. This agent checks whether the fetched documents are relevant to the user's reported symptoms before proceeding further.

This setup allow additional layer of validation to ensure accuracy.


## Key Features of the system

* **Supervisor-agent architecture**: A central supervisor delegates user queries to specialized agents based on the context.

* **Knowledge-base backed**: Suggestions are strictly drawn from the predefined knowledge base; unknown queries are rejected.

* **Profile-driven guidance**: Starts by collecting user profile details (e.g., age, gender, known condition) to offer tailored advice.

* **Dynamic profile updates**: The user profile is continuously updated as new information is shared.

* **Short-term memory**: Maintained using a `thread id` to handle ongoing conversations.

* **Long-term memory**: Retained using a `user id` to personalize interactions over different chat

* **Chat summarization**: Once the message count reaches 40, the system summarizes the conversation to support long-running sessions.



## Functional Features of the App

- **Multiple Chats per User**  
  Users can create and manage multiple conversations under the same user namespace.

- **Long-Running Conversations**  
  A **Summarizer Agent** helps maintain long conversations by summarizing message history when it exceeds a limit of 40 messages.

- **Short-Term Memory Support**  
  Each chat is mapped with chatid so that it can be fetched later.

- **Long-Term Memory Support**  
  A persistent memory shared across all chats for a user, allowing the system to recall key information like conditions, age, and gender.

- **Private and Public Chats**  
  Users can mark conversations as **private** (accessible only to them) or **public** (visible in shared/public view).

- **Theme Selection**  
  Users can toggle between **dark mode** and **light mode** for a personalized visual experience.







# Running the Project Locally

This project consists of two parts:

* **Frontend**: A [Next.js](https://nextjs.org/) application
* **Backend**: A set of services managed with Docker Compose

---

## Prerequisites

Before you begin, make sure you have the following installed:

* [Node.js](https://nodejs.org/) (v18 or higher recommended)
* [npm](https://www.npmjs.com/)
* [Docker](https://www.docker.com/)
* [Docker Compose](https://docs.docker.com/compose/)

---

## Step 1: Start the Frontend (Next.js) in Development Mode

Before starting the frontend, make sure to create a `.env` file in the `frontend` directory with the following contents:

```env
NEXT_PUBLIC_BASE_URL=http://127.0.0.1:8000
```

1. Open a terminal window.

2. Navigate to the frontend directory:

   ```bash
   cd frontend
   ```

3. Install dependencies:

   ```bash
   npm install
   ```

4. Start the development server:

   ```bash
   npm run dev
   ```

5. The app should now be running at: [http://localhost:3000](http://localhost:3000)

---

## Step 2: Start the Backend using Docker Compose

1. Open a second terminal window.

2. Navigate to the backend directory:

   ```bash
   cd backend
   ```

3. Make sure to create a `.env` file in the backend directory with the following contents:

   ```env
   DATABASE_URL="postgresql://postgres:postgres@localhost:5432/chatdb"
   OPENAI_API_KEY=""
   ```

4. Run the backend services:

   ```bash
   docker compose -f docker-compose.prod.yml up
   ```

   This will start all backend services defined in the `docker-compose.prod.yml` file.

---

## Notes

* Ensure that all required `.env` files exist in both the frontend and backend directories.
* Make sure ports used by the frontend and backend services are free or change them in the configs.
* To stop the backend services, use `Ctrl+C` in the terminal or run:

  ```bash
  docker compose -f docker-compose.prod.yml down
  ```
