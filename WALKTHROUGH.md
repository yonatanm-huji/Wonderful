# Pharmacy Agent – Block-by-Block Walkthrough

A guided tour of how the pharmacy agent is built: MD files first, then Python, with notes and improvement ideas.

---

## Part 1: The Markdown (Docs)

### README.md

**What it does:** Entry point for the project. It explains:

- **Goal:** Pharmacy agent for medication info, inventory, prescriptions.
- **How to run:** Clone, set `OPENAI_API_KEY`, `docker-compose up` or local Flask.
- **Stack:** Python backend, HTML frontend, `pharmacy.db`, six tools.
- **Requirements:** Conversational, streaming, English + Hebrew, **safe** (no medical advice; refer to professionals when needed).
- **Results:** Best at medication info; multi-tool and safety flows can be inconsistent (you documented this in `0_results_EVALUATION_PLAN.md`).
- **Database:** Three tables – Users, Medications, Prescriptions (10 users, 8 meds, sample prescriptions).
- **Tools:** Describes all six tools (Get Medication Info, Check Interactions, Check Inventory, Get User Allergies, Check Prescription, Refer to Professional) and what they need/return.

**Improvement:** Add a one-paragraph “Architecture” section: “Flask serves the UI and `/api/chat`; the agent in `src/agent/pharmacy_agent.py` uses OpenAI with function calling; tools in `src/tools/medication_tools.py` read/write `pharmacy.db`.”

---

### DOCKER_SETUP.md

**What it does:** How to run the app in Docker.

- **Prerequisites:** Docker, OpenAI API key.
- **Quick start:** `export OPENAI_API_KEY=...`, then `docker-compose up --build`, open http://localhost:5000.
- **Alternative:** `docker build` + `docker run` with `-e OPENAI_API_KEY=...`.
- **On startup:** Install deps, init DB (users, meds, prescriptions), add 3 interacting meds, start Flask on 5000.
- **Troubleshooting:** Port 5000 in use, API key, logs, dev mount, persistence, cleanup.
- **Security:** Don’t commit `.env` or hardcode keys.

**Improvement:** Mention where the DB is created (e.g. `init_db.py` or entrypoint) so someone can change or persist it.

---

### MULTI_STEP_FLOWS.md

**What it does:** Defines three target multi-step workflows for testing and evaluation.

1. **Flow 1 – Allergy safety:** “Can I pick up Amoxicillin for Jalen Brunson?”  
   Expected: `get_medication_info("Amoxicillin")` + `get_user_allergies("Jalen Brunson")` → detect penicillin allergy → warn, do not dispense, refer for alternatives.

2. **Flow 2 – Drug interaction:** “Do you have Aspirin?” then “I am taking Warfarin.”  
   Expected: inventory check, then interaction check, then strong warning (Aspirin + Warfarin), then refer for alternatives.

3. **Flow 3 – New prescription education:** “I just got prescribed Semaglutide. What is it?” then side effects, stock, interactions.  
   Expected: medication info, then side effects from context, then inventory, then interactions; stay factual.

Also: success criteria, Hebrew test prompts, expected tool sequences, and what screenshots to take.

**Important:** The doc assumes the agent can call `get_user_allergies`. In the current code, **that tool is not exposed to the model** (see Part 2 – agent/tools), so Flow 1 cannot work as designed until that’s fixed.

---

### 1_clean_EVALUATION_PLAN.md

**What it does:** The “clean” evaluation plan: objectives (accurate info, safety, policy, tool use, bilingual, context), methodology (functional tests, safety tests, tool matrix, language, edge cases), and how to record results.

---

### 0_results_EVALUATION_PLAN.md

**What it does:** Same structure as the clean plan, plus your **actual results and limitations**:

- Multi-tool orchestration is inconsistent (e.g. doesn’t always call both medication info and allergies).
- Tool result mistrust: agent sometimes says it “can’t check” even after a successful tool call.
- Query phrasing: “If I’m taking Warfarin, can I take Aspirin?” triggers refer-to-professional instead of interaction lookup.

