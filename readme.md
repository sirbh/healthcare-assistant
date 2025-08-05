# Health Care Assistant

This assistant is a multi-agent app that takes user input and provides diagnosis and lifestyle advice.

App is Live At : [https://healthcare-assistant-woad.vercel.app](https://healthcare-assistant-woad.vercel.app)

## System Diagrame

![System Diagrame](./system_diag.png)


## Key Features

* **Supervisor-agent architecture**: A central supervisor delegates user queries to specialized agents based on the context.

* **Knowledge-base backed**: Suggestions are strictly drawn from the predefined knowledge base; unknown queries are rejected.

* **Profile-driven guidance**: Starts by collecting user profile details (e.g., age, gender, known condition) to offer tailored advice.

* **Dynamic profile updates**: The user profile is continuously updated as new information is shared.

* **Short-term memory**: Maintained using a `thread id` to handle ongoing conversations.

* **Long-term memory**: Retained using a `user id` to personalize interactions over different chat

* **Chat summarization**: Once the message count reaches 40, the system summarizes the conversation to support long-running sessions.






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
