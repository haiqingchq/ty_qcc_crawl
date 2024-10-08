# -*- coding: utf-8 -*-
import os
from datetime import datetime
from tempfile import gettempdir
current_datetime = datetime.now()
FILENAME = current_datetime.strftime("%H-%M-%S")
DIRNAME = current_datetime.strftime("%Y-%m-%d")

"""
    项目的一些基本路径
"""
base_path = os.path.dirname(os.path.abspath(__file__))

# 完成任务记录保存地址
record_dir = os.path.join(base_path, "record")
if not os.path.exists(record_dir):
    os.mkdir(record_dir)
history_dir = os.path.join(base_path, "record/history")
if not os.path.exists(history_dir):
    os.mkdir(history_dir)
SCREENSHOT_HISTORY_PATH = os.path.join(base_path, 'record/history/screenshot.txt')
CREDITS_HISTORY_PATH = os.path.join(base_path, 'record/history/credits.txt')

# 错误保存地址
error_log_path = os.path.join(base_path, 'record/error/')
if not os.path.exists(error_log_path):
    os.makedirs(error_log_path)

# 爬取完成之后，未爬取成功的企业命名保存路径
UNDO_PATH = os.path.join(base_path, f'record/undo/{DIRNAME}')
if not os.path.exists(UNDO_PATH):
    os.makedirs(UNDO_PATH)

# 输出截图的位置
SCREENSHOT_OUT_DIR = os.path.join(base_path, 'out/screenshot')
if not os.path.exists(SCREENSHOT_OUT_DIR):
    os.makedirs(SCREENSHOT_OUT_DIR)
SCREENSHOT_OUT_PATH = os.path.join(SCREENSHOT_OUT_DIR, '{}.png')

# Excel 文件输出位置, 这段配置暂时搁置了，因为存在一些问题
# CREDIT_OUT_DIR = os.path.join(base_path, 'out/credit')
# if not os.path.exists(CREDIT_OUT_DIR):
#     os.makedirs(CREDIT_OUT_DIR)
# CREDIT_OUTPUT_PATH = os.path.join(CREDIT_OUT_DIR, 'target.xlsx')

"""
    获取项目启动的时间，用来当作统一的文件名和目录名
"""

CURRENT_ERR_DIR = os.path.join(error_log_path, DIRNAME)
CURRENT_ERR_PATH = os.path.join(CURRENT_ERR_DIR, FILENAME)

if not os.path.exists(CURRENT_ERR_DIR):
    os.makedirs(CURRENT_ERR_DIR)
"""
    登录状态保存位置：直接保存在当前操作系统的Temp目录中，方便管理
        1、ty_cookie_path 天眼的登录状态保存路径
        2、qcc_cookie_path 企查查登录状态保存路径
"""
temp_dir = gettempdir()
ty_cookie_path = os.path.join(temp_dir, 'ty.json')
qcc_cookie_path = os.path.join(temp_dir, 'qcc.json')

"""
    用来将Webdriver的属性置空的文件路径
"""

MIN_JS_PATH = os.path.join(base_path, 'data/stealth.min.js')
if not os.path.exists(MIN_JS_PATH):
    raise FileExistsError("{} does not exist".format(MIN_JS_PATH))

"""
    天眼url
        1、ty_search_url 搜索页面的url
        2、ty_search_target 截图页面的url
        3、ty_login_url 天眼登录页面url
"""
ty_search_url = "https://www.tianyancha.com/nadvance"
ty_search_target = r'https://www.tianyancha.com/company/(\d+)'
ty_login_url = "https://www.tianyancha.com/login?from=%2Fnadvance"

"""
    企查查url
        1、qcc_search_url 企查查收缩页面的url
        2、qcc_search_target 截图页面的url
        3、qcc_login_url 登录页面的url
        4、qcc_login_target_url 登录成功之后跳转到的url
"""
qcc_search_url = "https://www.qcc.com/"
qcc_search_target = r'https://www.qcc.com/firm/(.*).html'
qcc_login_url = "https://www.qcc.com/weblogin?back=%2Flogin"
qcc_login_target_url = 'https://www.qcc.com/login'

"""
    等待时长可以根据当前的网路状况以及自身情况进行调整
        1、screenshot_delay 1-2 s, 设置比较短的话，会截取到未加载完成的图片
        2、delay 是跳转页面之后的等待时长，0.5 - 2 s，这个跟网络速度有关系
"""
SCREENSHOT_DELAY = 1

DELAY = 1

"""
    选择平台的登录方式：
        1、"QRCODE"
        2、"PASSWORD"
            - 账号密码登录暂时处于测试开发阶段，暂时不可用
            - 需要将账号密码填写到下方
"""
LOGIN_TAP = "QRCODE"

# 天眼 账号 密码
TY_USERNAME = '17773059673'
TY_PASSWORD = 'chq20030306'

# 企查查 账号 密码
QCC_USERNAME = '17773059673'
QCC_PASSWORD = 'chq20030306'

"""
    异常重启功能的设置
"""
# 最大重启次数设置
MAX_ATTEMPTS = 5
# 每次重启的间隔时间，单位是秒
ATTEMPT_DELAY = 2

# User-Agent
User_Agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# disable-blink-features
Disable_Blink_Features = "AutomationControlled"

# 是否开启有头浏览器进行爬取
HEADLESS = False

# 两种功能，选择哪一种运行
# 1、截图功能
# 2、补充社会信用代码功能
OPTION = None
while True:
    OPTION = eval(input("\033[91m请输入需要使用的功能："))
    if OPTION in [1, 2]:
        break
    else:
        pass
"""
    指定Excel文件的文件头名称
"""
# 借款人企业名称
BUSINESS_NAME = "借款人企业名称"
# 社会统一信用代码
CREDIT_NAME = "社会统一信用代码"
# 命名
NAMED = "命名"
