from fastapi import APIRouter, Header, HTTPException, status
from app.core.config import settings

router = APIRouter()


@router.post("/seed-demo")
async def seed_demo_users(x_admin_token: str | None = Header(None)):
    """Seed demo educators on demand.

    Protected by header `X-Admin-Token` which must match `settings.SECRET_KEY`.
    This avoids needing to redeploy to run the seeding script.
    """
    if x_admin_token is None or x_admin_token != settings.SECRET_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden")

    try:
        from app.scripts.seed_demo_users import seed_demo_educators
        seed_demo_educators()
        return {"seeded": True}
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))
