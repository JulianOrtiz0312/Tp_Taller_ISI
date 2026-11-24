import logging

from myapp.extensions import db
from myapp.models.user import User

logger = logging.getLogger(__name__)


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
        clean_email = new_email.strip()
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
