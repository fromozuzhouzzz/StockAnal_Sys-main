#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试投资组合页面表头HTML结构
"""

import requests
from bs4 import BeautifulSoup

def test_table_headers():
    """测试表头HTML结构是否正确"""
    url = "http://127.0.0.1:8888/portfolio"
    
    try:
        print("正在获取投资组合页面...")
        response = requests.get(url)
        
        if response.status_code == 200:
            print("✅ 页面加载成功")
            
            # 解析HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找表头
            thead = soup.find('thead')
            if thead:
                print("✅ 找到表头元素")
                print("表头HTML内容:")
                print(thead.prettify())

                # 查找排序相关的元素
                sortable_headers = thead.find_all(class_='sortable-header')
                print(f"✅ 找到 {len(sortable_headers)} 个可排序表头")

                # 也尝试查找div元素
                sortable_divs = thead.find_all('div', class_='sortable-header')
                print(f"✅ 找到 {len(sortable_divs)} 个可排序div元素")
                
                for i, header in enumerate(sortable_headers):
                    onclick = header.get('onclick')
                    data_sort = header.get('data-sort')
                    
                    print(f"  排序表头 {i+1}:")
                    print(f"    onclick: {onclick}")
                    print(f"    data-sort: {data_sort}")
                    
                    # 查找排序指示器
                    indicator = header.find(class_='sort-indicator')
                    if indicator:
                        print(f"    排序指示器ID: {indicator.get('id')}")
                        print(f"    排序指示器文本: {indicator.get_text()}")
                    else:
                        print("    ❌ 未找到排序指示器")
                
                # 检查Material Icons是否正确引用
                material_icons = soup.find_all('i', class_='material-icons')
                print(f"✅ 页面中共有 {len(material_icons)} 个Material Icons")
                
                # 检查是否有JavaScript错误相关的内容
                scripts = soup.find_all('script')
                print(f"✅ 页面中共有 {len(scripts)} 个script标签")
                
            else:
                print("❌ 未找到表头元素")
                
        else:
            print(f"❌ 页面加载失败，状态码: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_table_headers()
