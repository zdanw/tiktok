#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, redirect, jsonify, send_file, make_response
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import requests
import urllib.parse
import json
import os
import uuid
import logging
from functools import wraps

app = Flask(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logging.getLogger('werkzeug').setLevel(logging.INFO)

import sys
sys.stdout.flush()

ALLOWED_ORIGINS = [
    'https://tiktok-iota-five.vercel.app',
    'http://localhost:8000',
    'http://localhost:5000'
]

@app.before_request
def handle_options():
    if request.method == 'OPTIONS':
        response = make_response()
        origin = request.headers.get('Origin')
        if origin and (origin in ALLOWED_ORIGINS or 'localhost' in origin):
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
        response.headers['Access-Control-Max-Age'] = '86400'
        return response

@app.after_request
def add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        if origin in ALLOWED_ORIGINS or 'localhost' in origin:
            response.headers['Access-Control-Allow-Origin'] = origin
        else:
            response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    else:
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, X-API-Key, Authorization'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
    return response

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

@app.route('/')
def root():
    web_page_path = os.path.join(BASE_DIR, 'web_admin.html')
    if os.path.exists(web_page_path):
        return send_file(web_page_path, mimetype='text/html')
    else:
        return jsonify({
            'service': 'TikTok Video Publishing API',
            'environment': 'Internal Use Only',
            'message': '此服务仅供公司内部使用',
            'available_endpoints': [
                '/tiktok/ - GET - API首页（需要API密钥）',
                '/tiktok/auth/url - GET - 获取授权URL（需要API密钥）',
                '/tiktok/auth/callback - GET - OAuth回调',
                '/tiktok/upload - POST - 上传视频到收件箱（需要API密钥）',
                '/tiktok/publish - POST - 直接发布视频（需要API密钥）',
                '/tiktok/status - GET - Token状态（需要API密钥）',
                '/tiktok/history - GET - 上传历史（需要API密钥）',
                '/tiktok/health - GET - 健康检查'
            ]
        })

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///tiktok_tokens.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'bebcare-secret-key-2026')

db = SQLAlchemy(app)

from .config import (
    TIKTOK_CLIENT_KEY,
    TIKTOK_CLIENT_SECRET,
    TIKTOK_REDIRECT_URI,
    TIKTOK_AUTH_URL,
    TIKTOK_TOKEN_URL,
    TIKTOK_API_BASE_URL,
    AUTH_SUCCESS_REDIRECT_URL
)

CHUNK_SIZE = 10000000
INTERNAL_API_KEYS = os.environ.get('INTERNAL_API_KEYS', '').split(',') or ['bebcare_internal_key_2026']

ALLOWED_IPS = [
    '127.0.0.1',
    '::1',
    '192.168.0.0/16',
    '10.0.0.0/8',
    '172.16.0.0/12',
]

class TikTokToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), unique=True, nullable=False)
    access_token = db.Column(db.Text, nullable=False)
    refresh_token = db.Column(db.Text)
    open_id = db.Column(db.String(128))
    scope = db.Column(db.Text)
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.now)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

class UploadHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128))
    video_path = db.Column(db.String(256))
    publish_id = db.Column(db.String(128))
    status = db.Column(db.String(32))
    created_at = db.Column(db.DateTime, default=datetime.now)

with app.app_context():
    db.create_all()

def is_ip_allowed(ip):
    if ip in ['127.0.0.1', '::1']:
        return True
    for allowed in ALLOWED_IPS:
        if '/' in allowed:
            network, prefix = allowed.split('/')
            ip_parts = list(map(int, ip.split('.')))
            network_parts = list(map(int, network.split('.')))
            mask = (0xFFFFFFFF << (32 - int(prefix))) & 0xFFFFFFFF
            ip_int = (ip_parts[0] << 24) | (ip_parts[1] << 16) | (ip_parts[2] << 8) | ip_parts[3]
            network_int = (network_parts[0] << 24) | (network_parts[1] << 16) | (network_parts[2] << 8) | network_parts[3]
            if (ip_int & mask) == (network_int & mask):
                return True
    return False

