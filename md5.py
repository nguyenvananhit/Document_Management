import hashlib
import itertools
import string

def md5_hash(text):
    """Tạo mã băm MD5 từ chuỗi văn bản"""
    return hashlib.md5(text.encode()).hexdigest()

def brute_force_md5(target_hash, max_length=4):
    """Tấn công bạo lực để tìm chuỗi văn bản khớp với mã băm MD5"""
    chars = string.ascii_letters + string.digits + string.punctuation
    for length in range(1, max_length + 1):
        for guess in itertools.product(chars, repeat=length):
            guess_text = ''.join(guess)
            if md5_hash(guess_text) == target_hash:
                return guess_text
    return None

# Mã băm MD5 cần giải mã
target_hash = 'e99a18c428cb38d5f260853678922e03'  # Ví dụ mã băm MD5 của '123456'

# Tìm chuỗi văn bản khớp với mã băm
result = brute_force_md5(target_hash, max_length=5)
if result:
    print(f'Mã băm MD5 khớp với chuỗi văn bản: {result}')
else:
    print('Không tìm thấy chuỗi văn bản khớp với mã băm MD5.')
