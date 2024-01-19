from flask_wtf import FlaskForm
from wtforms import StringField,PasswordField,SubmitField,EmailField,BooleanField,DateField,RadioField
from wtforms.validators import DataRequired,length,Email,EqualTo
from flask_wtf.file import FileField, FileAllowed, FileRequired

class BreakoutForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    #level = StringField('Level', validator=[DataRequired()])
    image = FileField(validators=[FileRequired(),FileAllowed(['jpg','jpeg','png'],'We only allow images')])
    # status = BooleanField('Status', validators=[DataRequired()])
    submit = SubmitField('Add Topic!')

