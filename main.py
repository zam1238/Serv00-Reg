import os
import re
import time
import string
import random
import ddddocr
import requests
from loguru import logger
from urllib.parse import quote
from requests.exceptions import JSONDecodeError
ocr = ddddocr.DdddOcr()
os.makedirs("static", exist_ok=True)
cache = {}
def remove_spaces(input_string: str) -> str:
    return input_string.replace(" ", "")
def get_user_name():
    url = "http://www.ivtool.com/random-name-generater/uinames/api/index.php?region=united%20states&gender=male&amount=5&="
    resp = requests.get(url, verify=False)
    if resp.status_code != 200:
        print(resp.status_code, resp.text)
        raise Exception("获取名字出错")
    data = resp.json()
    return data
def generate_random_username():
    length = random.randint(7, 10)
    characters = string.ascii_letters
    random_string = ''.join(random.choice(characters) for _ in range(length))
    return random_string
def start_task(input_email: str):
    background_task(input_email)
def background_task(input_email: str):
    while True:
        try:
            usernames = get_user_name()
            email = input_email
            Cookie = "csrftoken={}"
            url1 = "https://www.serv00.com/offer/create_new_account"
            captcha_url = "https://www.serv00.com/captcha/image/{}/"
            header2 = {"Cookie": Cookie}
            url3 = "https://www.serv00.com/offer/create_new_account.json"
            header3 = {
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://www.serv00.com/offer/create_new_account",
                "Cookie": Cookie
            }
            _ = usernames.pop()
            first_name = _["name"]
            last_name = _["surname"]
            username = generate_random_username().lower()
            logger.info(f"{email} {first_name} {last_name} {username}")
            with requests.Session() as session:
                logger.info("获取网页信息")
                resp = session.get(url=url1, verify=False)
                if resp.status_code != 200:
                    print(resp.status_code)
                    return
                headers = resp.headers
                content = resp.text
                csrftoken = re.findall(r"csrftoken=(\w+);", headers.get("set-cookie"))[0]
                header2["Cookie"] = header2["Cookie"].format(csrftoken)
                header3["Cookie"] = header3["Cookie"].format(csrftoken)
                captcha_0 = re.findall(r'id=\"id_captcha_0\" name=\"captcha_0\" value=\"(\w+)\">', content)[0]
                retry = 1
                while True:
                    time.sleep(random.uniform(0.5, 1.2))
                    logger.info("获取验证码")
                    resp = session.get(url=captcha_url.format(captcha_0), headers=dict(header2, **{"Cookie": header2["Cookie"].format(csrftoken)}), verify=False)
                    content = resp.content
                    with open("static/image.jpg", "wb") as f:
                        f.write(content)
                    captcha_1 = ocr.classification(content).lower()
                    if bool(re.match(r'^[a-zA-Z0-9]{4}$', captcha_1)):
                        logger.info(f"识别验证码成功: {captcha_1}")
                    else:
                        logger.warning("\033[4m验证码识别失败,正在重试...\033[0m")
                        retry += 1
                        if retry > 20: # 此处修改重试次数，默认20次.
                            print("验证码识别失败次数过多,退出重试.")
                            return
                        continue
                    logger.info(f"提交数据: captcha_0={captcha_0} captcha_1={captcha_1}")
                    data = f"csrfmiddlewaretoken={csrftoken}&first_name={first_name}&last_name={last_name}&username={username}&email={quote(email)}&captcha_0={captcha_0}&captcha_1={captcha_1}&question=0&tos=on"
                    time.sleep(random.uniform(0.5, 1.2))
                    logger.info("请求信息")
                    resp = session.post(url=url3, headers=dict(header3, **{"Cookie": header3["Cookie"].format(csrftoken)}), data=data, verify=False)
                    logger.info(f'请求状态码: {resp.status_code}')
                    print(resp.text)
                    try:
                        content = resp.json()
                    except JSONDecodeError:
                        logger.error("\033[7m获取信息错误,正在重试...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        continue
                    if content.get("captcha") and content["captcha"][0] == "Invalid CAPTCHA":
                        captcha_0 = content["__captcha_key"]
                        retry += 1
                        logger.warning("\033[4m验证码错误,正在重新获取...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        continue
                    if content.get("username") and content["username"][0] == "Maintenance time. Try again later.":
                        logger.error("\033[7m系统维护中,正在重试...\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        break
                    if content.get("email") and content["email"][0] == "Enter a valid email address.":
                        logger.error("\033[7m无效的邮箱,请重新输入.\033[0m")
                        time.sleep(random.uniform(0.5, 1.2))
                        return
                    else:
                        return
        except Exception as e:
            logger.error(f"发生异常: {e}, 正在重新开始任务...")
            time.sleep(random.uniform(0.5, 1.2))
        if input_email in cache:
            del cache[input_email]
if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    response = requests.get('https://ping0.cc/geo', verify=False)
    print(f"=============================\n\033[96m{response.text[:200]}\033[0m=============================")
    print("\033[91m输入邮箱开始自动任务,退出快捷键Ctrl+C.\033[0m")
    while True:
        input_email = input("\033[94m请输入邮箱:\033[0m")
        if '@' not in input_email:
            print("\033[93m无效的邮箱,请重新输入.\033[0m")
            continue
        start_task(input_email)
