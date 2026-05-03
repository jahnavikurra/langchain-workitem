import logging
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.models import (
    BacklogChatRequest,
    BacklogChatResponse,
    CreateBacklogRequest,
    CreateBacklogResponse,
    CreatedWorkItem,
)
from src.graph.backlog_graph import backlog_graph
from src.services.ado_client import create_work_item


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backlog-assist")

app = FastAPI(title="Backlog Assist API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "backlog-assist"
    }


@app.post("/backlog/chat", response_model=BacklogChatResponse)
def backlog_chat(request: BacklogChatRequest):
    try:
        result = backlog_graph.invoke(
            {
                "message": request.message,
                "work_item_type": request.work_item_type,
                "template_name": request.template_name,
                "project_name": request.project_name,
                "area_path": request.area_path,
                "iteration_path": request.iteration_path,
                "chat_history": [m.model_dump() for m in request.chat_history],
            }
        )

        parsed = result["parsed_response"]

        return BacklogChatResponse(
            assistant_message=parsed["assistant_message"],
            progress_steps=parsed["progress_steps"],
            items=parsed["items"],
        )

    except Exception as ex:
        logger.exception("Backlog chat failed")
        raise HTTPException(status_code=500, detail=str(ex))


@app.post("/backlog/create", response_model=CreateBacklogResponse)
def backlog_create(
    request: CreateBacklogRequest,
    authorization: str = Header(...),
):
    try:
        if not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=401,
                detail="Authorization header must be Bearer token"
            )

        ado_token = authorization.replace("Bearer ", "").replace("bearer ", "").strip()

        created_items: list[CreatedWorkItem] = []

        for item in request.items:
            created = create_work_item(
                ado_token=ado_token,
                project_name=request.project_name,
                item=item,
                area_path=request.area_path,
                iteration_path=request.iteration_path,
            )

            created_items.append(
                CreatedWorkItem(
                    id=created["id"],
                    url=created["_links"]["html"]["href"],
                    title=created["fields"]["System.Title"],
                    work_item_type=created["fields"]["System.WorkItemType"],
                )
            )

        return CreateBacklogResponse(created=created_items)

    except HTTPException:
        raise

    except Exception as ex:
        logger.exception("ADO work item creation failed")
        raise HTTPException(status_code=500, detail=str(ex))
