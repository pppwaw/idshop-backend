from flask import Flask, json
from model import db, Order
from websocket import socketio
from api import api
from admin import admin
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://idshop:idshop@8.210.9.78/idshop"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config["SECRET_KEY"] = "idshop"
app.register_blueprint(api)
db.init_app(app)
socketio.init_app(app)
admin.init_app(app,endpoint="/admin")







if __name__ == '__main__':
    socketio.run(app, host="::", debug=True)
