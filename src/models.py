from typing import Literal, Optional
from pydantic import BaseModel, Field


WorkItemType = Literal[
    "Epic",
    "Feature",
    "Product Backlog Item",
    "User Story",
    "Bug",
    "Task"
]


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class BacklogChatRequest(BaseModel):
    message: str
    work_item_type: WorkItemType = "Product Backlog Item"
    template_name: Optional[str] = None
    project_name: str
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    chat_history: list[ChatMessage] = []


class GeneratedBacklogItem(BaseModel):
    temp_id: str
    work_item_type: WorkItemType
    title: str
    description: str
    value_statement: str = ""
    assumptions: str = ""
    dependencies: str = ""
    acceptance_criteria: list[str] = []
    tasks: list[str] = []
    tags: list[str] = []
    priority: Optional[str] = None
    story_points: Optional[int] = None
    confidence: float = Field(default=0.7, ge=0, le=1)


class BacklogChatResponse(BaseModel):
    assistant_message: str
    progress_steps: list[str]
    items: list[GeneratedBacklogItem]


class CreateBacklogRequest(BaseModel):
    project_name: str
    area_path: Optional[str] = None
    iteration_path: Optional[str] = None
    link_to_epic_url: Optional[str] = None
    link_to_feature_url: Optional[str] = None
    items: list[GeneratedBacklogItem]


class CreatedWorkItem(BaseModel):
    id: int
    url: str
    title: str
    work_item_type: str


class CreateBacklogResponse(BaseModel):
    created: list[CreatedWorkItem]
