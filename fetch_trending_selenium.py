#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TopHub 热榜数据抓取脚本（使用Selenium获取动态内容）
用于抓取知乎和微博的热榜前十条，生成HTML文件
"""

import json
import re
import os
import sys
from datetime import datetime
from pathlib import Path

# 尝试导入selenium，如果没有则安装
try:
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options
except ImportError:
    print("正在安装Selenium...")
    os.system("pip3 install selenium -q")
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.chrome.options import Options

def fetch_tophub_data_selenium():
    """
    使用Selenium获取TopHub的动态加载内容
    """
    url = "https://tophub.today/c/news"
    
    # 配置Chrome选项
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
    
    driver = None
    try:
        # 初始化驱动
        driver = webdriver.Chrome(options=chrome_options)
        
        # 访问页面
        print(f"正在访问 {url}...")
        driver.get(url)
        
        # 等待页面加载
        print("等待页面加载...")
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CLASS_NAME, "list-item"))
        )
        
        # 获取页面文本
        page_text = driver.find_element(By.TAG_NAME, "body").text
        
        # 提取知乎和微博热榜数据
        zhihu_items = extract_zhihu_items(page_text)
        weibo_items = extract_weibo_items(page_text)
        
        return {
            'zhihu': zhihu_items,
            'weibo': weibo_items,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Selenium错误: {e}")
        # 降级到使用requests方法
        return fetch_tophub_data_requests()
    
    finally:
        if driver:
            driver.quit()

def fetch_tophub_data_requests():
    """
    使用requests获取TopHub数据（备选方案）
    """
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("正在安装requests和beautifulsoup4...")
        os.system("pip3 install requests beautifulsoup4 -q")
        import requests
        from bs4 import BeautifulSoup
    
    url = "https://tophub.today/c/news"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        
        # 获取页面文本
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # 提取知乎和微博热榜数据
        zhihu_items = extract_zhihu_items(page_text)
        weibo_items = extract_weibo_items(page_text)
        
        return {
            'zhihu': zhihu_items,
            'weibo': weibo_items,
            'timestamp': datetime.now().isoformat()
        }
    
    except Exception as e:
        print(f"Requests错误: {e}")
        return {
            'zhihu': [],
            'weibo': [],
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }

def extract_zhihu_items(text):
    """
    从文本中提取知乎热榜项目
    """
    items = []
    
    # 找到知乎部分的起始位置
    zhihu_start = text.find('知乎')
    if zhihu_start == -1:
        return items
    
    # 找到微博部分的起始位置（作为知乎部分的结束）
    weibo_start = text.find('微博')
    if weibo_start == -1:
        weibo_start = len(text)
    
    # 提取知乎部分的文本
    zhihu_section = text[zhihu_start:weibo_start]
    
    # 使用正则表达式提取排名和标题
    # 模式：数字 + 标题 + 热度数字 + "万热度"
    pattern = r'(\d+)\s+([^万\n]+?)\s+(\d+\.?\d*)\s*万热度'
    
    matches = re.findall(pattern, zhihu_section)
    
    for rank, title, heat in matches:
        if len(items) < 10:
            # 清理标题
            title = title.strip()
            # 移除多余的空格和换行
            title = re.sub(r'\s+', ' ', title)
            
            if title and len(title) > 2:
                items.append({
                    'title': title,
                    'heat': f'{heat} 万热度',
                    'url': ''
                })
    
    return items

def extract_weibo_items(text):
    """
    从文本中提取微博热搜项目
    """
    items = []
    
    # 找到微博部分的起始位置
    weibo_start = text.find('微博')
    if weibo_start == -1:
        return items
    
    # 找到微信部分的起始位置（作为微博部分的结束）
    weixin_start = text.find('微信')
    if weixin_start == -1:
        weixin_start = len(text)
    
    # 提取微博部分的文本
    weibo_section = text[weibo_start:weixin_start]
    
    # 使用正则表达式提取排名和标题
    # 模式：数字 + 标题 + 热度数字 + "万"
    pattern = r'(\d+)\s+([^万\n]+?)\s+(\d+\.?\d*)\s*万'
    
    matches = re.findall(pattern, weibo_section)
    
    for rank, title, heat in matches:
        if len(items) < 10:
            # 清理标题
            title = title.strip()
            # 移除多余的空格和换行
            title = re.sub(r'\s+', ' ', title)
            
            if title and len(title) > 1 and not title.isdigit():
                items.append({
                    'title': title,
                    'heat': f'{heat} 万',
                    'url': ''
                })
    
    return items

def generate_html(data):
    """
    根据抓取的数据生成HTML文件
    """
    html_template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>今日热榜 - 知乎 & 微博</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
                'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
                sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 40px;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        
        .header p {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .content {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-bottom: 40px;
        }}
        
        @media (max-width: 768px) {{
            .content {{
                grid-template-columns: 1fr;
            }}
        }}
        
        .section {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            overflow: hidden;
        }}
        
        .section-header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            font-size: 1.5em;
            font-weight: bold;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-header.zhihu {{
            background: linear-gradient(135deg, #0084ff 0%, #0066cc 100%);
        }}
        
        .section-header.weibo {{
            background: linear-gradient(135deg, #ff6600 0%, #ff3300 100%);
        }}
        
        .list {{
            list-style: none;
        }}
        
        .list-item {{
            padding: 15px 20px;
            border-bottom: 1px solid #f0f0f0;
            display: flex;
            align-items: center;
            gap: 15px;
            transition: background-color 0.3s;
        }}
        
        .list-item:hover {{
            background-color: #f9f9f9;
        }}
        
        .list-item:last-child {{
            border-bottom: none;
        }}
        
        .rank {{
            font-weight: bold;
            font-size: 1.2em;
            color: #667eea;
            min-width: 30px;
            text-align: center;
        }}
        
        .item-content {{
            flex: 1;
        }}
        
        .item-title {{
            font-size: 1em;
            color: #333;
            margin-bottom: 5px;
            line-height: 1.4;
        }}
        
        .item-heat {{
            font-size: 0.85em;
            color: #999;
        }}
        
        .footer {{
            text-align: center;
            color: white;
            padding: 20px;
            font-size: 0.9em;
        }}
        
        .footer a {{
            color: white;
            text-decoration: underline;
        }}
        
        .emoji {{
            font-size: 1.2em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 今日热榜</h1>
            <p>知乎 & 微博热榜前十</p>
            <p style="font-size: 0.9em; margin-top: 10px;">更新时间: {timestamp}</p>
        </div>
        
        <div class="content">
            <div class="section">
                <div class="section-header zhihu">
                    <span class="emoji">💡</span>
                    <span>知乎热榜</span>
                </div>
                <ul class="list">
                    {zhihu_items}
                </ul>
            </div>
            
            <div class="section">
                <div class="section-header weibo">
                    <span class="emoji">🔥</span>
                    <span>微博热搜</span>
                </div>
                <ul class="list">
                    {weibo_items}
                </ul>
            </div>
        </div>
        
        <div class="footer">
            <p>数据来源: <a href="https://tophub.today/c/news">TopHub 今日热榜</a></p>
            <p style="margin-top: 10px;">自动生成 | 每日更新</p>
        </div>
    </div>
</body>
</html>
"""
    
    # 生成知乎热榜项目
    zhihu_html = ""
    if data['zhihu']:
        for i, item in enumerate(data['zhihu'][:10], 1):
            zhihu_html += f"""
                    <li class="list-item">
                        <div class="rank">{i}</div>
                        <div class="item-content">
                            <div class="item-title">{item.get('title', '')}</div>
                            <div class="item-heat">{item.get('heat', '')}</div>
                        </div>
                    </li>
"""
    else:
        zhihu_html = '<li class="list-item"><div style="color: #999;">暂无数据</div></li>'
    
    # 生成微博热搜项目
    weibo_html = ""
    if data['weibo']:
        for i, item in enumerate(data['weibo'][:10], 1):
            weibo_html += f"""
                    <li class="list-item">
                        <div class="rank">{i}</div>
                        <div class="item-content">
                            <div class="item-title">{item.get('title', '')}</div>
                            <div class="item-heat">{item.get('heat', '')}</div>
                        </div>
                    </li>
"""
    else:
        weibo_html = '<li class="list-item"><div style="color: #999;">暂无数据</div></li>'
    
    # 格式化时间戳
    timestamp = data['timestamp']
    try:
        dt = datetime.fromisoformat(timestamp)
        timestamp = dt.strftime('%Y年%m月%d日 %H:%M:%S')
    except:
        pass
    
    # 填充模板
    html_content = html_template.format(
        zhihu_items=zhihu_html,
        weibo_items=weibo_html,
        timestamp=timestamp
    )
    
    return html_content

def main():
    """
    主函数：抓取数据并生成HTML文件
    """
    print("开始抓取TopHub热榜数据...")
    
    # 抓取数据（优先使用Selenium，失败则使用requests）
    data = fetch_tophub_data_selenium()
    
    print(f"知乎热榜项目数: {len(data['zhihu'])}")
    print(f"微博热搜项目数: {len(data['weibo'])}")
    
    if 'error' in data:
        print(f"错误: {data['error']}")
    
    # 生成HTML
    html_content = generate_html(data)
    
    # 保存HTML文件
    output_path = Path(__file__).parent / 'index.html'
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"HTML文件已生成: {output_path}")
    
    # 同时保存JSON数据备份
    json_path = Path(__file__).parent / 'data.json'
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"JSON数据已保存: {json_path}")
    
    return output_path

if __name__ == '__main__':
    main()
