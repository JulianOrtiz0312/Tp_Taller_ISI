from sqlalchemy.exc import IntegrityError

from myapp.extensions import db
from myapp.models.user import User, UserRole


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
