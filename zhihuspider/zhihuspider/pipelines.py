# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from .items import *
from twisted.enterprise import adbapi
import pymysql

class ZhihuspiderPipeline(object):
    def __init__(self):
        # 链接数据库，创建游标
        pass

    def process_item(self, item, spider):
        if isinstance(item, ZhihuAnswerItem):
            pass
        elif isinstance(item, ZhihuQuestionItem):
            pass
        return item


class ZhihuMysqlPipeline(object):
    def __init__(self, pool):
        self.dbpool = pool

    @classmethod
    def from_settings(cls, settings):
        """
        当爬虫启动的时候，scrapy会自动调用这些函数，加载配置数据。
        :param settings:
        :return:
        """
        params = dict(
            host=settings['MYSQL_HOST'],
            port=settings['MYSQL_PORT'],
            db=settings['MYSQL_DB'],
            user=settings['MYSQL_USER'],
            passwd=settings['MYSQL_PASSWD'],
            charset=settings['MYSQL_CHARSET'],
            cursorclass=pymysql.cursors.DictCursor
        )

        db_connect_pool = adbapi.ConnectionPool('pymysql', **params)

        # 初始化这个类的对象
        obj = cls(db_connect_pool)
        return obj

    def process_item(self, item, spider):
        """
        在连接池中，开始执行数据的多线程写入操作。
        :param item:
        :param spider:
        :return:
        """
        result = self.dbpool.runInteraction(self.insert, item)
        # 给result绑定一个回调函数，用于监听错误信息
        result.addErrback(self.error)

    def error(self, reason):
        print('--------', reason)

    def insert(self, cursor, item):
        if isinstance(item, ZhihuAnswerItem):
            insert_sql = 'INSERT INTO answer(answer_id, answer_question_id, answer_vote_up_nums) VALUES (%s, %s, %s)'
            cursor.execute(insert_sql, (item['answer_id'], item['answer_question_id'], item['answer_vote_up_nums']))
        elif isinstance(item, ZhihuQuestionItem)
            insert_sql = 'INSERT INTO question(question_id, question_title) VALUES (%s, %s)'
            cursor.execute(insert_sql, (item['question_id'], item['question_title']))


