import logging

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models import Category

logger = logging.getLogger(__name__)


class CategoryServiceError(Exception):
    pass


class CategoryNotFoundError(CategoryServiceError):
    pass


class CategoryValidationError(CategoryServiceError):
    pass


class CategoryConflictError(CategoryServiceError):
    pass


def update_category(category_id: int, raw_name: object) -> Category:
    category = db.session.get(Category, category_id)
    if category is None:
        raise CategoryNotFoundError("La categoria no existe.")

    if not isinstance(raw_name, str) or not raw_name.strip():
        raise CategoryValidationError("El nombre de la categoria no puede estar vacio.")

    clean_name = raw_name.strip()
    if len(clean_name) > 120:
        raise CategoryValidationError(
            "El nombre de la categoria no puede superar los 120 caracteres."
        )

    existing = db.session.scalar(
        db.select(Category).where(
            func.lower(Category.name) == clean_name.lower(),
            Category.id != category_id,
        )
    )
    if existing is not None:
        raise CategoryConflictError("Ya existe otra categoria con ese nombre.")

    category.name = clean_name

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise CategoryConflictError("Ya existe otra categoria con ese nombre.") from exc

    logger.info("Categoria id=%s actualizada a '%s'", category.id, category.name)
    return category
