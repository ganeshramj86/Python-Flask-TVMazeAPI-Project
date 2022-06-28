## CMP9312 DATA SERVICES ENGINEERING - ASSIGNMENT-2
## zID: 3228822

# Import Libraries
from flask import Flask, request, Response, jsonify
from flask_restx import Resource, Api, fields, reqparse
import sqlalchemy as db
import re
import requests
import datetime
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import text
from sqlalchemy import select, func
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
import io
import json

plt.ioff()

# Create DB file and engine
engine = db.create_engine('sqlite:///z3228822.db')

metadata = db.MetaData()
actors = db.Table('actors', metadata,
          db.Column('id', db.Integer(), primary_key=True),
          db.Column('tvmazeApiId', db.Integer(), unique=True, nullable=False),
          db.Column('name', db.String(255), nullable=False),
          db.Column('country', db.String(255), nullable=True),
          db.Column('birthday', db.Date, nullable=True),
          db.Column('deathday', db.Date, nullable=True),
          db.Column('gender', db.String(255), nullable=True),
          db.Column('shows', db.String(1024), default = '', nullable=True),
          db.Column('lastupdate', db.DateTime, default=datetime.datetime.now().replace(microsecond=0))
          )
metadata.create_all(engine)

# Flask App Declaration
app = Flask(__name__)
api = Api(app,
          default="Actors",  # Default namespace
          title="TV Actors API",  # Documentation Title
          description="API for TV Actors/ Actresses ")  # Documentation Description

class getalllinks(fields.Raw):
    def format(self, value):
        selfLink = request.host_url + "actors/" + str(value)
        links_dict = {}
        links_dict["self"] = {}
        links_dict["previous"] = {}
        links_dict["next"] = {}
        links_dict["self"]["href"] = selfLink
        
        # Check if previous link is there or not and update links
        query_previd = db.select([actors]).order_by(db.desc(actors.columns.id)) \
                        .filter(actors.columns.id < value)
        prevId = engine.execute(query_previd).first()
        
        if prevId is not None:
            prevLink = request.host_url + "actors/" + str(prevId[0])
            links_dict["previous"]["href"] = prevLink
        else :
            links_dict["previous"]["href"] = ""
        
        # Check if next link is there or not and update links
        query_nextid = db.select([actors]).order_by(db.asc(actors.columns.id)) \
                        .filter(actors.columns.id > value)
        nextId = engine.execute(query_nextid).first()
        
        if nextId is not None:
            nextLink = request.host_url + "actors/" + str(nextId[0])
            links_dict["next"]["href"] = nextLink
        else :
            links_dict["next"]["href"] = ""
        
        return links_dict

class getshowlist(fields.Raw):
    def format(self, value):
        return value.split(',')

class getselflinks(fields.Raw):
    def format(self, value):
        selfLink = request.host_url + "actors/" + str(value)
        links_dict = {}
        links_dict["self"] = {}
        links_dict["self"]["href"] = selfLink
        return links_dict

class getlastupdate(fields.Raw):
    def format(self, value):
        return value.strftime('%Y-%m-%d-%H:%M:%S')

actor_post_model = api.model('PostActor', {
        'id': fields.Integer,
        'last-update': getlastupdate(attribute='lastupdate'),
        '_links': getselflinks(attribute='id'),
    })

actor_get_model = api.model('GetActor', {
        'id': fields.Integer,
        'last-update': getlastupdate(attribute='lastupdate'),
        'name': fields.String,
        'country': fields.String,
        'birthday': fields.String,
        'deathday': fields.String,
        'gender': fields.String,
        'shows': getshowlist(attribute='shows'),
        '_links': getalllinks(attribute='id'),
    })


actor_model = api.model('Actor', {
    'name': fields.String,
    'country': fields.String,
    'birthday': fields.Date,
    'deathday': fields.Date,
    'shows': fields.List(fields.String),
    'gender': fields.String
})

# argument parser
parser = reqparse.RequestParser()
parser.add_argument('var1', type=str, required=True)

parser2 = reqparse.RequestParser()
parser2.add_argument('order', type=str, default='+id')
parser2.add_argument('page', type=int, default=1)
parser2.add_argument('size', type=int, default=10)
parser2.add_argument('filter', type=str, default='id,name')

