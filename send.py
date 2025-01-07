import subprocess, re, sqlite3, os
from datetime import datetime
from time import sleep
from serverchan_sdk import sc_send

def get_sms_list():
    result = subprocess.run(['mmcli', '-m', '0', '--messaging-list-sms'], capture_output=True, text=True)
    listStr = result.stdout.split("\n")
    r = r'SMS/(\d+)\s\((sent|received|unknown)\)'
    for line in listStr:
        match = re.search(r, line)
        if match:
            num = match.group(1)
            sms_type = match.group(2)
            get_sms_content(num, sms_type)

def save_sms_2_sqlite(sms_data):
    c = conn.cursor()
    if sms_data["type"] == "2":
        c.execute("select * from sms where number = ? and content = ? and timestamp = ? and type = ?", (sms_data['number'], sms_data['content'], sms_data['timestamp'], sms_data['type']))

        if c.fetchone() is None:
            try:
                send_received_msg(sms_data)
                c.execute("INSERT INTO sms (number, content, timestamp, type) VALUES (?, ?, ?, ?)", (sms_data['number'], sms_data['content'], sms_data['timestamp'], 2))
            except:
                print("发送失败，稍后再试")
            

    conn.commit()
    pass

def send_received_msg(sms_data):
    print("转发短信")
    msg_title = "收到来自%s的短信" % sms_data['number']
    msg_data= '''
收到来自%s的短信：      

%s     

时间：%s     

''' % (sms_data['number'], sms_data['content'], sms_data['timestamp'])
    
    response = sc_send(apikey, msg_title, msg_data, {"tags": "短信转发"})
    print(response)
    pass

def get_sms_content(num, sms_type):
    sms_data = {}
    switcher = {
        "sent": "1",
        "received": "2",
        "unknown": "3",
    }
    sms_data['num'] = num
    sms_data['type'] = switcher.get(sms_type)
    sms_data['timestamp'] = datetime.now()

    result = subprocess.run(['mmcli', '-m', '0', '--sms', num], capture_output=True, text=True)
    listStr = result.stdout.split("\n")
    r1 = r'number:\s+(\d{1,11}|\+\d{13})'
    r2 = r'text:\s+(.*)'
    r3 = r'timestamp:\s+(.*)'
    
    for line in listStr:
        if re.search(r1, line):
            sms_data['number'] = re.search(r1, line).group(1)
        elif re.search(r2, line):
            sms_data['content'] = re.search(r2, line).group(1)
        elif re.search(r3, line):
            sms_data['timestamp'] = re.search(r3, line).group(1)
    save_sms_2_sqlite(sms_data)
    pass

def init_sqlite(filename):
    if not os.path.exists(filename):
        conn = sqlite3.connect(filename)
        c = conn.cursor()
        c.execute('''CREATE TABLE sms (id INTEGER PRIMARY KEY AUTOINCREMENT, number TEXT, content TEXT, timestamp TEXT, type TEXT)''')
        conn.commit()
        return conn
    else:
        return sqlite3.connect(filename)


def main():
    db_file = os.path.dirname(os.path.abspath(__file__))+"/sms.db"
    print("数据库文件路径：", db_file)
    global conn
    global apikey

    apikey = "sctp1847tsppcpbegpbenuxft3qomyz"
    conn = init_sqlite(db_file)

    while True:
        get_sms_list()
        sleep(10)

if __name__ == '__main__':
    
    main()