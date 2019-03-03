# -*- coding: utf-8 -*-
import scrapy, json
from scrapy.loader import ItemLoader
from ..items import *

class ZhihuSpider(scrapy.Spider):
    name = 'zhihu'
    # 两种类型的问题结构：1.知乎问答(www.zhihu.com); 2.知乎专栏(zhuanlan.zhihu.com);
    allowed_domains = ['zhihu.com']
    # 问题列表页接口
    start_urls = ['https://www.zhihu.com/api/v3/feed/topstory?action_feed=True&limit=7&session_token=741d29fcd68f7b71943266341195e5ec&action=down&after_id=&desktop=true']

    def parse(self, response):
        """
        解析列表页返回的json数据，提取问题的id。
        :param response:
        :return:
        """
        list_json_dict = json.loads(response.text)
        data = list_json_dict['data']
        for question_dict in data:
            try:
                # 如果target中存在question，说明是问答页面(www.zhihu.com)
                question_id = question_dict['target']['question']['id']
                question_detail_url = 'https://www.zhihu.com/question/{}'.format(question_id)
            except:
                # 如果target中不存在question，说明是专栏页面(zhuanlan.zhihu.com)
                question_id = question_dict['target']['id']
                question_detail_url = 'https://zhuanlan.zhihu.com/p/{}'.format(question_id)

            yield scrapy.Request(url=question_detail_url, callback=self.parse_question, meta={'question_id': question_id})

            # 获取question_detail_url以后，可以区分是问答页面还是专栏页面。
            if 'question' in question_detail_url:
                # 问答页面
                answers_url = 'https://www.zhihu.com/api/v4/questions/{}/answers?include=data%5B*%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%3Bdata%5B*%5D.mark_infos%5B*%5D.url%3Bdata%5B*%5D.author.follower_count%2Cbadge%5B*%5D.topics&offset=0&limit=3&sort_by=default'.format(question_id)
                yield scrapy.Request(
                    url=answers_url,
                    callback=self.parse_answer
                )
            elif 'zhuanlan' in question_detail_url:
                zhuanlan_url = 'https://www.zhihu.com/api/v4/articles/{}/comments?include=data%5B*%5D.author%2Ccollapsed%2Creply_to_author%2Cdisliked%2Ccontent%2Cvoting%2Cvote_count%2Cis_parent_author%2Cis_author%2Calgorithm_right&order=normal&limit=20&offset=0&status=open'.format(question_id)
                yield scrapy.Request(
                    url=zhuanlan_url,
                    callback=self.parse_answer
                )

        is_end = list_json_dict['paging']['is_end']
        if is_end == False:
            next_url = list_json_dict['paging']['next']
            # 构造请求，放入调度器中
            yield scrapy.Request(
                url=next_url,
                callback=self.parse
            )

    def parse_question(self, response):
        """
        解析详情页的问题的信息，标题、关注者数量等。
        :param response:
        :return:
        """
        if 'question' in response.url:
            # question_title：问答页面和专栏页面的标签结构是不一样的。
            # 解决方法：
            # 1. 提取详情页的<head><title></title>中title标签的内容。
            # 2. 给question_title添加两个add_css/add_xpath，两个css只能有一个提取到数据。
            question_id = response.meta['question_id']
            item_loader = ItemLoader(item=ZhihuQuestionItem(), response=response)
            item_loader.add_value('question_id', question_id)
            item_loader.add_css('question_title', '.QuestionHeader-main > h1.QuestionHeader-title::text')
            # 问题的内容可能是不存在的。question_content
            item_loader.add_css('question_content', '.QuestionHeader-detail span.RichText > p::text')
            # 问题的主题分类
            item_loader.add_css('question_topic', '.QuestionHeader-topics .Popover > div::text')

            # 关注数和浏览数: 注意：这里获取的源码标签结构中，关注数和浏览数的标签结构和在浏览器中查看的网页源代码中的标签结构是不一样的。以response获取的网页源代码标签结构为准。。。。。
            item_loader.add_xpath('question_watch_num', '//div[contains(@class, "QuestionFollowStatus-counts")]/div[1]/div/strong/@title')
            item_loader.add_xpath('question_click_num', '//div[contains(@class, "QuestionFollowStatus-counts")]/div[2]/div/strong/@title')

            item_loader.add_css('question_answer_nums', 'h4.List-headerText > span::text')
            item_loader.add_css('question_comment_nums', 'div.QuestionHeader-Comment > button::text')

            item = item_loader.load_item()
            yield item
        else:
            # 专栏页面(标题、赞数量、评论数量)
            yield None

    def parse_answer(self, response):
        """
        获取问题的答案：一种是问答页面的答案；一种是知乎专栏的答案；
        :param response:
        :return:
        """
        answers_dict = json.loads(response.text)
        if 'answers' in response.url:
            # 问答页面的答案接口
            for answer_dic in answers_dict['data']:
                # 答案ID
                answer_id = answer_dic['id']
                # 答案所属的问题
                answer_question_id = answer_dic['question']['id']
                # 回答问题的用户
                answer_author_id = answer_dic['author']['id']
                # 回答问题的时间
                answer_time = answer_dic['created_time']
                # 答案获得的点赞数
                answer_vote_up_nums = answer_dic['voteup_count']
                # 答案获得的评论数
                answer_comment_num = answer_dic['comment_count']

                item = ZhihuAnswerItem()
                item['answer_id'] = answer_id
                item['answer_question_id'] = answer_question_id
                item['answer_author_id'] = answer_author_id
                item['answer_time'] = answer_time
                item['answer_vote_up_nums'] = answer_vote_up_nums
                item['answer_comment_num'] = answer_comment_num

                yield item

        elif 'comments' in response.url:
            # 专栏页面的答案接口
            for answer_dic in answers_dict['data']:
                # 答案ID
                answer_id = answer_dic['id']
                # 答案所属的问题：旨在表名这个答案是哪一个问题的答案。
                answer_question_id = 0
                # 回答问题的用户
                answer_author_id = answer_dic['author']['member']['id']
                # 回答问题的时间
                answer_time = answer_dic['created_time']
                # 答案获得的点赞数
                answer_vote_up_nums = answer_dic['vote_count']
                # 答案获得的评论数
                answer_comment_num = 0

                item = ZhihuAnswerItem()
                item['answer_id'] = answer_id
                item['answer_question_id'] = answer_question_id
                item['answer_author_id'] = answer_author_id
                item['answer_time'] = answer_time
                item['answer_vote_up_nums'] = answer_vote_up_nums
                item['answer_comment_num'] = answer_comment_num

                yield item

        # 获取下一页的答案内容
        is_end = answers_dict['paging']['is_end']
        if is_end == False:
            yield scrapy.Request(
                url=answers_dict['paging']['next'],
                callback=self.parse_answer
            )