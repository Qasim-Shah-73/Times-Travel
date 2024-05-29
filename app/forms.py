from flask_wtf import FlaskForm
from wtforms import FormField,StringField, TextAreaField, FieldList, BooleanField, SubmitField, IntegerField, PasswordField
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, ValidationError,Optional
from wtforms.fields import FormField as WTFormField
from calendar import monthrange
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

class HotelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[DataRequired(), Length(max=255)])
    location = StringField('Location', validators=[DataRequired(), Length(max=100)])
    availability = WTFormField(MonthAvailabilityForm)
    submit = SubmitField('Submit')

class UpdateHotelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = StringField('Location', validators=[DataRequired()])
    availability = WTFormField(MonthAvailabilityForm)
    submit = SubmitField('Update')

class RatesForm(FlaskForm):
    rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]))

class RoomForm(FlaskForm):
    hotel_id = IntegerField('Hotel ID', validators=[DataRequired()])
    type = StringField('Room Type', validators=[DataRequired()])
    availability = BooleanField('Availability')
    rooms_available = IntegerField('Rooms Available', validators=[DataRequired()])
    inclusion = StringField('Inclusion')
    january_rates = FormField(RatesForm)
    february_rates = FormField(RatesForm)
    march_rates = FormField(RatesForm)
    april_rates = FormField(RatesForm)
    may_rates = FormField(RatesForm)
    june_rates = FormField(RatesForm)
    july_rates = FormField(RatesForm)
    august_rates = FormField(RatesForm)
    september_rates = FormField(RatesForm)
    october_rates = FormField(RatesForm)
    november_rates = FormField(RatesForm)
    december_rates = FormField(RatesForm)
    submit = SubmitField('Create Room')