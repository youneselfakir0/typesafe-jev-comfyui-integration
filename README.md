# TypeSafe Jev Decision Node for ComfyUI

A custom ComfyUI node that interfaces with **TypeSafe's Jev System One model**, enabling fast, structured decisions from within ComfyUI workflows.

## Features

- **Three question types** supported:
  - `noul` — Yes/no probability (0 to 1), with confidence score
  - `choice` — Pick one option from up to 255 options, with full probability distribution
  - `score` — Rate on an ordered rubric (2–10 levels), with probability-weighted value and confidence
- **Parallel processing** — All questions in a single request run in parallel
- **Completely typed** — SDK provides full TypeScript/Python type inference
- **Auto-retries** — Built-in exponential backoff for rate limits (429/529 errors)
- **Confidence scores** — Each answer includes a calibrated confidence value

## Installation

1. Place `typesafe_jev_node.py` in your ComfyUI custom nodes directory:
   `<ComfyUI>/custom_nodes/typesafe_jev_node.py`

2. Install the TypeSafe SDK (done automatically on first run, or manually):
   ```bash
   pip install typesafe-sdk
   ```

3. Restart ComfyUI

4. Obtain an API key at: https://console.typesafe.ai/

5. Enter your API key in the node's `api_key` parameter

## Node Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `state` | `STRING` (multiline) | The content to evaluate — ticket text, chat log, JSON blob, etc. |
| `api_key` | `STRING` | Your TypeSafe API key (or set `TYPESAFE_API_KEY` env var) |
| `question_id` | `STRING` | Identifier for this question (not sent to the model) |
| `instructions` | `STRING` (multiline) | The decision question to evaluate |
| `question_type` | `["noul", "choice", "score"]` | Type of decision to make |
| `criteria_json` | `STRING` (multiline) | JSON criteria — see below |

## Criteria JSON Format

### `noul` (yes/no)
```json
{"true": "Explicitly time-sensitive", "false": "No urgency expressed"}
```

### `choice` (pick one option)
```json
{"billing": "Payments, invoicing, refunds", "technical": "Bugs, outages, integrations", "sales": "Pricing, upgrades"}
```
*Maximum 255 options. Use `null` for options needing no description: `{"option_a": null, "option_b": null}`*

### `score` (rubric rating)
```json
["Calm", "Frustrated", "Very angry"]
```
*Minimum 2 levels, maximum 10. Levels are indexed 0, 1, 2, ...*

## Outputs

| Output | Type | Description |
|--------|------|-------------|
| `decision_value` | `STRING` | The decision result as a string |
| `full_probabilities` | `STRING` (JSON) | Full probability distribution as JSON |
| `confidence` | `FLOAT` | How certain the model is (0 to 1) |
| `weighted_score` | `FLOAT` | Weighted score: for `choice` → probability of chosen option; for `score` → numeric score; for `noul` → yes-probability |

## Example Usage in ComfyUI

### Support Ticket Triage Workflow

1. **Text Input** → Provide ticket description
2. **TypeSafe Jev Node** → Decide routing
   - `question_type`: `choice`
   - `criteria_json`: `{"billing": "Payments, invoicing, refunds", "technical": "Bugs, outages, integrations", "sales": "Pricing, upgrades, new accounts"}`
   - `instructions`: "Which team should handle this ticket?"
3. **Route based on result**
   - If `choice` = `billing` → Send to billing workflow
   - If `choice` = `technical` → Send to technical workflow
   - If `choice` = `sales` → Send to sales workflow
4. **Confidence check** → If confidence < 0.7, escalate to human

### outputs after the node:

```
decision_value: "technical"
full_probabilities: '{"billing": 0.12, "technical": 0.85, "sales": 0.03}'
confidence: 0.89
weighted_score: 0.85
```

### Urgency Detection (noul)

```
decision_value: "noul=0.93"
full_probabilities: '{}'
confidence: 0.94
weighted_score: 0.93
```

### Frustration Scoring (score)

```
decision_value: "score=1.05 (Frustrated)"
full_probabilities: '{"0": 0.0, "1": 0.95, "2": 0.05}'
confidence: 0.92
weighted_score: 1.05
```

## SDK Integration (outside ComfyUI)

The same SDK can be used directly in Python/TypeScript outside ComfyUI:

```python
# Python
from typesafe_sdk import TypeSafeClient, Choice, Noul, Score

client = TypeSafeClient()
response = client.system_one(
    state="Customer is very angry about a double charge",
    questions={
        "urgency": Noul(instructions="Is this urgent?"),
        "department": Choice(
            instructions="Which team?",
            criteria={"billing": None, "technical": None, "sales": None}
        ),
        "frustration": Score(
            instructions="How frustrated?",
            criteria=["Calm", "Frustrated", "Very angry"]
        ),
    }
)

print("Urgency:", response.nouls["urgency"].noul)      # 0.93
print("Department:", response.choices["department"].choice)  # "technical"
print("Frustration score:", response.scores["frustration"].score)  # 1.05
```

```typescript
// TypeScript/ESM
import { TypeSafeClient, choice, noul, score } from "@typesafe-ai/sdk";

const client = new TypeSafeClient();
const response = await client.systemOne({
  state: "Customer is very angry about a double charge",
  questions: {
    urgency: noul("Is this urgent?"),
    department: choice("Which team?", {
      billing: "Payments, invoicing, refunds",
      technical: "Bugs, outages, integrations",
      sales: "Pricing, upgrades, new accounts",
    }),
    frustration: score("How frustrated?", ["Calm", "Frustrated", "Very angry"]),
  },
});

console.log("Urgency:", response.answers.urgency.noul);
console.log("Department:", response.answers.department.choice);
console.log("Frustration:", response.answers.frustration.score);
```

## Performance

- **Typical latency**: 70–500 ms per call (vs. 2–10 seconds for LLMs)
- **Cost**: $0.042 per million input tokens; output is free
- **Speed advantage**: ~193× faster than typical LLMs for decision tasks
- **No hallucinations**: Cannot output values outside the predefined schema

## Notes

- The `question_id` is for code identification only — it is **not** sent to the model
- Questions are evaluated in parallel within a single API request
- Confidence summarizes distribution concentration, not overall workflow correctness
- Pair with an LLM for hybrid systems: Jev handles routing/gating, LLM handles generation
- Validate performance with your specific data and question types