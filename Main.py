# -*- coding: utf-8 -*-
# Main.py
import time
from Utils import Invoice, DataParser
from Config import config
from Wechat import *

# Author  : 李达西


def main():
    """
    主方法
    一部分为发票识别和处理，另一部分对于指令做出反应
    """
    # 输出重定向，将print语句都写进系统日志文件
    file = open("./system_log.text", "a+")
    sys.stdout = file
    # 实例化微信机器人，传入群聊名和管理员名
    wechat = Wechat(config["group_name"], config["admin_name"])
    while True:
        time.sleep(1)
        wechat.get_group_mess()
        wechat.parse_mess()

        # 若群聊有要处理的图片，则迭代解析
        if wechat.pic_list:
            for pic in wechat.pic_list:
                invoice_data = Invoice.run(pic)
                if invoice_data:
                    data_parser = DataParser(invoice_data)
                    brief_mess, detail_mess = data_parser.parse()
                    wechat.send_group_mess(detail_mess)  # 先发送发票识别详细信息
                    time.sleep(0.5)
                    wechat.send_group_mess(brief_mess)  # 返回名称和税号是否有错误
                else:
                    wechat.send_group_mess("请求未成功，请重试或联系管理员")

        # 若有相关命令，则做出相应反应
        if wechat.order_list:
            for order in wechat.order_list:
                if "开票信息" in order.text:
                    wechat.send_group_mess(config["company_name"])
                    time.sleep(0.5)
                    wechat.send_group_mess(config["company_tax_number"])
                elif "SEND LOG" in order.text:
                    wechat.send_parse_log()
                elif "SEND SYSTEM LOG" in order.text:
                    wechat.send_system_log()
                elif "BREAK" in order.text:
                    wechat.send_group_mess("收到关机指令，正在关机")
                    file.close()
                    return None


if __name__ == "__main__":
    main()

