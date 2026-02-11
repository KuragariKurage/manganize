"""API endpoints for manga generation"""

import io
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import Response
from PIL import Image
from sse_starlette.sse import EventSourceResponse

from manganize_web.models.database import get_db_session
from manganize_web.models.generation import GenerationTypeEnum
from manganize_web.repositories.database_session import DatabaseSession
from manganize_web.schemas.generation import (
    CreateRevisionRequest,
    RevisionCreateResponse,
)
from manganize_web.services.generator import generator_service
from manganize_web.services.upload_source import upload_source_service
from manganize_web.templates import templates
from manganize_web.utils.filename import generate_download_filename

router = APIRouter()


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    db_session: DatabaseSession = Depends(get_db_session),
) -> dict[str, str]:
    """
    Upload a file to object storage and create upload metadata.

    Args:
        file: Uploaded file

    Returns:
        JSON with upload source metadata

    Raises:
        HTTPException: If file validation or upload fails
    """
    try:
        source = await upload_source_service.create_upload(file, db_session)

        return {
            "upload_id": source.id,
            "filename": source.original_filename,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"ファイルのアップロードに失敗しました: {str(e)}",
        )


@router.post("/generate")
async def create_generation(
    request: Request,
    topic: str = Form(""),
    character: str = Form(...),
    upload_id: str | None = Form(None),
    db_session: DatabaseSession = Depends(get_db_session),
):
    """
    Create a new manga generation request.

    Returns HTML partial with progress indicator and SSE connection.
    """
    # Delegate to service layer
    try:
        generation_id = await generator_service.create_generation_request(
            topic=topic,
            character_name=character,
            upload_id=upload_id,
            db_session=db_session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return HTML with SSE connection
    # The actual generation will be triggered by the SSE stream endpoint
    return templates.TemplateResponse(
        "partials/progress.html",
        {
            "request": request,
            "generation_id": generation_id,
        },
    )


@router.get("/generate/{generation_id}/progress")
async def get_generation_progress_partial(
    request: Request,
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
):
    """
    Get progress indicator partial for a generation request.

    Returns HTML partial with SSE connection bootstrap.
    """
    generation = await generator_service.get_generation_by_id(generation_id, db_session)
    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    return templates.TemplateResponse(
        "partials/progress.html",
        {
            "request": request,
            "generation_id": generation_id,
        },
    )


@router.post("/generations/{generation_id}/revisions")
async def create_revision_generation(
    generation_id: str,
    payload: CreateRevisionRequest,
    db_session: DatabaseSession = Depends(get_db_session),
) -> RevisionCreateResponse:
    """
    Create a new revision generation request from an existing generation.

    Args:
        generation_id: Parent generation ID
        payload: Revision request payload

    Returns:
        Revision generation ID
    """
    try:
        revision_generation_id = await generator_service.create_revision_request(
            parent_generation_id=generation_id,
            revision_payload=payload.model_dump(mode="json", exclude_none=True),
            db_session=db_session,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return RevisionCreateResponse(generation_id=revision_generation_id)


@router.get("/generate/{generation_id}/stream")
async def stream_generation_progress(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> EventSourceResponse:
    """
    Stream generation progress updates via Server-Sent Events.

    Args:
        generation_id: UUID of the generation

    Returns:
        EventSourceResponse with progress updates
    """

    generation = await generator_service.get_generation_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    async def event_generator():
        """Generate SSE events for progress updates"""
        async for status in generator_service.generate_for_request(
            generation_id,
            db_session,
        ):
            yield {
                "event": "progress",
                "data": status.model_dump_json(),
            }

            # If completed or error, close stream
            if status.status in ("completed", "error"):
                break

    return EventSourceResponse(event_generator())


@router.get("/generate/{generation_id}/result")
async def get_generation_result(
    request: Request,
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
):
    """
    Get generation result as HTML partial.

    Args:
        generation_id: UUID of the generation

    Returns:
        HTML partial with the generated image
    """

    generation = await generator_service.get_generation_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    return templates.TemplateResponse(
        "partials/result.html",
        {
            "request": request,
            "generation": generation,
            "status_value": (
                generation.status.value
                if hasattr(generation.status, "value")
                else str(generation.status)
            ),
            "generation_type_value": (
                generation.generation_type.value
                if hasattr(generation.generation_type, "value")
                else str(generation.generation_type)
            ),
            "is_revision": generation.generation_type == GenerationTypeEnum.REVISION,
        },
    )


@router.get("/images/{generation_id}")
async def serve_image(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> Response:
    """
    Serve generated manga image.

    Args:
        generation_id: UUID of the generation

    Returns:
        PNG image
    """

    generation = await generator_service.get_generation_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if not generation.image_data:
        raise HTTPException(status_code=404, detail="Image not yet generated")

    return Response(
        content=generation.image_data,
        media_type="image/png",
        headers={
            "Cache-Control": "public, max-age=31536000",
        },
    )


@router.get("/images/{generation_id}/download")
async def download_image(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> Response:
    """
    Download generated manga image with appropriate filename.

    Format: manganize_{datetime}_{title}.png

    Args:
        generation_id: UUID of the generation

    Returns:
        PNG image with Content-Disposition header for download
    """

    generation = await generator_service.get_generation_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if not generation.image_data:
        raise HTTPException(status_code=404, detail="Image not yet generated")

    # Generate filename
    filename = generate_download_filename(
        generation.generated_title,
        generation.created_at,
    )

    encoded_filename = quote(filename.encode("utf-8"))
    ascii_fallback = "manganize_manga.png"  # Simple ASCII fallback

    return Response(
        content=generation.image_data,
        media_type="image/png",
        headers={
            "Content-Disposition": f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{encoded_filename}",
            "Cache-Control": "public, max-age=31536000",
        },
    )


@router.get("/images/{generation_id}/thumbnail")
async def serve_thumbnail(
    generation_id: str,
    db_session: DatabaseSession = Depends(get_db_session),
) -> Response:
    """
    Serve generated manga image thumbnail (200x200).

    Args:
        generation_id: UUID of the generation

    Returns:
        Thumbnail PNG image
    """

    generation = await generator_service.get_generation_by_id(generation_id, db_session)

    if not generation:
        raise HTTPException(status_code=404, detail="Generation not found")

    if not generation.image_data:
        raise HTTPException(status_code=404, detail="Image not yet generated")

    # Load image from bytes
    try:
        image = Image.open(io.BytesIO(generation.image_data))

        # Generate thumbnail (200x200, maintain aspect ratio)
        image.thumbnail((200, 200), Image.Resampling.LANCZOS)

        # Save thumbnail to bytes
        thumbnail_buffer = io.BytesIO()
        image.save(thumbnail_buffer, format="PNG", optimize=True)
        thumbnail_data = thumbnail_buffer.getvalue()

        return Response(
            content=thumbnail_data,
            media_type="image/png",
            headers={
                "Cache-Control": "public, max-age=31536000",
            },
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate thumbnail: {str(e)}",
        )
