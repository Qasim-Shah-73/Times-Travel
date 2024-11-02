from flask_wtf import FlaskForm
from wtforms import FormField, EmailField, StringField, TextAreaField, FieldList, BooleanField, HiddenField, SubmitField, IntegerField, PasswordField, SelectField, DecimalField
from wtforms.validators import DataRequired, Length, NumberRange, Email, EqualTo, ValidationError,Optional, InputRequired
from wtforms.fields import FormField as WTFormField
from flask_wtf.file import FileField, FileAllowed
from calendar import monthrange
from app.models import User, Room, Hotel, Agency

class LoginForm(FlaskForm):
    email = StringField('Email Address', validators=[DataRequired()])
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

class UserUpdateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('New Password', validators=[Optional(), Length(min=6)])
    role = SelectField('Role', choices=[], coerce=str)
    submit = SubmitField('Update')
    
class UserCreateForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=64)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    role = SelectField('Role', choices=[], coerce=str)
    agency_id = HiddenField('Agency ID', validators=[DataRequired()])
    submit = SubmitField('Create')

class AgencyForm(FlaskForm):
    # Fields for Agency
    name = StringField('Agency Name', validators=[DataRequired()])
    email = StringField('Agency Email', validators=[DataRequired(), Email()])
    designation = StringField('Designation', validators=[DataRequired()])
    telephone = IntegerField('Telephone', validators=[DataRequired()])
    credit_limit = DecimalField('Credit Limit', validators=[Optional(), NumberRange(min=0)], default=0.00)
    used_credit = DecimalField('Used Credit', validators=[Optional(), NumberRange(min=0)], default=0.00)
    paid_back = DecimalField('Paid Back', validators=[Optional(), NumberRange(min=0)], default=0.00)
    allowed_accounts = IntegerField('Allowed Accounts', validators=[NumberRange(min=0)], default=0)


    # Fields for Admin User
    admin_username = StringField('Admin Username', validators=[DataRequired()])
    admin_email = StringField('Admin Email', validators=[DataRequired(), Email()])
    admin_password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    admin_password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('admin_password')])

    submit = SubmitField('Register')

    # Custom validation to ensure the admin email does not exist
    def validate_admin_email(self, admin_email):
        user = User.query.filter_by(email=admin_email.data).first()
        if user is not None:
            raise ValidationError('Please use a different email address for the admin.')

class UpdateAgencyForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=128)])
    email = EmailField('Email', validators=[DataRequired(), Email()])
    designation = StringField('Designation', validators=[Optional(), Length(max=128)])
    telephone = IntegerField('Telephone', validators=[Optional()])
    credit_limit = DecimalField('Credit Limit', validators=[Optional(), NumberRange(min=0)], default=0.00)
    used_credit = DecimalField('Used Credit', validators=[Optional(), NumberRange(min=0)], default=0.00)
    paid_back = DecimalField('Paid Back', validators=[Optional(), NumberRange(min=0)], default=0.00)
    allowed_accounts = IntegerField('Allowed Accounts', validators=[Optional(), NumberRange(min=0)], default=0)
    submit = SubmitField('Update')

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
    location = SelectField('Location', choices=[('Makkah', 'Makkah, Saudi Arabia'), ('Madinah', 'Madinah, Saudi Arabia')], validators=[InputRequired()])
    availability = WTFormField(MonthAvailabilityForm)
    image = FileField('Hotel Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    stars = IntegerField('Stars', validators=[InputRequired(), NumberRange(min=1, max=5)], default=1)
    vendor_id = SelectField('Vendor', choices=[], coerce=int, validators=[InputRequired()])
    submit = SubmitField('Submit')

class UpdateHotelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    location = SelectField('Location', choices=[('Makkah', 'Makkah, Saudi Arabia'), ('Madinah', 'Madinah, Saudi Arabia')], validators=[InputRequired()], render_kw={"size": 1})
    availability = WTFormField(MonthAvailabilityForm)
    image = FileField('Update Hotel Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])
    stars = IntegerField('Stars', validators=[InputRequired(), NumberRange(min=1, max=5)], default=1)
    vendor_id = SelectField('Vendor', choices=[], coerce=int, validators=[InputRequired()])
    submit = SubmitField('Update')

class RatesForm(FlaskForm):
    rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]))

    def populate_rates(self, rate_dict):
        for i, rate in rate_dict.items():
            self.rates.append_entry(rate)

class RoomForm(FlaskForm):
    hotel_id = IntegerField('Hotel ID', validators=[DataRequired()])
    type = SelectField('Room Type', choices=[
        ('Double', 'Double'),
        ('Triple', 'Triple'),
        ('Quad', 'Quad'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_type = StringField('Other Room Type')
    view_type = SelectField('View Type', choices=[
        ('Standard', 'Standard'),
        ('City', 'City'),
        ('Haram/Kabba', 'Haram/Kabba')
    ], validators=[DataRequired()])
    availability = BooleanField('Availability')
    rooms_available = IntegerField('Rooms Available', validators=[DataRequired()])
    inclusion = SelectField('Inclusion', choices=[
        ('Room Only', 'Room Only'),
        ('Bread & Breakfast', 'Bread & Breakfast'),
        ('Half Board', 'Half Board'),
        ('Full Board', 'Full Board'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_inclusion = StringField('Other Inclusion')
    approval = StringField('Approved by')
    notes = StringField('Notes')
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
    
class UpdateRoomForm(FlaskForm):
    hotel_id = IntegerField('Hotel ID', validators=[DataRequired()])
    type = SelectField('Room Type', choices=[
        ('Double', 'Double'),
        ('Triple', 'Triple'),
        ('Quad', 'Quad'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_type = StringField('Other Room Type')
    view_type = SelectField('View Type', choices=[
        ('Standard', 'Standard'),
        ('City', 'City'),
        ('Haram/Kabba', 'Haram/Kabba')
    ], validators=[DataRequired()])
    availability = BooleanField('Availability')
    rooms_available = IntegerField('Rooms Available', validators=[DataRequired()])
    inclusion = SelectField('Inclusion', choices=[
        ('Room Only', 'Room Only'),
        ('Bread & Breakfast', 'Bread & Breakfast'),
        ('Half Board', 'Half Board'),
        ('Full Board', 'Full Board'),
        ('Other', 'Other')
    ], validators=[DataRequired()])
    other_inclusion = StringField('Other Inclusion')
    approval = StringField('Approved by')
    notes = StringField('Notes')
    
    # Instead of using FormField, we'll use FieldList directly
    january_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    february_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=28, max_entries=28)
    march_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    april_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=30, max_entries=30)
    may_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    june_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=30, max_entries=30)
    july_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    august_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    september_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=30, max_entries=30)
    october_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    november_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=30, max_entries=30)
    december_rates = FieldList(IntegerField('Rate', validators=[Optional(), NumberRange(min=0)]), min_entries=31, max_entries=31)
    
    submit = SubmitField('Update Room')
       
class VendorCreateForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Vendor Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    phone_number = IntegerField('Phone Number', validators=[Optional()])
    bank_details = StringField('Bank Details', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Create Vendor')

class VendorUpdateForm(FlaskForm):
    name = StringField('Vendor Name', validators=[DataRequired(), Length(max=100)])
    email = StringField('Vendor Email', validators=[DataRequired(), Email(), Length(max=120)])
    contact_person = StringField('Contact Person', validators=[Optional(), Length(max=100)])
    phone_number = IntegerField('Phone Number', validators=[Optional()])
    bank_details = StringField('Bank Details', validators=[Optional(), Length(max=255)])
    submit = SubmitField('Update Vendor')