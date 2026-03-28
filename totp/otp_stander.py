import hmac
import hashlib
import time
import base64
import qrcode  # 仅用于生成二维码，可选（也可手动拼接URL让用户扫码）


def generate_totp_secret(length: int = 16) -> str:
    """
    生成TOTP共享密钥（原生随机生成，Base32编码，符合TOTP标准）
    :param length: 密钥字节长度（推荐16）
    :return: Base32编码的共享密钥（无=补位，符合验证器规范）
    """
    # 生成随机字节（原生os.urandom，安全）
    import os
    random_bytes = os.urandom(length)
    # Base32编码（转大写，去掉末尾的=补位，兼容手机验证器）
    secret = base64.b32encode(random_bytes).decode('utf-8').upper().replace('=', '')
    return secret

def generate_totp_secret_by_byte(data_byte) -> str:
    """
    生成TOTP共享密钥（原生随机生成，Base32编码，符合TOTP标准）
    :param length: 密钥字节长度（推荐16）
    :return: Base32编码的共享密钥（无=补位，符合验证器规范）
    """
    secret = base64.b32encode(data_byte).decode('utf-8').upper().replace('=', '')
    return secret

def get_time_step(timestamp: int = None, step: int = 30) -> int:
    """
    计算当前时间对应的时间窗口（每30秒一个窗口）
    :param timestamp: 时间戳（默认当前时间）
    :param step: 时间窗口长度（默认30秒）
    :return: 时间窗口数（整数）
    """
    if timestamp is None:
        timestamp = int(time.time())
    return timestamp // step


def totp_generate(secret: str, timestamp: int = None, step: int = 30, digits: int = 6) -> str:
    """
    原生计算TOTP验证码（核心函数）
    :param secret: Base32编码的共享密钥
    :param timestamp: 时间戳（默认当前时间）
    :param step: 时间窗口长度（默认30秒）
    :param digits: OTP位数（默认6位）
    :return: 6位OTP字符串
    """
    # 1. 补全Base32密钥的=补位（Base32编码要求长度是8的倍数）
    secret_padded = secret.ljust((len(secret) + 7) // 8 * 8, '=')
    try:
        secret_bytes = base64.b32decode(secret_padded, casefold=True)
    except base64.binascii.Error:
        raise ValueError("共享密钥不是有效的Base32编码")

    # 2. 获取时间窗口（转8字节大端序二进制）
    time_step = get_time_step(timestamp, step)
    time_bytes = time_step.to_bytes(8, byteorder='big')  # 8字节大端序

    # 3. HMAC-SHA1加密（TOTP标准算法）
    hmac_result = hmac.new(secret_bytes, time_bytes, hashlib.sha1).digest()

    # 4. 动态截取4字节数据（取最后4位作为偏移量）
    offset = hmac_result[-1] & 0x0F  # 取最后1字节的低4位作为偏移
    truncated = hmac_result[offset:offset + 4]  # 截取4字节

    # 5. 转整数并取后6位（去掉最高位的符号位）
    truncated_int = int.from_bytes(truncated, byteorder='big') & 0x7FFFFFFF
    otp = truncated_int % (10 ** digits)

    # 补零到6位（如123 → 000123）
    return f"{otp:0{digits}d}"


def totp_verify(secret: str, input_otp: str, step: int = 30, window: int = 1) -> bool:
    """
    验证OTP是否正确（支持时间窗口容错）
    :param secret: 共享密钥
    :param input_otp: 用户输入的OTP
    :param step: 时间窗口长度
    :param window: 容错窗口（±window个时间窗口，默认±30秒）
    :return: 验证结果
    """
    if len(input_otp) != 6:
        return False

    current_step = get_time_step(step=step)
    # 遍历容错窗口（当前窗口 ± window）
    for offset in range(-window, window + 1):
        test_step = current_step + offset
        expected_otp = totp_generate(secret, timestamp=test_step * step, step=step)
        if expected_otp == input_otp:
            return True
    return False


def generate_totp_qr(secret: str, username: str, issuer: str = "MySSL_VPN") -> None:
    """
    生成TOTP二维码（供手机验证器扫描）
    :param secret: 共享密钥
    :param username: 用户名
    :param issuer: 发行方（VPN名称）
    """
    # 构建OTP认证URL（符合手机验证器规范）
    otp_url = f"otpauth://totp/{issuer}:{username}?secret={secret}&issuer={issuer}"
    # 生成并保存二维码
    qr_img = qrcode.make(otp_url)
    qr_img.save(f"{username}_totp_qr.png")
    print(f"📷 二维码已保存为：{username}_totp_qr.png")



# ------------------- 测试示例 -------------------
if __name__ == "__main__":
    # 模拟用户
    username = "vpn_user@example.com"

    # 步骤1：生成共享密钥（管理员操作，需存数据库）
    # secret = generate_totp_secret()
    secret_bytes_pingcode = b')nDaeH8pgV;7QPMm'
    secret = generate_totp_secret_by_byte(secret_bytes_pingcode)

    # secret = "HT2DFOXYXE6ACECV4SYT3NWU6ICWVMCUNKFLXMRWB6GBL3Y6766Q"
    print(f"✅ 生成共享密钥（Base32）：{secret}")

    # 步骤2：生成二维码（用户扫码绑定）
    # generate_totp_qr(secret, username)

    # 步骤3：生成当前有效OTP（模拟手机验证器）
    current_otp = totp_generate(secret)
    print(f"\n🔢 当前30秒内有效OTP：{current_otp}")
    #
    # # 步骤4：验证用户输入的OTP（登录VPN时的逻辑）
    # user_input = input("\n请输入要验证的OTP码（输入上面的码即可）：")
    # is_valid = totp_verify(secret, user_input)
    #
    # if is_valid:
    #     print("✅ OTP验证通过！允许登录VPN")
    # else:
    #     print("❌ OTP验证失败！拒绝登录")