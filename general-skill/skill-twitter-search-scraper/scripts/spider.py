# !/usr/bin/env python
# -*- coding:utf-8 -*-
# @FileName  :x_keyword_spider_新版.py
# @Time      :2026-03-13 22:54

import os
import json
import datetime
import pandas as pd

import base64
import hashlib
import struct
import time
import random
import requests
from urllib.parse import urlparse

def vo(content: str) -> bytes:
    """Base64 decode like atob"""
    return base64.b64decode(content)
def or_func(n, W, t):
    return n ^ t[0] if W else n
def to_base64(data: bytes) -> str:
    """Base64 encode and strip '='"""
    return base64.b64encode(data).decode('utf-8').replace('=', '')

def word_array_to_byte_array(hash_bytes: bytes) -> bytes:
    """Take first 16 bytes from SHA-256 hash"""
    return hash_bytes[:16]

def get_id(n: str, W: str, content: str,k:str) -> str:
    base_time = 1682924400  # 1682924400000 ms => 1682924400 s
    current_time = int(time.time())
    d = current_time - base_time
    # 4-byte big endian representation of the timestamp
    f = list(struct.pack(">I", d))[::-1]
    # Decode content
    i = list(vo(content))
    # Hash input string
    # k = "12327e10051eb851eb851ec0051eb851eb851ec100"
    input_string = f"{W}!{n}!{d}obfiowerehiring{k}"
    hash_digest = hashlib.sha256(input_string.encode('utf-8')).digest()
    hash_part = list(word_array_to_byte_array(hash_digest))
    # Compose final byte array
    random_byte = int(random.random()*256)
    # array = [random_byte]+ i + f + hash_part + [3]
    result = [random_byte] + i + f + hash_part + [3]
    processed_array = []
    for i in range(len(result)):
        value = or_func(result[i],i,result)
        processed_array.append(value)
    new_result = bytes(processed_array)
    return to_base64(new_result)


