import json
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.ext import Updater, Dispatcher, CommandHandler, CallbackContext, ConversationHandler, MessageHandler, \
    Filters, CallbackQueryHandler
from telegram.bot import Update
import math
import logging
import requests
import socketio

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
goods_list = {
    # "DL": {
    #     "name": "驾照",
    #     "need": {
    #         "FIRSTNAME": "First Name",
    #         "LASTNAME": "Last Name",
    #         "ADDRESS1": "Address 1",
    #         "ADDRESS2": "Address 2",
    #         "CITY": "城市",
    #         "STATE": "州",
    #         "ZIPCODE": "Zip Code",
    #         "DOB": "生日（格式MM/DD/YYYY）",
    #         "CLASS": "Class",
    #         "SEX": "性别",
    #         "HAIR": "头发颜色",
    #         "HGT": "身高（单位英尺）",
    #         "WGT": "体重（单位磅）",
    #         "ISSUE": "签发时间（格式MM/DD/YYYY）",
    #         "DD": "DD（文档区分号）"
    #     },
    #     "must": ["FIRSTNAME", "LASTNAME", "ADDRESS1", "CITY", "STATE", "ZIPCODE", "DOB", "SEX"],
    #     "choice": {
    #         "SEX": ["Male", "Female"]
    #     }
    # }
}
start_text = """
你好，{name}！这里是我的自动ID商店
目前本店还有{wait}单待处理
使用 /make 来下订单
使用 /admins 来查看管理员列表
使用 /list 来查看所有订单"""
make_text = """
请在下方选择你要制作的证件
输入 /cancel 取消"""
list_text = "订单号：{} 类型：{} 状态：{} "
sio = socketio.Client()
paid_text = """您的订单 {} 付款成功！\n出图后将直接发送给你，你也可以找管理员去询问情况"""


def get_list():
    r = requests.get("http://127.0.0.1:5000/goods").json()
    return r


def check(txid):
    r = requests.get("http://127.0.0.1:5000/check/" + txid)
    if r.status_code == 200 and r.text != "pending":
        return True
    else:
        return False


def muggle_pay(order_id):
    r = requests.get("http://127.0.0.1:5000/pay/muggle/" + order_id)
    return r.text


def create_pay(pay_type, order_id):
    return paymethods[pay_type](order_id)


def create(order: dict, userid):
    order_type = order["TYPE"]
    order_pre = order.copy()
    del order_pre["TYPE"]
    data = {"type": order_type, "data": json.dumps(order_pre), "userid": userid}
    return requests.post("http://127.0.0.1:5000/create", data=data).text


def d_to_2d(lis):
    l = math.ceil(math.sqrt(len(lis)))
    rtn = []
    x = 0
    for i in range(l - 1):
        rtn.append([])
        for j in range(l):
            rtn[i].append(lis[x])
            x += 1
    rtn.append([])
    for i in range(x, len(lis)):
        rtn[-1].append(lis[x])
        x += 1

    return rtn


def start(bot: Update, message: CallbackContext):
    bot.message.reply_text(
        start_text.format(
            name=bot.effective_user.full_name,
            wait=0
        )
    )


def admins(bot: Update, message: CallbackContext):
    bot.message.reply_text(
        "目前管理员列表: @idman666 @butdown"
    )


def lists(bot: Update, message: CallbackContext):
    l = requests.get("http://127.0.0.1:5000/list/user/" + str(bot.message.from_user.id)).json()
    rtn = ""
    for i in l:
        rtn += list_text.format(i["order_id"], i["type"], i["status"])
        rtn += "\n"
    bot.message.reply_text(rtn)


def make(bot: Update, message: CallbackContext):
    goods = list(goods_list.keys())
    bot.message.reply_text(make_text, reply_markup=ReplyKeyboardMarkup(d_to_2d(goods), True, True))
    message.user_data["x"] = -1
    message.user_data["order"] = {}
    return CHOICE


def getdata(bot: Update, message: CallbackContext):
    order_type = message.user_data["order"].get("TYPE")
    if message.user_data["x"] == -1:
        message.user_data["order"]["TYPE"] = bot.message.text
        order_type = message.user_data["order"]["TYPE"]
    else:
        now = list(goods_list[order_type]["need"].keys())[message.user_data["x"]]
        if now not in goods_list[order_type]["must"] and bot.message.text == "/skip":
            message.user_data["order"][now] = ""
        # TODO: verify data
        else:
            message.user_data["order"][now] = bot.message.text
    # TODO: verify data
    message.user_data["x"] += 1
    now = list(goods_list[order_type]["need"].keys())[message.user_data["x"]]
    markup = None
    if now in goods_list[order_type]["choice"]:
        do = "选择"
        markup = ReplyKeyboardMarkup(d_to_2d(goods_list[order_type]["choice"][now]), True, True)
    else:
        do = "输入"
    getdata_text = "请{do}{id}的{text}".format(do=do, id=goods_list[order_type]["name"],
                                             text=goods_list[order_type]["need"][now])
    if now not in goods_list[order_type]["must"]:
        getdata_text += "\n输入 /skip 跳过"
    getdata_text += "\n输入 /cancel 取消"
    bot.message.reply_text(getdata_text, reply_markup=markup)
    if message.user_data["x"] == len(goods_list[order_type]["need"].keys()) - 1:
        return FINISH
    return CHOICE


