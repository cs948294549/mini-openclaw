class WeatherSkill:
    def __init__(self):
        pass
    
    def get_weather(self, location):
        """获取指定地点的天气信息"""
        # 这里使用模拟数据，实际应用中可以调用真实的天气API
        weather_data = {
            "北京": "晴，22°C，风力3级",
            "上海": "多云，18°C，风力2级",
            "广州": "阴，25°C，风力1级",
            "深圳": "小雨，23°C，风力4级"
        }
        
        if location in weather_data:
            return f"{location}的天气：{weather_data[location]}"
        else:
            return f"抱歉，暂未查询到{location}的天气信息"
    
    def handle_request(self, params):
        """处理天气查询请求"""
        location = params.get('location', '北京')
        return self.get_weather(location)