from fastapi import APIRouter, HTTPException
from app.models import WebhookCreate, WebhookUpdate, WebhookOut
from app.services import webhook_service

router = APIRouter(prefix="/api/webhooks", tags=["webhooks"])


@router.get("", response_model=list[WebhookOut])
async def list_webhooks():
    return await webhook_service.list_webhooks()


@router.get("/{webhook_id}", response_model=WebhookOut)
async def get_webhook(webhook_id: int):
    wh = await webhook_service.get_webhook(webhook_id)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    return wh


@router.post("", response_model=WebhookOut, status_code=201)
async def create_webhook(data: WebhookCreate):
    return await webhook_service.create_webhook(data.model_dump())


@router.put("/{webhook_id}", response_model=WebhookOut)
async def update_webhook(webhook_id: int, data: WebhookUpdate):
    updates = {k: v for k, v in data.model_dump().items() if v is not None}
    wh = await webhook_service.update_webhook(webhook_id, updates)
    if not wh:
        raise HTTPException(404, "Webhook not found")
    return wh


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: int):
    ok = await webhook_service.delete_webhook(webhook_id)
    if not ok:
        raise HTTPException(404, "Webhook not found")
    return {"ok": True}
