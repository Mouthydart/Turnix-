"""Lógica de negocio del CRUD de negocios.

Reglas principales:
- Solo los usuarios con rol `owner` (o `admin`) pueden crear negocios.
- Un `owner` solo accede a los negocios que posee; un `admin` accede a todos.
- El `slug` es único; se genera a partir del nombre si no se proporciona.
"""

from fastapi import HTTPException, status

from app.core.utils import slugify
from app.db.repositories import business_repository
from app.models import Business, PlanName, User, UserRole, WeeklySchedule
from app.models.types import validate_object_id
from app.schemas.business import BusinessCreate, BusinessUpdate


def _assert_can_create(user: User) -> None:
    """Comprueba que el usuario pueda crear negocios."""
    if user.role not in (UserRole.OWNER, UserRole.ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo los propietarios pueden crear negocios",
        )


def _assert_can_manage(user: User, business: Business) -> None:
    """Comprueba que el usuario sea el propietario del negocio (o admin)."""
    if user.role == UserRole.ADMIN:
        return
    if business.owner_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes acceso a este negocio",
        )


async def _unique_slug(base: str) -> str:
    """Genera un slug libre, añadiendo un sufijo numérico si ya está en uso."""
    slug = base
    suffix = 2
    while await business_repository.exists({"slug": slug}):
        slug = f"{base}-{suffix}"
        suffix += 1
    return slug


async def _get_managed_business(business_id: object, user: User) -> Business:
    """Carga un negocio y verifica que el usuario pueda gestionarlo."""
    try:
        object_id = validate_object_id(business_id)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado",
        ) from exc

    business = await business_repository.get_by_id(object_id)
    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado",
        )
    _assert_can_manage(user, business)
    return business


async def create_business(user: User, payload: BusinessCreate) -> Business:
    """Crea un negocio cuyo propietario es el usuario autenticado."""
    _assert_can_create(user)

    if payload.slug:
        if await business_repository.exists({"slug": payload.slug}):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="El slug ya está en uso",
            )
        slug = payload.slug
    else:
        slug = await _unique_slug(slugify(payload.name))

    business = Business(
        name=payload.name,
        slug=slug,
        owner_id=user.id,
        plan=PlanName.FREEMIUM,
        timezone=payload.timezone,
        currency=payload.currency,
        phone=payload.phone,
        address=payload.address,
        description=payload.description,
        schedule=payload.schedule or WeeklySchedule.default(),
    )
    return await business_repository.insert(business)


async def list_businesses(user: User) -> list[Business]:
    """Lista los negocios del usuario (todos, si es admin)."""
    if user.role == UserRole.ADMIN:
        return await business_repository.find_many()
    return await business_repository.find_many({"owner_id": user.id})


async def get_business(business_id: object, user: User) -> Business:
    """Devuelve un negocio gestionable por el usuario."""
    return await _get_managed_business(business_id, user)


async def update_business(business_id: object, user: User, payload: BusinessUpdate) -> Business:
    """Actualiza parcialmente un negocio gestionable por el usuario."""
    business = await _get_managed_business(business_id, user)

    changes = payload.model_dump(exclude_unset=True)
    new_slug = changes.get("slug")
    if new_slug and new_slug != business.slug and await business_repository.exists(
        {"slug": new_slug}
    ):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El slug ya está en uso",
        )

    if not changes:
        return business

    updated = await business_repository.update(business.id, changes)
    if updated is None:  # pragma: no cover - el negocio existe, no debería ocurrir
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negocio no encontrado",
        )
    return updated


async def delete_business(business_id: object, user: User) -> None:
    """Elimina un negocio gestionable por el usuario.

    Nota: por ahora no elimina en cascada los empleados, servicios ni reservas
    asociados; se abordará cuando existan esas entidades.
    """
    business = await _get_managed_business(business_id, user)
    await business_repository.delete(business.id)
