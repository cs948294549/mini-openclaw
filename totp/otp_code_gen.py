import time
import hmac
import hashlib
import base64

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


def otp(alg="SHA1", secret_bytes=None):
    alg_map = {
        "MD5": hashlib.md5,
        "SHA1": hashlib.sha1,
        "SHA256": hashlib.sha256,
        "SHA512": hashlib.sha512
    }

    # 2. 获取时间窗口（转8字节大端序二进制）
    time_step = get_time_step()
    time_bytes = time_step.to_bytes(8, byteorder='big')  # 8字节大端序

    # 3. HMAC-SHA1加密（TOTP标准算法）
    hmac_result = hmac.new(secret_bytes, time_bytes, alg_map[alg]).digest()

    # 4. 动态截取4字节数据（取最后4位作为偏移量）
    offset = hmac_result[-1] & 0x0F  # 取最后1字节的低4位作为偏移
    truncated = hmac_result[offset:offset + 4]  # 截取4字节

    # 5. 转整数并取后6位（去掉最高位的符号位）
    truncated_int = int.from_bytes(truncated, byteorder='big') & 0x7FFFFFFF
    otp = truncated_int % (10 ** 6)

    return f"{otp:0{6}d}"

k = "HT2DFOXYXE6ACECV4SYT3NWU6ICWVMCUNKFLXMRWB6GBL3Y6766Q"

def base32_byte(secret):
    secret_padded = secret.ljust((len(secret) + 7) // 8 * 8, '=')
    try:
        secret_bytes = base64.b32decode(secret_padded, casefold=True)
        return secret_bytes
    except base64.binascii.Error:
        raise ValueError("共享密钥不是有效的Base32编码")

if __name__ == '__main__':
    



    secret_bytes_vpn = base32_byte(k)

    secret_bytes_dk = b'\xf4\xc1\x8eL\xf7&\xce\xe6\xdeyV\x9b\xc5+\x9a\x15\xc7\xdfqn'

    secret_bytes_pingcode = b')nDaeH8pgV;7QPMm'

    # secret_bytes = b'<\xf42\xba\xf8\xb9<\x01\x10U\xe4\xb1=\xb6\xd4\xf2\x05j\xb0Tj\x8a\xbb\xb26\x0f\x8c\x15\xef\x1e\xff\xbd'


    print(otp(alg="SHA1", secret_bytes=secret_bytes_pingcode))

