#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TikTok视频发布系统 - 配置文件

此文件包含项目的所有配置参数，包括API密钥等。
配置项采用环境变量优先的策略，便于生产环境部署。
"""

import os

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

dotenv_path = os.path.join(BASE_DIR, '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)

# ==================== TikTok API配置 ====================
TIKTOK_CLIENT_KEY = os.environ.get('TIKTOK_CLIENT_KEY', 'sbawpsx2c0ozgfc1hk')
TIKTOK_CLIENT_SECRET = os.environ.get('TIKTOK_CLIENT_SECRET', '0ov7gg7gF3krD3OmvdrPTTvypUwLFrHo')

# ==================== TikTok OAuth配置 ====================
TIKTOK_REDIRECT_URI = os.environ.get(
    'TIKTOK_REDIRECT_URI',
    
)

TIKTOK_AUTH_URL = os.environ.get('TIKTOK_AUTH_URL', "https://www.tiktok.com/v2/auth/authorize/")

TIKTOK_TOKEN_URL = os.environ.get('TIKTOK_TOKEN_URL', "https://open.tiktokapis.com/v2/oauth/token/")
TIKTOK_API_BASE_URL = os.environ.get('TIKTOK_API_BASE_URL', "https://open.tiktokapis.com/v2/")

# ==================== 授权成功后重定向配置 ====================
# 授权成功后重定向到的页面（可以修改为其他地址）
AUTH_SUCCESS_REDIRECT_URL = os.environ.get('AUTH_SUCCESS_REDIRECT_URL', 'https://tiktokcallback.bebcare.com')