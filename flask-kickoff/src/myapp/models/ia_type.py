from myapp.extensions import db


class IAType(db.Model):
    __tablename__ = "ia_types"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)

    def __repr__(self):
        return f"<IAType {self.name}>"

    def to_dist(self):
        return {"id": self.id, "name": self.name, "is_active": self.is_active}
