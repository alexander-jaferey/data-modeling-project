#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

from datetime import datetime
from flask_wtf import Form
from wtforms import StringField, SelectField, SelectMultipleField, DateTimeField, BooleanField
from wtforms.validators import DataRequired, AnyOf, URL, ValidationError, Optional
from re import fullmatch
from enumerations import State, Genre


#----------------------------------------------------------------------------#
# Functions
#----------------------------------------------------------------------------#

def validate_phone(form, field):
    if not fullmatch(r'^(?:\+)?(1)?[\s.-]?(\()?([0-9]{3})(\))?[\s.-]?([0-9]{3})[\s.-]?([0-9]{4})', field):
        # regular expression matching for common phone number formats, including
        # optional +1 country code, optional parentheses around area code, and
        # optional spaces, dots, or hyphens between blocks of digits
        raise ValidationError('Hmm, that doesn\'t look like a US phone number. Try again!')

#----------------------------------------------------------------------------#
# Forms
#----------------------------------------------------------------------------#

class ShowForm(Form):
    artist_id = StringField(
        'artist_id',
        validators=[DataRequired()]
    )
    venue_id = StringField(
        'venue_id',
        validators=[DataRequired()]
    )
    start_time = DateTimeField(
        'start_time',
        validators=[DataRequired()],
        default= datetime.today()
    )

class VenueForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices()
    )
    address = StringField(
        'address', validators=[DataRequired()]
    )
    phone = StringField(
        'phone', validators=[validate_phone]
    )
    image_link = StringField(
        'image_link'
    )
    genres = SelectMultipleField(
        # TODO DONE implement enum restriction
        'genres', validators=[DataRequired()],
        choices=Genre.choices()
    )
    facebook_link = StringField(
        'facebook_link', validators=[Optional(), URL()]
    )
    website_link = StringField(
        'website_link', validators=[Optional(), URL()]
    )

    seeking_talent = BooleanField( 'seeking_talent' )

    seeking_description = StringField(
        'seeking_description'
    )

class ArtistForm(Form):
    name = StringField(
        'name', validators=[DataRequired()]
    )
    city = StringField(
        'city', validators=[DataRequired()]
    )
    state = SelectField(
        'state', validators=[DataRequired()],
        choices=State.choices()
    )
    phone = StringField(
        # TODO DONE implement validation logic for phone 
        'phone', validators=[validate_phone]
    )
    image_link = StringField(
        'image_link'
    )
    genres = SelectMultipleField(
        'genres', validators=[DataRequired()],
        choices=Genre.choices()
    )
    facebook_link = StringField(
        # TODO implement enum restriction
        'facebook_link', validators=[Optional(), URL()]
     )

    website_link = StringField(
        'website_link', validators=[Optional(), URL()]
     )

    seeking_venue = BooleanField( 'seeking_venue' )

    seeking_description = StringField(
            'seeking_description'
     )

