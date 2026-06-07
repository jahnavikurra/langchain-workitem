import json
import uuid
from langchain_core.messages import SystemMessage, HumanMessage

from src.prompts import BACKLOG_SYSTEM_PROMPT
from src.services.llm import get_llm


def analyze_requirement_node(state: dict) -> dict:
    state["progress_steps"] = [
        "Analyzing meeting notes",
        "Extracting key requirements",
        "Generating Product Backlog Items",
        "Prioritizing and estimating",
    ]
    return state


def generate_backlog_items_node(state: dict) -> dict:
    llm = get_llm()

    user_prompt = {
        "message": state["message"],
        "work_item_type": state.get("work_item_type", "Product Backlog Item"),
        "template_name": state.get("template_name"),
        "project_name": state.get("project_name"),
        "area_path": state.get("area_path"),
        "iteration_path": state.get("iteration_path"),
        "chat_history": state.get("chat_history", []),
    }

    response = llm.invoke(
        [
            SystemMessage(content=BACKLOG_SYSTEM_PROMPT),
            HumanMessage(content=json.dumps(user_prompt)),
        ]
    )

    state["llm_raw_response"] = response.content
    return state


def parse_response_node(state: dict) -> dict:
    raw = state.get("llm_raw_response", "")

    try:
        parsed = json.loads(raw)
    except Exception:
        parsed = {
            "assistant_message": "I generated a backlog draft, but response parsing failed.",
            "progress_steps": state.get("progress_steps", []),
            "items": []
        }

    for index, item in enumerate(parsed.get("items", []), start=1):
        item.setdefault("temp_id", f"PBI-{index}")
        item.setdefault("work_item_type", state.get("work_item_type", "Product Backlog Item"))
        item.setdefault("description", "")
        item.setdefault("value_statement", "")
        item.setdefault("assumptions", "")
        item.setdefault("dependencies", "")
        item.setdefault("acceptance_criteria", [])
        item.setdefault("tasks", [])
        item.setdefault("tags", [])
        item.setdefault("confidence", 0.7)

    parsed.setdefault("progress_steps", state.get("progress_steps", []))
    parsed.setdefault("assistant_message", "Generated backlog items for review.")

    state["parsed_response"] = parsed
    return state
