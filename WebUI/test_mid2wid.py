# 62 to 10 dict
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
DICT = {}


def get_dict():
    for index in range(len(ALPHABET)):
        DICT[ALPHABET[index]] = index


# 62 to 10
def key62_to_key10(str_62):
    value = 0;
    for s in str_62:
        value = value * 62 + DICT[s]
    return value

# 10 to 62
def key10_to_key62(value):
    if value == 0:
        return ALPHABET[0]
    result = ''
    while value > 0:
        result = ALPHABET[value % 62] + result
        value = value // 62
    return result

# transfrom msg_url to msg_id
def wid_to_mid(wid):
    length = len(wid)
    mid = ''
    group = int(length / 4)  # four characters per group
    last_count = length % 4  # head group character counts

    for loop in range(group):
        value = key62_to_key10(wid[length - (loop + 1) * 4:length - loop * 4])
        mid = str(value) + mid
    if last_count:
        value = key62_to_key10(wid[:length - group * 4])
        mid = str(value) + mid
    return mid


# transform mid to wid
def mid_to_wid(mid):
    # mid to wid follows reverse steps of wid_to_mid
    mid_len = len(mid)
    wid = ''

    while mid_len > 0:
        group = 7  # Every group should have 7 digits in mid
        if mid_len < 7:
            group = mid_len

        sub_mid = mid[mid_len - group: mid_len]
        value = int(sub_mid)

        # Convert 10 base value to 62 base
        wid_group = key10_to_key62(value)
        wid = wid_group + wid

        mid_len -= group

    return wid

if __name__ == "__main__":
    get_dict()
    wid = "QcIif0Rd7"
    print(wid_to_mid(wid))
    mid = "5231122749326560" # "5230302030204545"
    print(mid_to_wid(mid))