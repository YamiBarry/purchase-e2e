# -*- coding: utf-8 -*-
"""
分析整批自动化报告，提取失败/错误用例，复制截图，输出修复列表
用法：python analyze_reports.py 报告1.html 报告2.html ...
截图规律：报告路径去掉 .html 加 _files 即为截图目录，如 ios1.html -> ios1_files/
"""
import sys
import re
import os
import shutil
sys.stdout.reconfigure(encoding='utf-8')
from bs4 import BeautifulSoup
from collections import defaultdict

# 截图保存目录（统一复制到这里供 Image 工具读取）
screenshot_dir = r"D:\workspace\skills\autoqa_fix_skill\screenshots"
os.makedirs(screenshot_dir, exist_ok=True)

# 从命令行获取报告路径
report_paths = sys.argv[1:] if len(sys.argv) > 1 else []
if not report_paths:
    print("用法: python analyze_reports.py 报告1.html 报告2.html ...")
    sys.exit(1)


def get_files_dir(report_path):
    """根据报告路径推断截图目录，如 ios1.html -> ios1_files/"""
    base = os.path.splitext(report_path)[0]  # 去掉 .html
    return base + "_files"


def parse_report(path):
    """解析单个报告，返回用例结果字典"""
    report_name = os.path.basename(path)
    report_dir = os.path.dirname(os.path.abspath(path))
    files_dir = get_files_dir(os.path.abspath(path))

    try:
        with open(path, encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
    except Exception as e:
        print(f"读取报告失败: {path} - {e}")
        return {}

    # 提取截图路径（本地 _files 目录里的文件）
    case_screenshots = {}
    for tr in soup.find_all('tr'):
        text = tr.get_text(separator=' ', strip=True)
        m = re.search(r'(test_\w+)', text)
        if not m:
            continue
        case_name = m.group(1)
        imgs = tr.find_all('img')
        paths = []
        for img in imgs:
            src = img.get('src', '')
            if not src:
                continue
            if src.startswith('http'):
                # CDN 链接（旧格式报告）
                paths.append(src)
            else:
                # 本地相对路径，转为绝对路径
                # src 格式如 ./ios1_files/xxx.webp 或 ios1_files/xxx.webp
                src_clean = src.lstrip('./')
                abs_path = os.path.join(report_dir, src_clean)
                if os.path.exists(abs_path):
                    paths.append(abs_path)
        if paths:
            case_screenshots[case_name] = paths

    # 提取用例结果和日志
    results = {}
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
            continue

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

        results[case_name] = {
            'status': status,
            'log': detail_log,
            'screenshots': case_screenshots.get(case_name, []),
            'report': report_name,
        }
    return results


def get_error_summary(log):
    """从日志提取关键错误行"""
    lines = []
    for line in log.split('\n'):
        line = line.strip()
        if any(k in line for k in ['错误信息', 'Exception', 'Error:', 'Action: ', 'raise ']):
            lines.append(line[:150])
    return '\n'.join(lines[:5])


def get_action(log):
    """提取失败的 Action 名"""
    m = re.search(r'Action: (\w+) 执行失败', log)
    if m:
        return m.group(1)
    m = re.search(r"错误信息: (.{1,50})", log)
    if m:
        return m.group(1)[:40]
    return 'unknown'


def copy_screenshot(case_name, urls):
    """复制最后3张截图到 screenshots 目录，统一保存为 .jpg
    返回所有复制成功的路径列表，最后一张在最后
    """
    if not urls:
        return []
    # 取最后3张
    last3 = urls[-3:]
    saved = []
    for i, src in enumerate(last3):
        # i=0 是倒数第3张，i=2 是最后一张
        idx = len(last3) - i  # 3,2,1
        filename = f"{case_name}_last{idx}.jpg"
        local_path = os.path.join(screenshot_dir, filename)
        try:
            if src.startswith('http'):
                import urllib.request
                urllib.request.urlretrieve(src, local_path)
            else:
                shutil.copy2(src, local_path)
            saved.append(local_path)
        except Exception:
            pass
    return saved


# 合并所有报告，同名用例以最后一个报告为准
all_cases = {}
for path in report_paths:
    cases = parse_report(path)
    for name, info in cases.items():
        all_cases[name] = info

# 分类
need_fix = {k: v for k, v in all_cases.items() if v['status'] in ('FAIL', 'ERROR')}
passed = {k: v for k, v in all_cases.items() if v['status'] == 'PASS'}

# 复制截图（最后3张）
print("正在准备截图...")
screenshot_paths = {}
for name, info in need_fix.items():
    paths = copy_screenshot(name, info['screenshots'])
    if paths:
        screenshot_paths[name] = paths

# 按根因分组
by_action = defaultdict(list)
for name, info in sorted(need_fix.items()):
    action = get_action(info['log'])
    by_action[action].append((name, info))

print("\n" + "=" * 80)
print("报告分析结果")
print("总计: %d 个  需修复: %d 个  通过: %d 个" % (len(all_cases), len(need_fix), len(passed)))
print("=" * 80)

print("\n【需修复用例列表】")
for action, cases in sorted(by_action.items()):
    print("\n▌ 根因: %s（%d 个）" % (action, len(cases)))
    for name, info in cases:
        print("  [%s] %s  (%s)" % (info['status'], name, info['report']))
        summary = get_error_summary(info['log'])
        if summary:
            for line in summary.split('\n'):
                print("       >> %s" % line)
        if name in screenshot_paths:
            paths = screenshot_paths[name]
            print("       截图(共%d张，最后1张): %s" % (len(paths), paths[-1]))

print("\n" + "=" * 80)
print("通过用例共 %d 个" % len(passed))
print("=" * 80)
