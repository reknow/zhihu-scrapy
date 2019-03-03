# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy, re
from scrapy.loader.processors import Join, MapCompose, TakeFirst

def process_comment(value):
    num = re.search(re.compile(r'(\d+)'), value)
    if num:
        return num.group(1)
    return '0'

class ZhihuQuestionItem(scrapy.Item):
    # 问题ID
    question_id = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 问题标题
    question_title = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 问题的分类
    question_topic = scrapy.Field(
        # ['视频', 'IT']
        output_processor=Join(';')
    )
    # 问题的内容
    question_content = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 关注者数量
    question_watch_num = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 浏览数量
    question_click_num = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 答案的总数量
    question_answer_nums = scrapy.Field(
        output_processor=TakeFirst()
    )
    # 问题获得的评论
    question_comment_nums = scrapy.Field(
        # 评论 ['12 条评论'] 通过函数process_comment处理：['12']
        input_processor=MapCompose(process_comment),
        output_processor=TakeFirst()
    )


class ZhihuAnswerItem(scrapy.Item):
    # 答案ID
    answer_id = scrapy.Field()
    # 答案所属的问题
    answer_question_id = scrapy.Field()
    # 回答问题的用户
    answer_author_id = scrapy.Field()
    # 回答问题的时间
    answer_time = scrapy.Field()
    # 答案获得的点赞数
    answer_vote_up_nums = scrapy.Field()
    # 答案获得的评论数
    answer_comment_num = scrapy.Field()