parser3 = reqparse.RequestParser()
parser3.add_argument('format', type=str, required=True, default='json')
parser3.add_argument('by', type=str, required=True, default='country,gender')

def get_plot(stat_by, resp_dict):
    attr_list = stat_by.split(',')
    num_of_plots = 1
    for attr in attr_list:
        if attr == 'birthday':
            num_of_plots += 2
        else:
            num_of_plots += 1
    plt.rcParams.update({'font.size': 22})
    axes_num = 0
    fig, axes = plt.subplots(nrows=num_of_plots, ncols=1, figsize=(30,20))
    
    total_dict = dict(list(resp_dict.items())[:2])
    list_total = ['total actors in Database', 'total actors updated in last 24 hours']
    axes[axes_num].bar(range(len(total_dict)), list(total_dict.values()), align='center')
    axes[axes_num].set_xticks(range(len(total_dict)), list_total)
    axes_num += 1
    
    # plot each of the attribute
    for attr in attr_list:

        if attr == 'country':
            country_dict = resp_dict['by-country']
            labels = []
            sizes = []
            for k, v in country_dict.items():
                labels.append(k)
                sizes.append(v)
            _, _, autotexts = axes[axes_num].pie(sizes, radius=1.2, labels=labels, autopct='%1.0f%%')
            #plt.axis('equal')
            axes[axes_num].text(-1,.6,'Actors (by Country)',
                        horizontalalignment='center', fontweight='bold', fontsize=20,
                        transform=axes[axes_num].transAxes)
            for autotext in autotexts:
                    autotext.set_color('white')
            
            axes_num += 1
        
        elif attr == 'gender':
            gender_dict = resp_dict['by-gender']
            labels_g = []
            sizes_g = []
            for k, v in gender_dict.items():
                labels_g.append(k)
                sizes_g.append(v)
            _, _, autotexts = axes[axes_num].pie(sizes_g, radius=1.2, labels=labels_g, autopct='%1.0f%%')
            #plt.axis('equal')
            axes[axes_num].text(-1,.6,'Actors (by Gender)',
                        horizontalalignment='center', fontweight='bold', fontsize=20,
                        transform=axes[axes_num].transAxes)
            for autotext in autotexts:
                    autotext.set_color('white')
            
            axes_num += 1
        
        elif attr == 'birthday':
            birthyear_dict = resp_dict['by-birthyear']
            axes[axes_num].bar(range(len(birthyear_dict)), list(birthyear_dict.values()), align='center')
            axes[axes_num].set_xticks(range(len(birthyear_dict)), list(birthyear_dict.keys()))
            axes[axes_num].text(0.8,.9,'Actors (by Birth Year)',
                        horizontalalignment='center', fontweight='bold', fontsize=20,
                        transform=axes[axes_num].transAxes)
            
            axes_num += 1
            
            birthmonth_dict = resp_dict['by-birthmonth']
            axes[axes_num].bar(range(len(birthmonth_dict)), list(birthmonth_dict.values()), align='center')
            axes[axes_num].set_xticks(range(len(birthmonth_dict)), list(birthmonth_dict.keys()))
            axes[axes_num].text(0.8,.9,'Actors by (Birth Month)',
                        horizontalalignment='center', fontweight='bold', fontsize=20,
                        transform=axes[axes_num].transAxes)
            
            axes_num += 1
        
        else:
            alive_dict = resp_dict['by-alive']
            labels_a = []
            sizes_a = []
            for k, v in alive_dict.items():
                labels_a.append(k)
                sizes_a.append(v)
            _, _, autotexts = axes[axes_num].pie(sizes_a, radius=1.2, labels=labels_a, autopct='%1.0f%%')
            for autotext in autotexts:
                    autotext.set_color('white')
            axes[axes_num].text(-1,.6,'Life Status of Actors',
                        horizontalalignment='center', fontweight='bold', fontsize=20,
                        transform=axes[axes_num].transAxes)
            
            axes_num += 1
    
    #studentid = 'z3228822'
    #plt.savefig("{}-Q6.png".format(studentid))
    
    return fig

