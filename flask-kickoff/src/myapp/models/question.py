from myapp.extensions import db
from sqlalchemy import func

class Question(db.Model):
	__tablename__ = "question"

	id = db.Column(db.Integer, primary_key = True)
	titulo = db.Column(db.String(200), nullable = False)
	cuerpo = db.Column(db.Text, nullable = False)
	fecha = db.Column(db.Date, server_default=func.current_date(), nullable = False)

	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)
	category_id = db.Column(db.Integer, db.ForeignKey("categories.id"), nullable = False)

	user = db.relationship("User", backref = db.backref("questions", lazy = True))
	category = db.relationship("Category", backref = db.backref("questions", lazy = True))

	def __repr__(self):
		return f"<Question {self.titulo}>"


	def to_dict(self):
		return {
			"id": self.id,
			"titulo": self.titulo,
			"cuerpo": self.cuerpo,
			"categoria": self.category_id,
			"fecha": self.fecha.isoformat() if self.fecha else None,
			"autor": self.user_id
		}

