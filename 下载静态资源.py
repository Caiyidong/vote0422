"""
下载前端静态资源到本地，解决 CDN 加载失败问题
运行方式：python 下载静态资源.py
"""
import urllib.request
import os

BASE = os.path.join(os.path.dirname(__file__), 'static', 'lib')
os.makedirs(BASE, exist_ok=True)

files = [
    # (保存文件名, 下载地址)
    ('bootstrap.min.css',
     'https://mirrors.bootcdn.net/bootstrap/5.3.0/css/bootstrap.min.css'),
    ('bootstrap-icons.css',
     'https://mirrors.bootcdn.net/bootstrap-icons/1.11.0/font/bootstrap-icons.min.css'),
    ('bootstrap.bundle.min.js',
     'https://mirrors.bootcdn.net/bootstrap/5.3.0/js/bootstrap.bundle.min.js'),
    ('chart.umd.min.js',
     'https://mirrors.bootcdn.net/Chart.js/4.4.0/chart.umd.min.js'),
]

for filename, url in files:
    dest = os.path.join(BASE, filename)
    if os.path.exists(dest):
        print(f'已存在，跳过：{filename}')
        continue
    print(f'正在下载：{filename} ...')
    try:
        urllib.request.urlretrieve(url, dest)
        size = os.path.getsize(dest)
        print(f'  完成 ✓  ({size // 1024} KB)')
    except Exception as e:
        print(f'  失败 ✗  {e}')
        print(f'  请手动下载：{url}')

print('\n全部完成！')
