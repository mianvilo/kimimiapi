# encoding:utf-8
import requests
import plugins
from bridge.context import ContextType
from bridge.reply import Reply, ReplyType
from plugins import *

full_response_text = ""

def read_config_json():
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)
    return config


def create_new_chat(headers):
    api_url = 'https://kimi.moonshot.cn/api/chat'
    data={
    "name": "未命名会话",
    "is_example": False
    }
    response=requests.post(api_url,json=data,headers=headers)
    if response.status_code == 200:
        chat_id=json.loads(response.text)["id"]
        config = read_config_json()
        api_url_reg = api_url + "/" + chat_id+"/completion/stream"
        print(api_url_reg)
        config["api_url"] = api_url_reg
        curdir = os.path.dirname(__file__)
        config_path = os.path.join(curdir, "config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        # api_url_reg=api_url+"/"+chat_id
        # requests.get(api_url_reg, json=data, headers=headers)
        return chat_id
def get_refresf_token(next_token):


    api_url = 'https://kimi.moonshot.cn/api/auth/token/refresh'
    token=next_token
    # 请求头，添加了User-Agent和Bearer令牌
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Authorization': f'Bearer {token}'
    }

    resp=requests.get(api_url,headers=headers)
    # print(resp.text)
    next_token=json.loads(resp.text)["refresh_token"]
    current_token=json.loads(resp.text)["access_token"]
    curdir = os.path.dirname(__file__)
    config_path = os.path.join(curdir, "config.json")
    config=read_config_json()
    config["current_token"]=current_token
    config["next_token"] = next_token
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=4)

def fetch_full_response(api_url, query, token):
    global  full_response_text
    # 请求体
    payload = {
        "messages": [{"role": "user", "content": query}],
        "refs": [],
        "use_search": True
    }

    # 请求头，添加了User-Agent和Bearer令牌
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Authorization': f'Bearer {token}'
    }


    try:
        response=requests.post(api_url, json=payload, headers=headers, stream=True)
        print(response.status_code)
        # print(response.text)
        if response.status_code==401:#token过期，更换token
            config=read_config_json()
            next_token=config["next_token"]
            get_refresf_token(next_token)
            ref_config=read_config_json()
            return fetch_full_response(api_url,query,ref_config["current_token"])
        elif response.status_code==400:
            chat_id=create_new_chat(headers)
            api_url=f'https://kimi.moonshot.cn/api/chat/{chat_id}/completion/stream'
            return fetch_full_response(api_url, query, token)
        elif  response.status_code==200:
            full_response_text = ""
            for line in response.iter_lines():
                # 解码每行数据并忽略保持连接的空行
                if line:
                    decoded_line = line.decode('utf-8')

                    # 检查行是否以"data: "开头
                    if decoded_line.startswith('data: '):
                        # 从行中提取JSON对象
                        json_str = decoded_line.split('data: ', 1)[1]
                        try:
                            json_obj = json.loads(json_str)
                            if 'text' in json_obj:
                                full_response_text += json_obj['text']
                        except json.JSONDecodeError:
                            print(f"Error decoding JSON: {json_str}")

                    # 检查是否收到表示数据流结束的事件
                    if '"event":"all_done"' in decoded_line:
                        break

            return full_response_text
    except Exception as e:
        print("tigger")
        print(e)





@plugins.register(
    name="kimi",
    desire_priority=88,
    hidden=True,
    desc="使用Kimi作为问答模型",
    version="0.1",
    author="Francis",
)
class Kimi(Plugin):
    def __init__(self):
        super().__init__()
        self.handlers[Event.ON_HANDLE_CONTEXT] = self.on_handle_context

    def on_handle_context(self, e_context: EventContext):
        if e_context["context"].type not in [
            ContextType.TEXT,
            ContextType.JOIN_GROUP,
            ContextType.PATPAT,
        ]:
            return

        content = e_context["context"].content
        logger.debug("[Hello] on_handle_context. content: %s" % content)
        if e_context["context"].type == ContextType.TEXT:
            reply = Reply()
            reply.type = ReplyType.TEXT
            query = content
            print(query)
            config=read_config_json()
            response = fetch_full_response(config["api_url"], query, config["current_token"])
            print(response)
            reply.content = response
            e_context["reply"] = reply
            e_context.action = EventAction.BREAK_PASS

    def get_help_text(self, **kwargs):
        help_text = "使用kimi chat 作为问答模型，支持联网搜索"
        return help_text
