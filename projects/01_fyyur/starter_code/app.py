#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import sys
import json
import datetime
import logging
from logging import FileHandler, Formatter

import babel
import dateutil.parser
from flask import (Flask, Response, flash, redirect, render_template, request,
                   url_for, abort, jsonify)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import Form

from connection import app, db, moment
from forms import *
from models import Artist, Show, Venue

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

#app = Flask(__name__)
#moment = Moment(app)
migrate = Migrate(app, db)

# TODO: DONE connect to a local postgresql database

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE, MMMM d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: DONE replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

  data = []
  cities = db.session.query(Venue).with_entities(Venue.city, Venue.state).distinct()
  # create query object with each unique city in the venues table
  for city in cities:
    city_dict = dict(city)
    venue_list = []
    venues = db.session.query(Venue).with_entities(Venue.id, Venue.name).filter_by(city=city[0]).order_by('id')
    # for each city:
    # create a dictionary to hold the individual venues
    # create query object with all venues in that city
    for venue in venues:
      venue_dict = dict(venue)
      upcoming = db.session.query(Show).filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).count()
      venue_dict['num_upcoming_shows'] = upcoming
      venue_list.append(venue_dict)
      # for each venue:
      # create a dictionary to hold venue information
      # calculate upcoming shows by filtering shows associated with venue by time compared to now
      # add number of upcoming shows to dict
      # add dict to list of venues for city
    city_dict['venues'] = venue_list
    data.append(city_dict)
    # add list of venues to city dictionary
    # add city dictionary to data list

  return render_template('pages/venues.html', areas=data)

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: DONE implement search on venues with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"
  
  search_term = request.form.get('search_term', '')
  search = db.session.query(Venue.id, Venue.name).where(Venue.name.ilike("%" + search_term + "%"))
  # create query object, using case insensitive filtering by name
  data = []
  
  for i in search:
    search_dict = dict(i)
    search_dict['num_upcoming_shows'] = db.session.query(Show).filter_by(venue_id=search_dict['id']).filter(Show.start_time > datetime.now()).count()
    data.append(search_dict)
    # for each venue in the query object:
    # create dictionary with information on venue and add to data list
  count = len(data)
  
  response={
    "count": count,
    "data": data 
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id

  error = False
  try:
    venue = dict(db.session.query(Venue.id, Venue.name, Venue.genres, Venue.address, Venue.city, Venue.state, Venue.phone, Venue.website_link.label('website'), Venue.facebook_link, Venue.seeking_talent, Venue.seeking_description, Venue.image_link).filter_by(id=venue_id).first())
    # create dictionary with venue info, filtering by ID
    venue['genres'] = venue['genres'].strip('{}').split(',')
    # reformat genre list

    past_shows = []
    pshows = db.session.query(Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time).join(Artist).filter_by(venue_id=venue_id).filter(Show.start_time < datetime.now())
    for pshow in pshows:
      pshow_dict = dict(pshow)
      pshow_dict['start_time'] = pshow_dict['start_time'].isoformat()
      past_shows.append(pshow_dict)
    venue['past_shows'] = past_shows
    # create list of past shows, querying a joined table by venue ID and filtering for shows started before current moment, and add to data dictionary

    upcoming_shows = []
    ushows = db.session.query(Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time).join(Artist).filter_by(venue_id=venue_id).filter(Show.start_time > datetime.now())
    for ushow in ushows:
      ushow_dict = dict(ushow)
      ushow_dict['start_time'] = ushow_dict['start_time'].isoformat()
      upcoming_shows.append(ushow_dict)
    venue['upcoming_shows'] = upcoming_shows
    # create list of upcoming shows, same as past shows

    venue['past_shows_count'] = len(past_shows)
    venue['upcoming_shows_count'] = len(upcoming_shows)
  except Exception as e:
    error = True
    print(e)
  if error:
    abort(404)
    # if error occurs (probably nonexistent ID), redirect 404
  else:
    return render_template('pages/show_venue.html', venue=venue)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():

  error = False
  try:
    if 'seeking_talent' in request.form:
      seeking_talent = True
    else:
      seeking_talent = False
    new_venue = Venue(
      name=request.form['name'].title(),
      city=request.form['city'].title(),
      state=request.form['state'],
      address=request.form['address'].title(),
      phone=request.form['phone'],
      image_link=request.form['image_link'],
      genres=request.form.getlist('genres'),
      website_link=request.form['website_link'],
      facebook_link=request.form['facebook_link'],
      seeking_talent=seeking_talent,
      seeking_description=request.form['seeking_description']
    )
    # create venue object with submitted data from form, creating boolean value from existence of 'seeking_talent' field
    db.session.add(new_venue)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    print(e)
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
    # add and commit venue to database, rolling back changes and redirecting 500 if an error occurs 

  # TODO: DONE insert form data as a new Venue record in the db, instead
  # TODO: modify data to be the data object returned from db insertion

  # on successful db insert, flash success
  #flash('Venue ' + request.form['name'] + ' was successfully listed!')
  # TODO: on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Venue ' + data.name + ' could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/
  #return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: DONE Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

  error = False
  venue = Venue.query.get(venue_id)
  try:
    db.session.delete(venue)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    print(e)
  finally:
    db.session.close()
  if error:
    flash('An error occurred. Venue ' + venue.name + ' could not be deleted.')
    return jsonify({ 'success': False })
  else:
    flash('Venue ' + venue.name + ' was deleted.')
    return jsonify({ 'success': True })
  # get venue by ID and delete from database, rolling back changes with error
  
  # BONUS CHALLENGE: DONE Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: DONE replace with real data returned from querying the database
  
  data = []
  artists = db.session.query(Artist.id, Artist.name)
  # create query object with all artist IDs and names
  for artist in artists:
    artist_dict = dict(artist)
    upcoming = db.session.query(Show).filter_by(artist_id=artist.id).filter(Show.start_time > datetime.now()).count()
    artist_dict['num_upcoming_shows'] = upcoming
    data.append(artist_dict)
  # for each artist in the query object:
  # add data to dictionary, along with number of upcoming shows calculated by querying shows and filtering for time vs now
  # add dictionary to data list
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: DONE implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".

  search_term = request.form.get('search_term', '')
  search = db.session.query(Artist.id, Artist.name).where(Artist.name.ilike("%" + search_term + "%"))
  # get search term and run case insensitive query, returning artist info
  data = []
  
  for i in search:
    search_dict = dict(i)
    search_dict['num_upcoming_shows'] = db.session.query(Show).filter_by(artist_id=search_dict['id']).filter(Show.start_time > datetime.now()).count()
    data.append(search_dict)
  # for each artist in the query object:
  # get information and add to a dictionary, along with upcoming shows count
  # add dictionary to list of data
  count = len(data)

  response={
    "count": count,
    "data": data 
  }
  
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  # shows the artist page with the given artist_id
  # TODO: DONE replace with real artist data from the artist table, using artist_id
  error = False
  try:
    artist = dict(db.session.query(Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, Artist.phone, Artist.website_link.label('website'), Artist.facebook_link, Artist.seeking_venue, Artist.seeking_description, Artist.image_link).filter_by(id=artist_id).first())
    # create dictionary with artist info, filtering by ID
    artist['genres'] = artist['genres'].strip('{}').split(',')
    # reformat genre list

    past_shows = []
    pshows = db.session.query(Show.venue_id, Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time).join(Venue).filter_by(artist_id=artist_id).filter(Show.start_time < datetime.now())
    for pshow in pshows:
      pshow_dict = dict(pshow)
      pshow_dict['start_time'] = pshow_dict['start_time'].isoformat()
      past_shows.append(pshow_dict)
    artist['past_shows'] = past_shows
    # create list of past shows, querying a joined table by artist ID and filtering for shows started before current moment, and add to data dictionary

    upcoming_shows = []
    ushows = db.session.query(Show.venue_id, Venue.name.label('venue_name'), Venue.image_link.label('venue_image_link'), Show.start_time).join(Venue).filter_by(artist_id=artist_id).filter(Show.start_time > datetime.now())
    for ushow in ushows:
      ushow_dict = dict(ushow)
      ushow_dict['start_time'] = ushow_dict['start_time'].isoformat()
      upcoming_shows.append(ushow_dict)
    artist['upcoming_shows'] = upcoming_shows
    # create list of upcoming shows, same as past shows

    artist['past_shows_count'] = len(past_shows)
    artist['upcoming_shows_count'] = len(upcoming_shows)
  except Exception as e:
    error = True
    print(e)
  if error:
    abort(404)
    # if error occurs (probably nonexistent ID), redirect 404
  else:
    return render_template('pages/show_artist.html', artist=artist)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  error = False
  try:
    artist = dict(db.session.query(Artist.id, Artist.name, Artist.genres, Artist.city, Artist.state, Artist.phone, Artist.website_link, Artist.facebook_link, Artist.seeking_venue, Artist.seeking_description, Artist.image_link).filter_by(id=artist_id).first())
    # create dictionary from query object containing artist attributes
    artist['genres'] = artist['genres'].strip('{}').split(',')
    # format genre list
  except Exception as e:
    error = True
    print(e)
  if error:
    abort(404)
    # if error occurs (probably nonexistent ID), redirect 404
  else:
  # TODO: DONE populate form with fields from artist with ID <artist_id>
    form = ArtistForm(obj=artist)
    form.name.data = artist['name']
    form.genres.data = artist['genres']
    form.city.data = artist['city']
    form.state.data = artist['state']
    form.phone.data = artist['phone']
    form.website_link.data = artist['website_link']
    form.facebook_link.data = artist['facebook_link']
    form.seeking_venue.data = artist['seeking_venue']
    form.seeking_description.data = artist['seeking_description']
    form.image_link.data = artist['image_link']
    # populate form fields with data from query
    
    return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  # TODO: take values from the form submitted, and update existing
  # artist record with ID <artist_id> using the new attributes
  error = False
  try:
    if 'seeking_venue' in request.form:
      seeking_venue = True
    else:
      seeking_venue = False
    # set seeking_venue boolean
    db.session.query(Artist).filter_by(id=artist_id).update({\
    'name': request.form['name'], \
    'city': request.form['city'], \
    'state': request.form['state'], \
    'phone': request.form['phone'], \
    'genres': request.form.getlist('genres'), \
    'image_link': request.form['image_link'], \
    'website_link': request.form['website_link'], \
    'facebook_link': request.form['facebook_link'], \
    'seeking_venue': seeking_venue, \
    'seeking_description': request.form['seeking_description'], \
    })
    db.session.commit()
    # update database with data from form
  except Exception as e:
    error = True
    print(sys.exc_info())
    print(e)
    db.session.rollback()
    # rollback database in case of error
  finally:
    db.session.close()
  if error:
    print(sys.exc_info())
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be edited.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully edited!')

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  ## TODO: DONE populate form with values from venue with ID <venue_id>
  #return render_template('forms/edit_venue.html', form=form, venue=venue)
  error = False
  try:
    venue = dict(db.session.query(Venue.id, Venue.name, Venue.genres, Venue.address, Venue.city, Venue.state, Venue.phone, Venue.website_link, Venue.facebook_link, Venue.seeking_talent, Venue.seeking_description, Venue.image_link).filter_by(id=venue_id).first())
    # create dictionary from query object containing venue attributes
    venue['genres'] = venue['genres'].strip('{}').split(',')
    # format genre list
  except Exception as e:
    error = True
    print(e)
  if error:
    abort(404)
    # if error occurs (probably nonexistent ID), redirect 404
  else:
  # TODO: DONE populate form with fields from venue with ID <venue_id>
    form = VenueForm(obj=venue)
    form.name.data = venue['name']
    form.genres.data = venue['genres']
    form.address.data = venue['address']
    form.city.data = venue['city']
    form.state.data = venue['state']
    form.phone.data = venue['phone']
    form.website_link.data = venue['website_link']
    form.facebook_link.data = venue['facebook_link']
    form.seeking_talent.data = venue['seeking_talent']
    form.seeking_description.data = venue['seeking_description']
    form.image_link.data = venue['image_link']
    # populate form fields with data from query
    
    return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  # TODO: DONE take values from the form submitted, and update existing
  # venue record with ID <venue_id> using the new attributes
  error = False
  try:
    if 'seeking_talent' in request.form:
      seeking_talent= True
      # set seeking_talent boolean
    else:
      seeking_talent= False
    db.session.query(Venue).filter_by(id=venue_id).update({\
    'name': request.form['name'], \
    'address': request.form['address'], \
    'city': request.form['city'], \
    'state': request.form['state'], \
    'phone': request.form['phone'], \
    'genres': request.form.getlist('genres'), \
    'image_link': request.form['image_link'], \
    'website_link': request.form['website_link'], \
    'facebook_link': request.form['facebook_link'], \
    'seeking_talent': seeking_talent, \
    'seeking_description': request.form['seeking_description'], \
    })
    db.session.commit()
    # update database with data from form
  except Exception as e:
    error = True
    print(sys.exc_info())
    print(e)
    db.session.rollback()
    # rollback database in case of error
  finally:
    db.session.close()
  if error:
    print(sys.exc_info())
    flash('An error occurred. Venue ' + request.form['name'] + ' could not be edited.')
  else:
    flash('Venue ' + request.form['name'] + ' was successfully edited!')

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  # called upon submitting the new artist listing form
  error = False
  # TODO: DONE insert form data as a new Venue record in the db, instead
  try:
    if 'seeking_venue' in request.form:
      seeking_venue = True
    else:
      seeking_venue = False
    new_artist = Artist(
      name = request.form['name'],
      city = request.form['city'],
      state = request.form['state'],
      phone = request.form['phone'],
      genres = request.form.getlist('genres'),
      image_link = request.form['image_link'],
      website_link = request.form['website_link'],
      facebook_link = request.form['facebook_link'],
      seeking_venue = seeking_venue,
      seeking_description = request.form['seeking_description'],
    )
    # create artist object with submitted data from form, creating boolean value from existence of 'seeking_venue' field
    db.session.add(new_artist)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    print(e)
    flash('An error occurred. Artist ' + request.form['name'] + ' could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
    return render_template('pages/home.html')
    # add and commit artist to database, rolling back changes and redirecting 500 if an error occurs 

  # TODO: DONE modify data to be the data object returned from db insertion
  # on successful db insert, flash success
  # TODO: DONE on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Artist ' + data.name + ' could not be listed.')

#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  # TODO: DONE replace with real venues data.
  data = []
  shows = db.session.query(Show.venue_id, Venue.name.label('venue_name'), Show.artist_id, Artist.name.label('artist_name'), Artist.image_link.label('artist_image_link'), Show.start_time).join(Venue).join(Artist).all()
  # create query object containing the venue id and name and artist id, name, and image link for every show using a join
  for show in shows:
    show_dict = dict(show)
    show_dict['start_time'] = show_dict['start_time'].isoformat()
    data.append(show_dict)
  # for each show in the query object:
  # create a dictionary with information and format the start time

  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error = False
  try:
    new_show = Show(
      artist_id=request.form['artist_id'],
      venue_id=request.form['venue_id'],
      start_time=request.form['start_time']
    )
    # create show object with submitted data from form
    db.session.add(new_show)
    db.session.commit()
  except Exception as e:
    error = True
    db.session.rollback()
    print(sys.exc_info())
    print(e)
    flash('An error occurred. Show could not be listed.')
  finally:
    db.session.close()
  if error:
    abort(500)
  else:
    flash('Show was successfully listed!')
    return render_template('pages/home.html')
  # add and commit artist to database, rolling back changes and redirecting 500 if an error occurs 
  
  # TODO: DONE insert form data as a new Show record in the db, instead
  # on successful db insert, flash success
  # TODO: DONE on unsuccessful db insert, flash an error instead.
  # e.g., flash('An error occurred. Show could not be listed.')
  # see: http://flask.pocoo.org/docs/1.0/patterns/flashing/

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
