# -*- coding: utf-8 -*-
import json
from skills.weather_skill import WeatherSkill
from skills.switch_skill import SwitchSkill
from skills.device_skill import DeviceSkill
from volcenginesdkarkruntime import Ark
from config import key

class MiniOpenClaw:
    def __init__(self):
        self.skills = {
            'weather': WeatherSkill(),
            'switch': SwitchSkill(),
            'device_ip': DeviceSkill()
        }
        # 初始化豆包AI客户端
        self.client = Ark(
            base_url='https://ark.cn-beijing.volces.com/api/v3',
            api_key=key,
        )
        # SOP列表
        self.sop_list = [
            {
                "name": "交换机健康检查",
                "description": "检查交换机的基本状态、接口状态和版本信息",
                "instructions": "1.查询交换机所有接口信息，返回状态为up的接口列表\n2.查询交换机ip情况，返回ip接口为down的接口列表\n3.查询交换机基础信息，返回交换机的版本号",
                "parameters": ["ip"]
            },
            {
                "name": "天气查询",
                "description": "查询指定城市的天气信息",
                "instructions": "查询指定城市的天气信息并返回",
                "parameters": ["location"]
            },
            {
                "name": "设备接入位置查询",
                "description": "通过查询相关联交换机的arp、mac、lldp综合信息，获取设备在网络中的接入位置",
                "instructions": "1.登录10.92.42.64交换机，通过arp信息查出设备IP对应的MAC地址, 参考命令 dis arp all | in ip\n2.查询该mac地址出接口，参考命令 dis mac-add | in mac地址\n3.查询交换机lldp信息，关联mac的出接口定位下一台交换机名称，参考命令dis lldp nei brie\n4.根据交换机名称查询交换机IP,这里需要使用device_ip的技能去获取下一个交换机的IP\n5.根据查到的交换机IP，先查询mac出接口，再根据出接口查询lldp，直到出接口不在lldp列表中，最后返回所有相关联的交换机IP及端口名称",
                "parameters": ["dev_ip"]
            },
        ]
        # 技能描述（用于默认提示词）
        self.skill_descriptions = {
            'weather': '查询天气信息, 参数 location',
            'switch': '执行交换机命令, 参数 ip:交换机IP,cmds: ["待执行命令"], vendor: "huawei/h3c/cisco等，可不填"',
            'device_ip': '通过设备名查询设备IP, 参数 name: 设备名称',
        }
    
    def call_doubao(self, prompt, model="doubao-seed-1-6-251015"):
        """调用豆包AI并返回响应"""
        try:
            response = self.client.responses.create(
                model=model,
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

            # 提取响应内容
            if hasattr(response, 'output'):
                for item in response.output:
                    if hasattr(item, 'type') and item.type == 'reasoning':
                        if hasattr(item, 'summary'):
                            for summary_item in item.summary:
                                if hasattr(summary_item, 'type') and summary_item.type == 'summary_text':
                                    if hasattr(summary_item, 'text'):
                                        print("===思考过程==", summary_item.text)

                    if hasattr(item, 'type') and item.type == 'message':
                        if hasattr(item, 'content'):
                            for content_item in item.content:
                                if hasattr(content_item, 'type') and content_item.type == 'output_text':
                                    if hasattr(content_item, 'text'):
                                        return content_item.text
            return None
        except Exception as e:
            print(f"调用豆包AI时发生错误：{str(e)}")
            return None
    
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
    
    def find_sop(self, user_query):
        """根据用户请求寻找合适的SOP流程"""
        # 构建简化的SOP列表，只包含name和description
        simplified_sop_list = []
        for sop in self.sop_list:
            simplified_sop = {
                "name": sop.get("name"),
                "description": sop.get("description"),
                "parameters": sop.get("parameters"),
            }
            simplified_sop_list.append(simplified_sop)
        
        sop_list_str = json.dumps(simplified_sop_list, ensure_ascii=False)
        prompt = f"""你需要根据用户的请求，从以下SOP列表中选择最适合的流程：

{sop_list_str}

用户的请求是：{user_query}

请返回一个JSON格式的响应，包含以下字段：
- selected_sop: 选择的SOP名称
- parameters: 从用户请求中提取的参数，用于填充SOP中的占位符

例如：
用户请求：检查10.92.42.60的健康状态
响应：{{"selected_sop": "交换机健康检查", "parameters": {{"ip": "10.92.42.60"}}}}
用户请求：北京的天气怎么样？
响应：{{"selected_sop": "天气查询", "parameters": {{"location": "北京"}}}}

若缺少参数，则直接返回信息
例如：
{{"selected_sop": "选择的SOP名称","status": "failed", "msg":"原因"}}

"""
        # 调用豆包AI
        print("=2=发送给豆包AI的提示词：", prompt)
        response_text = self.call_doubao(prompt)
        print("=2=豆包AI的响应：", response_text)
        
        # 解析AI响应
        if response_text:
            try:
                parsed_response = json.loads(response_text)
                # 为选中的SOP添加instructions
                for sop in self.sop_list:
                    if sop['name'] == parsed_response.get('selected_sop'):
                        parsed_response['instructions'] = sop.get('instructions')
                        break
                return parsed_response
            except:
                pass
        return None
    
    def execute_sop(self, sop_name, parameters, instructions=None):
        """执行SOP流程"""
        # 找到对应的SOP
        selected_sop = None
        for sop in self.sop_list:
            if sop['name'] == sop_name:
                selected_sop = sop
                break
        
        if not selected_sop:
            return f"未找到名为 {sop_name} 的SOP流程"
        
        # 获取SOP指令
        sop_instructions = instructions or selected_sop.get('instructions', '')
        
        # 初始化任务执行状态
        results = []
        previous_results = []
        current_step = 1
        max_steps = 20  # 防止无限循环

        # 附加可用技能
        skill_list_str = "\n".join([f"- {skill}: {desc}" for skill, desc in self.skill_descriptions.items()])
        # 逐个执行任务，根据前一个任务的结果动态调整
        while current_step <= max_steps:
            # 构建提示词，让AI根据当前状态生成下一个任务
            _previous_str = '\n'.join(previous_results) if previous_results else "无"
            prompt = f"""你需要根据以下SOP指令、当前执行状态和之前的结果，生成下一个任务：

SOP名称：{sop_name}
SOP指令：{sop_instructions}
初始参数：{parameters}
之前的执行结果：
{_previous_str}

可用的技能：
{skill_list_str}

请返回一个JSON格式的响应，包含：
- task: 下一个要执行的任务（包含skill和params）
- is_complete: 是否所有任务都已完成

例如：
输入：
SOP名称：交换机健康检查
SOP指令：1.查询交换机所有接口信息，返回状态为up的接口列表
2.查询交换机ip情况，返回ip接口为down的接口列表
3.查询交换机基础信息，返回交换机的版本号
初始参数：{{"ip": "10.92.42.60"}}
之前的执行结果：无

响应：
{{
  "task": {{"skill": "switch", "params": {{"ip": "10.92.42.60", "cmds": ["dis interface status"], "vendor": "huawei"}}}},
  "is_complete": false
}}
"""
            
            # 调用豆包AI生成下一个任务
            print("=3=发送给豆包AI的提示词：", prompt)
            response_text = self.call_doubao(prompt)
            print("=3=豆包AI的响应：", response_text)

            
            # 解析AI响应
            if not response_text:
                return "无法生成下一个任务"
            
            try:
                parsed_response = json.loads(response_text)
                task = parsed_response.get('task')
                is_complete = parsed_response.get('is_complete', False)
                
                # 检查是否所有任务都已完成
                if is_complete:
                    break
                
                # 执行任务
                if task:
                    skill_name = task.get('skill')
                    params = task.get('params', {})
                    if skill_name:
                        result = self.process_request(skill_name, params)
                        results.append(result)
                        previous_results.append(result)
                        print(f"执行任务 {current_step} 完成：{skill_name}")
                    else:
                        results.append("任务缺少技能名称")
                else:
                    results.append("未生成任务")
            except Exception as e:
                print(f"处理任务时发生错误：{str(e)}")
                results.append(f"处理任务时发生错误：{str(e)}")
            
            current_step += 1
        
        if current_step > max_steps:
            return "任务执行超时，可能存在无限循环"
        
        # 将结果发送给AI进行总结
        task_results = "\n\n".join(results)
        summary_prompt = f"""请对以下SOP执行结果进行总结，使其更加直观易懂：

SOP名称：{sop_name}
SOP指令：{sop_instructions}
执行结果：
{task_results}

请提供一个清晰、简洁的总结，突出关键信息。
"""
        
        # 调用豆包AI进行总结
        print("=4=发送给豆包AI的提示词：", summary_prompt)
        summary = self.call_doubao(summary_prompt)
        print("=4=豆包AI的响应：", summary)
        
        if summary:
            return f"SOP流程 '{sop_name}' 执行完成\n\nAI总结：\n{summary}"
        else:
            return f"SOP流程 '{sop_name}' 执行完成\n" + "\n\n".join(results)
    
    def process_with_ai(self, user_query):
        """使用AI处理用户请求 主方法"""
        try:
            # 构建简化的提示词
            skill_list_str = "\n".join([f"- {skill}: {desc}" for skill, desc in self.skill_descriptions.items()])
            prompt = f"""你是一个智能助手，需要分析用户的请求并决定如何处理。

可用的技能：
{skill_list_str}

请分析用户的请求，并返回一个JSON格式的响应，包含以下字段：
- type: 处理类型，可以是 'direct'（直接调用技能）或 'sop'（使用SOP流程）
- skill: 当type为'direct'时，指定要调用的技能名称
- params: 当type为'direct'时，指定技能所需的参数
- sop_needed: 当type为'sop'时，指定是否需要使用SOP流程

例如：
用户请求：北京的天气怎么样？
响应：{{"type": "direct", "skill": "weather", "params": {{"location": "北京"}}}}

用户请求：检查交换机的健康状态
响应：{{"type": "sop", "sop_needed": true}}

现在用户的请求是：{user_query}
"""
            
            # 调用豆包AI
            print("正在调用豆包AI进行初步分析...")

            print("=1=发送给豆包AI的提示词：", prompt)
            ai_response = self.call_doubao(prompt)
            print("=1=豆包AI的响应：", ai_response)

            if not ai_response:
                return "无法获取AI响应"

            # 解析AI响应
            parsed_response = json.loads(ai_response)
            
            if parsed_response.get('type') == 'direct':
                # 直接调用技能
                skill_name = parsed_response.get('skill')
                params = parsed_response.get('params', {})
                if skill_name:
                    result = self.process_request(skill_name, params)
                    return f"AI处理结果：{result}"
                else:
                    return "AI响应中未包含技能名称"
            elif parsed_response.get('type') == 'sop' and parsed_response.get('sop_needed'):
                # 使用SOP流程
                print("正在寻找合适的SOP流程...")
                sop_result = self.find_sop(user_query)
                print("找到的sop流程", sop_result)
                if sop_result:
                    sop_name = sop_result.get('selected_sop')
                    status = sop_result.get('status', None)
                    if status and status=="failed":
                        return "用户输入缺失参数，原因{}".format(sop_result)
                    parameters = sop_result.get('parameters', {})
                    instructions = sop_result.get('instructions')
                    if sop_name:
                        print(f"选择了SOP流程：{sop_name}")
                        print(f"提取的参数：{parameters}")
                        print(f"SOP指令：{instructions}")
                        return self.execute_sop(sop_name, parameters, instructions)
                    else:
                        return "AI未选择SOP流程"
                else:
                    return "无法找到合适的SOP流程"
            else:
                return "AI响应格式不正确"
        except Exception as e:
            error_msg = f"处理AI请求时发生错误：{str(e)}"
            print(error_msg)
            return error_msg

if __name__ == "__main__":
    # 初始化系统
    mini_openclaw = MiniOpenClaw()
    
    # 显示可用技能
    print("可用技能：", mini_openclaw.get_available_skills())
    
    # 显示SOP列表f
    print("\n可用SOP流程：")
    for sop in mini_openclaw.sop_list:
        print(f"- {sop['name']}: {sop['description']}")

    # 测试AI处理SOP请求（交换机健康检查）
    # print("\n测试AI处理SOP请求（交换机健康检查）：")
    # ai_sop_result = mini_openclaw.process_with_ai("检查10.92.42.60的健康状态")
    # print("AI处理交换机健康检查结果：", ai_sop_result)

    # 测试AI处理SOP请求（设备接入位置查询）
    print("\n测试AI处理SOP请求（设备接入位置查询）：")
    ai_sop_result = mini_openclaw.process_with_ai("帮我查一下设备192.168.110.153接在哪个交换机下")
    print("AI处理设备接入位置查询结果：", ai_sop_result)