You correctly note that tools work when called; the issues are LLM behavior and orchestration, and that ReAct or another multi-step framework could help.

---

## Part 2: The Python – Entry and Web Layer

### app.py (block by block)

```python
# Lines 1–15: Imports and path
```
- Flask app, CORS, json, sys, os.
- `sys.path.append(...'src')` so `from agent.pharmacy_agent import PharmacyAgent` works when running from project root.

```python
# Lines 17–21: App and agent
app = Flask(__name__)
CORS(app)
agent = PharmacyAgent()
```
- One global agent instance. All users share the same conversation history (fine for a single-user / demo; for multi-user you’d key history by session).

```python
# Lines 23–25: GET /
def index():
    return render_template('index.html')
```
- Serves the chat UI.

```python
# Lines 27–61: POST /api/chat
```
- Reads `message` from JSON.
- Calls `agent.chat(user_message, stream=False)` (non-streaming).
- **Tool-call extraction:** Scans `agent.conversation_history` backwards for the last assistant message that has `tool_calls`, then maps each to `{ name, arguments }` for the UI.
- Returns `{ response, tool_calls }` or 400/500.

**Improvement:** The UI shows tool calls from the **last** assistant message only. If the agent does multiple rounds (e.g. tools then a follow-up), only the last round’s tool calls are shown. You could instead return tool calls for the **current** turn (e.g. the turn that produced `response`) so multi-round flows are clearer.

```python
# Lines 64–68: POST /api/reset
```
- Calls `agent.reset_conversation()` and returns success.

```python
# Lines 70–121: POST /api/stream
```
- Intended for streaming, but the implementation **bypasses** the agent’s normal tool loop: it appends the user message, then calls `agent.client.chat.completions.create(..., stream=True)` with the same tools. It only yields **text** deltas; it does **not** handle tool_calls in the stream (no execution of tools, no second request with tool results). So if the model requests a tool in this path, the user never sees the tool run or the final answer that uses it.
- **Improvement:** Either remove `/api/stream` or implement it by: (1) streaming until you see tool_calls, (2) running tools, (3) sending tool results back and streaming the final reply (or falling back to non-streaming for the tool round, like `chat_stream` in the agent).

```python
# Lines 123–130: __main__
```
- Prints a short banner and runs `app.run(debug=True, port=5000)`.

---

## Part 3: The Agent

### src/agent/pharmacy_agent.py

**Role:** The brain. Holds system prompt, conversation history, and one round of “call model → if tool_calls → run tools → call model again with results.”

```python
# Imports and path (lines 1–18)
```
- OpenAI client, dotenv, and `sys.path` so `from tools.medication_tools import ...` works when running from `src/agent/`.

```python
# __init__ (lines 29–106)
```
- **API key:** From argument or `OPENAI_API_KEY` in env; raises if missing.
- **Client/model:** `OpenAI(api_key=...)`, default model `gpt-4o`.
- **Tools:** `self.tools = MedicationTools()` (default DB path `pharmacy.db`).
- **System prompt:** Long string defining “Duane the Rock Reade”: personality, **safety protocols** (e.g. when user gives name + medication, call both `get_medication_info` and `get_user_allergies` in the same response, then check allergy conflict), policies (factual only, no medical advice, refer when needed), language (EN/HE), when to use which tool, safety-first.
- **Conversation history:** `self.conversation_history = []`.

```python
# _call_tool (lines 108–137)
```
- Maps tool **name** to a method on `self.tools`, runs it with `**arguments`, returns the result.
- **Critical bug:** The map only has four tools:
  - `get_medication_info`
  - `check_active_ingredients_and_interactions`
  - `check_inventory`
  - `refer_to_professional`
