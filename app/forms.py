from flask_wtf import FlaskForm
from wtforms import (StringField,TextAreaField,FloatField,BooleanField,DateTimeField,SubmitField,IntegerField,FormField,PasswordField,HiddenField)
from wtforms.validators import (DataRequired,Length,NumberRange,Email,EqualTo,ValidationError)
from app.models import User, Room, Hotel

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address.')

class MonthAvailabilityForm(FlaskForm):
    January = BooleanField('January')
    February = BooleanField('February')
    March = BooleanField('March')
    April = BooleanField('April')
    May = BooleanField('May')
    June = BooleanField('June')
    July = BooleanField('July')
    August = BooleanField('August')
    September = BooleanField('September')
    October = BooleanField('October')
    November = BooleanField('November')
    December = BooleanField('December')

class MonthRatesForm(FlaskForm):
    January = FloatField('January', validators=[NumberRange(min=0)])
    February = FloatField('February', validators=[NumberRange(min=0)])
    March = FloatField('March', validators=[NumberRange(min=0)])
    April = FloatField('April', validators=[NumberRange(min=0)])
    May = FloatField('May', validators=[NumberRange(min=0)])
    June = FloatField('June', validators=[NumberRange(min=0)])
    July = FloatField('July', validators=[NumberRange(min=0)])
    August = FloatField('August', validators=[NumberRange(min=0)])
    September = FloatField('September', validators=[NumberRange(min=0)])
    October = FloatField('October', validators=[NumberRange(min=0)])
    November = FloatField('November', validators=[NumberRange(min=0)])
    December = FloatField('December', validators=[NumberRange(min=0)])

class MonthWeekendRatesForm(FlaskForm):
    January = FloatField('January', validators=[NumberRange(min=0)], default=0)
    February = FloatField('February', validators=[NumberRange(min=0)], default=0)
    March = FloatField('March', validators=[NumberRange(min=0)], default=0)
    April = FloatField('April', validators=[NumberRange(min=0)], default=0)
    May = FloatField('May', validators=[NumberRange(min=0)], default=0)
    June = FloatField('June', validators=[NumberRange(min=0)], default=0)
    July = FloatField('July', validators=[NumberRange(min=0)], default=0)
    August = FloatField('August', validators=[NumberRange(min=0)], default=0)
    September = FloatField('September', validators=[NumberRange(min=0)], default=0)
    October = FloatField('October', validators=[NumberRange(min=0)], default=0)
    November = FloatField('November', validators=[NumberRange(min=0)], default=0)
    December = FloatField('December', validators=[NumberRange(min=0)], default=0)

class HotelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=255)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    availability = FormField(MonthAvailabilityForm)
    submit = SubmitField('Submit')

class UpdateHotelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    availability = FormField(MonthAvailabilityForm)
    submit = SubmitField('Update')

class RoomForm(FlaskForm):
    hotel_id = HiddenField('Hotel ID', validators=[DataRequired()])
    type = StringField('Type', validators=[DataRequired(), Length(max=100)])
    availability = BooleanField('Availability')
    rooms_available = IntegerField('Rooms Available', validators=[DataRequired(), NumberRange(min=1)])
    rates = FormField(MonthRatesForm)
    weekend_rates_addition = FormField(MonthWeekendRatesForm)
    submit = SubmitField('Submit')