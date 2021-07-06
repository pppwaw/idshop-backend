from model import Order, Goods
from requests import post, get

headers = {'content-type': 'application/json', "token": "74161750-d820-11eb-83ba-f321ddf1825b"}


def muggle_pay(order: Order):
    good: Goods = Goods.query.filter_by(name=order.type).all()[0]
    data = {
        "price_amount": good.price / 100,
        "price_currency": "CNY",
        "title": good.name,
        "description": order.order_id,
        "merchant_order_id": order.order_id,
        "callback_url": "http://pay.pppwaw.top:5000/callback"
    }
    r = post("https://api.mugglepay.com/v1/orders", json=data, headers=headers)
    return "请点击 " + r.json()["payment_url"] + " 完成支付"


pay_methods = {"muggle": muggle_pay}
