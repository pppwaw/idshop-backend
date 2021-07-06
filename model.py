from flask_sqlalchemy import SQLAlchemy
import uuid

db = SQLAlchemy()


class Goods(db.Model):
    id = db.Column("id", db.INT, autoincrement=True, primary_key=True)
    name = db.Column("name", db.TEXT)
    price = db.Column("price", db.INT)  # 单位：分
    data = db.Column("data", db.TEXT)

    def __init__(self, name, price, data):
        self.name = name
        self.price = price
        self.data = data


class Order(db.Model):
    id = db.Column("id", db.INT, autoincrement=True, primary_key=True)
    order_id = db.Column("order_id", db.TEXT, default=uuid.uuid4)
    user_id = db.Column("user_id", db.INT)
    type = db.Column("type", db.TEXT)
    data = db.Column("data", db.TEXT)
    status = db.Column("status", db.TEXT, default="pending")  # pending, paid, complete
    images = db.Column("images", db.TEXT, default="")  # 用,分割，图片文件URL

    def __init__(self, type, data, userid):
        self.type = type
        self.user_id = userid
        self.data = data
