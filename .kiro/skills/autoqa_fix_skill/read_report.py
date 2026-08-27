# -*- coding: utf-8 -*-
"""
读取本地测试报告 reports/report.html
用法：python read_report.py [report_path]
"""
import sys, re, os
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
import urllib.request

report_path = sys.argv[1] if len(sys.argv) > 1 else \
    r"D:\workspace\yami-code-master\IntegrationTesting\reports\report.html"

# 截图保存目录
screenshot_dir = r"D:\workspace\skills\autoqa_fix_skill\screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

with open(report_path, encoding='utf-8', errors='ignore') as f:
    soup = BeautifulSoup(f.read(), 'html.parser')

# Step1: 从summary行提取截图CDN链接
case_screenshots = {}
for tr in soup.find_all('tr'):
    text = tr.get_text(separator=' ', strip=True)
    m = re.search(r'(test_\w+)', text)
    if not m:
        continue
    case_name = m.group(1)
    imgs = tr.find_all('img')
    paths = [img.get('src', '') for img in imgs if 'cdn.yamibuy' in img.get('src', '')]
    if paths:
        case_screenshots[case_name] = paths

# Step2: 从pre标签提取用例结果和日志
results = []
for pre in soup.find_all('pre'):
    text = pre.get_text(strip=True)
    if '执行——>' not in text:
        continue
    m = re.search(r'(test_\w+)\s+\(', text)
    if not m:
        continue
    case_name = m.group(1)

    if '通过' in text:
        status = 'PASS'
    elif '失败' in text or 'Failure' in text:
        status = 'FAIL'
    elif '错误' in text or 'Error' in text:
        status = 'ERROR'
    else:
        status = 'UNKNOWN'

    # 找详细日志
    detail_log = ''
    next_el = pre.find_next_sibling()
    while next_el:
        if next_el.name == 'pre':
            t = next_el.get_text(strip=True)
            if 'Traceback' in t or 'ERROR' in t or '错误信息' in t:
                detail_log = t
                break
            if '执行——>' in t:
                break
        next_el = next_el.find_next_sibling()

    results.append({
        'case': case_name,
        'status': status,
        'log': detail_log,
        'screenshots': case_screenshots.get(case_name, []),
    })

# 去重取最后一次
seen = {}
for r in results:
    seen[r['case']] = r
results = list(seen.values())

pass_count = sum(1 for r in results if r['status'] == 'PASS')
fail_count = sum(1 for r in results if r['status'] == 'FAIL')
error_count = sum(1 for r in results if r['status'] == 'ERROR')

print("=" * 80)
print("总计: %d 个  通过: %d  失败: %d  错误: %d" % (len(results), pass_count, fail_count, error_count))
print("=" * 80)

for r in results:
    print("\n[%s] %s" % (r['status'], r['case']))
    if r['status'] in ('FAIL', 'ERROR') and r['log']:
        for line in r['log'].split('\n'):
            line = line.strip()
            if any(k in line for k in ['ERROR', '错误信息', 'Exception', 'Error:', 'Action: ']):
                print("  >> %s" % line[:150])

    # 复制最后3张截图，统一保存为 .jpg，命名 last3/last2/last1（last1最新）
    if r['screenshots']:
        last3 = r['screenshots'][-3:]
        saved = []
        for i, url in enumerate(last3):
            idx = len(last3) - i  # 3,2,1
            filename = r['case'] + f'_last{idx}.jpg'
            local_path = os.path.join(screenshot_dir, filename)
            try:
                if url.startswith('http'):
                    urllib.request.urlretrieve(url, local_path)
                else:
                    import shutil
                    shutil.copy2(url, local_path)
                saved.append(local_path)
            except Exception:
                pass
        if saved:
            print("  截图已保存(共%d张，最后1张): %s" % (len(saved), saved[-1]))
