from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Length


class LoginForm(FlaskForm):
    username = StringField(validators=[DataRequired(message='Поле не должно быть пустым!'),
                                       Length(max=15, message=('Длина имени до 15 знаков!'))],
                           render_kw={'class': 'form-control', 'id': 'lableName', 'placeholder': 'Имя:'})
