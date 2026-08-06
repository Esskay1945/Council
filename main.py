import os
import json
import asyncio
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Load environment variables from a .env file (if it exists)
load_dotenv()

# Initialize the FastAPI app
app = FastAPI()

# Tell FastAPI to serve the static folder for our HTML, CSS, and JS
app.mount("/static", StaticFiles(directory="static"), name="static")

# Get the API key from the environment
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "")
print(MISTRAL_API_KEY)
# ---------------------------------------------------------
# Helper Function: Call the Mistral API
# ---------------------------------------------------------
async def call_mistral(messages, model="mistral-small-latest", max_tokens=400):
    """
    This function makes a simple HTTP POST request to the Mistral API.
    We use mistral-small-latest for ultra-fast low-latency responses.
    """
    if not MISTRAL_API_KEY or MISTRAL_API_KEY == "your_mistral_api_key_here":
        raise ValueError("MISTRAL_API_KEY is missing! Please set your key in a .env file (MISTRAL_API_KEY=your_key) or environment variable.")

    url = "https://api.mistral.ai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, headers=headers, json=data)
        if response.status_code == 401:
            raise ValueError("Mistral API Key Unauthorized (401). Please verify your MISTRAL_API_KEY.")
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

# ---------------------------------------------------------
# Core Logic: Multi-Round Agent Debate Loop
# ---------------------------------------------------------
MAX_REVISIONS = 3
TARGET_SCORE = 90
async def agent_loop(user_prompt: str):
    """
    This is an asynchronous generator. It yields (streams) data back to the
    frontend as Server-Sent Events (SSE) so the user sees the chat live.
    """
    
    # 1. Shared conversation memory for the council
    conversation_history = [
        {"role": "user", "content": f"User Request: '{user_prompt}'"}
    ]
    
    # 2. Multi-Round Debate Agenda
    debate_sequence = [
        {
            "name": "Product Manager",
            "role": "You are a Senior Product Manager. Briefly propose a core feature list and user flow for the user's request. Keep it punchy, technical, and concise (under 150 words)."
        },
        {
            "name": "UI/UX Designer",
            "role": "You are a world-class UI/UX Designer. Based on the PM's proposal, briefly outline the visual design: HSL color palette, dark mode aesthetic, flex/grid layout, and key micro-interactions (under 150 words)."
        },
        {
            "name": "Security Agent",
            "role": "You are a Senior Security Architect. Briefly review the PM and Designer proposals. Identify security vulnerabilities, input sanitization, and DOM edge cases (under 100 words)."
        },
        {
            "name": "The Interviewer",
            "role": "You are the Devil's Advocate. Interrogate the PM, Designer, and Security Agent. Directly attack their proposals, point out unnecessary bloat, and demand pros/cons justification (under 150 words)."
        },
        {
            "name": "Product Manager (Rebuttal)",
            "role": "You are the Product Manager. Briefly defend essential features against The Interviewer's attack and drop useless bloat (under 100 words)."
        },
        {
            "name": "UI/UX Designer (Rebuttal)",
            "role": "You are the UI/UX Designer. Briefly simplify layout complexities while keeping the UI modern and high-end (under 100 words)."
        },
        {
            "name": "Implementation Plan Generator",
            "role": "You are a Staff Software Architect. Synthesize this debate into a strict, bulleted Technical Implementation Plan for HTML/CSS/JS (under 200 words)."
        }
    ]
    
    # 3. Stream each debate stage with ultra-low latency
    for step in debate_sequence:
        yield f"data: {json.dumps({'agent': step['name'], 'status': 'typing'})}\n\n"
        
        messages_for_api = conversation_history.copy()
        messages_for_api.append({"role": "system", "content": step["role"]})
        
        try:
            reply = await call_mistral(messages_for_api, model="mistral-small-latest", max_tokens=350)
        except Exception as e:
            reply = f"🚨 {str(e)}"
            
        conversation_history.append({"role": "assistant", "content": f"{step['name']}: {reply}"})
        
        yield f"data: {json.dumps({'agent': step['name'], 'message': reply})}\n\n"
        
    # ---------------------------------------------------------
    # 4. Final Stage: The Coding Agent Execution
    # ---------------------------------------------------------
    tester_prompt = (
    "You are a Frontend QA Tester.\n"
    "Review the HTML, CSS and JavaScript.\n"
    "Check for:\n"
    "- Missing functions\n"
    "- Broken event listeners\n"
    "- Invalid selectors\n"
    "- Syntax errors\n"
    "- Integration issues\n\n"
    "Return ONLY valid JSON in this format:\n"
    '{'
    '"score":95,'
    '"issues":["issue1","issue2"]'
    '}'
    )
    coding_agent_name = "Coding Agent"
    tester_agent_name = "Tester"

    current_code = ""
    best_code = ""
    best_score = 0
    test_result={}
    for revision in range(MAX_REVISIONS):

        yield f"data: {json.dumps({'agent': coding_agent_name,'status':'typing','revision':revision+1})}\n\n"

        if revision == 0:

            coding_prompt = (
            "You are a Senior Frontend Developer.\n"
            "Using the implementation plan, generate one complete HTML file.\n"
            "Embed CSS in <style> and JavaScript in <script>.\n"
            "Implement all requested features.\n"
            "Return only valid HTML beginning with <!DOCTYPE html>."
            )

            messages = conversation_history.copy()
            messages.append({
            "role": "system",
            "content": coding_prompt
            })

        else:

            fix_prompt = (
            "You are a Senior Frontend Developer.\n"
            "Here is the current HTML:\n\n"
            f"{current_code}\n\n"
            "Tester found these issues:\n"
            + "\n".join(test_result["issues"]) +
            "\n\nFix ONLY these issues.\n"
            "Return the complete corrected HTML."
            )

            messages = [
            {
                "role": "system",
                "content": fix_prompt
            }
            ]

        current_code = await call_mistral(
        messages,
        model="mistral-small-latest",
        max_tokens=6500
        )

        current_code = current_code.replace("```html", "").replace("```", "").strip()

        yield f"data: {json.dumps({'agent': coding_agent_name,'code':current_code})}\n\n"

        yield f"data: {json.dumps({'agent': tester_agent_name,'status':'typing'})}\n\n"

        tester_messages = [
        {
            "role":"system",
            "content":tester_prompt
        },
        {
            "role":"user",
            "content":current_code
        }
        ]

        try:

            tester_reply = await call_mistral(
            tester_messages,
            model="mistral-small-latest",
            max_tokens=300
            )

            tester_result = json.loads(tester_reply)

        except Exception:

            tester_result = {
            "score":0,
            "issues":["Tester failed to parse response."]
            }

        score = tester_result["score"]

        if score > best_score:
            best_score = score
            best_code = current_code

        yield f"data: {json.dumps({'agent':tester_agent_name,'message':tester_result})}\n\n"

        if score >= TARGET_SCORE:
            break

    yield f"data: {json.dumps({'agent':'Final','code':best_code,'score':best_score})}\n\n"

    yield "data: [DONE]\n\n"


# ---------------------------------------------------------
# API Routes
# ---------------------------------------------------------

@app.get("/api/stream")
async def stream_debate(prompt: str):
    """
    This endpoint is called by the frontend. It returns a StreamingResponse
    which keeps the connection open and sends data chunks as they become available.
    """
    return StreamingResponse(agent_loop(prompt), media_type="text/event-stream")

@app.get("/", response_class=HTMLResponse)
async def read_index():
    """
    Serve the main HTML page when a user visits the root URL (http://127.0.0.1:8000/)
    """
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()
