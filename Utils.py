# -*- coding: utf-8 -*-
# Utils.py
import base64
import csv
import os
import time
import requests
from Config import config


class Invoice:
    """
    发票识别类
    使用百度发票识别API，免费使用
    官方地址 https://ai.baidu.com/docs#/OCR-API/5099e085
    其它功能及配置请移步官网
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
        调用百度接口，返回识别后的发票数据
        以下内容基本根据API调用的要求所写，无需纠结
        各类报错码在官网文档可查
        百度API注册及使用教程：http://ai.baidu.com/forum/topic/show/867951
        """
        # 识别质量可选high及normal
        # normal（默认配置）对应普通精度模型，识别速度较快，在四要素的准确率上和high模型保持一致，
        # high对应高精度识别模型，相应的时延会增加，因为超时导致失败的情况也会增加（错误码282000）
        access_token = "你的access_token"
        api_url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/vat_invoice?access_token={access_token}"
        quality = "high"
        header = {"Content-Type": "application/x-www-form-urlencoded"}
        # 图像数据，base64编码后进行urlencode，要求base64编码和urlencode后大小不超过4M，
        # 最短边至少15px，最长边最大4096px,支持jpg/jpeg/png/bmp格式
        image_data = base64.b64encode(image_binary)
        try:
            data = {"accuracy": quality, "image": image_data}
            response = requests.post(api_url, data=data, headers=header)
            if response.status_code != 200:
                print(time.ctime()[:-5], "Failed to get info")
                return None
            else:
                result = response.json()["words_result"]
                invoice_data = {
                    '检索日期': '-'.join(time.ctime().split()[1:3]),
                    '发票代码': result['InvoiceCode'],
                    '发票号码': result['InvoiceNum'],
                    '开票日期': result['InvoiceDate'],
                    '合计金额': result['TotalAmount'],
                    '价税合计': result['AmountInFiguers'],
                    '销售方名称': result['SellerName'],
                    '销售方税号': result['SellerRegisterNum'],
                    '购方名称': result['PurchaserName'],
                    '购方税号': result['PurchaserRegisterNum'],
                    "发票类型": result["InvoiceType"]
                }
                return invoice_data
        except:
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
                "token": "你的Token",
                "user": "你的User",
                "message": message
            })
        except Exception as e:
            print(time.ctime()[:-5], "Pushover failed", e, sep="\n>>>>>>>>>>\n")
