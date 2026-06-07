from typing import TypedDict, Optional, Any


class BacklogGraphState(TypedDict, total=False):
    message: str
    work_item_type: str
    template_name: Optional[str]
    project_name: str
    area_path: Optional[str]
    iteration_path: Optional[str]
    chat_history: list[dict[str, str]]

    progress_steps: list[str]
    llm_raw_response: str
    parsed_response: dict[str, Any]
