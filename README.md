# ImmiAssistAi
This project is an AI-powered web application designed to assist users with immigration-related inquiries. It features an intelligent, multi-agent system built with Python, Django, and Celery that processes user requests asynchronously.

# AI-Powered Immigration Assistant

This project is a sophisticated, AI-powered web application designed to assist users with complex immigration-related inquiries. It leverages a multi-agent system to understand user needs, process data, and perform tasks like web scraping and data organization.

## Key Features

* **Natural Language Chat Interface:** Users can interact with the application through simple chat, asking questions in plain English.
* **Structured Profile Creation:** A dedicated form allows users to input detailed personal, professional, and educational information for tailored assistance.
* **Asynchronous Task Processing:** Utilizes Celery to handle long-running AI and web scraping tasks in the background, ensuring the user interface remains responsive.
* **Multi-Agent AI Backend:** The core of the application is a powerful system of interconnected AI agents, each with a specialized role, orchestrated to handle complex workflows.
* **Dynamic Web Scraping:** The application can dynamically scrape websites to find relevant institutions (universities, companies) and extract specific details like application requirements and deadlines.
* **Structured Data Handling:** Employs Pydantic for robust data validation and structuring, ensuring data integrity throughout the AI processing pipeline.

## How It Works: Architectural Overview

The application follows a clean, decoupled architecture that separates the user interface from the complex backend processing.

1. **User Interaction (Django Views):** The user interacts with the frontend via Django-rendered templates. The main entry points are the `chat_interface` and the `profile_creation_form`.
2. **Task Delegation (Celery):** When a user submits a query or a form, the Django view doesn't process it directly. Instead, it creates an asynchronous task and delegates it to a Celery worker. This returns a `task_id` to the frontend immediately.
3. **Frontend Polling:** The frontend uses the `task_id` to periodically poll an endpoint (`get_task_result`) to check the status of the task and retrieve the result when it's ready.
4. **Core AI Logic:** The Celery task executes the main `process_request` function in `ai_logic.py`, which kicks off the AI agent workflow.

## The AI Agent System

The intelligence of this application comes from a hierarchy of specialized AI agents built with `pydantic-ai`. They work together to interpret and execute user requests.

### 1. `Command_evaluation_agent`
This is the "brain" of the operation. It has two primary responsibilities:
* **Initial Input Processing:** It receives the raw input from the user (either a chat message or a JSON object from the profile form) and translates it into a structured, actionable command. This command is encapsulated in a `CommandGen` object, which contains the `Command` to be executed and the necessary `Context`.
* **Output Evaluation:** (Future capability) It's designed to evaluate the output of other agents to ensure quality and can trigger new commands if the result is unsatisfactory.

### 2. `Orchestrator_agent`
This is the "director" or "router." It receives the `CommandGen` object from the `Command_evaluation_agent`. Its sole purpose is to decide which specialized agent (or "tool") is best suited to execute the command and then call it.

### 3. Specialized Agents (Tools)
These are the "workers" that perform the actual tasks, implemented as tools for the `Orchestrator_agent`.

* **`User_AssistantAgent`:** A general-purpose agent that handles conversational queries and provides information based on the context it's given.
* **`SearchingNameAgent`:** A web scraping agent that takes a query (e.g., "Data Science Masters in Germany") and searches the web to generate a list of names of relevant institutions (universities, companies).
* **`SearchingDetailAgent`:** A more focused web scraping agent. It takes a list of names (from the `SearchingNameAgent`) and visits their websites to extract specific, detailed information like admission requirements, deadlines, etc.
* **`Save_data_to_file`:** This agent is triggered when a user submits the profile form. It takes the validated `ImmigrationProfileModel` and saves it as a JSON file (`llm_extracted_data.json`) for persistence and later use.

## Data Models (Pydantic)

The entire system relies on Pydantic models for structuring and validating data. This ensures that information flows between agents in a predictable and error-free manner.

* **`ImmigrationProfileModel`:** A comprehensive model that defines the structure of a user's profile, including fields for education, work experience, financial status, and more.
* **`CommandGen`:** The standardized object for passing instructions between the evaluation and orchestration agents.
* **`output_agent`:** A generic wrapper for all agent outputs, indicating the type of request and the data payload. This allows the frontend to correctly interpret and display the results.

## Technologies Used

* **Backend:** Django
* **Asynchronous Tasks:** Celery, Redis/RabbitMQ (as a message broker)
* **AI & Data Modeling:** pydantic-ai, OpenAI
* **Database:** SQLite (for Django's default ORM)
* **Environment Management:** python-dotenv

## Getting Started

### Prerequisites
* Python 3.9+
* An OpenAI API Key
* A message broker like Redis or RabbitMQ for Celery.

### Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone <your-repo-url>
   cd <your-repo-directory>
   ```

2. **Create a virtual environment and activate it:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install dependencies:**
   *This project uses a `requirements.txt` file. Install the packages using pip:*
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file in the project root and add your API keys:
   ```
   Main_agents_key="your_openai_api_key_for_main_agents"
   Sub_Agent_Key="your_openai_api_key_for_sub_agents"
   ```

5. **Run Django database migrations:**
   ```bash
   python ai_immigration_ui/manage.py migrate
   ```

### Running the Application

You need to run two separate processes: the Django development server and the Celery worker.

1. **Start the Celery Worker:**
   Open a terminal and run:
   ```bash
   celery -A ai_immigration_ui.ai_immigration_ui worker --loglevel=info
   ```

2. **Start the Django Development Server:**
   Open a second terminal and run:
   ```bash
   python ai_immigration_ui/manage.py runserver
   ```

The application will now be available at `http://127.0.0.1:8000/`.
