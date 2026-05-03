import html
import requests
from typing import Optional

from src.config import settings
from src.models import GeneratedBacklogItem


def build_default_description_html(item: GeneratedBacklogItem) -> str:
    return f"""
    <div>
      <p>
        <b style="color:#005A9E;">Description:</b><br/>
        {html.escape(item.description or "")}
      </p>

      <p>
        <b style="color:#005A9E;">Value Statement:</b><br/>
        {html.escape(item.value_statement or "")}
      </p>

      <p>
        <b style="color:#005A9E;">Assumptions (if applicable):</b><br/>
        {html.escape(item.assumptions or "")}
      </p>

      <p>
        <b style="color:#005A9E;">Dependencies (if applicable):</b><br/>
        {html.escape(item.dependencies or "")}
      </p>
    </div>
    """


def build_acceptance_criteria_html(criteria: list[str]) -> str:
    criteria_html = "".join(
        f"<li>{html.escape(item)}</li>"
        for item in criteria
        if item
    )

    return f"""
    <div>
      <p>
        <b style="color:#005A9E;">
          Meets the Definition of Done (DoD). DoD may include reviewing,
          final approvals, various levels of testing like unit, functional,
          security, integration, regression, 508, UAT, performance etc.
          to be completed and successfully passed (as applicable).
        </b>
      </p>

      <p><b style="color:#005A9E;">Acceptance Criteria:</b></p>
      <ul>
        {criteria_html}
      </ul>
    </div>
    """


def build_tags(tags: list[str]) -> str:
    return "; ".join(tag.strip() for tag in tags if tag and tag.strip())


def build_patch_document(
    item: GeneratedBacklogItem,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
) -> list[dict]:
    patch_document = [
        {
            "op": "add",
            "path": "/fields/System.Title",
            "value": item.title,
        },
        {
            "op": "add",
            "path": "/fields/System.Description",
            "value": build_default_description_html(item),
        },
        {
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.AcceptanceCriteria",
            "value": build_acceptance_criteria_html(item.acceptance_criteria),
        },
    ]

    if area_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.AreaPath",
            "value": area_path,
        })

    if iteration_path:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.IterationPath",
            "value": iteration_path,
        })

    if item.tags:
        patch_document.append({
            "op": "add",
            "path": "/fields/System.Tags",
            "value": build_tags(item.tags),
        })

    if item.story_points is not None:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Scheduling.StoryPoints",
            "value": item.story_points,
        })

    if item.priority:
        patch_document.append({
            "op": "add",
            "path": "/fields/Microsoft.VSTS.Common.Priority",
            "value": item.priority,
        })

    return patch_document


def create_work_item(
    ado_token: str,
    project_name: str,
    item: GeneratedBacklogItem,
    area_path: Optional[str] = None,
    iteration_path: Optional[str] = None,
) -> dict:
    work_item_type = item.work_item_type

    url = (
        f"{settings.ADO_ORG_URL}/{project_name}"
        f"/_apis/wit/workitems/${work_item_type}"
        f"?api-version=7.1-preview.3"
    )

    headers = {
        "Authorization": f"Bearer {ado_token}",
        "Content-Type": "application/json-patch+json",
        "Accept": "application/json",
    }

    patch_document = build_patch_document(
        item=item,
        area_path=area_path,
        iteration_path=iteration_path,
    )

    response = requests.post(
        url,
        headers=headers,
        json=patch_document,
        timeout=60,
    )

    if response.status_code >= 400:
        raise Exception(
            f"ADO create failed. Status={response.status_code}, Body={response.text}"
        )

    return response.json()