class TwitterKeywordSearchSpider:
    def __init__(self, cookies,saveFileName,ck_index):
        self.searchCondition = None
        self.headers = {
            "accept": "*/*",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8",
            "authorization": "Bearer AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA",
            "cache-control": "no-cache",
            "content-type": "application/json",
            "pragma": "no-cache",
            "priority": "u=1, i",
            "referer": "https://x.com/search?q=TO%20MY%20GREAT%20FELLOW&src=typed_query&f=live",
            "sec-ch-ua": "\"Chromium\";v=\"140\", \"Not=A?Brand\";v=\"24\", \"Google Chrome\";v=\"140\"",
            "sec-ch-ua-arch": "\"x86\"",
            "sec-ch-ua-bitness": "\"64\"",
            "sec-ch-ua-full-version": "\"140.0.7339.80\"",
            "sec-ch-ua-full-version-list": "\"Chromium\";v=\"140.0.7339.80\", \"Not=A?Brand\";v=\"24.0.0.0\", \"Google Chrome\";v=\"140.0.7339.80\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-model": "\"\"",
            "sec-ch-ua-platform": "\"Windows\"",
            "sec-ch-ua-platform-version": "\"8.0.0\"",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "x-client-transaction-id": "fyDw2msqfs3E+N6hExZDOaC4oFEBF42ytKWX7HeVlxB8L5MOECbYu9sLi6M6LQUQN1bQCnu116tzZJxNpVCkc4amrOqtfA",
            "x-csrf-token": "4290f3d1e1c087a1afa736d16781ef745f481045b34c5afc40ed40febec9dddc1c3a6308c35b6e7af2dee3e325d1ce07f636c0fcd164502fa4b208bde65432bd2a310dce3adbcff63e7757b0c8d17f64",
            "x-twitter-active-user": "yes",
            "x-twitter-auth-type": "OAuth2Session",
            "x-twitter-client-language": "zh-cn",
            "x-xp-forwarded-for": "937b7379ee14ffbe5dcf2457b5eb1bcce4c5d37abd225ef7dc671200ce1d6659017781dcdeb6824c42c27003544cd627d30b9b14a7ace77924b46f06145b90bdc687926416694200053c3388be96aa52142d7a1d59b1d20afc52a937fb144d9b3c6ffd3ff12bbc973cb57e4e6db2a4f8778cd65414a9a71b0dfc42dc2cc518ecfbf7e64e17f92a60d25e63b0c288d0a95a518b96b03724664ac7930374024a9f618f8205457b730752ccbe3dadfcd6aeef84dda517a8d28a9a0948c3d66a75f8201dd38d7c1a53b69c6711048320b00fc2d095fb06df975cece8c0769a67f54537c41d1f46081a3dd6f58066e357a5675f40d28183af44abaf0d65"
        }
        self.cookies_list = cookies
        self.current_cookie_index = ck_index
        self.saveFileName = saveFileName
        self.record_date = ""
        self.is_end = False

    def cookie_str_to_dict(self, cookie_str: str) -> dict:
        cookie_dict = {}
        cookies = [i.strip() for i in cookie_str.split('; ') if i.strip() != ""]
        for cookie in cookies:
            key, value = cookie.split('=', 1)
            cookie_dict[key] = value
        return cookie_dict

    def get(self, cursor, searchCondition):
        url = "https://x.com/i/api/graphql/7fWgap3nJOk9UpFV7UqcoQ/SearchTimeline"
        path = urlparse(url).path
        content = 'W+51xo20Et9hinNoyUNZXTU0TAyPyBOYcUafLN+UeppmbeQYfmuFJH2i0OTAiJ69'
        k_value = "f4c1930e6666666666668070a3d70a3d70a4070a3d70a3d70a40e666666666666800"
        x_id = get_id(path, "GET", content, k_value)
        self.headers["x-client-transaction-id"] = x_id
        while True:
            if not self.cookies_list:
                input("No cookies available, please update cookies.txt: ")
                self.cookies_list = [c.strip() for c in open('cookies.txt', encoding='utf-8').readlines() if
                                     c.strip() != ""]
            cookie_strings = self.cookies_list[self.current_cookie_index]
            cookies = self.cookie_str_to_dict(cookie_strings)
            self.headers["x-csrf-token"] = cookies.get('ct0', '')
            variables = {"rawQuery": searchCondition, "count": 20, "querySource": "typed_query", "product": "Latest"}
            if cursor != "-1":
                variables["cursor"] = cursor
            params = {
                "variables": json.dumps(variables, separators=(",", ":")),
                "features": "{\"rweb_video_screen_enabled\":false,\"payments_enabled\":false,\"profile_label_improvements_pcf_label_in_post_enabled\":true,\"rweb_tipjar_consumption_enabled\":true,\"verified_phone_label_enabled\":false,\"creator_subscriptions_tweet_preview_api_enabled\":true,\"responsive_web_graphql_timeline_navigation_enabled\":true,\"responsive_web_graphql_skip_user_profile_image_extensions_enabled\":false,\"premium_content_api_read_enabled\":false,\"communities_web_enable_tweet_community_results_fetch\":true,\"c9s_tweet_anatomy_moderator_badge_enabled\":true,\"responsive_web_grok_analyze_button_fetch_trends_enabled\":false,\"responsive_web_grok_analyze_post_followups_enabled\":true,\"responsive_web_jetfuel_frame\":true,\"responsive_web_grok_share_attachment_enabled\":true,\"articles_preview_enabled\":true,\"responsive_web_edit_tweet_api_enabled\":true,\"graphql_is_translatable_rweb_tweet_is_translatable_enabled\":true,\"view_counts_everywhere_api_enabled\":true,\"longform_notetweets_consumption_enabled\":true,\"responsive_web_twitter_article_tweet_consumption_enabled\":true,\"tweet_awards_web_tipping_enabled\":false,\"responsive_web_grok_show_grok_translated_post\":false,\"responsive_web_grok_analysis_button_from_backend\":false,\"creator_subscriptions_quote_tweet_preview_enabled\":false,\"freedom_of_speech_not_reach_fetch_enabled\":true,\"standardized_nudges_misinfo\":true,\"tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled\":true,\"longform_notetweets_rich_text_read_enabled\":true,\"longform_notetweets_inline_media_enabled\":true,\"responsive_web_grok_image_annotation_enabled\":true,\"responsive_web_grok_imagine_annotation_enabled\":true,\"responsive_web_grok_community_note_auto_translation_is_enabled\":false,\"responsive_web_enhance_cards_enabled\":false}"
            }
            try:
                response = requests.get(url, headers=self.headers, cookies=cookies, params=params, timeout=(3, 10))
                status_code = response.status_code
                print(f"Response status: {status_code}")
                if status_code == 429:
                    print("Rate limit reached. Rotating cookie...")
                    self.current_cookie_index = (self.current_cookie_index + 1) % len(self.cookies_list)
                    print("Switched to cookie ->",self.cookies_list[self.current_cookie_index])
                    self.save_index()
                    continue
                elif status_code == 200:
                    data = response.json()
                    try:
                        error_name = data["errors"][0]["name"]
                    except:
                        error_name = ""
                    if error_name == "AuthorizationError":
                        self.cookies_list.remove(cookie_strings)
                        if self.current_cookie_index == len(self.cookies_list):
                            self.current_cookie_index = 0
                        else:
                            self.current_cookie_index = self.current_cookie_index % len(self.cookies_list)
                        print("AuthorizationError, switching cookie ->", self.cookies_list[self.current_cookie_index])
                        self.save_cookie()
                        self.save_index()
                        continue
                    else:
                        return data
                elif status_code == 404:
                    x_id = get_id(path, "GET", content, k_value)
                    self.headers["x-client-transaction-id"] = x_id
                    continue
                else:
                    print("Other status code encountered...")
                    self.cookies_list.remove(cookie_strings)
                    if self.current_cookie_index == len(self.cookies_list):
                        self.current_cookie_index = 0
                    else:
                        self.current_cookie_index = self.current_cookie_index % len(self.cookies_list)
                    print("Switched to cookie ->", self.cookies_list[self.current_cookie_index])
                    self.save_cookie()
                    self.save_index()
                    continue
            except Exception as e:
                print(f"Search error: {e}")
                # return None

    def transfrom_time(self,date_str):
        GMT_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'
        timeArray = datetime.datetime.strptime(date_str, GMT_FORMAT)
        return timeArray.strftime("%Y-%m-%d %H:%M:%S")
    def save_cookie(self):
        with open("cookies.txt", 'w', encoding='utf-8') as f:
            ck_str = "\n".join(self.cookies_list)
            f.write(ck_str)
    def save_index(self):
        with open("cookie_index.txt", 'w', encoding='utf-8') as f:
            f.write(str(self.current_cookie_index))
    def transTime(self,dd):
        GMT_FORMAT = '%a %b %d %H:%M:%S +0000 %Y'
        timeArray = datetime.datetime.strptime(dd, GMT_FORMAT)
        gmt_offset = datetime.timedelta(hours=8)
        return (timeArray + gmt_offset).strftime("%Y-%m-%d %H:%M:%S")
    def parse_data(self, entries, keyword):
        resultList = []
        contentList = []
        for ent in entries:
            try:
                entryId = ent.get('entryId', "")
                if 'tweet' in entryId:
                    l_result = ent['content']['itemContent']['tweet_results']['result'] if ent['content'].get(
                        'itemContent') else None
                    if l_result:
                        contentList.append(l_result)
                elif "profile-conversation" in entryId:
                    items = ent['content']['items']
                    for i in items:
                        l_result = i['item']['itemContent']['tweet_results']['result'] if i['item'].get(
                            'itemContent') else None
                        if l_result:
                            contentList.append(l_result)
            except Exception as e:
                print(f"Error processing entry: {e}")
                continue

        for l in contentList:
            try:
                result = l.get('tweet') if l.get('tweet') else l
                legacy = result['legacy']
                core = result['core']
                views_count = int(result['views'].get("count", 0))
                id_str = legacy.get("id_str")
                created_at = self.transfrom_time(legacy.get('created_at'))
                self.record_date = str(created_at)
                full_text = legacy.get('full_text')
                note_tweet = result.get('note_tweet')
                if note_tweet:
                    try:
                        full_text = note_tweet['note_tweet_results']['result']['text']
                    except:
                        pass
                video_url_list = []
                image_url_list = []
                entities = legacy["entities"]
                try:
                    media = entities["media"]
                    for m in media:
                        m_type = m['type']
                        if m_type == "video":
                            image_url = m['media_url_https']
                            image_url_list.append(image_url)
                            variants = m['video_info']['variants']
                            bitrate = 0
                            for va in variants:
                                if va.get("content_type") == "video/mp4":
                                    if va.get("bitrate") > bitrate:
                                        bitrate = va.get("bitrate")
                                        video_url = va.get("url")
                                        video_url_list.append(video_url)
                        if m_type == "photo":
                            image_url = m['media_url_https']
                            image_url_list.append(image_url)
                        if m_type == "animated_gif":
                            image_url = m['media_url_https']
                            image_url_list.append(image_url)
                            variants = m['video_info']['variants']
                            bitrate = 0
                            for va in variants:
                                if va.get("content_type") == "video/mp4":
                                    if va.get("bitrate") > bitrate:
                                        bitrate = va.get("bitrate")
                                        video_url = va.get("url")
                                        video_url_list.append(video_url)
                except:
                    pass
                video_url = "; ".join(video_url_list)
                image_url = "; ".join(image_url_list)
                favorite_count = legacy.get('favorite_count')  # 点赞
                reply_count = legacy.get('reply_count')  # 回复
                retweet_count = legacy.get('retweet_count', 0)
                quote_count = legacy.get('quote_count', 0)
                lang = legacy.get('lang')
                u_legacy = core['user_results']['result']['legacy']
                is_blue_verified = "Yes" if core['user_results']['result']['is_blue_verified'] else "No"
                can_dm = "Yes" if core['user_results']['result']['dm_permissions']['can_dm'] else "No"
                can_media_tag = "Yes" if core['user_results']['result']['media_permissions']['can_media_tag'] else "No"
                is_yellow_verified = "Yes" if core['user_results']['result']['verification'].get('verified_type') else "No"
                hash_uname = core['user_results']['result']['core']['screen_name']
                profile_url = f"https://x.com/{hash_uname}"
                d_url = f"https://x.com/{hash_uname}/status/{id_str}"
                uname = core['user_results']['result']['core']['name']
                uid = core['user_results']['result']['rest_id']
                u_created_at = self.transTime(core['user_results']['result']['core'].get('created_at'))
                statuses_count = u_legacy.get('statuses_count')
                description = u_legacy['description']
                favourites_count = u_legacy.get('favourites_count')
                friends_count = u_legacy['friends_count']
                followers_count = u_legacy.get('followers_count')
                media_count = u_legacy['media_count']
                listed_count = u_legacy['listed_count']
                profile_banner_url = u_legacy.get('profile_banner_url', "-")
                profile_image_url = u_legacy.get('profile_image_url_https', '-')
                item = {
                    "TweetID":id_str,
                    "CreatedAt":created_at,
                    "TweetText":full_text,
                    "TweetURL":d_url,
                    "ReplyCount":reply_count,
                    "RetweetCount":retweet_count,
                    "QuoteCount":quote_count,
                    "LikeCount":favorite_count,
                    "ViewsCount":views_count,
                    "Language":lang,
                    "ImageURL":image_url,
                    "VideoURL":video_url,
                    "UserID":uid,
                    "UserHandle":hash_uname,
                    "UserName":uname,
                    "ProfileURL":profile_url,
                    "UserBio":description,
                    "AccountCreatedAt":u_created_at,
                    "StatusesCount":statuses_count,
                    "FavouritesCount":favourites_count,
                    "FriendsCount":friends_count,
                    "FollowersCount":followers_count,
                    "MediaCount":media_count,
                    "ListedCount":listed_count,
                    "IsBlueVerified":is_blue_verified,
                    "IsGoldVerified":is_yellow_verified,
                    "CanDM":can_dm,
                    "CanMediaTag":can_media_tag,
                    "ProfileBannerURL":profile_banner_url,
                    "ProfileImageURL":profile_image_url,
                    "Keyword":keyword
                }

                print(item)
                resultList.append(item)
            except Exception as e:
                print(f"Parsing error: {e}")

        return resultList

    def get_cursor(self, dataJson):
        instructions = dataJson['data']['search_by_raw_query']['search_timeline']['timeline']['instructions']
        entries = []
        cursor = None
        for ins in instructions:
            if ins.get('type') == "TimelineAddEntries":
                entries = ins.get('entries')
                for ent in entries:
                    cursorType = ent.get('content').get('cursorType')
                    if cursorType == 'Bottom':
                        cursor = ent.get('content').get('value')
                        break
        if not cursor:
            for ins in instructions:
                cursorType = ins.get('entry', {}).get('content', {}).get('cursorType')
                if cursorType == 'Bottom':
                    cursor = ins.get('entry').get('content').get('value')
                    break
        else:
            entries = entries[:-2]
        return cursor, entries
    def calxulate_date(self,date):
        p_datetime = datetime.datetime.strptime(date, "%Y-%m-%d %H:%M:%S")
        ts = int(datetime.datetime.timestamp(p_datetime))
        return ts

    def save_data(self, resultList):
        if resultList:
            df = pd.DataFrame(resultList)
            if not os.path.exists(f'./{self.saveFileName}.csv'):
                df.to_csv(f'./{self.saveFileName}.csv', index=False, mode='a', sep=",", encoding="utf_8_sig")
            else:
                df.to_csv(f'./{self.saveFileName}.csv', index=False, mode='a', sep=",", encoding="utf_8_sig",
                          header=False)
            print("Saved successfully")
    def run(self,keyword,since_time,endDatetime):
        cursor = "-1"
        searchCondition = f"{keyword} until_time:{endDatetime} since_time:{since_time}"
        with open("scrape_log.txt", 'w', encoding='utf-8') as f:
            f.write(f"{keyword}_{cursor}")
        resqJson = self.get(cursor, searchCondition)
        cursor, entries = self.get_cursor(resqJson)
        if entries:
            resultList = self.parse_data(entries, keyword)
            self.save_data(resultList)

    def main(self,start_date,end_date,keyword):
        start_date = start_date + " 00:00:00"
        end_date = end_date + " 23:59:59"
        end_date_ts = self.calxulate_date(end_date)
        while self.calxulate_date(start_date) < end_date_ts:
            start_date_ts = end_date_ts - (60*60*6)
            self.run(keyword,start_date_ts,end_date_ts)
            end_date_ts = start_date_ts
            time.sleep(random.randint(2, 3))

if __name__ == '__main__':
    #2018年3月 – 2018年8月，2019年5月-2019年10月，2024年4月-2024年7月
    ck_index = int(open('./cookie_index.txt',encoding='utf-8').read())
    saveFileName = "demo_post_36"
    cookie_strings = [cookie_str.strip() for cookie_str in open('./cookies.txt',encoding='utf-8').readlines() if cookie_str.strip()]
    ctks = TwitterKeywordSearchSpider(cookie_strings,saveFileName,ck_index)
    # 设置关键词
    keyword = "(#USChinaTrade OR #TradeNegotiations OR #ChinaUSTrade OR #TradeWar OR #Tariffs)"
    # 设置日期时间范围
    start_date = '2025-07-11'
    end_date = '2025-07-31'
    ctks.main(start_date, end_date, keyword)