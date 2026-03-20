import json
from skills.weather_skill import WeatherSkill
from skills.switch_skill import SwitchSkill
from volcenginesdkarkruntime import Ark
from config import key

class MiniOpenClaw:
    def __init__(self):
        self.skills = {
            'weather': WeatherSkill(),
            'switch': SwitchSkill()
        }
        # 初始化豆包AI客户端
        self.client = Ark(
            base_url='https://ark.cn-beijing.volces.com/api/v3',
            api_key=key,
        )
    
    def process_request(self, skill_name, params):
        """处理请求并返回结果"""
        if skill_name in self.skills:
            skill = self.skills[skill_name]
            return skill.handle_request(params)
        else:
            return f"未知的技能：{skill_name}"
    
    def get_available_skills(self):
        """获取可用的技能列表"""
        return list(self.skills.keys())
    
    def process_with_ai(self, user_query):
        """使用AI处理用户请求"""
        try:
            # 构建提示词，告诉AI如何处理请求
            prompt = f"""你是一个智能助手，需要根据用户的请求调用相应的技能。
可用的技能：
1. weather - 查询天气，参数：location（地点）
2. switch - 执行交换机命令，参数：ip（交换机IP）、cmds（命令列表）、vendor（厂商）

请根据用户的请求，返回一个JSON格式的响应，包含以下字段：
- skill: 要调用的技能名称
- params: 技能所需的参数

例如：
用户请求：北京的天气怎么样？
响应：{{"skill": "weather", "params": {{"location": "北京"}}}}

用户请求：查询10.92.42.60的接口状态
响应：{{"skill": "switch", "params": {{"ip": "10.92.42.60", "cmds": ["dis ip int brie"], "vendor": "huawei"}}}}

现在用户的请求是：{user_query}
"""
            
            # 调用豆包AI
            print("正在调用豆包AI...")
            response = self.client.responses.create(
                model="doubao-seed-1-6-251015",
                input=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_text",
                                "text": prompt
                            }
                        ]
                    }
                ]
            )
            
            # 直接访问response对象的属性
            print("响应对象类型：", type(response))
            print("响应对象属性：", dir(response))
            
            # 尝试获取output属性
            if hasattr(response, 'output'):
                output = response.output
                print("Output属性：", output)
                
                # 遍历output列表，找到message类型的输出
                for item in output:
                    if hasattr(item, 'type') and item.type == 'message':
                        # 获取message的content
                        if hasattr(item, 'content'):
                            content = item.content
                            print("Message内容：", content)
                            
                            # 遍历content列表，找到text类型的内容
                            for content_item in content:
                                if hasattr(content_item, 'type') and content_item.type == 'output_text':
                                    # 获取text内容
                                    if hasattr(content_item, 'text'):
                                        json_str = content_item.text
                                        print("提取的JSON字符串：", json_str)
                                        
                                        try:
                                            parsed_response = json.loads(json_str)
                                            
                                            # 调用相应的技能
                                            skill_name = parsed_response.get('skill')
                                            params = parsed_response.get('params', {})
                                            
                                            if skill_name:
                                                result = self.process_request(skill_name, params)
                                                return f"AI处理结果：{result}"
                                            else:
                                                return "AI响应中未包含技能名称"
                                        except json.JSONDecodeError as e:
                                            print("JSON解析错误：", e)
                                            return "无法解析AI响应中的JSON"
            
            # 如果无法直接获取，尝试其他方式
            response_str = str(response)
            print("响应字符串：", response_str)
            
            # 尝试简单的字符串匹配
            import re
            json_match = re.search(r'"text":"(\{[^}]*\})"', response_str)
            if json_match:
                json_str = json_match.group(1)
                json_str = json_str.replace('\\"', '"')
                try:
                    parsed_response = json.loads(json_str)
                    
                    # 调用相应的技能
                    skill_name = parsed_response.get('skill')
                    params = parsed_response.get('params', {})
                    
                    if skill_name:
                        result = self.process_request(skill_name, params)
                        return f"AI处理结果：{result}"
                    else:
                        return "AI响应中未包含技能名称"
                except json.JSONDecodeError as e:
                    print("JSON解析错误：", e)
                    return "无法解析AI响应中的JSON"
            else:
                return "无法从AI响应中提取JSON"
        except Exception as e:
            error_msg = f"处理AI请求时发生错误：{str(e)}"
            print(error_msg)
            return error_msg

if __name__ == "__main__":
    # 初始化系统
    mini_openclaw = MiniOpenClaw()
    
    # 显示可用技能
    print("可用技能：", mini_openclaw.get_available_skills())
    
    # 测试天气查询技能
    weather_result = mini_openclaw.process_request('weather', {'location': '北京'})
    print("天气查询结果：", weather_result)
    
    # 测试交换机命令执行技能
    switch_result = mini_openclaw.process_request('switch', {'ip': '10.92.42.60', 'cmds': ['dis ip int brie'], 'vendor': 'huawei'})
    print("交换机命令执行结果：", switch_result)
    
    # 测试安全策略
    print("\n测试安全策略：")
    security_result = mini_openclaw.process_request('switch', {'ip': '10.92.42.60', 'cmds': ['undo interface gi0/0/1'], 'vendor': 'huawei'})
    print("安全策略测试结果：", security_result)
    
    # 测试AI处理交换机接口状态查询
    print("\n测试AI处理交换机接口状态查询：")
    ai_interface_result = mini_openclaw.process_with_ai("查询10.92.42.60的接口状态")
    print("AI处理交换机接口状态查询结果：", ai_interface_result)
    
    # 测试AI处理交换机版本信息查询
    print("\n测试AI处理交换机版本信息查询：")
    ai_version_result = mini_openclaw.process_with_ai("查询10.92.42.60的版本信息")
    print("AI处理交换机版本信息查询结果：", ai_version_result)