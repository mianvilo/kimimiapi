
import requests
import json
######
api_url = 'https://kimi.moonshot.cn/api/auth/token/refresh'
token = 'Bearer_token'

# 请求头，添加了User-Agent和Bearer令牌
headers = {
    'Content-Type': 'application/json',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
    'Authorization': f'Bearer {token}'
}

resp=requests.get(api_url,headers=headers)
print(json.loads(resp.text)["refresh_token"])
print(json.loads(resp.text)["access_token"])


#access_token为当前携带token。
#refresh_token 为下次更新时携带token。
#1、准备新的token，然后请求refresh_token 2
#2、将refresh_token保存起来，当请求出错时，将refresh_token作为token传入headers
#3、再次请求refresh_token，获取access_token放入headers，请求stream



