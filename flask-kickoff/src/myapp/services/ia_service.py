from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models.ia_type import IAType
from myapp.models.user import User, UserRole


class IAServiceError(ValueError):
    pass


class UnauthorizedIAError(IAServiceError):
    pass


class DuplicateIAError(IAServiceError):
    pass


class InvalidIANameError(IAServiceError):
    pass


class IATypeNotFoundError(IAServiceError):
    pass


class InactiveIAError(IAServiceError):
    pass


def create_ia_type(
    name: str,
    user_id: int | None,
) -> IAType:

    if user_id is None:
        raise UnauthorizedIAError("el id no debe ser vacio")

    user = db.session.get(User, user_id)

    if user is None or user.role != UserRole.ADMIN:
        raise UnauthorizedIAError("usuario no encontrado o rol equivocado")

    name_clean = (name or "").strip().lower()
    if not name_clean:
        raise InvalidIANameError("el nombre de la ia no debe ser vacio")

    existe = db.session.scalar(db.select(IAType).where(IAType.name == name_clean))
    if existe is not None:
        raise DuplicateIAError("la ia ya esta estaba guardada")

    has_selected = (
        db.session.scalar(db.select(IAType).where(IAType.is_selected.is_(True)))
        is not None
    )

    ia = IAType(name=name_clean, is_active=True, is_selected=not has_selected)
    db.session.add(ia)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicateIAError("la ia ya existe en el sistema") from exc

    db.session.refresh(ia)
    return ia


def list_ia_types(only_active: bool = False) -> list[IAType]:
    consulta = db.select(IAType).order_by(IAType.id)
    if only_active:
        consulta = consulta.where(IAType.is_active.is_(True))
    return list(db.session.scalars(consulta).all())


def switch_ia_type(ia_id: int, user_id: int| None)-> IAType:
    if user_id is None:
        raise UnauthorizedIAError("el id no debe ser vacio")

    user = db.session.get(User,user_id)
    if user is None or user.role != UserRole.ADMIN:
        raise UnauthorizedIAError("usuario no encontrado o rol euqivocado")

    target_ia = db.session.get(IAType, ia_id)
    if target_ia is None:
        raise IATypeNotFoundError("la ia no existe")

    if not target_ia.is_active:
        raise InactiveIAError("esa ia no esta habilitada")


    if target_ia.is_selected:
        return target_ia

    current_selected = db.session.scalar(db.select(IAType).where(IAType.is_selected.is_(True)))
    if current_selected is not None:
        current_selected.is_selected = False

    target_ia.is_selected = True
    db.session.commit()
    db.session.refresh(target_ia)
    return target_ia


def get_selected_ia_type() -> IAType | None:
    return db.session.scalar(
        db.select(IAType).where(
            IAType.is_selected.is_(True),
            IAType.is_active.is_(True),
        )
    )
    