from model import Order, Goods, db
from flask import jsonify, Blueprint, request, json
from websocket import socketio
from pay import pay_methods

api = Blueprint("api", __name__)


@api.route("/list/user/<int:userid>")
def list_by_user(userid):
    res = Order.query.filter_by(user_id=userid).all()
    rtn = [{"order_id": i.order_id, "type": i.type, "status": i.status} for i in res]
    return jsonify(rtn)


@api.route("/goods")
def get_goods_list():
    res = Goods.query.all()
    rtn = {}
    for i in res:
        rtn[i.name] = json.loads(i.data)
        rtn[i.name]["price"] = i.price / 100
    return jsonify(rtn)


@api.route("/complete", methods=["POST"])
def complete_order():
    a = request.json  # {order_id:xxxxx}


@api.route("/create", methods=["POST"])
def create_order():
    goods = [i.name for i in Goods.query.all()]
    a = request.form
    if a["type"] not in goods:
        return "not support type", 404
    order = Order(a["type"], a["data"], a["userid"])
    db.session.add(order)
    db.session.commit()

    return order.order_id


@api.route("/pay/<string:method>/<string:order_id>")
def pay(method, order_id):
    res = Order.query.filter_by(order_id=order_id).all()
    if not res:
        return "not found", 404
    elif res[-1].status != "pending":
        return "already paid", 400
    else:
        if method not in pay_methods:
            return "not found pay method", 404
        else:
            return pay_methods[method](res[-1])


@api.route("/check/<string:order_id>")
def check(order_id):
    res = Order.query.filter_by(order_id=order_id).all()
    if not res:
        return "", 404
    else:
        return res[-1].status


@api.route("/callback", methods=["POST"])
def callback():
    body = request.json
    if body["status"] == "PAID":
        Order.query.filter_by(order_id=body["merchant_order_id"]).update({"status": "paid"})
        order = Order.query.filter_by(order_id=body["merchant_order_id"]).all()[0]
        socketio.send({"order_id": order.order_id, "status": "paid", "userid": order.user_id})
        db.session.commit()
    return jsonify({"status": 200})
