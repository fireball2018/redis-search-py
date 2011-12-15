#!/usr/bin/env python
# encoding: utf-8

import redis

complete_max_length = 10
pinyin_match        = True

class Config:

    r = None
    debug = False

    def __init__(self):
        """docstring for init"""
        pass

    @classmethod
    def redis(self):
        """docstring for redis"""

        if self.r is None:
            self.r = redis.StrictRedis(host='localhost', port=6379, db=0)

        return self.r

