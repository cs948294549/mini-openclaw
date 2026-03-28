import base64
import urllib.parse
# 导入编译生成的 Protobuf 模块
import otpauth_migration_pb2

def parse_otpauth_migration_url(url):
    """
    解析 otpauth-migration 链接，提取所有 OTP 令牌参数
    :param url: 完整的迁移链接（如：otpauth-migration://offline?data=xxx）
    :return: MigrationPayload 对象（包含所有 OTP 参数）
    """
    # 步骤1：解析 URL，提取 data 参数并 URL 解码
    parsed_url = urllib.parse.urlparse(url)
    query_params = urllib.parse.parse_qs(parsed_url.query)
    if "data" not in query_params:
        raise ValueError("迁移链接缺少 data 参数")
    data_b64 = urllib.parse.unquote(query_params["data"][0])

    # 步骤2：Base64Url 解码（兼容标准 Base64）
    # 补充填充符，确保 Base64 格式合法
    padding = 4 - (len(data_b64) % 4)
    if padding != 4:
        data_b64 += "=" * padding
    # 解码为二进制字节
    data_bytes = base64.urlsafe_b64decode(data_b64)

    # 步骤3：反序列化为 Protobuf 对象
    payload = otpauth_migration_pb2.MigrationPayload()
    payload.ParseFromString(data_bytes)

    return payload

# 测试：解析你提供的迁移链接
if __name__ == "__main__":
    # 你的迁移链接
    migration_url = "otpauth-migration://offline?data=CjcKECluRGFlSDhwZ1Y7N1FQTW0SE2FkbWluQDEyNC4xNjAuNDIuNjYaCFBpbmdDb2RlIAEoATACEAEYASAAKN3Q6JT9%2F%2F%2F%2F%2FwE%3D"
    try:
        # 解析链接
        payload = parse_otpauth_migration_url(migration_url)

        # 打印解析结果（核心参数）
        print("=== otpauth-migration 解析结果 ===")
        print(f"协议版本：{payload.version}")
        print(f"批次大小：{payload.batch_size}")
        print(f"批次索引：{payload.batch_index}")
        print(f"批次 ID：{payload.batch_id}")
        print("\n=== OTP 令牌列表 ===")

        # 遍历所有 OTP 令牌
        for idx, otp in enumerate(payload.otp_parameters):
            print(f"\n【令牌 {idx+1}】")
            print(f"  发行方（issuer）：{otp.issuer}")
            print(f"  账户名（name）：{otp.name}")
            print(f"  密钥原始字节：{otp.secret}")
            print(f"  密钥数字字符串：{int.from_bytes(otp.secret, 'big')}")  # 转为你需要的数字格式
            print(f"  算法：{otpauth_migration_pb2.MigrationPayload.Algorithm.Name(otp.algorithm)}")
            print(f"  验证码位数：{otpauth_migration_pb2.MigrationPayload.DigitCount.Name(otp.digits)}")
            print(f"  OTP 类型：{otpauth_migration_pb2.MigrationPayload.OtpType.Name(otp.type)}")
            print(f"  HOTP 计数器：{otp.counter}")

        print("\n✅ 解析成功！")
    except Exception as e:
        print(f"\n❌ 解析失败：{e}")