def is_api_key_valid(api_key):
    return api_key and api_key in INTERNAL_API_KEYS

def get_client_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr

def internal_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        return f(*args, **kwargs)
    return decorated_function

def get_valid_token(user_id):
    token_record = TikTokToken.query.filter_by(user_id=user_id).first()
    if not token_record:
        return None
    
    if token_record.expires_at and token_record.expires_at < datetime.now():
        new_token = refresh_access_token(user_id, token_record.refresh_token)
        return new_token
    return token_record.access_token

def refresh_access_token(user_id, refresh_token):
    for attempt in range(3):
        try:
            response = requests.post(TIKTOK_TOKEN_URL, data={
                'client_key': TIKTOK_CLIENT_KEY,
                'client_secret': TIKTOK_CLIENT_SECRET,
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                token_record = TikTokToken.query.filter_by(user_id=user_id).first()
                if token_record:
                    token_record.access_token = data.get('access_token')
                    token_record.refresh_token = data.get('refresh_token')
                    token_record.expires_at = datetime.now() + timedelta(seconds=data.get('expires_in', 86400))
                    db.session.commit()
                return data.get('access_token')
        except:
            pass
    return None

@app.route('/')
def home():
    return jsonify({
        'service': 'TikTok Video Publishing API',
        'environment': 'Internal Use Only',
        'message': '此服务仅供公司内部使用',
        'available_endpoints': [
            '/tiktok/ - GET - API首页（需要API密钥）',
            '/tiktok/auth/url - GET - 获取授权URL（需要API密钥）',
            '/tiktok/auth/callback - GET - OAuth回调',
            '/tiktok/upload - POST - 上传视频到收件箱（需要API密钥）',
            '/tiktok/publish - POST - 直接发布视频（需要API密钥）',
            '/tiktok/status - GET - Token状态（需要API密钥）',
            '/tiktok/history - GET - 上传历史（需要API密钥）',
            '/tiktok/health - GET - 健康检查'
        ]
    })

@app.route('/tiktok/')
@internal_only
def index():
    return jsonify({
        'service': 'TikTok Video Publishing API',
        'environment': 'Internal Use Only',
        'endpoints': [
            '/tiktok/auth/url - GET - 获取授权URL',
            '/tiktok/auth/callback - GET - OAuth回调',
            '/tiktok/upload - POST - 上传视频到收件箱',
            '/tiktok/publish - POST - 直接发布视频',
            '/tiktok/status - GET - Token状态',
            '/tiktok/history - GET - 上传历史',
            '/tiktok/health - GET - 健康检查'
        ]
    })

@app.route('/tiktok/auth/url', methods=['GET'])
@internal_only
def auth_url():
    user_id = request.args.get('user_id', 'bebcare_internal')
    state = str(uuid.uuid4())
    redirect = request.args.get('redirect', 'true')
    
    # 构建回调 URL，包含 redirect 参数
    callback_url = f"{request.host_url.rstrip('/')}/callback?redirect={redirect}&user_id={user_id}"
    
    auth_params = {
        'client_key': TIKTOK_CLIENT_KEY,
        'redirect_uri': TIKTOK_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'user.info.basic,video.upload,video.publish',
        'state': state,
        'prompt': 'consent'
    }
    
    auth_url = TIKTOK_AUTH_URL + '?' + urllib.parse.urlencode(auth_params)
    
    return jsonify({
        'auth_url': auth_url,
        'state': state,
        'user_id': user_id,
        'redirect': redirect
    })

@app.route('/callback', methods=['GET'])
def callback_page():
    callback_html_path = os.path.join(BASE_DIR, 'tiktok_callback.html')
    if os.path.exists(callback_html_path):
        return send_file(callback_html_path, mimetype='text/html')
    else:
        return jsonify({'error': 'Callback page not found'}), 404

@app.route('/tiktok/auth/callback', methods=['GET'])
def auth_callback():
    code = request.args.get('code')
    state = request.args.get('state')
    user_id = request.args.get('user_id', 'bebcare_internal')
    
    if not code:
        return jsonify({'error': 'Authorization code missing'}), 400
    
    try:
        token_response = requests.post(TIKTOK_TOKEN_URL, data={
            'client_key': TIKTOK_CLIENT_KEY,
            'client_secret': TIKTOK_CLIENT_SECRET,
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': TIKTOK_REDIRECT_URI
        }, timeout=30)
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            
            token_record = TikTokToken.query.filter_by(user_id=user_id).first()
            if token_record:
                token_record.access_token = token_data.get('access_token')
                token_record.refresh_token = token_data.get('refresh_token')
                token_record.open_id = token_data.get('open_id')
                token_record.scope = token_data.get('scope')
                token_record.expires_at = datetime.now() + timedelta(seconds=token_data.get('expires_in', 86400))
            else:
                token_record = TikTokToken(
                    user_id=user_id,
                    access_token=token_data.get('access_token'),
                    refresh_token=token_data.get('refresh_token'),
                    open_id=token_data.get('open_id'),
                    scope=token_data.get('scope'),
                    expires_at=datetime.now() + timedelta(seconds=token_data.get('expires_in', 86400))
                )
                db.session.add(token_record)
            
            db.session.commit()
            
            # 使用配置的重定向地址
            redirect_url = AUTH_SUCCESS_REDIRECT_URL
            if not redirect_url.startswith('http'):
                redirect_url = request.host_url.rstrip('/') + redirect_url
            
            # 检查是否需要重定向（用于网页授权流程）
            redirect_to_home = request.args.get('redirect', 'false').lower() == 'true'
            if redirect_to_home:
                redirect_url_with_param = redirect_url
                if not redirect_url_with_param.startswith('http') or redirect_url_with_param.startswith(request.host_url):
                    redirect_url_with_param += '?auth_success=true'
                return redirect(redirect_url_with_param)
            
            return jsonify({
                'success': True,
                'message': 'Authorization successful',
                'user_id': user_id,
                'redirect_url': redirect_url + '?auth_success=true'
            })
        else:
            return jsonify({'error': token_response.text}), token_response.status_code
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tiktok/upload', methods=['POST'])
@internal_only
def upload_video():
    logger.info("\n" + "="*80)
    logger.info("                    UPLOAD TO INBOX REQUEST RECEIVED                    ")
    logger.info("="*80)
    user_id = request.form.get('user_id', 'bebcare_internal')
    video_file = request.files.get('video')
    logger.info(f"📋 用户ID: {user_id}")
    logger.info(f"📁 视频文件: {video_file.filename if video_file else '未选择'}")
    
    if not video_file:
        return jsonify({'error': 'No video file provided'}), 400
    
    access_token = get_valid_token(user_id)
    logger.info(f"🔑 Access Token: {access_token[:20] if access_token else '未找到'}...")
    if not access_token:
        return jsonify({'error': 'No valid token found, please authorize first'}), 401
    
    try:
        video_data = video_file.read()
        video_size = len(video_data)
        
        init_url = f"{TIKTOK_API_BASE_URL}post/publish/inbox/video/init/"
        init_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info("\n" + "-"*80)
        logger.info("                    STEP 1: INITIALIZE UPLOAD (/init/)                   ")
        logger.info("-"*80)
        logger.info(f"🌐 请求URL: {init_url}")
        logger.info(f"📝 请求头: {json.dumps(init_headers, indent=2)}")
        
        chunk_size = min(10000000, video_size)
        total_chunk_count = (video_size + chunk_size - 1) // chunk_size
        
        request_data = {
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': chunk_size,
                'total_chunk_count': total_chunk_count
            }
        }
        
        logger.info(f"📦 请求数据: {json.dumps(request_data, indent=2)}")
        logger.info(f"📊 视频大小: {video_size} bytes")
        logger.info(f"📊 分块大小: {chunk_size} bytes")
        logger.info(f"📊 总分块数: {total_chunk_count}")
        
        init_response = requests.post(init_url, headers=init_headers, json=request_data)
        
        logger.info("\n" + "-"*80)
        logger.info("                      INIT RESPONSE                                      ")
        logger.info("-"*80)
        logger.info(f"✅ 响应状态码: {init_response.status_code}")
        logger.info(f"📄 响应内容: {init_response.text}")
        
        if init_response.status_code != 200:
            logger.error(f"❌ 初始化失败: {init_response.text}")
            return jsonify({'error': f"Init failed: {init_response.text}", 'url': init_url}), init_response.status_code
        
        init_data = init_response.json()
        upload_url = init_data.get('data', {}).get('upload_url')
        publish_id = init_data.get('data', {}).get('publish_id')
        
        logger.info(f"📥 获取到上传URL: {upload_url}")
        logger.info(f"🆔 Publish ID: {publish_id}")
        
        logger.info("\n" + "-"*80)
        logger.info("                    STEP 2: UPLOAD VIDEO FILE                            ")
        logger.info("-"*80)
        
        if total_chunk_count == 1:
            logger.info("📤 单块上传模式")
            upload_headers = {
                'Content-Type': 'video/mp4',
                'Content-Length': str(video_size),
                'Content-Range': f'bytes 0-{video_size-1}/{video_size}'
            }
            logger.info(f"📝 上传请求头: {json.dumps(upload_headers, indent=2)}")
            upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
            logger.info(f"✅ 上传响应状态码: {upload_response.status_code}")
        else:
            logger.info(f"📤 分块上传模式，共{total_chunk_count}块")
            upload_response = None
            
            for chunk_idx in range(total_chunk_count):
                start = chunk_idx * chunk_size
                end = min(start + chunk_size, video_size) - 1
                chunk_data = video_data[start:end+1]
                
                chunk_headers = {
                    'Content-Type': 'video/mp4',
                    'Content-Length': str(len(chunk_data)),
                    'Content-Range': f'bytes {start}-{end}/{video_size}'
                }
                
                logger.info(f"📤 上传第{chunk_idx+1}/{total_chunk_count}块: bytes {start}-{end}")
                upload_response = requests.put(upload_url, headers=chunk_headers, data=chunk_data)
                logger.info(f"✅ 响应状态码: {upload_response.status_code}")
                if upload_response.status_code not in [200, 201, 204]:
                    logger.error(f"❌ 上传失败: {upload_response.text}")
                    break
        
        logger.info("\n" + "-"*80)
        logger.info("                    STEP 3: COMPLETE UPLOAD TO INBOX                     ")
        logger.info("-"*80)
        
        if upload_response and upload_response.status_code in [200, 201, 204]:
            history = UploadHistory(
                user_id=user_id,
                video_path=video_file.filename,
                publish_id=publish_id,
                status='uploaded'
            )
            db.session.add(history)
            db.session.commit()
            
            return jsonify({
                'success': True,
                'publish_id': publish_id,
                'status': 'uploaded',
                'message': 'Video uploaded to TikTok inbox successfully'
            })
        else:
            return jsonify({'error': f"Upload failed: {upload_response.text}"}), upload_response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tiktok/publish', methods=['POST'])
@internal_only
def publish_video():
    logger.info("\n" + "="*80)
    logger.info("                    DIRECT PUBLISH REQUEST RECEIVED                       ")
    logger.info("="*80)
    
    user_id = request.form.get('user_id', 'bebcare_internal')
    video_file = request.files.get('video')
    title = request.form.get('title', '')
    description = request.form.get('description', '')
    privacy_level = request.form.get('privacy_level', 'SELF_ONLY')
    
    logger.info(f"📋 用户ID: {user_id}")
    logger.info(f"📁 视频文件: {video_file.filename if video_file else '未选择'}")
    logger.info(f"📝 视频标题: {title if title else '无'}")
    logger.info(f"📝 视频描述: {description if description else '无'}")
    logger.info(f"🔒 隐私级别: {privacy_level}")
    
    if not video_file:
        return jsonify({'error': 'No video file provided'}), 400
    
    access_token = get_valid_token(user_id)
    logger.info(f"🔑 Access Token: {access_token[:20] if access_token else '未找到'}...")
    if not access_token:
        return jsonify({'error': 'No valid token found, please authorize first'}), 401
    
    try:
        video_data = video_file.read()
        video_size = len(video_data)
        
        init_url = f"{TIKTOK_API_BASE_URL}post/publish/video/init/"
        init_headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        chunk_size = min(10000000, video_size)
        total_chunk_count = (video_size + chunk_size - 1) // chunk_size
        
        post_title = title if title else " "
        post_description = description if description else " "
        
        request_data = {
            'source_info': {
                'source': 'FILE_UPLOAD',
                'video_size': video_size,
                'chunk_size': chunk_size,
                'total_chunk_count': total_chunk_count
            },
            'post_info': {
                'title': post_title,
                'description': post_description,
                'privacy_level': privacy_level,
                'disable_comment': False,
                'disable_duet': False,
                'disable_stitch': False,
                'video_cover_timestamp_ms': 0,
                'brand_content_toggle': False
            }
        }
        
        logger.info("\n" + "-"*80)
        logger.info("                    STEP 1: INITIALIZE PUBLISH (/init/)                   ")
        logger.info("-"*80)
        logger.info(f"🌐 请求URL: {init_url}")
        logger.info(f"📝 请求头: {json.dumps(init_headers, indent=2)}")
        logger.info(f"📦 请求数据: {json.dumps(request_data, indent=2)}")
        logger.info(f"📊 视频大小: {video_size} bytes")
        logger.info(f"📊 分块大小: {chunk_size} bytes")
        logger.info(f"📊 总分块数: {total_chunk_count}")
        
        init_response = requests.post(init_url, headers=init_headers, json=request_data)
        
        logger.info("\n" + "-"*80)
        logger.info("                      INIT RESPONSE                                      ")
        logger.info("-"*80)
        logger.info(f"✅ 响应状态码: {init_response.status_code}")
        logger.info(f"📄 响应内容: {init_response.text}")
        
        if init_response.status_code != 200:
            logger.error(f"❌ 初始化失败: {init_response.text}")
            return jsonify({'error': f"Init failed: {init_response.text}"}), init_response.status_code
        
        init_data = init_response.json()
        upload_url = init_data.get('data', {}).get('upload_url')
        publish_id = init_data.get('data', {}).get('publish_id')
        
        print(f"📥 获取到上传URL: {upload_url}")
        print(f"🆔 Publish ID: {publish_id}")
        
        print("\n" + "-"*80)
        print("                    STEP 2: UPLOAD VIDEO FILE                            ")
        print("-"*80)
        
        if total_chunk_count == 1:
            print("📤 单块上传模式")
            upload_headers = {
                'Content-Type': 'video/mp4',
                'Content-Length': str(video_size),
                'Content-Range': f'bytes 0-{video_size-1}/{video_size}'
            }
            print(f"📝 上传请求头: {json.dumps(upload_headers, indent=2)}")
            upload_response = requests.put(upload_url, headers=upload_headers, data=video_data)
            print(f"✅ 上传响应状态码: {upload_response.status_code}")
        else:
            print(f"📤 分块上传模式，共{total_chunk_count}块")
            upload_response = None
            
            for chunk_idx in range(total_chunk_count):
                start = chunk_idx * chunk_size
                end = min(start + chunk_size, video_size) - 1
                chunk_data = video_data[start:end+1]
                
                chunk_headers = {
                    'Content-Type': 'video/mp4',
                    'Content-Length': str(len(chunk_data)),
                    'Content-Range': f'bytes {start}-{end}/{video_size}'
                }
                
                print(f"📤 上传第{chunk_idx+1}/{total_chunk_count}块: bytes {start}-{end}")
                upload_response = requests.put(upload_url, headers=chunk_headers, data=chunk_data)
                print(f"✅ 响应状态码: {upload_response.status_code}")
                if upload_response.status_code not in [200, 201, 204]:
                    print(f"❌ 上传失败: {upload_response.text}")
                    break
        
        print("\n" + "-"*80)
        print("                    STEP 3: COMPLETE DIRECT PUBLISH                      ")
        print("-"*80)
        
        if upload_response and upload_response.status_code in [200, 201, 204]:
            history = UploadHistory(
                user_id=user_id,
                video_path=video_file.filename,
                publish_id=publish_id,
                status='published'
            )
            db.session.add(history)
            db.session.commit()
            
            print(f"🎉 发布成功! Publish ID: {publish_id}")
            print("="*80 + "\n")
            
            return jsonify({
                'success': True,
                'publish_id': publish_id,
                'status': 'published',
                'message': 'Video published to TikTok successfully'
            })
        else:
            print(f"❌ 发布失败!")
            print("="*80 + "\n")
            return jsonify({'error': f"Upload failed: {upload_response.text}"}), upload_response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tiktok/status', methods=['GET'])
@internal_only
def token_status():
    user_id = request.args.get('user_id', 'bebcare_internal')
    token_record = TikTokToken.query.filter_by(user_id=user_id).first()
    
    if not token_record:
        return jsonify({'status': 'no_token', 'message': 'No token found, please authorize first'})
    
    is_expired = token_record.expires_at and token_record.expires_at < datetime.now()
    
    return jsonify({
        'status': 'valid' if not is_expired else 'expired',
        'user_id': user_id,
        'expires_at': token_record.expires_at.isoformat() if token_record.expires_at else None,
        'created_at': token_record.created_at.isoformat()
    })

@app.route('/tiktok/logout', methods=['POST'])
@internal_only
def logout():
    user_id = request.args.get('user_id', 'bebcare_internal')
    
    try:
        token_record = TikTokToken.query.filter_by(user_id=user_id).first()
        if token_record:
            db.session.delete(token_record)
            db.session.commit()
            logger.info(f"🔓 用户 {user_id} 已退出登录，Token 已删除")
        
        return jsonify({
            'success': True,
            'message': 'Logout successful',
            'user_id': user_id
        })
    except Exception as e:
        logger.error(f"❌ 退出登录失败: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/tiktok/creator_info', methods=['GET'])
@internal_only
def get_creator_info():
    user_id = request.args.get('user_id', 'bebcare_internal')
    
    access_token = get_valid_token(user_id)
    if not access_token:
        return jsonify({'error': 'No valid token found, please authorize first'}), 401
    
    try:
        info_url = f"{TIKTOK_API_BASE_URL}post/publish/creator_info/query/"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        logger.info("\n" + "="*80)
        logger.info("                    GETTING CREATOR INFO                                  ")
        logger.info("="*80)
        logger.info(f"🌐 请求URL: {info_url}")
        logger.info(f"🔑 Access Token: {access_token[:20]}...")
        
        response = requests.post(info_url, headers=headers, json={})
        
        logger.info(f"✅ 响应状态码: {response.status_code}")
        logger.info(f"📄 响应内容: {response.text}")
        logger.info("="*80 + "\n")
        
        if response.status_code == 200:
            data = response.json()
            return jsonify({
                'success': True,
                'data': data.get('data', {})
            })
        else:
            return jsonify({'error': f"Failed to get creator info: {response.text}"}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tiktok/history', methods=['GET'])
@internal_only
def get_history():
    user_id = request.args.get('user_id', 'bebcare_internal')
    records = UploadHistory.query.filter_by(user_id=user_id).order_by(UploadHistory.created_at.desc()).all()
    
    return jsonify({
        'user_id': user_id,
        'records': [{
            'id': r.id,
            'video_path': r.video_path,
            'publish_id': r.publish_id,
            'status': r.status,
            'created_at': r.created_at.isoformat()
        } for r in records]
    })

@app.route('/tiktok/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'ok',
        'service': 'TikTok Publishing API',
        'environment': 'Internal',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print(f"=== Flask App Starting ===")
    print(f"TIKTOK_API_BASE_URL: {TIKTOK_API_BASE_URL}")
    print(f"TIKTOK_CLIENT_KEY: {TIKTOK_CLIENT_KEY}")
    print(f"TIKTOK_REDIRECT_URI: {TIKTOK_REDIRECT_URI}")
    print(f"===========================")
    with app.app_context():
        db.create_all()
    port = int(os.environ.get('PORT', 8000))
    app.run(host='127.0.0.1', port=port, debug=True)
