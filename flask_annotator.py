__author__ = 'Roland'
from StringIO import StringIO
from contextlib import closing
import cPickle
from SimpleCV import Image
from flask import Flask, render_template, jsonify, make_response
import sqlite3
from flask import request, g

# configuration
app = Flask(__name__)
app.config.from_object(__name__)
app.config.from_pyfile('config.cfg')

if 'SK_MODEL' in app.config:
    f = open(app.config['SK_MODEL'], "rb")
    sk_model = cPickle.load(f)
    f.close()
if 'SK_LABEL' in app.config:
    f = open(app.config['SK_LABEL'], "rb")
    labels = cPickle.load(f)
    f.close()


def connect_db():
    return sqlite3.connect(app.config['DATABASE'])


def init_db():
    with closing(connect_db()) as db:
        with app.open_resource('schema.sql', mode='r') as f:
            db.cursor().executescript(f.read())
        db.commit()


@app.before_request
def before_request():
    g.db = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    if db is not None:
        db.close()


@app.route('/')
@app.route("/<int:id>")
def index(id=0):
    return render_template('images.html', i=id)


@app.route('/add', methods=['POST'])
def add_blob():
    g.db.execute('INSERT INTO annotations (image, x, y, width, height, label) VALUES (?, ?, ?,?,?,?)',
                 [request.form['image'], request.form['x'], request.form['y'], request.form['width'],
                  request.form['height'], request.form['label']])
    g.db.commit()
    return jsonify(success=True)


@app.route('/query_blob/<int:id>', methods=['POST'])
def query_blob(id):
    blob = Image("static\\img\\%d.jpg" % id).crop(int(request.form['x']), int(request.form['y']),
                                                  int(request.form['width']), int(request.form['height']))
    if blob and 'SK_MODEL' in app.config:
        if blob.height > blob.width:
            blob = blob.resize(h=app.config['PATCH_SIZE'])
        else:
            blob = blob.resize(w=app.config['PATCH_SIZE'])
        blob = blob.embiggen((app.config['PATCH_SIZE'], app.config['PATCH_SIZE']))
        np_img = blob.getGrayNumpy().transpose().reshape(-1)
        pred = labels.inverse_transform(sk_model.predict(np_img))[0]
        return jsonify(prediction=pred)
    else:
        return jsonify(prediction='')


@app.route('/line_blobs/<int:id>', methods=['GET'])
def line_blobs(id):
    cur = g.db.execute('SELECT id, x, y, width, height FROM blobs WHERE image=?', [id])
    blobs = cur.fetchall()
    entries = []
    img = Image("static\\img\\%d.jpg" % id)
    for i, entry in enumerate(blobs):
        blob = img.crop(entry[1], entry[2], entry[3], entry[4])
        if blob and 'SK_MODEL' in app.config:
            if blob.height > blob.width:
                blob = blob.resize(h=app.config['PATCH_SIZE'])
            else:
                blob = blob.resize(w=app.config['PATCH_SIZE'])
            blob = blob.embiggen((app.config['PATCH_SIZE'], app.config['PATCH_SIZE']))
            np_img = blob.getGrayNumpy().transpose().reshape(-1)
            pred = labels.inverse_transform(sk_model.predict(np_img))[0]
            if app.config['DEBUG']:
                blob.save("tmp\\pic%d %s.jpg" % (i, pred))
            entries.append(dict(x=entry[1], y=entry[2], width=entry[3], height=entry[4], pred=pred))
        else:
            entries.append(dict(x=entry[1], y=entry[2], width=entry[3], height=entry[4]))
    return jsonify(blobs=entries)


@app.route('/blob/<int:id>', methods=['GET'])
def blob(id):
    cur = g.db.execute('SELECT id, image, x, y, width, height FROM annotations WHERE annotations.id=?', [id])
    line = cur.fetchone()

    img = Image("static\\img\\%d.jpg" % int(line[1]))
    blob = img.crop(line[2], line[3], line[4], line[5])
    io = StringIO()
    blob.save(io)
    data = io.getvalue()
    resp = make_response(data)
    resp.content_type = "image/jpeg"
    return resp

@app.route('/blob/<int:id>', methods=['POST'])
def change_blob(id):
    g.db.execute('UPDATE annotations SET label = ? WHERE id = ?', [request.form['label'], id])
    g.db.commit()
    return jsonify(success=True)

@app.route('/blob/<int:id>', methods=['DELETE'])
def delete_blob(id):
    g.db.execute('DELETE FROM annotations WHERE id = ?', [id])
    g.db.commit()
    return jsonify(success=True)

@app.route('/admin')
@app.route('/admin/<int:page>')
def admin(page=0):
    cur = g.db.execute('SELECT annotations.id, annotations.label FROM annotations LIMIT ?, 100', [page*100])
    blobs = cur.fetchall()
    return render_template('admin.html', annotations=blobs, page=page)

if __name__ == "__main__":
    app.run(host='0.0.0.0')