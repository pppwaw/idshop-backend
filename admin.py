from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from model import db, Goods, Order
import json

class OrderView(ModelView):
    column_labels = {
        "id": "序号",
        "order_id": "订单号",
        "user_id": "用户id",
        "type": "类型",
        "data": "数据",
        "status": "状态"
    }

    def __init__(self, session, **kwargs):
        super(OrderView, self).__init__(Order, session, **kwargs)


class GoodsView(ModelView):
    column_labels = {
        "id": "序号",
        "name": "名字",
        "price": "价格(分)",
        "data": "数据",
    }

    def __init__(self, session, **kwargs):
        super(GoodsView, self).__init__(Goods, session, **kwargs)


admin = Admin()
admin.add_view(OrderView(db.session, category='Models'))
admin.add_view(GoodsView(db.session, category='Models'))
