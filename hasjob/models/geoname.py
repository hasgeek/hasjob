from hasjob.models import db, BaseNameMixin
import re


class GeoName(db.Model):
    __tablename__ = 'geoname'
    idref = 'geo'
    
    geonameid = db.Column(db.Integer,primary_key=True,nullable=True) 
    name = db.Column(db.String(200),nullable=True) 
    asciiname = db.Column(db.String(200),nullable=True) 
    alternatenames = db.Column(db.String(5000),nullable=True) 
    latitude = db.Column(db.String(100),nullable=True) 
    longitude = db.Column(db.String(100),nullable=True) 
    feature_class  =db.Column(db.String(1),nullable=True) 
    feature_code  =db.Column(db.String(10),nullable=True) 
    country_code  =db.Column(db.String(2),nullable=True) 
    cc2  =db.Column(db.String(60),nullable=True) 
    admin1_code  =db.Column(db.String(20),nullable=True) 
    admin2_code  =db.Column(db.String(80),nullable=True) 
    admin3_code  =db.Column(db.String(20),nullable=True) 
    admin4_code  =db.Column(db.String(20),nullable=True) 
    population  =db.Column(db.Integer,nullable=True) 
    elevation  =db.Column(db.Integer,nullable=True) 
    dem  =db.Column(db.Integer,nullable=True) 
    timezone  =db.Column(db.String(40),nullable=True) 
    modification_date  =db.Column(db.Date(),nullable=True) 


def __call__(self):
    return self.title


def text2location(text):
    SPLIT_RE = re.compile(" ?, ?| or | ?/ ?")
    loc_list = re.split(SPLIT_RE,text)
    split_list = list()
   
    loc_list.append(text)
        
def get_geoid(model=GeoName,text=''):
    loc_list = text2location(GeoNametext)
    