- So **`get_user_allergies`** and **`check_prescription`** are **not** in the map. If the model calls either, the code returns `{"error": "Unknown tool: ..."}`. So the safety flow in the system prompt (call both medication info and user allergies) can never succeed for allergies, and prescription checks will fail at execution even if the model asks for them.
- **Fix:** Add to the map:
  - `"get_user_allergies": self.tools.get_user_allergies`
  - `"check_prescription": self.tools.check_prescription`
- And ensure both are in `TOOL_DEFINITIONS` in `medication_tools.py` (see below).

```python
# chat (lines 139–246)
```
- Appends user message to `conversation_history`.
- Builds `messages = [system] + conversation_history`.
- **First API call:** `client.chat.completions.create(..., tools=TOOL_DEFINITIONS, tool_choice="auto", stream=False)`.
- **If** `assistant_message.tool_calls`:
  - For each tool call: parse `arguments`, call `_call_tool(name, arguments)`, collect `{ role: "tool", tool_call_id, content: json.dumps(result) }`.
  - Append the assistant message (with `tool_calls`) to history.
  - Append all tool results to history.
  - **Second API call:** same messages (now including assistant + tool results), **no** `tools` argument, so the model just generates the final reply in natural language.
  - Append that final reply to history and return it.
- **Else:** Append assistant content to history and return it.
- So the agent does **one** round of tool use per user message; if the model wanted to call tools again after the first reply, it would need another user turn (or you’d add a loop).

**Improvement:** Add a loop (e.g. max 3 rounds) so that if the **second** response again has `tool_calls`, you run them and call the API again, until the model responds with only text. That would support multi-step tool use in one turn.

```python
# chat_stream (lines 248–308)
```
- Appends user message, then calls the API with `stream=True`.
- It only collects **content** and **tool_calls** from deltas. If there are tool calls, it **doesn’t** execute them in streaming fashion; it just says “Processing tool calls...” and then calls `self.chat(user_message, stream=False)`, which replays the same user message and does the full non-streaming tool loop. So streaming is only for “no tools” or “tools handled by a second request”; the UX is a bit inconsistent (e.g. no token-by-token during tool use).

```python
# reset_conversation, test_agent, interactive_mode, __main__
```
- Reset clears history. The rest is for local testing and an interactive CLI.

---

## Part 4: The Tools and Their Definitions

### src/tools/medication_tools.py

**Role:** All DB-backed operations the agent can use, plus the OpenAI function definitions.

- **Class `MedicationTools`:** Takes `db_path` (default `"pharmacy.db"`). Uses `_get_connection()` for sqlite3 connections.
- **Methods:**  
  - `get_medication_info(medication_name)` – one med by name/generic; returns full details or error.  
  - `check_active_ingredients_and_interactions(medication_name)` – ingredients + interactions.  
  - `check_inventory(medication_name)` – stock quantity, status (out of stock / low / available), requires_prescription.  
  - `refer_to_professional(query_type, reason)` – no DB; returns a referral message and resources.  
  - `get_user_allergies(user_name)` – `users` table, name (LIKE), returns name, allergies, current_medications.  
  - `get_all_medications_list()` – list of meds with prescription and stock flags (not currently in TOOL_DEFINITIONS).  
  - `check_prescription(user_name, medication_name)` – checks if med is Rx, then if user has a prescription on file; returns status and details.

**TOOL_DEFINITIONS (lines 371–437):** List of OpenAI function specs. Currently you have five:  
`get_medication_info`, `check_active_ingredients_and_interactions`, `check_inventory`, `refer_to_professional`, **`check_prescription`**.  
So **`get_user_allergies` is missing from TOOL_DEFINITIONS**. The system prompt tells the model to call it, but the API never sees it, so the model can’t call it.

**Fixes:**
1. Add a function definition for `get_user_allergies` to `TOOL_DEFINITIONS` (name, description, parameters: `user_name`).
2. In `pharmacy_agent.py`, add `get_user_allergies` and `check_prescription` to `_call_tool`’s `tool_map`.

