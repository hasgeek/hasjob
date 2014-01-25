import json
import requests
from hasjob import app

'''
Returns the docId when the upload is successful.
Input type is fileobject
'''
def upload(fileobject):
    resp = requests.post("http://apis.docspad.com/v1/upload.php", files={'doc':fileobject},
                         data={'key': app.config['DOCSPAD_CONSUMER_KEY']})
    returned_vals = json.loads(resp.text)
    if 'error' in returned_vals:
        raise Exception(returned_vals['error']['msg'])
    else:
        return returned_vals['docId']

'''
Returns the status (a dictionary of 'conversion_status' and 'file_status' received from Docspad for the given docId
'''
def get_status(docId):
    resp = requests.post("http://apis.docspad.com/v1/status.php", data={'key': app.config['DOCSPAD_CONSUMER_KEY'],
                                                                        'docId': docId})
    returned_vals = json.loads(resp.text)
    if 'error' in returned_vals:
        raise Exception(returned_vals['error']['msg'])
    else:
        return returned_vals

'''
Returns the sessionId received from Docspad for the given docId
'''
def get_session(docId):
    resp = requests.post("http://apis.docspad.com/v1/session.php", data={'key': app.config['DOCSPAD_CONSUMER_KEY'],
                                                                             'docId':docId})
    returned_vals = json.loads(resp.text)
    if 'error' in returned_vals:
        raise Exception(returned_vals['error']['msg'])
    else:
        return returned_vals['sessionId']