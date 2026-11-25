import logging

from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models.user import User, UserRole

logger = logging.getLogger(__name__)


class UserServiceError(ValueError):
    """Error de dominio en operaciones de usuario."""


class DuplicateEmailError(UserServiceError):
    """El correo electrónico ya se encuentra registrado."""


def register_user(
    name: str,
    email: str,
    password: str,
    role: UserRole = UserRole.GENERAL,
) -> User:
    name_clean = name.strip()
    email_clean = email.strip().lower()

    if not name_clean:
        raise UserServiceError("El nombre es obligatorio.")

    if not email_clean or "@" not in email_clean:
        raise UserServiceError("Debe ingresar un correo electrónico válido.")

    if not password or len(password) < 6:
        raise UserServiceError("La contraseña debe tener al menos 6 caracteres.")

    existing = db.session.scalar(db.select(User).where(User.email == email_clean))
    if existing is not None:
        raise DuplicateEmailError("El correo electrónico ya está registrado.")

    user = User(name=name_clean, email=email_clean, role=role)
    user.set_password(password)
    db.session.add(user)

    try:
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise DuplicateEmailError("El correo electrónico ya está registrado.") from exc

    return user


def list_users() -> list[User]:
    return list(db.session.scalars(db.select(User)).all())


def update_user_data(
    acting_user_id: int,
    target_user_id: int,
    new_email: str | None = None,
    current_password: str | None = None,
    new_password: str | None = None,
) -> User:
    if acting_user_id != target_user_id:
        raise PermissionError("No tienes permiso para modificar otra cuenta.")

    user = db.session.get(User, target_user_id)
    if not user:
        raise LookupError("Usuario no encontrado.")

    if new_email is not None:
        clean_email = new_email.strip().lower()
        if not clean_email or clean_email == user.email:
            raise ValueError(
                "El nuevo correo no puede estar vacío ni ser igual al anterior."
            )

        existing_user = db.session.scalar(
            db.select(User).where(User.email == clean_email)
        )
        if existing_user is not None:
            raise ValueError(
                "El nuevo correo electrónico ya está asociado a otra cuenta."
            )

        user.email = clean_email

    if new_password is not None:
        if not current_password or not user.check_password(current_password):
            raise ValueError("Debes ingresar correctamente tu contraseña actual.")

        if not new_password.strip() or user.check_password(new_password):
            raise ValueError(
                "La nueva contraseña no puede estar vacía ni ser igual a la anterior."
            )

        user.set_password(new_password)

    db.session.commit()
    logger.info("Cuenta actualizada correctamente para user_id=%s", user.id)
    return user


def assign_user_role(target_user_id: int, new_role: str | UserRole) -> User:
    if isinstance(new_role, UserRole):
        parsed_role = new_role
    elif isinstance(new_role, str):
        normalized = new_role.strip().lower()
        try:
            parsed_role = UserRole(normalized)
        except ValueError as exc:
            raise UserServiceError(
                "Rol inválido. Los valores permitidos son: 'admin' o 'general'."
            ) from exc
    else:
        raise UserServiceError("El rol debe ser una cadena de texto válida.")

    user = db.session.get(User, target_user_id)
    if user is None:
        raise LookupError("El usuario destino no existe.")

    user.role = parsed_role
    db.session.commit()
    db.session.refresh(user)
    logger.info("Rol actualizado a '%s' para user_id=%s", parsed_role.value, user.id)
    return user


def delete_user(acting_user_id: int, target_user_id: int) -> None:
    user = db.session.get(User, target_user_id)
    if user is None:
        raise LookupError("La cuenta de usuario no existe.")

    if acting_user_id != target_user_id:
        raise PermissionError("No tienes permiso para eliminar otra cuenta.")

    db.session.delete(user)
    db.session.commit()
    logger.info("Cuenta eliminada completamente para user_id=%s", target_user_id)