**Improvement:** Use a single source of truth: e.g. a list of `(name, method, schema)` and build both the tool_map and TOOL_DEFINITIONS from it, so new tools can’t be “defined but not wired” or “wired but not defined.”

---

## Part 5: Database and Scripts

### src/database/init_db.py

**Role:** Create and seed the SQLite DB.

- **Tables:**  
  - **users:** user_id, name, email, phone, date_of_birth, allergies, current_medications, created_at.  
  - **medications:** medication_id, name, generic_name, active_ingredients, dosage_forms, common_dosages, description, requires_prescription, stock_quantity, interactions, side_effects, contraindications, created_at.  
  - **prescriptions:** prescription_id, user_id, medication_id, dosage, frequency, prescribed_date, refills_remaining, prescribing_doctor (and FKs).
- **Seed data:** 10 users (e.g. Knicks players), 5 medications (Aspirin, Metformin, Semaglutide, Ibuprofen, Amoxicillin), then sample prescriptions linking some users to meds.
- **`create_database()`** does the create + insert; **`view_database()`** prints a summary. Run as `python src/database/init_db.py` (or via Docker) to bootstrap `pharmacy.db`.

**Improvement:** Make `pharmacy.db` path configurable (e.g. env or argument) so Docker and local can point to the same path as the app.

### src/tools/add_medications.py

**Role:** Add three more medications (Warfarin, Glyburide, Probenecid) and some prescriptions. Used to test interactions (e.g. Warfarin + Aspirin). Run once after init_db if you want 8 meds.

### src/tools/update_inventory.py

**Role:** Set Probenecid stock to 15 to test “low stock” messaging. Simple `UPDATE` script.

---

## Part 6: Frontend (templates/index.html)

- **Single page:** Header “Duane the Rock Reade”, reset button, chat area, input + Send.
- **Welcome state:** Greeting and example queries (Aspirin vs Ibuprofen, Semaglutide stock, Warfarin interactions, Hebrew example).
- **JS:**  
  - `addMessage(role, content, toolCalls)` – appends a message; if `toolCalls`, adds a “Tool Calls” block with name + arguments.  
  - `sendMessage()` – POST to `/api/chat`, then shows response and optional tool calls.  
  - Typing indicator shown during request, removed when response arrives.  
  - Reset calls `/api/reset` and restores the welcome view.
- **Styling:** Clean, Spotify-like (dark header, green accent #00d76d), tool calls in a yellow box.

**Improvement:** The UI uses `/api/chat` only (non-streaming). If you fix `/api/stream` to handle tools and then use it from the frontend, you could stream tokens and still show tool calls for that turn.

---

## Summary of Critical Fixes and Improvements

**Critical (must-fix for safety flows):**
1. **Expose and wire `get_user_allergies`:** Add it to `TOOL_DEFINITIONS` in `medication_tools.py` and add it (and `check_prescription`) to `_call_tool` in `pharmacy_agent.py`.
2. **Wire `check_prescription`:** It’s already in `TOOL_DEFINITIONS`; add it to the agent’s `tool_map` so it doesn’t return “Unknown tool”.

**Improvements (when you have time):**
- **Multi-round tool loop:** In `chat()`, if the model’s follow-up message again has `tool_calls`, execute them and call the API again (with a max iterations cap).
- **Streaming:** Fix `/api/stream` to run tools and then stream the final reply (or document that streaming is “text-only” and use `/api/chat` for tool turns).
- **Single source of truth for tools:** Derive both the tool_map and TOOL_DEFINITIONS from one list so you can’t have a tool defined but not callable.
- **Session-scoped history:** If you ever support multiple users, store `conversation_history` per session ID instead of one global list.
- **DB path:** Make `pharmacy.db` path configurable and use it in init_db, MedicationTools, and Docker so everything points to the same file.

Once the two critical fixes are in place, Flow 1 in MULTI_STEP_FLOWS.md (allergy check) and prescription checks can work as intended; the rest will help with robustness and UX.
