# ComplaintIQ Documentation

## Overview
ComplaintIQ is a Unified Customer Complaint Communication Dashboard powered by Gen-AI. It aggregates complaints from multiple channels into a single intelligent platform. The system uses NLP and Gen-AI to automatically categorize complaints, extract key issues, identify duplicate or related complaints, and suggest resolution templates. It provides a 360-degree view of each complaint with full communication history, SLA tracking, escalation management, and regulatory reporting capabilities.

## Repository Link
**GitHub Repository:**  : [Complain HQ](https://github.com/tridibesh9/Idea-2.0)

## Key Points & Architecture

### 1. Ingestion Engine
* **Listeners**: Continuously monitor incoming emails, Telegram bot webhooks, web forms, and social media channels.
* **Smart Router**: Resolves mapping of categories to departments and routes tickets to the agent with the lowest active workload to balance the queue.

### 2. Gen-AI & Vector Layer
* **Gemini Classifier**: Determines metadata (Sentiment, Severity, Key Issues, regulatory warnings) in real-time.
* **pgvector Embeddings**: High-dimensional vectors created using `models/gemini-embedding-2` and stored in PostgreSQL. Used for finding similar historical tickets and matching relevant articles in the RAG Knowledge Base.

### 3. Agent UI & Dashboard
* **Live Feed**: Instant server notifications of incoming issues or SLA breaches using WebSockets.
* **Draft Refinement**: Iterative modification of AI draft responses by agents using natural language instructions.
* **Cluster Scatter Chart**: Projects embeddings into 2D spaces using PCA and visualizes them using K-Means clustering.

## Features List

- **Multi-channel complaint aggregation:** Seamlessly ingests from Email, chat, Twitter, phone, and web forms.
- **AI-powered complaint classification:** Automatically categorizes by category, product, severity, and sentiment.
- **Duplicate/similar complaint detection:** Uses pgvector embeddings to find related historical tickets instantly.
- **Automated draft responses:** Includes tone selection (formal, empathetic, neutral).
- **SLA tracking & escalation management:** Includes background scheduler for automated breach checks and alert notifications.
- **Real-time updates:** WebSocket-powered live feed for continuous monitoring.
- **360° complaint view:** Full communication history and ticket lifecycle tracking.
- **Root cause analysis:** Provides trend insights across complaint data to identify systemic issues.
- **Audit logging:** Comprehensive logging for compliance & regulatory tracking.
- **Responsive React frontend:** Includes a live analytics dashboard with real-time charts.
- **RAG-Powered Knowledge Base:** Retrieves relevant company support policies using pgvector semantic search to guide Gemini draft responses.
- **Iterative Response Refinement:** Agents can interactively refine Gemini response drafts using natural language commands.
- **Interactive PCA Cluster Mapping:** Visualizes high-dimensional complaint embeddings as an interactive scatter map on the dashboard to spot issue clusters.
- **Workload-Balanced Smart Routing:** Automatically routes and assigns incoming complaints to agents based on their current active workload.
- **Two-Way Channel Simulator:** Interactive simulator module for testing incoming/outgoing communications across mock Email and Telegram channels.

## Tech Stack
- **Frontend**: React 18, Vite, Tailwind CSS, Recharts
- **Backend**: FastAPI (Python 3.11)
- **Database**: PostgreSQL with pgvector
- **AI/LLM**: Google Gemini 2.0/2.5 Flash API, Google gemini-embedding-2
- **Real-time**: WebSockets (FastAPI)
- **Deployment**: Docker Compose
