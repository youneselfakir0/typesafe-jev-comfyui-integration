"""
TypeSafe Jev Decision Node for ComfyUI

A custom ComfyUI node that interfaces with TypeSafe's Jev System One model.
Allows making fast, structured decisions (Choice, Noul, Score) from within
ComfyUI workflows.

Usage:
- Place this file in <ComfyUI>/custom_nodes/
- Restart ComfyUI
- Find the node under "TypeSafe" category
- Provide state text, API key, and question config
- Connect outputs to other nodes
"""

import json
import os
import sys

# Ensure typesafe_sdk is importable
try:
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score
except ImportError:
    print("typesafe-sdk not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "typesafe-sdk"])
    from typesafe_sdk import TypeSafeClient, Choice, Noul, Score


class TypeSafeJevNode:
    """
    A ComfyUI node that calls TypeSafe Jev API to make structured decisions.
    
    Supports three question types:
    - noul: Yes/no probability (0 to 1)
    - choice: Pick one option from a set (up to 255 options)
    - Score: Rate on an ordered rubric (2-10 levels)
    """
    
    # NOTE: The NODE_CLASS_MAPPINGS below is required for ComfyUI to discover this node.
    # When you restart ComfyUI after adding this file, the node will appear.

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "state": ("STRING", {
                    "default": "Support ticket: Customer says their payment failed and they need a refund.",
                    "multiline": True
                }),
                "api_key": ("STRING", {
                    "default": "",
                    "placeholder": "sk-... your TypeSafe API key"
                }),
                "question_id": ("STRING", {
                    "default": "routing_decision",
                    "description": "Identifier for this question (not sent to the model)"
                }),
                "instructions": ("STRING", {
                    "default": "Which team should handle this ticket?",
                    "multiline": True,
                    "description": "The decision question to evaluate"
                }),
                "question_type": (["noul", "choice", "score"], {
                    "default": "noul",
                    "description": "Type of decision to make"
                }),
                "criteria_json": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "description": "JSON criteria. For choice: {'option': 'description'}. For score: ['level1', 'level2']. For noul: optional {'true': 'meaning', 'false': 'meaning'}"
                })
            }
        }

    RETURN_TYPES = ("STRING", "STRING", "FLOAT", "FLOAT")
    RETURN_NAMES = ("decision_value", "full_probabilities", "confidence", "weighted_score")
    FUNCTION = " evaluate"
    CATEGORY = "typewise"
    OUTPUT_NODE = True

    def evaluate(self, state, api_key, question_id, instructions, question_type, criteria_json):
        """
        Call TypeSafe Jev API and return the structured decision.
        
        Returns:
            - decision_value: The chosen/Scored/Yes-probability value as string
            - full_probabilities: JSON string of all option/probability pairs
            - confidence: How certain the model is (0 to 1)
            - weighted_score: For score type, the weighted position; for others, the value
        """
        # Set API key
        if api_key.strip():
            os.environ["TYPESAFE_API_KEY"] = api_key.strip()
        
        # Parse criteria JSON
        criteria = None
        try:
            if criteria_json.strip():
                criteria = json.loads(criteria_json)
        except json.JSONDecodeError:
            # Fallback based on question type
            if question_type == "noul":
                criteria = {"true": "Yes", "false": "No"}
            elif question_type == "choice":
                criteria = {"option_a": "Option A", "option_b": "Option B"}
            elif question_type == "score":
                criteria = ["Low", "Medium", "High"]
        
        # Build the appropriate question type
        question = None
        
        if question_type == "noul":
            question = Noul(instructions=instructions)
            # Add criteria if provided
            if criteria and "true" in criteria:
                # The Noul type handles criteria via the true/false descriptions
                pass
        
        elif question_type == "choice":
            if criteria and isinstance(criteria, dict):
                # Build choice criteria map: option -> description (or None)
                choice_criteria = {}
                for option, desc in criteria.items():
                    choice_criteria[option] = desc if desc else None
                question = Choice(instructions=instructions, criteria=choice_criteria)
            else:
                # Default minimal choice
                question = Choice(instructions=instructions, criteria={
                    "option_a": None,
                    "option_b": None
                })
        
        elif question_type == "score":
            if criteria and isinstance(criteria, list) and len(criteria) >= 2:
                levels = criteria
            else:
                levels = ["Low", "Medium", "High"]
            question = Score(instructions=instructions, criteria=levels)
        
        if question is None:
            # Fallback to noul
            question = Noul(instructions=instructions)
        
        # Call TypeSafe API
        try:
            client = TypeSafeClient()
            response = client.system_one(
                state=state,
                questions={question_id: question}
            )
            
            # Extract answer
            ans = response.answers.get(question_id)
            if ans is None:
                # Try getting by any available key
                ans = list(response.answers.values())[0] if response.answers else None
            
            if ans is None:
                return ("Error: no answer", "{}", 0.0, 0.0)
            
            # Format output based on question type
            if question_type == "noul":
                noul_value = getattr(ans, 'noul', 0.0)
                confidence = getattr(ans, 'confidence', 0.0)
                decision = f"noul={noul_value:.3f}"
                probs_json = json.dumps({})  # noul doesn't have per-option probs
                weighted = noul_value
                return (decision, probs_json, confidence, weighted)
            
            elif question_type == "choice":
                choice_value = getattr(ans, 'choice', 'unknown')
                probabilities = getattr(ans, 'probabilities', {})
                confidence = getattr(ans, 'confidence', 0.0)
                probs_json = json.dumps(probabilities)
                # Return the choice value and its probability
                weighted = probabilities.get(choice_value, 0.0) if isinstance(probabilities, dict) else 0.0
                return (choice_value, probs_json, confidence, weighted)
            
            elif question_type == "score":
                score_value = getattr(ans, 'score', 0.0)
                legend = getattr(ans, 'legend', {})
                probabilities = getattr(ans, 'probabilities', {})
                confidence = getattr(ans, 'confidence', 0.0)
                probs_json = json.dumps(probabilities)
                # Format the decision value with legend info
                decision_str = f"score={score_value:.2f}"
                if legend:
                    # Try to show level name
                    for k, v in legend.items():
                        decision_str += f" ({v})"
                        break
                probs_json = json.dumps(probabilities)
                weighted = score_value
                return (decision_str, probs_json, confidence, weighted)
            
            else:
                # Default fallback
                decision = str(ans) if ans else "unknown"
                return (decision, "{}", 0.0, 0.0)
        
        except Exception as e:
            # Return error information
            error_msg = f"TypeSafe API Error: {str(e)}"
            return (error_msg, "{}", 0.0, 0.0)


# Mapping for ComfyUI to discover this node
NODE_CLASS_MAPPINGS = {
    "TypeSafeJevNode": TypeSafeJevNode
}

# Human-readable name in ComfyUI UI
NODE_DISPLAY_NAME_MAPPINGS = {
    "TypeSafeJevNode": "TypeSafe Jev Decision"
}