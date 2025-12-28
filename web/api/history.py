"""API endpoints for generation history management"""

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, Response

from web.models.database import get_db_session
from web.repositories.database_session import DatabaseSession
from web.schemas.generation import GenerationResponse
from web.services.history import history_service
from web.templates import templates

router = APIRouter()


@router.get("/history", response_class=HTMLResponse)
async def list_history(
    request: Request,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(10, ge=1, le=50, description="Items per page"),
    db_session: DatabaseSession = Depends(get_db_session),
):
    """
    Get paginated generation history list.

    Returns HTML partial with history items for HTMX infinite scroll.
    """
    generations, total_count = await history_service.list_history(
        db_session=db_session,
        page=page,
        limit=limit,
    )

    # Calculate if there are more pages
    has_more = (page * limit) < total_count

    return templates.TemplateResponse(
        "partials/history_list.html",
        {
            "request": request,
            "generations": generations,
            "page": page,
            "has_more": has_more,
        },
    )


@router.get("/history/{generation_id}")
async def get_history_detail(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> GenerationResponse:
    """
    Get detailed information about a specific generation.

    Returns JSON response with generation details.
    """
    generation = await history_service.get_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    return GenerationResponse(
        id=generation.id,
        character_name=generation.character_name,
        input_topic=generation.input_topic,
        generated_title=generation.generated_title,
        status=generation.status,
        error_message=generation.error_message,
        created_at=generation.created_at,
        completed_at=generation.completed_at,
    )


@router.delete("/history/{generation_id}", response_class=HTMLResponse)
async def delete_history(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
):
    """
    Delete a generation from history.

    Returns empty HTML response for HTMX to remove the item from DOM.
    """
    deleted = await history_service.delete_by_id(generation_id, db_session)

    if not deleted:
        raise HTTPException(status_code=404, detail="Generation not found")

    # Return empty response - HTMX will remove the element with hx-swap="outerHTML"
    return Response(content="", media_type="text/html")
