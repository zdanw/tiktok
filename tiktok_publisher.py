#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TikTok发布模块

实现TikTok OAuth 2.0授权流程和视频上传发布功能。

主要功能：
1. 生成授权URL（OAuth 2.0授权码流程）
2. 获取Access Token（使用授权码交换）
3. 刷新Access Token
4. 上传视频到TikTok收件箱
5. 直接发布视频
6. 检查发布状态
"""

import requests
import json
import urllib.parse
import os
import time
from config import (
    TIKTOK_CLIENT_KEY,
    TIKTOK_CLIENT_SECRET,
    TIKTOK_REDIRECT_URI,
    TIKTOK_AUTH_URL,
    TIKTOK_TOKEN_URL,
    TIKTOK_API_BASE_URL
)


class TikTokPublisher:
    """
    TikTok视频发布器

    实现TikTok API的OAuth授权和视频上传功能。
    """

    # TikTok API 分块大小（十进制字节）
    CHUNK_SIZE = 10000000

    def __init__(self):
        """初始化发布器"""
        self.client_key = TIKTOK_CLIENT_KEY
        self.client_secret = TIKTOK_CLIENT_SECRET
        self.redirect_uri = TIKTOK_REDIRECT_URI
        self.auth_url = TIKTOK_AUTH_URL
        self.token_url = TIKTOK_TOKEN_URL
        self.api_base_url = TIKTOK_API_BASE_URL

        self.access_token = None
        self.refresh_token = None
        self.open_id = None

    def get_auth_url(self, scopes=None, state=None):
        """
        生成TikTok授权URL

        Args:
            scopes (list): 授权范围列表，默认为[user.info.basic, video.upload, video.publish]
            state (str): 防CSRF攻击的状态值，默认为随机生成

        Returns:
            str: 完整的授权URL
        """
        import uuid

        if scopes is None:
            scopes = ["user.info.basic", "video.upload", "video.publish"]

        if state is None:
            state = str(uuid.uuid4())

        params = {
            "client_key": self.client_key,
            "redirect_uri": self.redirect_uri,
            "response_type": "code",
            "scope": ",".join(scopes),
            "state": state,
            "prompt": "consent"
        }

        url = self.auth_url + "?" + urllib.parse.urlencode(params)
        return url

    def get_access_token(self, auth_code, max_retries=3, timeout=30):
        """
        使用授权码换取Access Token

        Args:
            auth_code (str): OAuth授权码
            max_retries (int): 最大重试次数
            timeout (int): 请求超时时间（秒）

        Returns:
            dict|None: Token响应数据，包含access_token等信息；失败返回None
        """
        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "code": auth_code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        for attempt in range(max_retries):
            try:
                print(f"正在请求Token (attempt {attempt + 1}/{max_retries}): {self.token_url}")

                response = requests.post(self.token_url, data=data, headers=headers, timeout=timeout)

                print(f"响应状态码: {response.status_code}")
                print(f"响应内容: {response.text}")

                response.raise_for_status()
                result = response.json()

                if 'access_token' in result:
                    self.access_token = result['access_token']
                    self.refresh_token = result.get('refresh_token')
                    self.open_id = result.get('open_id')
                    return result

                return None

            except Exception as e:
                print(f"获取Access Token失败 (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    print(f"等待2秒后重试...")
                    time.sleep(2)

        return None

    def refresh_access_token(self, max_retries=3, timeout=30):
        """
        使用Refresh Token刷新Access Token

        Args:
            max_retries (int): 最大重试次数
            timeout (int): 请求超时时间（秒）

        Returns:
            dict|None: 新的Token响应数据，失败返回None
        """
        if not self.refresh_token:
            return None

        data = {
            "client_key": self.client_key,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }

        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }

        for attempt in range(max_retries):
            try:
                response = requests.post(self.token_url, data=data, headers=headers, timeout=timeout)
                response.raise_for_status()
                result = response.json()

                if 'access_token' in result:
                    self.access_token = result['access_token']
                    self.refresh_token = result.get('refresh_token')
                    return result

                return None

            except Exception as e:
                print(f"刷新Access Token失败 (attempt {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2)

        return None

    def get_creator_info(self):
        """
        获取创作者信息

        Returns:
            dict|None: 创作者信息，失败返回None
        """
        if not self.access_token:
            print("请先获取Access Token")
            return None

        url = self.api_base_url + "post/publish/creator_info/query/"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        try:
            response = requests.post(url, headers=headers, json={})
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"获取创作者信息失败: {e}")
            print(f"响应内容: {response.text if 'response' in dir() else 'N/A'}")
            return None

    def upload_video_to_inbox(self, video_path, title="", description=""):
        """
        上传视频到TikTok收件箱（草稿箱）

        Args:
            video_path (str): 视频文件路径
            title (str): 视频标题
            description (str): 视频描述

        Returns:
            dict|None: 上传结果，包含publish_id和status；失败返回None
        """
        if not self.access_token:
            print("请先获取Access Token")
            return None

        video_size = os.path.getsize(video_path)

        url = self.api_base_url + "post/publish/inbox/video/init/"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        chunk_size = min(self.CHUNK_SIZE, video_size)
        total_chunk_count = (video_size + chunk_size - 1) // chunk_size

        data = {
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count
            }
        }

        try:
            print(f"正在初始化视频上传: {url}")
            print(f"请求数据: {json.dumps(data)}")

            response = requests.post(url, headers=headers, json=data)
            print(f"初始化响应状态码: {response.status_code}")
            print(f"初始化响应内容: {response.text}")
            response.raise_for_status()
            init_result = response.json()

            if 'data' in init_result and 'upload_url' in init_result['data']:
                upload_url = init_result['data']['upload_url']
                publish_id = init_result['data']['publish_id']
                print(f"视频上传URL获取成功，upload_url: {upload_url}")

                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()

                total_size = len(video_data)

                if total_chunk_count == 1:
                    upload_headers = {
                        'Content-Type': 'video/mp4',
                        'Content-Length': str(total_size),
                        'Content-Range': f'bytes 0-{total_size-1}/{total_size}'
                    }
                    print(f"上传视频 (1 chunk): {total_size} bytes")
                    upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
                else:
                    upload_response = None
                    for chunk_idx in range(total_chunk_count):
                        start = chunk_idx * chunk_size
                        end = min(start + chunk_size, total_size) - 1
                        chunk_data = video_data[start:end+1]

                        upload_headers = {
                            'Content-Type': 'video/mp4',
                            'Content-Length': str(len(chunk_data)),
                            'Content-Range': f'bytes {start}-{end}/{total_size}'
                        }

                        print(f"上传分块 {chunk_idx+1}/{total_chunk_count}: {len(chunk_data)} bytes")
                        upload_response = requests.put(upload_url, headers=upload_headers, data=chunk_data)

                        if upload_response.status_code not in [200, 201, 204]:
                            print(f"分块 {chunk_idx+1} 上传失败")
                            break

                if upload_response and upload_response.status_code in [200, 201, 204]:
                    print("视频上传完成")
                    return {
                        "publish_id": publish_id,
                        "status": "uploaded"
                    }
                else:
                    print(f"视频上传失败: {upload_response.text if upload_response else 'Unknown error'}")
                    return None

            else:
                print(f"初始化上传失败: {init_result}")
                return None

        except Exception as e:
            print(f"上传视频失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def publish_video_direct(self, video_path, title="", description="", privacy_level="PUBLIC_TO_EVERYONE"):
        """
        直接发布视频（不需要先上传到收件箱）

        Args:
            video_path (str): 视频文件路径
            title (str): 视频标题
            description (str): 视频描述
            privacy_level (str): 隐私级别，默认为PUBLIC_TO_EVERYONE

        Returns:
            dict|None: 发布结果，包含publish_id和status；失败返回None
        """
        if not self.access_token:
            print("请先获取Access Token")
            return None

        video_size = os.path.getsize(video_path)

        url = self.api_base_url + "post/publish/video/init/"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        post_info = {
            "title": title if title else "",
            "description": description,
            "privacy_level": privacy_level,
            "disable_comment": False,
            "disable_duet": False,
            "disable_stitch": False,
            "video_cover_timestamp_ms": 0,
            "brand_content_toggle": False
        }

        chunk_size = min(self.CHUNK_SIZE, video_size)
        total_chunk_count = (video_size + chunk_size - 1) // chunk_size

        data = {
            "post_info": post_info,
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": total_chunk_count
            }
        }

        try:
            print(f"正在初始化视频发布: {url}")
            print(f"请求数据: {json.dumps(data)}")

            response = requests.post(url, headers=headers, json=data)
            print(f"初始化响应状态码: {response.status_code}")
            print(f"初始化响应内容: {response.text}")
            response.raise_for_status()
            init_result = response.json()

            if 'data' in init_result and 'upload_url' in init_result['data']:
                upload_url = init_result['data']['upload_url']
                publish_id = init_result['data']['publish_id']
                print(f"视频上传URL获取成功，upload_url: {upload_url}")

                with open(video_path, 'rb') as video_file:
                    video_data = video_file.read()

                total_size = len(video_data)

                if total_chunk_count == 1:
                    upload_headers = {
                        'Content-Type': 'video/mp4',
                        'Content-Length': str(total_size),
                        'Content-Range': f'bytes 0-{total_size-1}/{total_size}'
                    }
                    print(f"上传视频 (1 chunk): {total_size} bytes")
                    upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
                else:
                    upload_response = None
                    for chunk_idx in range(total_chunk_count):
                        start = chunk_idx * chunk_size
                        end = min(start + chunk_size, total_size) - 1
                        chunk_data = video_data[start:end+1]

                        upload_headers = {
                            'Content-Type': 'video/mp4',
                            'Content-Length': str(len(chunk_data)),
                            'Content-Range': f'bytes {start}-{end}/{total_size}'
                        }

                        print(f"上传分块 {chunk_idx+1}/{total_chunk_count}: {len(chunk_data)} bytes")
                        upload_response = requests.put(upload_url, headers=upload_headers, data=chunk_data)

                        if upload_response.status_code not in [200, 201, 204]:
                            print(f"分块 {chunk_idx+1} 上传失败")
                            break

                if upload_response and upload_response.status_code in [200, 201, 204]:
                    print("视频上传完成")
                    status_result = self.check_post_status(publish_id)
                    if status_result:
                        status = status_result.get('data', {}).get('status', 'unknown')
                        return {
                            "publish_id": publish_id,
                            "status": status
                        }
                    return {
                        "publish_id": publish_id,
                        "status": "uploaded"
                    }
                else:
                    print(f"视频上传失败: {upload_response.text if upload_response else 'Unknown error'}")
                    return None

            else:
                print(f"初始化发布失败: {init_result}")
                return None

        except Exception as e:
            print(f"发布视频失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def check_post_status(self, publish_id):
        """
        检查视频发布状态

        Args:
            publish_id (str): 发布ID

        Returns:
            dict|None: 发布状态信息，失败返回None
        """
        if not self.access_token:
            print("请先获取Access Token")
            return None

        url = self.api_base_url + "post/publish/status/fetch/"

        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json; charset=UTF-8"
        }

        data = {
            "publish_id": publish_id
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            print(f"获取发布状态失败: {e}")
            print(f"响应内容: {response.text if 'response' in dir() else 'N/A'}")
            return None

    def upload_and_publish(self, video_path, caption_data):
        """
        上传并发布视频（默认上传到收件箱）

        Args:
            video_path (str): 视频文件路径
            caption_data (dict): 文案数据

        Returns:
            dict|None: 上传结果
        """
        result = self.upload_video_to_inbox(
            video_path,
            title=caption_data.get('title', ''),
            description=caption_data.get('script', '')
        )

        return result