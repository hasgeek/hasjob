import json
from hasjob import app
from flask import render_template, request, Response, g
from hasjob import docspad

@app.route("/upload_using_docspad", methods=["POST"])
def upload():
    if g.user:
        uploaded_file = request.files['file']
        try:
            docId = docspad.upload(uploaded_file)
            sessionId = docspad.get_session(docId)
            return Response(status=200, mimetype='application/json',response=json.dumps({'sessionId':sessionId}))
        except Exception as e:
            print e.message
            return Response(status=400, mimetype='application/json',response=json.dumps({'error':'Unable to upload file.'}))
    else:
        return Response(status=401)
@app.route("/view_doc/<sessionId>", methods=["GET"])
def view(sessionId):
    return render_template("view_doc.html", sessionId = sessionId)
