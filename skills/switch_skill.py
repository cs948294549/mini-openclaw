import requests
import json

class SwitchSkill:
    def __init__(self):
        self.target_base = "http://192.168.110.153:8000/"
    
    def run_switch_command(self, ip, cmds, vendor):
        """执行交换机命令"""
        # 安全策略：只允许执行display开头的命令
        filtered_cmds = []
        for cmd in cmds:
            if cmd.lower().startswith('display') or cmd.lower().startswith('dis'):
                filtered_cmds.append(cmd)
            else:
                return f"安全策略限制：只允许执行display开头的命令，当前命令 '{cmd}' 被拒绝"
        
        url = self.target_base + "ssh/run_cmd"
        headers = {
            "Content-Type": "application/json",
        }
        body = {
            "ip": ip,
            "cmds": filtered_cmds,
            "vendor": vendor
        }
        
        try:
            response = requests.post(url, headers=headers, data=json.dumps(body))
            if response.status_code == 200:
                data = json.loads(response.text)
                if data.get('code') == 0 and data.get('message') == 'success':
                    result_data = data.get('data', {})
                    result_info = result_data.get('result', {})
                    if result_info.get('status') == 'success':
                        command_results = result_info.get('data', {})
                        output = []
                        for cmd, result in command_results.items():
                            output.append(f"命令：{cmd}\n结果：{result}")
                        return f"交换机{ip}命令执行成功\n" + "\n\n".join(output)
                    else:
                        return f"交换机{ip}命令执行失败：{result_info.get('msg', '未知错误')}"
                else:
                    return f"API调用失败：{data.get('message', '未知错误')}"
            else:
                return f"执行交换机命令失败，状态码：{response.status_code}"
        except Exception as e:
            return f"执行交换机命令时发生错误：{str(e)}"
    
    def handle_request(self, params):
        """处理交换机信息查询请求"""
        ip = params.get('ip', '10.92.42.60')
        cmds = params.get('cmds', ['dis ip int brie'])
        vendor = params.get('vendor', 'huawei')
        return self.run_switch_command(ip, cmds, vendor)