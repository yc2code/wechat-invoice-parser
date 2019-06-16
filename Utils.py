# -*- coding: utf-8 -*-
import base64
import csv
import hashlib
import os
import time
import requests


class Invoice:
    """
    发票识别类
    本次使用票小秘发票识别API，可以试用
    官网 http://fapiao.glority.cn/
    可以识别上传的各类发票信息，具体功能及配置请移步官网
    """

    @staticmethod
    def get_pic_content(image_path):
        """
        方法--打开图片
        以二进制格式打开
        """
        with open(image_path, 'rb') as pic:
            return pic.read()

    @staticmethod
    def parse_invoice(image_binary):
        """
        方法--识别图片
        调用接口，返回识别后的发票数据
        以下内容基本根据API调用的要求所写，无需纠结
        各类报错码在官网文档可查
        """
        api_url = "http://fapiao.glority.cn/v1/item/get_item_info"
        appkey = "5ca1b6b6"
        appsecret = "2f194b2c74db7b00927aef58de7c1b61"
        image_data = base64.b64encode(image_binary)
        timestamp = int(time.time())
        m = hashlib.md5()
        token = appkey + "+" + str(timestamp) + "+" + appsecret
        m.update(token.encode('utf-8'))
        token = m.hexdigest()
        try:
            data = {'image_data': image_data, 'app_key': appkey, 'timestamp': str(timestamp), 'token': token}
            r = requests.post(api_url, data=data)
            if r.status_code != 200:
                print(time.ctime()[:-5], "Failed to get info")
                return None
            else:
                result = r.json()
                invoice_type = result['response']['data']['identify_results'][0]['type']
                # "10100"和"10101"为均API的参数选项，代表只识别专票和普票，可以换成你想要识别的票据种类
                if invoice_type == '10100' or invoice_type == '10101':
                    invoice_data_raw = result['response']['data']['identify_results'][0]['details']
                    invoice_data = {
                        '检索日期': '-'.join(time.ctime().split()[1:3]),
                        '发票代码': invoice_data_raw['code'],
                        '发票号码': invoice_data_raw['number'],
                        '开票日期': invoice_data_raw['date'],
                        '合计金额': invoice_data_raw['pretax_amount'],
                        '价税合计': invoice_data_raw['total'],
                        '销售方名称': invoice_data_raw['seller'],
                        '销售方税号': invoice_data_raw['seller_tax_id'],
                        '购方名称': invoice_data_raw['buyer'],
                        '购方税号': invoice_data_raw['buyer_tax_id']
                    }
                    return invoice_data
                else:
                    return None
        except:
            # 笔者在有试用次数的情况下出现过调用失败，问客服后得知流量不够了，得充钱
            # 若不想使用Pushover，可以直接注释后pass，或者输出错误信息日志
            message = "发票识别API调用出现错误"
            Pushover.push_message(message)
            return None
        finally:
            print(time.ctime()[:-5], "产生一次了调用")

    @staticmethod
    def save_to_csv(invoice_data):
        """
        方法--日志保存
        将识别记录写入文件夹下work_log.csv文件
        若无此文件则自动创建并写入表头
        """
        if "work_log.csv" not in os.listdir():
            not_found = True
        else:
            not_found = False

        with open('./work_log.csv', 'a+') as file:
            writer = csv.writer(file)
            if not_found:
                writer.writerow(invoice_data.keys())
            writer.writerow(invoice_data.values())

    @staticmethod
    def run(image_path):
        """
        主方法
        解析完成返回True，否则返回False
        """
        image_binary = Invoice.get_pic_content(image_path)
        invoice_data = Invoice.parse_invoice(image_binary)
        if invoice_data:
            Invoice.save_to_csv(invoice_data)
            return invoice_data
        return None


class DataParser:
    """
    数据分析类
    对识别返回后的数据进行整理，并于默认信息对比，查看有无错误
    这里只简单实现整理信息和检查名称和税号的方法，有兴趣可以增加其他丰富的方法
    """

    def __init__(self, invoice_data):
        self.invoice_data = invoice_data

    def get_detail_message(self):
        """
        对得到的发票信息的格式进行整理
        :return: 返回整理好的发票信息
        """
        values = [value for value in self.invoice_data.values()]
        detail_mess = f"完整信息为：" \
            f"\n发票代码: {values[1]}\n发票号码: {values[2]}\n开票日期: {values[3]}" \
            f"\n合计金额: {values[4]}\n价税合计: {values[5]}\n销售方名称: {values[6]}" \
            f"\n销售方税号: {values[7]}\n购方名称: {values[8]}\n购方税号:{values[9]}"
        return detail_mess

    def get_brief_message(self):
        """
        将信息中的名称和税号和默认值进行对比
        只做对错判断，读者丰富一下可以增加指出错误位置的信息
        :return: 返回判断的信息
        """
        if self.invoice_data["购方名称"] == config["company_name"]:
            brief_mess = "购方名称正确"
        else:
            brief_mess = "!购方名称错误!"
        if self.invoice_data["购方税号"] == config["company_tax_number"]:
            brief_mess += "\n购方税号正确"
        else:
            brief_mess += "\n!购方税号错误!"
        return brief_mess

    def parse(self):
        brief_mess = self.get_brief_message()
        detail_mess = self.get_detail_message()
        return brief_mess, detail_mess


class Pushover:
    """
    消息推送类
    本次使用Pushover为推送消息软件（30 RMB，永久，推荐）
    官网 https://pushover.net/
    可以向微信一样把相关信息推送至不同设备
    如果不需要可以把相关代码注释掉
    """

    @staticmethod
    def push_message(message):
        message += ">>>来自Python发票校验"
        try:
            requests.post("https://api.pushover.net/1/messages.json", data={
                "token": "acupz8oowmunebm7rmkacehei3cpp6",
                "user": "u7aqhzhuzpfr2pqs2s7mcou8dyftse",
                "message": message
            })
        except Exception as e:
            print(time.ctime()[:-5], "Pushover failed", e, sep="\n>>>>>>>>>>\n")
