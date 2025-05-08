from fastapi import HTTPException, Request, FastAPI

from config import GITLAB_WEBHOOKS_TOKEN
from database import session
from models import Service, ServiceSubscription

app = FastAPI()


@app.post("/gitlab-webhook")
async def gitlab_webhook(request: Request):
    token = request.headers.get("X-Gitlab-Token")
    if token != GITLAB_WEBHOOKS_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: invalid token")

    data = await request.json()
    event_type = request.headers.get("X-Gitlab-Event")

    if event_type == "Merge Request Hook":
        action = data["object_attributes"]["action"]
        repo_name = data["project"]["name"]
        mr_title = data["object_attributes"]["title"]
        mr_url = data["object_attributes"]["url"]

        service = session.query(
            Service,
        ).filter_by(git_repo_name=repo_name).first()
        if not service:
            return {"status": "service not registered"}

        subscriptions = session.query(
            ServiceSubscription,
        ).filter_by(service_id=service.id).all()
        for subscription in subscriptions:
            employee_id = subscription.employee_id

    return {"status": "ok"}


__all__ = []
