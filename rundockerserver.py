from hasjob import app, init_for

init_for('docker')

app.run('0.0.0.0')
