from StringIO import StringIO
from contextlib import closing
import cPickle
import gzip
from SimpleCV import Image
from scipy import misc
import numpy as np
__author__ = 'Roland'
from flask import Flask, render_template, jsonify, make_response
import sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash

# configuration
DATABASE = 'D:\\AI\\Bonuri\\annotator\\tmp\\annotations.db'
DEBUG = True
SECRET_KEY = 'development key'
USERNAME = 'admin'
PASSWORD = 'default'
app = Flask(__name__)
app.config.from_object(__name__)

f = open("log_model.pkl","rb")
logistic_model = cPickle.load(f)
f.close()
f = open("labels.pkl","rb")
labels = cPickle.load(f)
f.close()
# labels = [u'!', u'#', u'%', u'(', u')', u'*', u',', u'-', u'.', u'/', u'0',
#        u'1', u'2', u'3', u'4', u'5', u'6', u'7', u'8', u'9', u':', u'=',
#        u'A', u'B', u'C', u'D', u'E', u'F', u'G', u'H', u'I', u'J', u'K',
#        u'L', u'M', u'N', u'O', u'P', u'Q', u'R', u'S', u'T', u'U', u'V',
#        u'W', u'X', u'Z', u'a', u'b', u'c', u'd', u'e', u'f', u'g', u'h',
#        u'i', u'l', u'm', u'n', u'o', u'p', u'r', u's', u'star', u't', u'u',
#        u'v', u'w', u'x', u'y', u'z']
# labels = ['!', '#', '%', '(', ')', ',', '-', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', '=', 'A', 'B', 'C',
#           'colon', 'D', 'dot', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'slash',
#           'star', 'T', 'U', 'V', 'W', 'x', 'y', 'Z']

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
def hello(id=0):
    return render_template('images.html', i=id)

@app.route('/add', methods=['POST'])
def add_entry():
    g.db.execute('insert into letters (line, x, y, width,'
                 ' height, charac) values (?, ?, ?,?,?,?)',
                 [request.form['line'], request.form['x'],
                  request.form['y'], request.form['width'],
                  request.form['height'], request.form['charac']])
    g.db.commit()
    return jsonify(success=True)

@app.route('/query_blob/<int:id>', methods=['POST'])
def query_blob(id):
    cur = g.db.execute('select bon, x, y from lines where (lines.id - 1)= ?', [id])
    line = cur.fetchone()
    print(line)
    img = Image("D:\\AI\\Bonuri\\imgs\\cleaned\\%d.jpg" % int(line[0]))
    lett = img.crop(int(request.form['x']) + line[1], int(request.form['y']) + line[2],
                    int(request.form['width']), int(request.form['height']))#.invert()
    if lett:
        if int(request.form['height']) > int(request.form['width']):
            lett = lett.resize(h=30)
        else:
            lett = lett.resize(w=30)
        lett = lett.embiggen((30,30))
        charac = labels.inverse_transform(logistic_model.predict(lett.rotate90().flipVertical().getGrayNumpy().reshape(-1)))[0]
    # return jsonify(blobs=sorted(entries,key= lambda x:x["x"]))
    print(charac)
    probs = logistic_model.predict_proba(lett.rotate90().flipVertical().getGrayNumpy().reshape(-1))
    print(np.argmax(probs))
    print(np.max(probs))
    print(np.mean(probs))
    return jsonify(prediction=charac)

@app.route('/line_blobs/<int:id>', methods=['GET'])
def line_blob(id):
    cur = g.db.execute('select blobs.id, lines.bon, line, blobs.x, blobs.y, blobs.width, blobs.height,'
                       'lines.x, lines.y, lines.width, lines.height '
                       'from blobs JOIN lines on (lines.id - 1)= blobs.line where line=?', [id])
    blobs = cur.fetchall()
    entries = []
    img = Image("D:\\AI\\Bonuri\\imgs\\cleaned\\%d.jpg" % int(blobs[0][1]))
    i = 0
    print(blobs[0][1])
    for entry in blobs:
        entries.append(dict(x=entry[3], y=entry[4], width=entry[5], height=entry[6]))
        lett = img.crop(entry[3]+entry[7], entry[4]+entry[8], entry[5], entry[6])#.invert()
        if lett:
            if entry[6] > entry[5]:
                lett = lett.resize(h=30)
            else:
                lett = lett.resize(w=30)
            lett = lett.embiggen((30,30))
            i += 1
            print(logistic_model.predict(lett.rotate90().flipVertical().getGrayNumpy().reshape(-1)))
            entries[-1]["charac"] = labels.inverse_transform(logistic_model.predict(lett.rotate90().flipVertical()
                                          .getGrayNumpy().reshape(-1)))[0]
            try:
                misc.imsave("tmp\\pic%d %s.jpg" % (i, entries[-1]["charac"]),lett.rotate90().flipVertical().getGrayNumpy())
            except Exception:
                pass
    print(entries)
    return jsonify(blobs=entries)

@app.route('/blob/<int:id>', methods=['GET'])
def blob(id):
    cur = g.db.execute('select letters.id, lines.bon, line, letters.x, letters.y,'
                       ' letters.width, letters.height,'
                       'lines.x, lines.y, lines.width, lines.height '
                       'from letters JOIN lines on (lines.id - 1)= letters.line where letters.id=?', [id])
    line = cur.fetchone()
    print(line)
    scale = 30.0/line[10]
    print(scale)

    scale = 1/scale
    print(scale)
    img = Image("D:\\AI\\Bonuri\\imgs\\cleaned\\%d.jpg" % int(line[1]))
    # @todo frickin scaling because I resized lines
    lett = img.crop(round(line[3]*scale + line[7]), round(line[4]*scale + line[8]), round(line[5]*scale),
                    round(line[6]*scale))
    io = StringIO()
    lett.save(io)
    data = io.getvalue()
    resp = make_response(data)
    resp.content_type = "image/jpeg"
    return resp

@app.route('/admin')
def admin():
    cur = g.db.execute('select letters.id, letters.charac from letters limit 0, 100')
    blobs = cur.fetchall()
    return render_template('admin.html', letters=blobs)

if __name__ == "__main__":
    app.run(host='0.0.0.0')