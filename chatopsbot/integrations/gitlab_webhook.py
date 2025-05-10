from fastapi import HTTPException, Request, FastAPI

from config import GITLAB_WEBHOOKS_TOKEN
from database import session
from models import Service, MergeRequest

app = FastAPI()


@app.post("/gitlab-webhook")
async def gitlab_webhook(request: Request):
    token = request.headers.get("X-Gitlab-Token")
    if token != GITLAB_WEBHOOKS_TOKEN:
        raise HTTPException(status_code=403, detail="Forbidden: invalid token")

    data = await request.json()
    event_type = request.headers.get("X-Gitlab-Event")

    if (event_type == "Merge Request Hook"
            and data["object_attributes"]["action"] == "merge"):
        repo_name = data["project"]["name"]
        mr_title = data["object_attributes"]["title"]
        mr_url = data["object_attributes"]["url"]

        service = session.query(
            Service,
        ).filter_by(git_repo_name=repo_name).first()
        if not service:
            return {"status": "service not registered"}

        merge_request = MergeRequest(
            service_id=service.id,
            title=mr_title,
            url=mr_url,
        )
        session.add(merge_request)
        session.commit()
    return {"status": "ok"}


__all__ = []