@api.route('/actors')
class ActorsList(Resource):
    @api.response(400, 'Validation Error')
    @api.response(404, 'Not Found')
    @api.response(200, 'OK')
    @api.doc(parser = parser2)
    @api.doc(description="Get the list of available Actors")
    def get(self):
        
        args2 = parser2.parse_args(strict=True)
        order_by = args2.get('order')
        pages = args2.get('page')
        sizes = args2.get('size')
        filter_by = args2.get('filter')
        
        if (pages < 1):
            api.abort(400, "Page Number cannot be less than 1")
        if (sizes < 1):
            api.abort(400, "Size cannot be less than 1")
        
        order_keys = ['id', 'name', 'country', 
                      'birthday', 'deathday', 'lastupdate']
        
        # process order query
        order_by_str = ''
        for item in order_by.split(','):
            if not (item.startswith('+')  or
                item.startswith('-')):
                api.abort(400, "Order Parameter shoud begin with + or -")
                #return {"message": "Order Parameter shoud begin with + or -"}, 400
            sort_order = item[0]
            sort_item = item[1:]
            if '-' in sort_item:
                sort_item = sort_item.replace('-', '')
            if sort_item not in order_keys:
                api.abort(400, "{} Attribute cannot be used to order".format(sort_item))
                #return {"message": "{} Attribute cannot be used to order".format(sort_item)}, 400
            
            if (sort_order == '+'):
                order_by_str += str(sort_item) + ' ASC, '
            else:
                order_by_str += ' ' + str(sort_item) + ' DESC, '
            
        order_by_str = order_by_str.rstrip()
        order_by_str = order_by_str.rstrip(',')
        
        # process filter query
        filter_by_str = ''
        filter_keys = order_keys
        filter_keys.append('shows')
        
        for filt in filter_by.split(','):
            if '-' in filt:
                filt = filt.replace('-', '')
            if filt not in filter_keys:
                api.abort(400, "{} Attribute cannot be used to filter".format(filt))
                #return {"message": "{} Attribute cannot be used to filter".format(filt)}, 400
            filter_by_str += str(filt) +  ','
        
        filter_by_str = filter_by_str.rstrip(',')
        
        # Get offset
        offset_pages = (pages-1) * sizes
        
        # check max page
        query_tot_record = db.select([db.func.count(actors.columns.id)])
        total_record = engine.execute(query_tot_record).scalar()
        max_pages = -(-total_record//sizes)
        
        if (pages > max_pages):
            api.abort(404, "Page Number {} Exceeds Record.".format(pages))
            #return {"message": "Page Number {} Exceeds Record.".format(pages)}, 404
        
        query_order = select(text(filter_by_str)).select_from(actors) \
                            .order_by(text(order_by_str)).offset(offset_pages).limit(sizes)
        
        available_actors = engine.execute(query_order).fetchall()
        
        filter_tuples = tuple(filter_by_str.split(','))
        available_actors.insert(0, filter_tuples)
        
        result_dict = {}
        result_dict['page'] = pages
        result_dict['page-size'] = sizes
        result_dict['actors'] = []
        
        len_actors = len(available_actors)
        
        for i in range(1, len_actors):
            actor = available_actors[i]
            actor_dict = {}
            for j in range(len(actor)):
                if (available_actors[0][j] == 'lastupdate'):
                    a = actor[j].split('.')[0]
                    actor_dict[available_actors[0][j]] = a
                    #actor_dict[available_actors[0][j]] = actor[j].replace(microsecond=0)
                elif (available_actors[0][j] == 'shows'):
                    actor_dict[available_actors[0][j]] = actor[j].split(',')
                else:
                    actor_dict[available_actors[0][j]] = actor[j]
            result_dict['actors'].append(actor_dict)
        
        selfLink = request.host_url + "actors/" + "?" \
                    + "order=" + order_by + "&" \
                    + "page=" + str(pages) + "&" \
                    + "size=" + str(sizes) + "&" \
                    + "filter=" + filter_by
        
        result_dict["_links"] = {}
        result_dict["_links"]["self"] = {}
        result_dict["_links"]["next"] = {}
        result_dict["_links"]["self"]["href"] = selfLink
        result_dict["_links"]["next"]["href"] = ""
        
        if (pages < max_pages):
            nextLink = request.host_url + "actors/" + "?" \
                        + "order=" + order_by + "&" \
                        + "page=" + str(pages + 1) + "&" \
                        + "size=" + str(sizes) + "&" \
                        + "filter=" + filter_by
            result_dict["_links"]["next"]["href"] = nextLink
        
        return result_dict, 200
    
    @api.response(201, 'Created')
    @api.response(400, 'Validation Error')
    @api.response(404, 'Not Found')
    @api.doc(description="Add a new Actor")
    @api.expect(parser, validate=True)
    @api.marshal_with(actor_post_model)
    def post(self):
        args = parser.parse_args()
        name = args['var1']
        name = re.sub("[^a-zA-Z0-9]+", " ",name)
        
        try:
            resp = requests.get("https://api.tvmaze.com/search/people", 
                                params={'q': name})
        except:
            api.abort(504, "Unable to reach Tvmaze API Server at the moment")
            
        getactors = resp.json()
        
        getID = -1
        actorIndex = -1
        # if there are no actors
        if len(getactors) == 0:
            api.abort(404, "{} does not exist in TV Maze API".format(name))
            #return {"message": "{} does not exist in TV Maze API".format(name)}, 400
        # if there are many actors choose one which is not there in DB
        else:
            for i in range(len(getactors)):
                getName = getactors[i]['person']['name']
                if (getName.lower() == name.lower()):
                    getID = getactors[i]['person']['id']
                    actorIndex = i
                    break
        
        if (getID == -1):
            api.abort(400, "Actors returned by TV Maze API does not match query:{}".format(name))
       
        query_actorid = db.select([actors]). \
                        where(actors.columns.tvmazeApiId == getID)
        isActorthere = engine.execute(query_actorid).fetchall()
        
        if (len(isActorthere) > 0):
            api.abort(400, "Actor {} already exist".format(name))
        
        try:
            req_string = "https://api.tvmaze.com/people/" + str(getID) + "/castcredits"
        except:
            api.abort(504, "Unable to reach Tvmaze API Server at the moment")
        
        resp2 = requests.get(req_string, params={'embed': 'show'})
        show_names = resp2.json()
        show_list = []
        for i in range(len(show_names)):
            show = show_names[i]
            show_list.append(show['_embedded']['show']['name'])
        
        tvmazeapiid_db = getID
        name_db = getactors[actorIndex]['person']['name']
        
        country_str = getactors[actorIndex]['person']['country']
        if country_str is None:
            country_db = 'UNKNOWN'
        else:
            country_db = getactors[actorIndex]['person']['country']['name']
        
        birth_str = getactors[actorIndex]['person']['birthday']
        if birth_str is None:
            birth_db = None
        else:
            birth_db = datetime.datetime.strptime(birth_str, '%Y-%m-%d').date()
        
        death_str = getactors[actorIndex]['person']['deathday']
        if death_str is None:
            death_db = None
        else:
            death_db = datetime.datetime.strptime(death_str, '%Y-%m-%d').date()
        
        
        gender_str = getactors[actorIndex]['person']['gender']
        if gender_str is None:
            gender_db = 'UNKNOWN'
        else:
            gender_db = getactors[actorIndex]['person']['gender']
        

        shows_db = ','.join(s for s in show_list)
        
        timestamp = datetime.datetime.now().replace(microsecond=0)
        
        query = db.insert(actors).values(tvmazeApiId=tvmazeapiid_db, 
                                         name=name_db, country=country_db, 
                                         birthday=birth_db, deathday=death_db, 
                                         gender=gender_db, shows=shows_db,
                                         lastupdate=timestamp) 
        
        try:
            ResultProxy = engine.execute(query).inserted_primary_key
        except IntegrityError as e:
            api.abort(400, "An actor with name = {} is already in the database".format(name_db))
            #return {"message": "An actor with name = {} is already in the database".format(name_db)}, 400
            
        insertedId = ResultProxy[0]
        
        query_actorid = db.select([actors]). \
                        where(actors.columns.id == insertedId)
        getActor = engine.execute(query_actorid).fetchall()
        
        return getActor, 201
    

    @api.route('/actors/<int:id>')
    @api.param('id', 'The Actor identifier')
    class Actors(Resource):
        
        @api.response(404, 'Actor was not found')
        @api.response(200, 'OK')
        @api.doc(description="Get an Actor by its ID")
        @api.marshal_with(actor_get_model)
        def get(self, id):
            query_actorid = db.select([actors]). \
                            where(actors.columns.id == id)
            getActor = engine.execute(query_actorid).fetchall()
            if len(getActor) == 0:
                api.abort(404, "Actor {} doesn't exist".format(id))
            
            return getActor, 200
        
        
        @api.response(404, 'Actor was not found')
        @api.response(200, 'OK')
        @api.doc(description="Delete an Actor by its ID")
        def delete(self, id):
            query_actorid = db.select([actors]). \
                            where(actors.columns.id == id)
            getActor = engine.execute(query_actorid).fetchall()
            if len(getActor) == 0:
                api.abort(404, "Actor {} doesn't exist".format(id))
            
            query_delete = db.delete(actors). \
                            where(actors.columns.id == id)
            results = engine.execute(query_delete)
            
            resp_dict = {}
            del_msg = "The actor with id " + str(id) + " was removed from the database!"
            resp_dict["message"] = del_msg
            resp_dict["id"] = id
            
            return resp_dict, 200
        
        @api.response(404, 'Actor was not found')
        @api.response(401, 'Actor already exists')
        @api.response(400, 'Validation Error')
        @api.response(200, 'OK')
        @api.doc(description="Partial Update an Actor by its ID")
        @api.expect(actor_model, validate=True)
        @api.marshal_with(actor_post_model)
        def patch(self, id):
            query_actorid = db.select([actors]). \
                            where(actors.columns.id == id)
            getActor = engine.execute(query_actorid).fetchall()
            if len(getActor) == 0:
                api.abort(404, "Actor {} doesn't exist".format(id))
            
            # get the payload and convert it to a JSON
            actor = request.json
            
            # new update Logic
            params = {}
            for key, value in actor.items():
                
                if key not in actor_model.keys():
                    # unexpected column
                    api.abort(400, "Property {} is invalid".format(key))
                    #return {"message": "Property {} is invalid".format(key)}, 400
                
                if key == "shows":
                    params[key] = ','.join(s for s in value)
                elif key == 'name':
                    value = re.sub("[^a-zA-Z0-9\s]+", "",value)
                    query_name = db.select([db.func.count(actors.columns.name)]) \
                                            .where(actors.columns.name == value)
                    count_name = engine.execute(query_name).scalar()
                    if (count_name > 0):
                        api.abort(400, "Actor {} already exist".format(value))
                    params[key] = value
                elif key == 'gender':
                    value = re.sub("[^a-zA-Z0-9\s]+", "",value)
                    gender_list = ['male', 'female']
                    if value.lower() not in gender_list:
                        value = 'UNKNOWN'
                    params[key] = value
                elif key == 'country':
                    value = re.sub("[^a-zA-Z0-9\s]+", "",value)
                    params[key] = value
            
            params['lastupdate'] = datetime.datetime.now().replace(microsecond=0)
            query_update = actors.update() \
                                .values(params) \
                                .where(actors.columns.id == id)
                
            try:
                results = engine.execute(query_update)
            except:
                api.abort(400, "Update Failed. Enter valid date format : YYYY-MM-DD")
                
            query_actorid = db.select([actors]). \
                            where(actors.columns.id == id)
            getActor = engine.execute(query_actorid).fetchall()
                    
            return getActor, 200
        
        
        
        @api.route('/actors/statistics')
        class ActorsStats(Resource):
            @api.response(400, 'Validation Error')
            @api.response(404, 'Not Found')
            @api.response(200, 'OK')
            @api.doc(parser = parser3)
            @api.doc(description="Get the Statistics of existing Actors")
            def get(self):
                args3 = parser3.parse_args()
                format_type = args3.get('format')
                stat_by = args3.get('by')
                
                # process by parameters
                format_list = ['json', 'image']
                by_list = ['country', 'birthday', 'gender', 'life_status']
                
                if format_type not in format_list:
                    api.abort(400, "Format {} is invalid".format(format_type))
                
                for stat in stat_by.split(','):
                    if stat not in by_list:
                        api.abort(400, "Attribute {} is invalid".format(stat_by))
                
                resp_dict = {}
                # total records
                query_tot_record = db.select([db.func.count(actors.columns.id)])
                total_record = engine.execute(query_tot_record).scalar()
                resp_dict['total'] = total_record
                
                if (total_record < 1):
                    api.abort(404, "No Records")
                
                # total record updated in last 24 hours
                now = datetime.datetime.now().replace(microsecond=0)
                time_day = datetime.timedelta(hours=24)
                query_tot_update = db.select([db.func.count(actors.columns.lastupdate)]) \
                                     .where(db.and_((now - time_day) <= actors.columns.lastupdate, \
                                            actors.columns.lastupdate <= now))
                
                total_update = engine.execute(query_tot_update).scalar()
                resp_dict['total-updated'] = total_update
                
                for stat in stat_by.split(','):
                    
                    if stat == 'country':
                        query_country = select([text('country'), func.count(text('country'))]) \
                                            .select_from(actors) \
                                            .group_by(text('country'))
                                            
                        country_stats = engine.execute(query_country).fetchall()
                        
                        country_dict = dict(country_stats)
                        for key, value in country_dict.items():
                            #country_dict[key] = str(round(100 * (value / total_record), 2)) + "%"
                            country_dict[key] = round(100 * (value / total_record), 2)
                        resp_dict['by-country'] = country_dict

                    elif stat == 'birthday':
                        query_birthyear = select([db.func.strftime('%Y', text('birthday')) ,func.count(text('id'))]) \
                                            .select_from(actors) \
                                            .group_by(db.func.strftime('%Y', text('birthday')))
                        
                        birthyear_stats = engine.execute(query_birthyear).fetchall()
                        birthyear_dict = dict(birthyear_stats)
                        for key, value in birthyear_dict.items():
                            #birthyear_dict[key] = str(round(100 * (value / total_record), 1)) + "%"
                            birthyear_dict[key] = round(100 * (value / total_record), 1)
                            #birthyear_dict[key] = value
                        
                        if None in birthyear_dict:
                            birthyear_dict['UNKNOWN'] = birthyear_dict.pop(None)
                        
                        resp_dict['by-birthyear'] = birthyear_dict
                        
                        #group-by records - birth Month
                        months_dict = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr',
                                       '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug',
                                       '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec',
                                       None: 'UNKNOWN'}
                        
                        query_birthmonth = select([db.func.strftime('%m', text('birthday')) ,func.count(text('id'))]) \
                                            .select_from(actors) \
                                            .group_by(db.func.strftime('%m', text('birthday')))
                        
                        
                        birthmonth_stats = engine.execute(query_birthmonth).fetchall()
                        birthmonth_dict = {}
                        for key, value in birthmonth_stats:
                            #birthmonth_dict[months_dict[key]] = str(round(100 * (value / total_record), 1)) + "%"
                            birthmonth_dict[months_dict[key]] = round(100 * (value / total_record), 1)
                            #birthmonth_dict[months_dict[key]] = value
                        
                        if 'None' in birthmonth_dict:
                            birthmonth_dict['Unknown'] = birthmonth_dict.pop('None')
                        
                        resp_dict['by-birthmonth'] = birthmonth_dict
                    
                    elif stat == 'gender':
                        query_gender = select([text('gender'), func.count(text('gender'))]) \
                                            .select_from(actors) \
                                            .group_by(text('gender'))
                         
                        gender_stats = engine.execute(query_gender).fetchall()
                        gender_dict = dict(gender_stats)
                        for key, value in gender_dict.items():
                            #gender_dict[key] = str(round(100 * (value / total_record), 2)) + "%"
                            gender_dict[key] = round(100 * (value / total_record), 2)
                            #gender_dict[key] = value
                        
                        if 'None' in gender_dict:
                            gender_dict['UNKNOWN'] = gender_dict.pop('None')
                        
                        resp_dict['by-gender'] = gender_dict
                    
                    elif stat == 'life_status':
                        query_dead = select([func.count(text('deathday'))]) \
                                            .select_from(actors) \
                                            .where(text('deathday') != None)
                         
                        dead_stats = engine.execute(query_dead).fetchall()
                        dead = dead_stats[0][0]
                        alive = total_record - dead
                        alive_list = [('alive', alive), ('dead', dead)]
                        alive_dict = dict(alive_list)
                        for key, value in alive_dict.items():
                            #alive_dict[key] = str(round(100 * (value / total_record), 1)) + "%"
                            alive_dict[key] = round(100 * (value / total_record), 1)
                        
                        resp_dict['by-alive'] = alive_dict
                
                # Based on format type, send json or image
                if format_type == 'json':
                    return resp_dict, 200
                elif format_type == 'image':
                    fig = get_plot(stat_by, resp_dict)
                    output = io.BytesIO()
                    FigureCanvas(fig).print_png(output)
                    return Response(output.getvalue(), mimetype='image/png')

if __name__ == '__main__':
    app.run()