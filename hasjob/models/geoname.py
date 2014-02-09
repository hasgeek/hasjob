from hasjob.models import db,JobPost
import re,requests


class GeoName(db.Model):
    __tablename__ = 'geoname'
    idref = 'geo'
    
    geonameid = db.Column(db.Integer,primary_key=True,nullable=True) 
    name = db.Column(db.String(200),nullable=True) 
    asciiname = db.Column(db.String(200),nullable=True) 
    alternatenames = db.Column(db.String(5000),nullable=True) 
    latitude = db.Column(db.String(100),nullable=True) 
    longitude = db.Column(db.String(100),nullable=True) 
    feature_class = db.Column(db.String(1),nullable=True) 
    feature_code = db.Column(db.String(10),nullable=True) 
    country_code = db.Column(db.String(2),nullable=True) 
    cc2 = db.Column(db.String(60),nullable=True) 
    admin1_code = db.Column(db.String(20),nullable=True) 
    admin2_code = db.Column(db.String(80),nullable=True) 
    admin3_code = db.Column(db.String(20),nullable=True) 
    admin4_code = db.Column(db.String(20),nullable=True) 
    population = db.Column(db.Integer,nullable=True) 
    elevation = db.Column(db.Integer,nullable=True) 
    dem = db.Column(db.Integer,nullable=True) 
    timezone = db.Column(db.String(40),nullable=True) 
    modification_date = db.Column(db.Date(),nullable=True) 

    
    def __repr__(self):
        return "<Geoname %s %s >" % (self.geonameid, self.title)


class GeoJobView(db.Model):
    __tablename__ = 'geoview'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'))
    jobpost = db.relationship(JobPost)
    geo_id = db.Column(None, db.ForeignKey('geoname.geonameid'))
    geo = db.relationship(GeoName)


def add_geoview(jobpost_id,geoid):
    count = GeoJobView.query.count() + 1
    for i in geoid:
        temp = GeoJobView(id = count)
        count += 1
        temp.jobpost_id = jobpost_id
        temp.geo_id = i
        db.session.add(temp)


def add_geo(geonames):
    for i in geonames:
        id = i["geonameId"]
        count = GeoName.query.filter_by(geonameid=id).count
        if count == 0:
            temp = GeoName(geonameid=id)
            temp.name = i["name"]
            alt_list = [ x["lang"] for x in i["alternatenames"] ]
            temp.alternatenames = ";".join(alt_list)
            temp.latitude = i["lat"]
            temp.longitude = i["lng"]
            temp.country_code = i["countryCode"]
            temp.timezone = i["timezone"]["timeZoneId"]
            db.session.add(temp)
        else:
            continue


def response_format(geonames):
    # currently returns only 1 geoid per location
    result = list()
    for i in geonames:
        result.append(geonames[i]["geonameId"])

    return result


def loc_request(name='',formatted=True,maxRows=1,lang='en',username='demo',style='full'):
    base = 'http://api.geonames.org/searchJSON'
    uri = base + '?formatted='+ str(formatted).lower()
    uri += '&q=' + name 
    uri += '&maxRows=' + str(maxRows)
    uri += '&lang=' + lang
    uri += '&username=' + username
    uri += '&style=' + style
    headers = {'Accept' : 'application/json'}
    print uri
    response = requests.get(uri)
    if response.status_code == 200:
        try:
            add_geo(response.json()["geonames"])
            return response_format(response.json()["geonames"])
        except KeyError, e:
            print response.json()["status"]
            return response_format(list())
    else:
        return list()


# Right now using a simple parser
# What has to be done for Anywhere
def text2location(text=''):
    SPLIT_RE = re.compile(" ?, ?| or | ?/ ?")
    loc_list = re.split(SPLIT_RE,text)
    loc_list.append(text)
    loc_list = filter(None,loc_list)
    return loc_list


def get_geoid(text=''):
    loc_list = text2location(text)
    geoid = list()
    for i in loc_list:
        geoid += loc_request(i)
    return geoid


def insert_geotag(jobpost_id,location):
    geoid_list = get_geoid(location)
    add_geoview(jobpost_id,geoid_list)

