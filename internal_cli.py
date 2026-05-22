#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
TikTok视频发布系统 - 内部命令行工具

仅供公司内部员工使用。

使用方法：
python internal_cli.py [命令]

命令：
  auth        - 获取TikTok授权
  upload      - 上传视频到TikTok收件箱
  publish     - 直接发布视频
  status      - 检查Token状态
  history     - 查看上传历史

环境变量：
  INTERNAL_API_KEY - 内部API密钥
  API_BASE_URL     - API服务地址，默认 http://localhost:5000/tiktok
"""

import os
import sys
import requests
import json

API_BASE_URL = os.environ.get('API_BASE_URL', 'http://localhost:8000/tiktok')
API_KEY = os.environ.get('INTERNAL_API_KEY', 'bebcare_internal_key_2026')

HEADERS = {
    'X-API-Key': API_KEY
}

def print_banner():
    print("=" * 60)
    print("  TikTok视频发布工具")
    print("=" * 60)

def cmd_auth():
    print("\n获取TikTok授权...")
    
    params = {'user_id': 'bebcare_internal'}
    
    try:
        response = requests.get(f"{API_BASE_URL}/auth/url", params=params, headers=HEADERS)
        if response.status_code == 200:
            data = response.json()
            print(f"授权URL: {data['auth_url']}")
            print("\n请复制以上URL到浏览器中完成授权")
            
            import webbrowser
            try:
                webbrowser.open(data['auth_url'])
                print("已自动打开浏览器")
            except:
                pass
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def cmd_upload():
    print("\n上传视频到TikTok收件箱")
    
    video_path = input("请输入视频文件路径: ").strip()
    
    if not os.path.exists(video_path):
        print(f"错误：文件不存在: {video_path}")
        return
    
    title = input("请输入视频标题 (可选): ").strip()
    description = input("请输入视频描述 (可选): ").strip()
    
    try:
        with open(video_path, 'rb') as f:
            files = {'video': (os.path.basename(video_path), f, 'video/mp4')}
            data = {
                'user_id': 'bebcare_internal',
                'title': title,
                'description': description
            }
            
            print("\n正在上传...")
            response = requests.post(f"{API_BASE_URL}/upload", files=files, data=data, headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ 上传成功!")
                print(f"  Publish ID: {result['publish_id']}")
                print(f"  状态: {result['status']}")
            else:
                print(f"\n✗ 上传失败: {response.text}")
    except Exception as e:
        print(f"\n✗ 上传失败: {e}")

def cmd_publish():
    print("\n直接发布视频到TikTok")
    
    video_path = input("请输入视频文件路径: ").strip()
    
    if not os.path.exists(video_path):
        print(f"错误：文件不存在: {video_path}")
        return
    
    title = input("请输入视频标题 (可选): ").strip()
    description = input("请输入视频描述 (可选): ").strip()
    
    print("\n隐私级别选项:")
    print("  1. PRIVATE (仅自己可见)")
    print("  2. SELF_ONLY (仅自己可见)")
    print("  3. MUTUAL_FOLLOW_FRIENDS (互相关注好友可见)")
    print("  4. PUBLIC_TO_EVERYONE (公开可见)")
    
    privacy_options = ['PRIVATE', 'SELF_ONLY', 'MUTUAL_FOLLOW_FRIENDS', 'PUBLIC_TO_EVERYONE']
    choice = input("请选择隐私级别 (1-4): ").strip()
    
    try:
        idx = int(choice) - 1
        privacy_level = privacy_options[idx]
    except:
        privacy_level = 'PRIVATE'
    
    print(f"\n选择的隐私级别: {privacy_level}")
    
    try:
        with open(video_path, 'rb') as f:
            files = {'video': (os.path.basename(video_path), f, 'video/mp4')}
            data = {
                'user_id': 'bebcare_internal',
                'title': title,
                'description': description,
                'privacy_level': privacy_level
            }
            
            print("\n正在发布...")
            response = requests.post(f"{API_BASE_URL}/publish", files=files, data=data, headers=HEADERS)
            
            if response.status_code == 200:
                result = response.json()
                print(f"\n✓ 发布成功!")
                print(f"  Publish ID: {result['publish_id']}")
                print(f"  状态: {result['status']}")
            else:
                print(f"\n✗ 发布失败: {response.text}")
    except Exception as e:
        print(f"\n✗ 发布失败: {e}")

def cmd_status():
    print("\n检查Token状态...")
    
    try:
        params = {'user_id': 'bebcare_internal'}
        response = requests.get(f"{API_BASE_URL}/status", params=params, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            status = result.get('status', 'unknown')
            is_valid = status == 'valid'
            print(f"\nToken状态: {'有效' if is_valid else '无效/过期'}")
            print(f"用户ID: {result.get('user_id', 'N/A')}")
            if result.get('expires_at'):
                print(f"过期时间: {result['expires_at']}")
            if result.get('created_at'):
                print(f"创建时间: {result['created_at']}")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def cmd_history():
    print("\n查看上传历史...")
    
    try:
        params = {'user_id': 'bebcare_internal'}
        response = requests.get(f"{API_BASE_URL}/history", params=params, headers=HEADERS)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n总记录数: {result['total']}")
            
            if result['total'] > 0:
                print("\n" + "-" * 80)
                print(f"{'时间':<20} {'视频':<30} {'Publish ID'}")
                print("-" * 80)
                
                for record in result['records']:
                    time = record['upload_time'][:19].replace('T', ' ')
                    video = os.path.basename(record['video_path'])
                    print(f"{time:<20} {video:<30} {record['publish_id']}")
            else:
                print("暂无上传记录")
        else:
            print(f"请求失败: {response.text}")
    except Exception as e:
        print(f"请求失败: {e}")

def cmd_help():
    print("\n使用方法:")
    print("  python internal_cli.py [命令]")
    print("\n命令列表:")
    print("  auth        - 获取TikTok授权")
    print("  upload      - 上传视频到TikTok收件箱")
    print("  publish     - 直接发布视频")
    print("  status      - 检查Token状态")
    print("  history     - 查看上传历史")
    print("  help        - 显示此帮助信息")
    print("\n环境变量:")
    print("  INTERNAL_API_KEY - 内部API密钥")
    print("  API_BASE_URL     - API服务地址")

def main():
    print_banner()
    
    if len(sys.argv) < 2:
        cmd_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'auth':
        cmd_auth()
    elif command == 'upload':
        cmd_upload()
    elif command == 'publish':
        cmd_publish()
    elif command == 'status':
        cmd_status()
    elif command == 'history':
        cmd_history()
    elif command == 'help':
        cmd_help()
    else:
        print(f"未知命令: {command}")
        cmd_help()

if __name__ == '__main__':
    main()
