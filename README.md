# 🧠 AI-First CRM HCP Module – LogInteractionScreen

## 📌 Project Overview

**AI-First CRM HCP Module** focuses on designing and developing the **Log Interaction Screen** for a modern Customer Relationship Management (CRM) system tailored specifically for **Healthcare Professionals (HCPs)**. This screen is designed from the perspective of a life science expert, enabling field representatives to record and manage interactions with HCPs either through a **structured form** or an **AI-powered conversational interface**.

## 🎯 Objective

To conceptualize and build a robust, scalable, and intelligent module that:
- Logs HCP interactions seamlessly using either forms or chat-based input.
- Leverages advanced **LLMs** to understand, summarize, and extract key insights from interaction data.
- Provides sales representatives with the ability to **log**, **edit**, and manage interactions efficiently using **LangGraph agents** and purpose-built tools.

## ⚙️ Tech Stack

| Layer      | Technology                                       |
|------------|--------------------------------------------------|
| Frontend   | ReactJS + Redux (UI/UX with Google Inter font)   |
| Backend    | Python + FastAPI                                 |
| AI Agent   | LangGraph framework                              |
| LLMs       | `gemma2-9b-it` via Groq API                      |
| Database   | MPostgreSQL                                      |

## 🧠 LangGraph AI Agent & Tools

The **LangGraph agent** orchestrates intelligent HCP interaction management. It serves as the backbone for automating, assisting, and enhancing CRM functionalities using structured tool-based logic.

### 🔧 Agent Tools

Below are the five core tools implemented within the LangGraph agent:

1. **Log Interaction**
   - Captures user input via form or conversation.
   - Utilizes LLMs to summarize dialogue, extract entities (e.g., doctor name, medication), and auto-fill structured fields.

2. **Edit Interaction**
   - Allows users to modify previous entries.
   - Ensures validation and context awareness through LangGraph’s memory features.

3. **Generate Meeting Summary**
   - Automatically generates a summary of the HCP meeting from raw input.
   - Uses LLM to ensure key points and outcomes are captured.

4. **Suggest Next Steps**
   - Based on previous interactions, the agent recommends follow-up actions (e.g., scheduling visits, sending resources).

5. **Fetch Interaction History**
   - Retrieves past interactions for the same HCP.
   - Helps in providing context to new engagements or tracking patterns.

## 🖼️ UI/UX Features

- Modern responsive interface using **React** with Redux for state management.
- Dual input mode: **Form-based logging** & **Conversational AI chat**.
- Consistent typography using **Google Inter font** for professional appeal.

## 🔐 API & Model Integration

- Uses **Groq's** inference engine for blazing-fast access to `gemma2-9b-it` and optionally `llama-3.3-70b-versatile`.
- A dedicated API key is used to authenticate requests.
