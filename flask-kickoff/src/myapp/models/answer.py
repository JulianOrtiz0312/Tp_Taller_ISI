from sqlalchemy import func

from myapp.extensions import db


class Answer(db.Model):
    __tablename__ = "answer"

    id_answer = db.Column(db.Integer, primary_key=True)
    cuerpo = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.Date, server_default=func.current_date(), nullable=False)
    accept = db.Column(db.Boolean, default=False, nullable=False)

    id_Autor = db.Column(
        db.Integer, db.ForeignKey("user.id", ondelete="SET NULL"), nullable=True
    )
    id_Question = db.Column(
        db.Integer, db.ForeignKey("question.id", ondelete="NO ACTION"), nullable=False
    )

    autor = db.relationship("User", backref=db.backref("answers", lazy=True))
    question = db.relationship("Question", backref=db.backref("answers", lazy=True))

    def __repr__(self):
        return f"<Answer {self.cuerpo}"

    def to_dict(self):
        return {
            "id_answer": self.id_answer,
            "cuerpo": self.cuerpo,
            "fecha": self.fecha,
            "accept": self.accept,
            "id_Autor": self.id_Autor,
            "id_Question": self.id_Question,
        }
