import json
from hasjob import app
from flask import render_template, request, Response, g, abort, url_for
from hasjob import docspad

@app.route("/view_doc/<sessionId>", methods=["GET"])
def view_doc(sessionId):
    return render_template("view_doc.html", sessionId = sessionId)
