import re


headers = {
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Origin': 'https://boink.boinkers.co',
    'Accept-Encoding': 'gzip, deflate',
    'Referer': 'https://boink.boinkers.co/sluts',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'sec-ch-ua-platform': '"Android"',
    'sec-ch-ua-mobile': "?1",
    'X-Requested-With': 'org.telegram.messenger.web'
}


def get_sec_ch_ua(user_agent):
    pattern = r'(Chrome|Chromium)\/(\d+)\.(\d+)\.(\d+)\.(\d+)'

    match = re.search(pattern, user_agent)

    if match:
        browser = match.group(1)
        version = match.group(2)

        if browser == 'Chrome':
            #sec_ch_ua = f'"Chromium";v="{version}", "Not;A=Brand";v="8", "Google Chrome";v="{version}"'
            sec_ch_ua =  f'"Not A(Brand";v = "8", "Chromium";v = "{version}", "Android WebView";v = "{version}"'
        else:
            sec_ch_ua = f'"Chromium";v="{version}", "Not;A=Brand";v="8"'

        return {'Sec-Ch-Ua': sec_ch_ua}
    else:
        return {}