#!/usr/bin/env python
# encoding: utf-8

import json
import logging

import config
from chinese_pinyin import Pinyin
from . import redis
from . import split_words, split_pinyin, utf8, mk_sets_key, mk_score_key, mk_condition_key, mk_complete_key

class Index(object):
    """docstring for Index"""
    
    def __init__(self, name, id, title, score="id", exts={}, condition_fields=[], prefix_index_enable=True):
        
        self.name  = name
        self.title = utf8(title)
        self.id    = id
        self.score = score
        self.exts  = exts
        self.condition_fields = condition_fields
        self.prefix_index_enable = prefix_index_enable
    
    def save(self):
        """docstring for save"""

        if not self.title:
            return False

        data = {
            'name':self.name,
            'id':self.id,
            'title':self.title
        }

        if self.exts:
            data.update(self.exts)

        # 将原始数据存入 hashes
        res = redis.hset(self.name, self.id, json.dumps(data))

        # 保存 sets 索引，以分词的单词为key，用于后面搜索，里面存储 ids
        words = self.split_words_for_index(self.title)

        if not words:
            logging.info("no words")
            return False

        for word in words:
            key = mk_sets_key(self.name, word)

            # word index for item id
            redis.sadd(key, self.id)

        # score for search sort
        redis.set(mk_score_key(self.name, self.id), self.score)

        # 将目前的编号保存到条件(conditions)字段所创立的索引上面
        for field in self.condition_fields:
            redis.sadd(mk_condition_key(self.name, field, utf8(data[field])), self.id)

        if self.prefix_index_enable:
            self.save_prefix_index()

    def remove(self, name, id, title):
        """docstring for remove"""
        
        redis.hdel(name, id)
        words = self.split_words_for_index(title)

        for word in words:
            key = mk_sets_key(name, word)
            redis.srem(key, id)
            redis.delete(mk_score_key(name, id))
            
        # remove set for prefix index key
        redis.srem(mk_sets_key(name, title, id))
    
    def split_words_for_index(self, title):
        """docstring for split_words_for_index"""

        words = split_words(title)
        if config.pinyin_match:
            words += split_pinyin(title)
        
        return words
    
    def save_prefix_index(self):
        """docstring for save_prefix_index"""
        words = []
        words.append(self.title.lower())
        
        redis.sadd(mk_sets_key(self.name, self.title), self.id)

        if config.pinyin_match:
            pinyin = Pinyin.t(self.title.lower(), "")
            words += pinyin
            redis.sadd(mk_sets_key(self.name, pinyin), self.id)

        key = mk_complete_key(self.name)
        for word in words:
            for i in range(0, len(word)):
                prefix = word[0:i]
                redis.zadd(key, 0, prefix)
            
            redis.zadd(key, 0, word + "*")
