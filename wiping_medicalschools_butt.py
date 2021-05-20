import json
import os
from tqdm import tqdm

root = os.getcwd() + '\\translate\\'
path = root + 'task1_train.txt'
new_path = root + 'en_task1_train.json'
en_path = root + 'en_temp.json'

with open(en_path,mode='r',encoding='utf-8') as f:
    lines = f.readlines()

with open(en_path,mode='w',encoding='utf-8') as f:
    pass

res = []
temp = ''

with tqdm(total=len(lines)) as tbar:
    for line in lines:
        if '}, {\n' in line:
            temp = temp + '}'
            with open(en_path,mode='a',encoding='utf-8') as f:
                f.write(temp + '\n')
            temp = '{'
        elif '{\n' in line:
            temp += line.strip()
        else :
            temp += line.strip()
        tbar.update(1)