#!/usr/bin/env python
# encoding: utf-8

import time
import json
import logging

from chinese_pinyin import Pinyin

import util
from util import split_words, split_pinyin, utf8, mk_sets_key, mk_score_key, mk_condition_key, mk_complete_key

def query(name, text, offset=0, limit=10, sort_field='id', conditions=None):
    """docstring for query"""

    conditions = conditions if isinstance(conditions, dict) and conditions else {}

    tm = time.time()
    result = []

    # 如果搜索文本和查询条件均没有，那就直接返回 []
    if not text.strip() and not conditions:
        return result

    text = utf8(text.strip())
    splited_words = split_words(text)

    words = []
    for word in splited_words:
        words.append(mk_sets_key(name, word))

    condition_keys = []
    if conditions:
        for c in conditions:
            condition_keys.append(mk_condition_key(name, c, utf8(conditions[c])))
            
        # 将条件的 key 放入关键词搜索集合内，用于 sinterstore 搜索
        words += condition_keys
    
    if not words:
        return result

    temp_store_key = "tmpinterstore:%s" % "+".join(words)
    
    if len(words) > 1:
        if not util.redis.exists(temp_store_key):
            # 将多个词语组合对比，得到交集，并存入临时区域
            util.redis.sinterstore(temp_store_key, words)
            
            # 将临时搜索设为1天后自动清除
            util.redis.expire(temp_store_key, 86400)
        
        # 拼音搜索
        if util.pinyin_match:
            splited_pinyin_words = split_pinyin(text)

            pinyin_words = []
            for w in splited_pinyin_words:
                pinyin_words.append(mk_sets_key(name, w))
                
            pinyin_words += condition_keys
            
            temp_sunion_key = "tmpsunionstore:%s" % "+".join(words)
            temp_pinyin_store_key = "tmpinterstore:%s" % "+".join(pinyin_words)
            
            # 找出拼音的
            util.redis.sinterstore(temp_pinyin_store_key, pinyin_words)
            
            # 合并中文和拼音的搜索结果
            util.redis.sunionstore(temp_sunion_key, [temp_store_key, temp_pinyin_store_key])
            
            # 将临时搜索设为1天后自动清除
            util.redis.expire(temp_pinyin_store_key, 86400)
            util.redis.expire(temp_sunion_key, 86400)
            
            temp_store_key = temp_sunion_key
    else:
        temp_store_key = words[0]

    # 根据需要的数量取出 ids
    ids = util.redis.sort(temp_store_key,
                    start = offset,
                    num = limit,
                    by = mk_score_key(name, "*"),
                    desc = True)

    result = util.hmget(name, ids, sort_field=sort_field)
    logging.debug("%s:\"%s\" | Time spend:%ss" % (name, text, time.time()-tm))
    return result

def complete(name, keyword, limit=10, conditions=None):
    """docstring for complete"""

    conditions = conditions if isinstance(conditions, dict) and conditions else {}

    if not keyword and not conditions:
        logging.debug("no word and conditions")
        return []

    keyword = utf8(keyword.strip())
    prefix_matchs = []
    
    # This is not random, try to get replies < MTU size
    rangelen = util.complete_max_length
    prefix = keyword.lower()
    key = mk_complete_key(name)

    start = util.redis.zrank(key, prefix)

    if start:
        count = limit
        max_range = start+(rangelen*limit)-1
        entries = util.redis.zrange(key, start, max_range)
        
        while len(prefix_matchs) <= count:
            
            start += rangelen
            if not entries or len(entries) == 0:
                break
            
            for entry in entries:
                minlen = min(len(entry), len(prefix))

                if entry[0:minlen] != prefix[0:minlen]:
                    count = len(prefix_matchs)
                    break

                if entry[-1] == "*" and len(prefix_matchs) != count:

                    match = entry[:-1]
                    if match not in prefix_matchs:
                        prefix_matchs.append(match)
          
            entries = entries[start:max_range]

    # 组合 words 的特别 key 名
    words = []
    for word in prefix_matchs:
        words.append(mk_sets_key(name, word))

    # 组合特别 key ,但这里不会像 query 那样放入 words， 因为在 complete 里面 words 是用 union 取的，condition_keys 和 words 应该取交集
    condition_keys = []
    if conditions:
        for c in conditions:
            condition_keys.append(mk_condition_key(name, c, utf8(conditions[c])))
    
    # 按词语搜索
    temp_store_key = "tmpsunionstore:%s" % "+".join(words)
    if len(words) == 0:
        logging.info("no words")
    elif len(words) > 1:
        if not util.redis.exists(temp_store_key):
            
            # 将多个词语组合对比，得到并集，并存入临时区域   
            util.redis.sunionstore(temp_store_key, words)
            
            # 将临时搜索设为1天后自动清除
            util.redis.expire(temp_store_key, 86400)
        # 根据需要的数量取出 ids
    else:
        temp_store_key = words[0]

    # 如果有条件，这里再次组合一下
    if condition_keys:
        if not words:
            condition_keys += temp_store_key
            
        temp_store_key = "tmpsinterstore:%s" % "+".join(condition_keys)
        if not util.redis.exists(temp_store_key):
            util.redis.sinterstore(temp_store_key, condition_keys)
            util.redis.expire(temp_store_key, 86400)
     
    ids = util.redis.sort(temp_store_key,
                    start = 0,
                    num = limit,
                    by = mk_score_key(name, "*"),
                    desc = True)
    if not ids:
        return []
        
    return util.hmget(name, ids)

