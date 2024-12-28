import sys
import random
import string
import time

try:
    import requests
    import ddddocr
    from loguru import logger
except ImportError:
    print(
        'run "pip install requests ddddocr loguru" with python<3.11 to install required packages'
    )
    exit()

debugging = True
max_retry = 1200

# 动态输入邮箱和用户名
inputs = {
    "name": input("Enter the name (e.g., John Doe): "),
    "email": input("Enter the email (e.g., example@example.com): "),
    "username": input("Enter the username: "),
}

params = {
    "csrfmiddlewaretoken": "",
    "first_name": "",
    "last_name": "",
    "username": "",
    "email": "",
    "captcha_0": "",
    "captcha_1": "",
    "question": "free",
    "tos": "on",
}

headers = {
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7",
    "Cache-Control": "no-cache",
    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
    "Cookie": "",
    "Origin": "https://www.serv00.com",
    "Pragma": "no-cache",
    "Priority": "u=1, i",
    "Referer": "https://www.serv00.com",
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "X-Requested-With": "XMLHttpRequest",
}

logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time: HH:mm:ss}</green> | <level>{message}</level>",
    level="TRACE" if debugging else "INFO",
)


def get_proxy():
    psid = "".join(random.choices(string.ascii_letters + string.digits, k=12))
    logger.info(f"proxy session: {psid}")
    return {
        "https": f"https://nZ8GRjnG4Q7s:y3XDOZVrlA8Z_ttl-1h_session-{psid}@superproxy.zenrows.com:1338"
    }


# 检查输入是否完整
if not inputs["email"] or not inputs["username"] or not inputs["name"]:
    print("All fields (name, email, username) are required.")
    exit()

first_name, last_name = inputs["name"].split(" ")
params["first_name"] = first_name
params["last_name"] = last_name
params["username"] = inputs["username"]
params["email"] = inputs["email"]

retry = 1
maybe_down = 0
captcha_0 = None
csrftoken = None

proxies = get_proxy()

ocr = ddddocr.DdddOcr(show_ad=False, old=True)
ocr.set_ranges(2)

logger.info(f"start for {inputs['email']} - {inputs['username']} - {inputs['name']}")

while retry < max_retry:
    t1 = time.time()
    logger.info(f"retry: {retry}")

    if retry > 0 and retry % 20 == 0:
        proxies = get_proxy()

    if captcha_0 == None:
        t2 = time.time()
        headers["Cookie"] = ""
        headers["Referer"] = "https://www.serv00.com"
        html_url = "https://www.serv00.com/offer/create_new_account"
        html_res = requests.get(
            url=html_url, headers=headers, proxies=proxies, verify=False
        )

        csrftoken = html_res.cookies.get("csrftoken")
        group = html_res.text.split('name="captcha_0" value="')
        captcha_0 = group[1].split('"')[0] if len(group) > 1 else None

        if captcha_0 == None:
            maybe_down += 1
            if maybe_down > 10:
                logger.error("maybe the site is down, exit...")
                exit()

            proxies = get_proxy()
            logger.warning("no captcha_0 found, retry...")
            continue

        maybe_down = 0
        headers["Cookie"] = f"csrftoken={csrftoken}"
        headers["Referer"] = "https://www.serv00.com/offer/create_new_account"
        logger.trace(f"duration: refresh csrftoken: {time.time() - t2:.2}s")

    try:
        t2 = time.time()
        captcha_url = f"https://www.serv00.com/captcha/image/{captcha_0}"
        captcha_res = requests.get(
            captcha_url, headers=headers, proxies=proxies, verify=False
        )

        if captcha_res.status_code != 200:
            logger.error("captcha image fetch failed, retry...")
            captcha_0 = None
            continue

        logger.trace(f"duration: fetch captcha: {time.time() - t2:.2}s")

        t2 = time.time()
        captcha_1 = ocr.classification(captcha_res.content)
        captcha_1 = captcha_1.upper()

        if debugging:
            logger.debug(f"captcha_url: {captcha_url}")
            logger.debug(f"captcha_ocr: {captcha_1}")

        logger.trace(f"duration: process captcha: {time.time() - t2:.2}s")

        if len(captcha_1) != 4 or not captcha_1.isalpha():
            captcha_0 = None
            logger.warning("bad ocr process, skip...")
            continue

        params["csrfmiddlewaretoken"] = csrftoken
        params["captcha_0"] = captcha_0
        params["captcha_1"] = captcha_1

        t2 = time.time()
        reg_url = "https://www.serv00.com/offer/create_new_account.json"
        reg_res = requests.post(
            url=reg_url, headers=headers, data=params, proxies=proxies, verify=False
        )
        logger.trace(f"duration: create account: {time.time() - t2:.2}s")

        reg_ret = reg_res.json()
        logger.debug(reg_ret)

        if "username" in reg_ret:
            error_msg = reg_ret["username"][0]
            logger.warning(f"username: {error_msg}")
            if "Maintenance time" not in error_msg:
                exit()

        if "email" in reg_ret:
            error_msg = reg_ret["email"][0]
            logger.warning("email: {error_msg}")
            exit()

        if "captcha" in reg_ret:
            logger.warning(f"captcha: {reg_ret['captcha'][0]}")

        if reg_res.status_code == 200 and len(reg_ret.keys()) == 2:
            ip = requests.get("https://api.ipify.org", proxies=proxies).text
            logger.success(f"🎉 account created! proxy: {ip}")
            exit()

        captcha_0 = reg_ret["__captcha_key"]

    except Exception as e:
        logger.error(e)
    finally:
        logger.trace(f"duration: total: {time.time() - t1:.2f}s")
        retry += 1
