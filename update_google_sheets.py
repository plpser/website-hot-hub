# -*- coding: utf-8 -*-
"""
将 README.md 内容追加写入 Google Sheets 的脚本
"""

import os
import re
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

def parse_readme_content(readme_content):
    """解析 README.md 内容，提取各平台的热点数据"""
    platforms = {}
    
    # 定义平台标识和对应的正则表达式
    platform_patterns = {
        '36KR': r'<!-- BEGIN 36KR -->(.*?)<!-- END 36KR -->',
        'BILIBILI': r'<!-- BEGIN BILIBILI -->(.*?)<!-- END BILIBILI -->',
        'GITHUB': r'<!-- BEGIN GITHUB -->(.*?)<!-- END GITHUB -->',
        'DOUYIN': r'<!-- BEGIN DOUYIN -->(.*?)<!-- END DOUYIN -->',
        'JUEJIN': r'<!-- BEGIN JUEJIN -->(.*?)<!-- END JUEJIN -->',
        'SSPAI': r'<!-- BEGIN SSPAI -->(.*?)<!-- END SSPAI -->',
        'WEREAD': r'<!-- BEGIN WEREAD -->(.*?)<!-- END WEREAD -->',
        'KUAISHOU': r'<!-- BEGIN KUAISHOU -->(.*?)<!-- END KUAISHOU -->'
    }
    
    for platform, pattern in platform_patterns.items():
        match = re.search(pattern, readme_content, re.DOTALL)
        if match:
            content = match.group(1)
            # 提取更新时间
            time_match = re.search(r'<!-- 最后更新时间 (.*?) -->', content)
            update_time = time_match.group(1) if time_match else '未知'
            
            # 提取热点条目
            items = []
            # 使用更精确的正则表达式匹配条目
            item_pattern = r'\d+\.\s*(\[[^\]]+\]\([^)]+\)|[^\n]+)'
            item_matches = re.findall(item_pattern, content)
            
            for match in item_matches:
                if match.startswith('['):
                    # 链接格式: [title](url)
                    title_match = re.search(r'\[([^\]]+)\]', match)
                    url_match = re.search(r'\(([^)]+)\)', match)
                    if title_match and url_match:
                        title = title_match.group(1).strip()
                        url = url_match.group(1).strip()
                        items.append({'title': title, 'url': url})
                else:
                    # 纯文本格式
                    items.append({'title': match.strip(), 'url': ''})
            
            platforms[platform] = {
                'update_time': update_time,
                'items': items[:50]  # 限制最多50条
            }
    
    return platforms

def update_google_sheets(platforms_data, spreadsheet_id):
    """将解析的数据追加写入到 Google Sheets"""
    try:
        # 设置 Google Sheets API 凭据
        scope = ['https://spreadsheets.google.com/feeds',
                 'https://www.googleapis.com/auth/spreadsheets',
                 'https://www.googleapis.com/auth/drive.file',
                 'https://www.googleapis.com/auth/drive']
        
        # 从环境变量获取凭据
        creds_json = os.getenv('GOOGLE_SHEETS_CREDS')
        if not creds_json:
            print("错误：未找到 GOOGLE_SHEETS_CREDS 环境变量")
            return False
            
        creds_data = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_data, scope)
        client = gspread.authorize(creds)
        
        # 打开 Google Sheets
        sheet = client.open_by_key(spreadsheet_id)
        
        # 获取当前时间作为数据收集时间
        collection_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # 为每个平台创建或更新工作表
        for platform, data in platforms_data.items():
            try:
                # 尝试打开现有的工作表，如果不存在则创建
                try:
                    worksheet = sheet.worksheet(platform)
                except:
                    # 工作表不存在，创建新的
                    worksheet = sheet.add_worksheet(title=platform, rows="1000", cols="20")
                    # 添加标题行（仅在创建新工作表时）
                    headers = ['抓取时间', '平台更新时间', '排名', '标题', '链接']
                    worksheet.append_row(headers)
                
                # 追加数据行
                for i, item in enumerate(data['items'], 1):
                    row = [collection_time, data['update_time'], i, item['title'], item['url']]
                    worksheet.append_row(row)
                
                print(f"成功追加写入 {platform} 工作表，共 {len(data['items'])} 条数据")
                
            except Exception as e:
                print(f"追加写入 {platform} 工作表时出错: {str(e)}")
                continue
        
        return True
        
    except Exception as e:
        print(f"连接 Google Sheets 时出错: {str(e)}")
        return False

def main():
    """主函数"""
    # 读取 README.md 文件
    try:
        with open('README.md', 'r', encoding='utf-8') as f:
            readme_content = f.read()
    except Exception as e:
        print(f"读取 README.md 文件时出错: {str(e)}")
        return
    
    # 解析 README 内容
    platforms_data = parse_readme_content(readme_content)
    
    # 获取 Google Sheets ID
    spreadsheet_id = "1X3qHRJMJpGKFEQ39T_Xi7kwLKBFDacUPE-udheNmOK0"
    
    # 更新 Google Sheets
    success = update_google_sheets(platforms_data, spreadsheet_id)
    
    if success:
        print("成功将 README 内容追加写入到 Google Sheets")
    else:
        print("追加写入 Google Sheets 失败")

if __name__ == "__main__":
    main()