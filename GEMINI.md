# Project Overview

This project is a Python-based web application designed for intelligent management of travel photos. It uses a system of five specialized AI agents to automatically organize, assess, categorize, and caption photographs. The application provides both a web interface and a command-line interface (CLI) for interacting with the system.

The core of the application is a workflow that processes images through a series of agents:
1.  **Metadata Extraction Agent:** Extracts EXIF, GPS, and camera data.
2.  **Quality Assessment Agent:** Evaluates technical quality like sharpness and exposure.
3.  **Aesthetic Assessment Agent:** Assesses artistic composition.
4.  **Filtering & Categorization Agent:** Categorizes images and filters them based on quality.
5.  **Caption Generation Agent:** Generates descriptive captions.

The backend is built with Python, using Flask for the web server. The AI capabilities are powered by Google's Vertex AI with Gemini. The frontend is built with HTML, CSS, and vanilla JavaScript.

# Building and Running

The project uses `uv` for package management.

## Installation

1.  **Install `uv`:**
    ```bash
    curl -LsSf https://astral.sh/uv/install.sh | sh
    ```
2.  **Install dependencies:**
    ```bash
    uv sync
    ```
3.  **Set up environment variables:**
    ```bash
    cp .env.example .env
    ```

## Configuration

-   **Vertex AI:** Configure your Google Cloud project details in `config.yaml`:
    ```yaml
    vertex_ai:
      project: "your-project-id"
      location: "us-central1"
    ```
-   **Authentication:** Set up Application Default Credentials (ADC) for Vertex AI:
    ```bash
    gcloud auth application-default login
    ```

## Running the Application

### Web App

-   **Start the Flask server:**
    ```bash
    uv run python web_app/app.py
    ```
-   Access the application at `http://localhost:5001`.

### CLI

-   **Run the workflow on sample images:**
    ```bash
    uv run python orchestrator.py
    ```

# Development Conventions

-   **Code Style:** The project follows standard Python conventions (PEP 8).
-   **Configuration:** Application settings are managed in `config.yaml`, allowing for easy modification of agent behavior, API keys, and thresholds.
-   **Modularity:** The project is organized into distinct modules: `agents`, `utils`, and `web_app`, promoting separation of concerns.
-   **Logging:** The application uses a structured logging setup, with logs saved to the `output` directory.
-   **Error Handling:** The orchestrator includes error handling and retry logic for agent execution.
-   **Parallelization:** The workflow uses a `ThreadPoolExecutor` to run agents in parallel for improved performance.
-   **Testing:** While no dedicated testing framework is immediately apparent, the modular structure and validation utilities suggest that testing is a consideration.
