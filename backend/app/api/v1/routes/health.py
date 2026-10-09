from fastapi import APIRouter

router = APIRouter()


@router.get("", summary="Estado del servicio v1")
async def health_v1() -> dict[str, str]:
    return {"service": "turnix-api", "version": "v1"}
