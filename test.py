#!/usr/bin/env python
# encoding: utf-8

import logging

from redis_search import split_words
from redis_search.index import Index
from redis_search import query, complete

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s:%(msecs)03d %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M')

words = split_words("最主要的更动是：张无忌最后没有选定自己的配偶。:,.")

for w in words:
    print w

i = Index("test", 1, "Redis")
i.save()

i = Index("test", 2, "Redhat")
i.save()

i = Index("test", 3, "张无忌最后没有选定自己的配偶", "id", exts= {
     'username':"jiedan", 'email':'lxb429@gmail.com'
})
i.save()

i = Index("test", 4, "Redis 是一个高性能的key-value数据库", "id", exts= {
    'username':"jiedan", 'email':'lxb429@gmail.com'
})
i.save()

print "自动完成: r"
users = complete('test', "r")

for user in users:
    print user['id'], user['title']

print "自动完成: redi"
users = complete('test', "redi")

for user in users:
    print user['id'], user['title']

print "自动完成: 张"
users = complete('test', "张")

for user in users:
    print user['id'], user['title']

print "搜索: Redis"
users = query('test', "Redis")
 
for user in users:
    print user['id'], user['title']

print "搜索: 张无忌"
users = query('test', "张无忌")
 
for user in users:
    print user['id'], user['title']

print "拼音搜索: zhang"
users = query('test', "zhang")
 
for user in users:
    print user['id'], user['title']
