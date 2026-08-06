# Council of High Intelligence (v0 Clone)

This is a simple, highly readable multi-agent system designed to teach 2nd and 3rd year students how AI orchestration and agentic workflows operate in Python.

It mimics the functionality of `v0.dev` or `lovable.dev` by:
1. Taking a raw user prompt.
2. Spinning up a council of 5 agents (PM, Designer, Security, Interviewer, Plan Generator) to debate the idea in a live group chat.
3. Using a 6th agent (Coding Agent) to write the final HTML, CSS, and JS.
4. Rendering the final output live in an `iframe`.

## How to run:

1. Navigate to this directory in your terminal.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Set your Mistral API key (or create a `.env` file in this directory containing `MISTRAL_API_KEY=your_key`):
   ```bash
   export MISTRAL_API_KEY="your_mistral_key"
   ```
4. Run the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```
5. Open your web browser and go to `http://127.0.0.1:8000`

## Architecture overview for Students
- `main.py`: Contains the FastAPI backend and the core Agent Orchestration loop. Read the `agent_loop` function to see how Server-Sent Events (SSE) stream the AI's thoughts back to the browser in real-time.
- `static/index.html`: The HTML structure of the page.
- `static/style.css`: The styling.
- `static/script.js`: Contains the JavaScript that connects to the Python SSE stream and dynamically updates the UI.
