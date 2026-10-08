# TypeSafe Jev Workflow Templates

Three pre-configured ComfyUI workflow templates with the TypeSafe Jev Decision node. 
API keys are left empty (`""`) so you can load and execute immediately, then enter your key.

## 📁 Available Templates

### 1. `typesafe_jev_workflow.json` — Choice (Ticket Routing)
**Use case:** Route support tickets to the correct department
- **Question:** "Which team should handle this ticket?"
- **Options:** billing, technical, sales
- **Output:** decision_value = chosen department (e.g., "technical")
- **Confidence:** How certain the model is about the routing

### 2. `typesafe_jev_workflow_noul.json` — Noul (Urgency Detection)
**Use case:** Detect if a ticket needs immediate attention
- **Question:** "Does this convey urgency?"
- **Yes/No:** time-sensitive vs. no urgency
- **Output:** decision_value = "noul=0.93" (probability)
- **Confidence:** How certain about the yes/no call

### 3. `typesafe_jev_workflow_score.json` — Score (Frustration Rating)
**Use case:** Rate customer frustration level for prioritization
- **Question:** "How frustrated is the customer?"
- **Levels:** Calm → Frustrated → Very angry
- **Output:** decision_value = "score=1.05 (Frustrated)" + weighted_score
- **Confidence:** How certain about the rating

## 🚀 How to Use a Template

### Step 1: Load the Workflow
1. Open ComfyUI web interface
2. Click **"Load"** or go to "File" → "Load Workflow"
3. Navigate to: `C:\Users\administrator\ComfyUI\custom_nodes\`
4. Select the `.json` file you want:
   - `typesafe_jev_workflow.json` (choice/routing)
   - `typesafe_jev_workflow_noul.json` (noul/urgency)
   - `typesafe_jev_workflow_score.json` (score/frustration)

### Step 2: Enter Your API Key
1. The TypeSafe Jev Decision node will appear in your workflow
2. Find the `api_key` parameter
3. **Enter your TypeSafe API key** (get it at https://console.typesafe.ai/)
   - Or set env var: `set TYPESAFE_API_KEY=sk-XXXXXXXXXXXXXXXXXXXXXXXX`
4. If you don't have a key yet, you can use `""` (empty string) — the node will show an auth error until you add it

### Step 3: Execute
1. Click the **"Queue Prompt"** button (or press Ctrl+Enter)
2. The node will call TypeSafe Jev API
3. Results appear on the node's output ports:
   - `decision_value` — the choice/noul/score result
   - `full_probabilities` — JSON distribution
   - `confidence` — 0 to 1 certainty score
   - `weighted_score` — type-appropriate value

### Step 4: Connect to Other Nodes
- Connect `decision_value` output to route/compare nodes
- Use `confidence` to gate decisions (e.g., only route if confidence > 0.7)
- Use `full_probabilities` to see all competing options

## 📋 Template Details

### Choice Template (`typesafe_jev_workflow.json`)
```json
"state": "Customer says payment failed after 3 days and needs refund",
"instructions": "Which team should handle this ticket?",
"question_type": "choice",
"criteria_json": "{\"billing\": \"Payments, invoicing, refunds\", \"technical\": \"Bugs, outages, integrations\", \"sales\": \"Pricing, upgrades, new accounts\"}"
```
**Outputs:**
- `decision_value`: "billing" / "technical" / "sales"
- `full_probabilities`: `{"billing": 0.88, "technical": 0.12, "sales": 0.0}`
- `confidence`: 0.81
- `weighted_score`: 0.88 (probability of chosen option)

### Noul Template (`typesafe_jev_workflow_noul.json`)
```json
"state": "Customer says payment failed after 3 days and needs refund",
"instructions": "Does this convey urgency?",
"question_type": "noul",
"criteria_json": "{\"true\": \"Explicitly time-sensitive\", \"false\": \"No urgency expressed\"}"
```
**Outputs:**
- `decision_value`: "noul=0.93"
- `full_probabilities`: "{}"
- `confidence`: 0.94
- `weighted_score`: 0.93

### Score Template (`typesafe_jev_workflow_score.json`)
```json
"state": "Customer says payment failed after 3 days and needs refund",
"instructions": "How frustrated is the customer?",
"question_type": "score",
"criteria_json": "[\"Calm\", \"Frustrated\", \"Very angry\"]"
```
**Outputs:**
- `decision_value`: "score=1.05 (Frustrated)"
- `full_probabilities`: `{"0": 0.0, "1": 0.95, "2": 0.05}`
- `confidence`: 0.92
- `weighted_score`: 1.05

## 🛠️ Customizing Templates

To create your own template:

1. Copy one of the existing `.json` files
2. Modify these fields:
   - `state`: Your text/content to evaluate
   - `instructions`: Your decision question
   - `question_type`: "noul" / "choice" / "score"
   - `criteria_json`: JSON matching your chosen type (see templates above)
   - `question_id`: Any identifier (not sent to model)
3. Save with a new name
4. Load in ComfyUI and enter your API key

## ⚠️ Important Notes

- **API key required:** Templates have `api_key: ""` — you must enter a valid key for actual API calls
- **Empty key behavior:** Without a key, the node will show an authentication error until you add one
- **Workflow format:** These are standard ComfyUI prompt JSON files
- **Node location:** After loading, the TypeSafe Jev Decision node will appear under "TypeSafe" or "Typewise" category
- **Parallel processing:** All questions in a single request run in parallel (very fast ~70-500ms)

## 📦 File Locations

```
C:\Users\administrator\ComfyUI\custom_nodes\
├── typesafe_jev_node.py      ← The node itself
├── typesafe_jev_workflow.json      ← Choice routing template
├── typesafe_jev_workflow_noul.json ← Urgency detection template
├── typesafe_jev_workflow_score.json ← Frustration scoring template
└── WORKFLOW_TEMPLATES_README.md    ← This documentation
```

## 💡 Pro Tips

1. **Save multiple templates** for different use cases (routing, urgency, scoring, etc.)
2. **Use confidence thresholds** — only act on decisions where confidence > your minimum (e.g., 0.7)
3. **Combine with ComfyUI logic** — connect outputs to if/else nodes, routing nodes, etc.
4. **Hybrid with LLM** — use Jev for fast decisions, LLM for generation/summarization
5. **Batch processing** — you can add multiple Jev nodes to the same workflow for parallel decisions