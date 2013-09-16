#!/usr/bin/env python
# encoding: utf-8

import logging
import redis
import time

import redis_search

from redis_search.util import split_words
from redis_search.index import index
from redis_search.query import query, complete

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(msecs)03d %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M')

words = split_words("最主要的更动是：张无忌最后没有选定自己的配偶。:,.")
for w in words:
    print w

pool = redis.ConnectionPool(host='127.0.0.1', port=6379, db=8)
redis_search.util.redis = redis.Redis(connection_pool=pool)

i = index("test", 1, "Redis")
i.save()

i = index("test", 2, "Redhat")
i.save()

i = index("test", 3, "张无忌最后没有选定自己的配偶", "id", exts= {
     'username':"jiedan", 'email':'lxb429@gmail.com'
})
i.save()

i = index("test", 4, "Redis 是一个高性能的key-value数据库", "id", exts= {
    'username':"jiedan", 'email':'lxb429@gmail.com'
})
i.save()

i = index("test", 6, "回明朝当皇帝", "id", exts={"title":"回明朝当皇帝"})
i.save()

i = index("test", 7, "回明朝做皇帝", "id", exts={"title":"回明朝做皇帝"})
i.save()

print "自动完成: r"
users = complete('test', "r")

for user in users:
    print user['id'], user['title']

print "-"*10
print "自动完成: redi"
users = complete('test', "redi")

for user in users:
    print user['id'], user['title']

print "-"*10
print "自动完成: 张"
users = complete('test', "张")

for user in users:
    print user['id'], user['title']

print "-"*10
print "搜索: Redis"
users = query('test', "Redis")
 
for user in users:
    print user['id'], user['title']

print "-"*10
print "搜索: 张无忌"
users = query('test', "张无忌")
 
for user in users:
    print user['id'], user['title']

print "-"*10
print "搜索: 回明朝做皇帝"
users = query('test', "回明朝做皇帝")
 
for user in users:
    print user['id'], user['title']

print "-"*10
print "搜索: 皇帝"
users = query('test', "当皇帝")
 
for user in users:
    print user['id'], user['title']

print "-"*10
print "拼音搜索: zhang"
users = query('test', "zhang")
 
for user in users:
    print user['id'], user['title']
