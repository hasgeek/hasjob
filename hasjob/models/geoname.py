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


    # Right now using a simple parser
    # What has to be done for Anywhere
    def text2location(self,text=''):
        SPLIT_RE = re.compile(" ?, ?| or | ?/ ?")
        loc_list = re.split(SPLIT_RE,text,flags=re.IGNORECASE)
        loc_list.append(text)
        loc_list = filter(None,loc_list)
        return loc_list
        
    def get_geoid(self,text=''):
        loc_list = text2location(text)
        geoid = [ loc_request(location) for location in loc_list]
        return geoid


def loc_request(name='',formatter=True,maxRows=10,lang='en',username='demo',style='full'):
    base = 'http://api.geonames.org/searchJSON'
    uri = base + '?formatter='+ str(formatter).lower()
    uri += '&q=' + name 
    uri += '&maxRows=' + str(maxRows)
    uri += '&lang' + lang
    uri += '&username' + username
    uri += '&demo' + demo
    headers = {'Accept' : 'application/json'}
    response = requests.get(uri,headers)
    if response.status_code == 200:
        return response_format(response.json())
    else:
        return list()


def response_format(response):
    # On the fly insert into GeoName table ?
    # currently returns only geoid
    geonames = response["geonames"]
    return [ geonames[i]["geonameId"] for i in geonames ]

class GeoJobView(db.Model):
    __tablename__ = 'geoview'
    id = db.Column(db.Integer,primary_key=True,nullable=False)
    jobpost_id = db.Column(None, db.ForeignKey('jobpost.id'))
    jobpost = db.relationship(JobPost)
    geo_id = db.Column(None, db.ForeignKey('geoname.geonameid'))
    geo = db.relationship(GeoName)