def finish(bot: Update, message: CallbackContext):
    order_type = message.user_data["order"].get("TYPE")
    now = list(goods_list[order_type]["need"].keys())[message.user_data["x"]]
    if now not in goods_list[order_type]["must"] and bot.message.text == "/skip":
        message.user_data["order"][now] = ""
    # TODO: verify data
    else:
        message.user_data["order"][now] = bot.message.text
    finish_text = """全部信息输入完毕，请进行核对\n类型: {}\n""".format(order_type)
    for i, j in message.user_data["order"].items():
        if i == "TYPE":
            continue
        finish_text += "{}: {}\n".format(goods_list[order_type]["need"][i], j)
    finish_text += "确定请回复 yes \n不确定请回复 /cancel 重新开始"
    bot.message.reply_text(finish_text, reply_markup=ReplyKeyboardMarkup([["Yes", "/cancel"]], True, True))
    return PAY


paymethods = {"muggle": muggle_pay}


def pay(bot: Update, message: CallbackContext):
    if bot.message.text != "Yes":
        bot.message.reply_text("确定请回复 Yes \n不确定请回复 /cancel 重新开始",
                               reply_markup=ReplyKeyboardMarkup([["Yes", "/cancel"]], True, True))
        return PAY
    m = bot.message.reply_text("正在提交中......")
    try:
        oid = create(message.user_data["order"], bot.message.from_user.id)
    except:
        m.edit_text("出现错误，请联系管理员")
    else:
        m.edit_text("订单提交成功！订单号为： {}".format(oid))
        message.user_data["order"]["id"] = oid
    order_type = message.user_data["order"].get("TYPE")
    message.user_data["retry"] = 3
    price = goods_list[order_type]["price"]
    kb = d_to_2d([InlineKeyboardButton(i, callback_data=i) for i in paymethods.keys()])
    bot.message.reply_text("您的订单价格为" + str(price) + "\n请选择支付方式！",
                           reply_markup=InlineKeyboardMarkup(kb))
    return PAY_CALLBACK


def pay_callback(bot: Update, message: CallbackContext):
    query = bot.callback_query
    query.answer()
    query.edit_message_text("正在创建支付......")
    text = create_pay(query.data, message.user_data["order"]["id"])
    query.edit_message_text(text)
    del message.user_data["x"]
    del message.user_data["order"]
    return ConversationHandler.END


def cancel(bot: Update, message: CallbackContext):
    bot.message.reply_text("okay", reply_markup=ReplyKeyboardRemove())
    del message.user_data["x"]
    del message.user_data["order"]
    return ConversationHandler.END


@sio.event
def message(data: dict):
    text = ""
    if data["status"] == "paid":
        order_id, status, user_id = data.values()
        text = paid_text.format(order_id)
        bot.send_message(user_id, text)
    else:  # status == complete
        order_id, status, user_id, images = data.values()
        pass


CHOICE, FINISH, PAY, PAY_CALLBACK, DONE = 1, 2, 3, 4, 5
if __name__ == '__main__':
    goods_list = get_list()
    sio.connect("http://127.0.0.1:5000/")
    update = Updater("1742435872:AAEBGYtvM9y-9mYtAieTdwBxDpSAnMcHC_4")
    bot: Bot = update.bot
    dis: Dispatcher = update.dispatcher
    dis.add_handler(CommandHandler("start", start))
    dis.add_handler(CommandHandler("list", lists))
    dis.add_handler(CommandHandler("admins", admins))
    dis.add_handler(ConversationHandler(
        entry_points=[CommandHandler('make', make)],
        states={
            CHOICE: [MessageHandler(Filters.text & ~(Filters.regex("^/cancel$")), getdata)],
            FINISH: [MessageHandler(Filters.text & ~(Filters.regex("^/cancel$")), finish)],
            PAY: [MessageHandler(Filters.text & ~(Filters.regex("^/cancel$")), pay)],
            PAY_CALLBACK: [CallbackQueryHandler(pay_callback)]
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    ))
    update.start_polling()
