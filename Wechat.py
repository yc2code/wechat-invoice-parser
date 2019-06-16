# -*- coding: utf-8 -*-
# Wechat
import os
from wxpy import *


class Wechat:
    """
    微信处理类
    对微信的消息进行处理，分析并作出回应
    """

    def __init__(self, group_name, admin_name):
        self.bot = Bot()  # 类被实例化的时候即对机器人实例化

        self.group_name = group_name  # 指定群聊名
        self.admin_name = admin_name  # 管理员微信名

        self.received_mess_list = []  # 过滤后的消息列表
        self.order_list = []  # 管理命令列表
        self.pic_list = []  # 待解析图片绝对路径列表

    def get_group_mess(self):
        """
        方法--获取消息
        获取所有正常消息，进行过滤后存进消息列表
        """
        # 调用此方法时先清空上次调用时列表所存储的数据
        self.received_mess_list = []
        for message in self.bot.messages:
            # 如果为指定群聊或管理员的消息，存入group_mess
            sender = message.sender.name
            # >>>这里有一点要注意，如果你是用一个微信作为机器人且作为管理员<<<
            # >>>然后用这个微信号在群聊发消息，则信息sender会之指向自己而不是群聊<<<
            # >>>建议使用单独一个微信号作为机器人
            if sender == self.group_name or sender == self.admin_name:
                self.received_mess_list.append(message)
            # 其他的消息过滤掉
            self.bot.messages.remove(message)
        return None

    def parse_mess(self):
        """
        方法--处理群聊消息
        过滤获得的指定群聊消息
        设定所有新增群聊图片的绝对路径及群聊中产生的文字命令
        """
        # 调用此方法时先清空上次调用时列表所存储的数据
        self.pic_list = []
        self.order_list = []
        # self.group_order = []
        for message in self.received_mess_list:
            # 如果信息类型为图片，则保存图片并添加到图片列表
            if message.type == 'Picture' and message.file_name.split('.')[-1] != 'gif':
                self.pic_list.append(Wechat.save_file(message))
            # 如果消息类型为文字，则视为命令，保存到命令列表中
            if message.type == 'Text':
                self.order_list.append(message)
        return None

    @staticmethod
    def save_file(image):
        """
        方法--存储图片
        这里使用静态方法，是因为本方法和类没有内部交互，静态方法可以方便其他程序的调用
        解析名称，设定绝对路径，存储
        :param image: 接收到的图片(可以看成是wxpy产生的图片类，它具有方法和属性)
        :return: 返回图片的绝对路径
        """
        path = os.getcwd()
        # 如果路径下没有Pictures文件夹，则创建，以存放接收到的待识别图片
        if "Pictures" not in os.listdir():
            os.mkdir("Pictures")
        # 设定一个默认的图片格式后缀
        file_postfix = "png"
        try:
            # 尝试把图片的名称拆分，分别获取名称和后缀
            file_name, file_postfix = image.file_name.split('.')
        except Exception:
            # 当然有时候可能拆分不了，就把默认的后缀给它
            file_name = image.file_name
        # 赋予绝对路径
        file_path = path + '/Pictures/' + file_name + '.' + file_postfix
        # 将图片存储到指定路径下
        image.get_file(file_path)
        return file_path

    def send_group_mess(self, message):
        """
        方法--发送群消息
        :param message: 需要发送的内容
        """
        try:
            # 如果群聊名称被改变，搜索时会报错，如果找不到群聊，消息不会发送
            group = self.bot.groups().search(self.group_name)[0]
            group.send(message)
        except IndexError:
            print("找不到指定群聊，信息发送失败")
            return None

    def send_parse_log(self):
        """
        方法--发送查询日志
        向群聊内发送查询日志
        """
        try:
            # 如果群聊名称被改变，搜索时会报错，如果找不到群聊，消息不会发送
            group = self.bot.groups().search(self.group_name)[0]
        except IndexError:
            print("找不到指定群聊，查询日志发送失败")
            return None
        try:
            group.send_file("./work_log.csv")
        except:
            group.send("Oops, no log yet")
        return None

    def send_system_log(self):
        """
        方法--发送系统日志
        向群聊内发送查询日志
        """
        try:
            # 如果群聊名称被改变，搜索时会报错，如果找不到群聊，消息不会发送
            group = self.bot.groups().search(self.group_name)[0]
        except IndexError:
            print("找不到指定群聊，系统日志发送失败")
            return None
        try:
            group.send_file("./system_log.text")
        except:
            group.send("System log not found")
        return None
