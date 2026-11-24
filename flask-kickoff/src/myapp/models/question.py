from myapp.extensions import db
from sqlalchemy import func

class Question(db.Model):
	__tablename__ = "Question"

	id = db.Column(db.Integer, primary_key = True)
	titulo = db.Column(db.String(200), nullable = False)
	cuerpo = db.Column(db.Text, nullable = False)
	fecha = db.Column(db.Date, server_default=func.current_date(), nullable = False)

	user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable = False)

	user = db.relationship("User", backref = db.backref("questions", lazy = True))

	def __repr__(self):
		return f"<Question {self.titulo}>"


	def to_dict(self):
		return {
			"id": self.id,
			"titulo": self.titulo,
			"cuerpo": self.cuerpo,
			"fecha": self.fecha.isoformat() if self.fecha else None
			"auto": self.user_id
		}

