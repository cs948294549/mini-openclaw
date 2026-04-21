class DeviceSkill:
    def __init__(self):
        pass

    def get_device(self, name):
        """获取指定名称交换机的IP"""
        # 这里使用模拟数据，实际应用中可以调用真实的天气API
        device_data = {
            "DK-IDC-Center":"10.92.42.64",
            "DK-35F-DC-Management":"10.92.42.60",
            "DK-35F-DC-Management-B":"10.92.42.61",
            "DK-35F-DC-VMStack":"10.92.42.66",
            "DK-35F-DC-VMSack-B":"10.92.42.67",
            "DK-35F-Aceess-Office":"10.92.42.80",
            "DK-35F-A001":"10.92.42.81",
            "DK-35F-A002":"10.92.42.82",
            "DK-35F-A003":"10.92.42.83",
            "DK-35F-A004":"10.92.42.84",
            "DK-35F-A005":"10.92.42.85",
            "DK-35F-A006":"10.92.42.86",
            "DK-35F-A007":"10.92.42.87",
            "DK-35F-A008":"10.92.42.88",
            "DK-35F-A009-POE":"10.92.42.89",
            "DK-22F-Office-Center":"10.92.42.90",
            "DK-22F-Area-001":"10.92.42.91",
            "DK-22F-Area-002":"10.92.42.92",
            "DK-22F-Area-003":"10.92.42.93",
            "DK-22F-Area-004":"10.92.42.94",
            "DK-22F-Area-005":"10.92.42.95",
        }

        if name in device_data:
            return f"{name}的IP：{device_data[name]}"
        else:
            return f"抱歉，暂未查询到{name}的IP信息"

    def handle_request(self, params):
        """处理设备查询请求"""
        location = params.get('name', None)
        return self.get_device(location)