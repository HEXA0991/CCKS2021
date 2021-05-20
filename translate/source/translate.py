from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tmt.v20180321 import tmt_client, models
import json
import os
import time
from tqdm import tqdm
import re

root = os.getcwd() + '\\translate\\'
path = root + 'task1_train.txt'
new_path = root + 'en_task1_train.txt'
en_path = root + 'en_temp.txt'

secret_id = 'AKIDPct0NYm2uHRBi7CDvSMA0cxCBxS0HejY'
secret_key = 'mLgkOpGTQt6h4UAbstiJ5ey2tpXyBFbg'

class Loader:

    def __init__(self, path):
        '''
        input: 语料路径
        '''
        try:
            with open(path, mode='r', encoding='utf-8') as f:
                conts = f.readlines()
        except:
            with open(path, mode='r', encoding='gbk') as f:
                conts = f.readlines()
        
        self.corpuses = self.convert(conts)


    def convert(self, strs):
        '''
        input: 包含语料的字符串列表\n
        output: 语料字典
        '''
        jsons = [json.loads(cont) for cont in strs]
        try:
            jsons[0]['entities']    # 判断是否是标注好的语料
            for json_ in jsons:
                temp = []   # 暂时保存转换好的实体内容
                for entity in json_['entities']:
                    temp.append(dict(entity))
                json_['entities'] = temp
            self.labeled_flag = True    # 是否是标记好的语料标识符
            return jsons

        except:
            self.labeled_flag = False
            return jsons

class Processer:

    def __init__(self, path):
        '''
        input: 语料路径\n
        '''
        self.time_offset = 0.0              # 本机与服务器整秒时间偏移量
        self.t_prev = self.get_time() - 1 # 初始化翻译时间戳，由于服务器计时是按整秒所以转换成整形数
        self.cnt = 0                        # 一秒钟已经翻译几次的计数器
        loader = Loader(path)
        self.raw_corpuses = loader.corpuses
        self.labeled_flag = loader.labeled_flag
        self.process()
        

    def get_time(self):
        return time.time() - self.time_offset
    

    def process(self):
        '''
        input: null\n
        output: null\n
        将loader中语料翻译并写入文件
        '''
        self.ch_corpuses = self.pos_into_mark(self.raw_corpuses)
        # self.en_corpuses = self.chs_to_ens(self.ch_corpuses)

        # self.write_all(en_path, self.en_corpuses)
        if self.labeled_flag:
            self.done_corpuses = self.refill(en_path)
        else:
            self.done_corpuses = self.en_corpuses
        
        self.write_all(new_path, self.done_corpuses)
        
        pass


    def write_all(self, new_path, corpuses):
        with open(new_path, mode='w', encoding='utf-8') as f:
            pass
        with open(new_path, mode='a', encoding='utf-8') as f:
            for cor in corpuses:
                converted_json = json.dumps(cor, ensure_ascii=False)
                f.write(converted_json + '\n')


    def refill(self, en_path):
        '''
        input: 翻译完成的英文语料\n
        output: 将对应实体放回文本相应位置后的语料
        '''
        res = []   # 存放装填之后的语料
        en_corpuses = Loader(en_path).corpuses
        with tqdm(desc='Refilling', total=len(en_corpuses)) as tbar:
            for cor in en_corpuses:
                done = self.refill_sub(cor)
                res.append(done)
                tbar.update(1)
        return res


    def refill_sub(self, dic):
        '''
        input: 一个需要处理的英文语料dict\n
        output: 处理好的英文语料dict
        '''
        text = dic['originalText']
        ents = dic['entities']
        res = {
            'originalText' : None,
            'entities' : []
        } 
        for i in range(len(ents)):
            for item in ents:
                if item['#'] == i:
                    ent = item
            sign = '# (' + str(i) + ')'
            while True:
                try:
                    start_pos = text.index(sign)
                except:
                    sign = '# _ (' + str(i) + ')'
                    try:
                        start_pos = text.index(sign)
                    except:
                        break
                end = start_pos + len(sign)
                end_pos = start_pos + len(ent['entity'])
                text = text[:start_pos] + ent['entity'] + text[end:]
                res['entities'].append({
                    'start_pos' : start_pos,
                    'end_pos' : end_pos,
                    'label_type' : ents[i]['label_type']
                })

        
        res['originalText'] = text

        return res



    def chs_to_ens(self, ch_corpuses):
        '''
        input: 将实体位置替换后的中文语料文本和实体列表\n
        output: 翻译后的语料文本和实体列表
        '''
        en_corpuses = []    # 保存英文语料
        with tqdm(desc='Tran_dicts', total=len(ch_corpuses)) as tbar:
            for ch_cor in ch_corpuses:
                en_cor = self.ch_to_en(ch_cor)
                en_corpuses.append(en_cor)
                tbar.update(1)
        
        return en_corpuses


    def ch_to_en(self, dic):
        '''
        input: 一个将实体位置替换后的中文语料文本和实体词典\n
        output: 翻译成英文的语料
        '''
        res = {
            'originalText' : None
        }   # 保存翻译完成的文本

        # with tqdm(desc='Tran_text',total=(1 + len(dic['entities']))) as tbar:
        en_text = self.trans(dic['originalText'])
        # tbar.update(1)

        en_ents = []
        
        if self.labeled_flag:
            for ent in dic['entities']:
                en_ent_text = self.trans(ent['entity'])
                

                en_ents.append({
                    '#' : ent['#'],
                    'entity' : en_ent_text,
                    'label_type' : ent['label_type']
                })
                # tbar.update(1)

                
        res['originalText'] = en_text
        
        if self.labeled_flag:
            res['entities'] = en_ents

        return res

    def trans(self, text):
        '''
        input: 待翻译的文本\n
        output: 翻译好的文本
        是封装了保证能翻译以及等待和记录翻译时间的版本
        '''
        # 判断是否超过
        if (self.get_time() - self.t_prev) < 1 and self.cnt >= 4:
            # while (self.get_time() - self.t_prev) == 0:
                # pass
            self.t_prev = self.get_time()    
            self.cnt = 0
        elif (self.get_time() - self.t_prev) >= 1:
            self.t_prev = self.get_time()
            self.cnt = 0

        en_text = self.translate(text)

        if not en_text:
            # 如果没有返回内容代表翻译失败，需要再次翻译
            while not en_text:
                # time.sleep(0.03)  等待不如重试快
                en_text = self.translate(text)
                # self.time_offset += 0.05 # 校准本机时间偏移
            
            self.t_prev = self.get_time()    # 记录调用翻译的时间戳
            self.cnt = 1
        else:
            self.cnt += 1
        
        return en_text

    def translate(self, text):
        '''
        input: 待翻译的文本，实体位置用 #(number)代替\n
        output: 翻译好的文本
        '''
        try: 
            cred = credential.Credential(secret_id, secret_key) 
            httpProfile = HttpProfile()
            httpProfile.endpoint = "tmt.tencentcloudapi.com"

            clientProfile = ClientProfile()
            clientProfile.httpProfile = httpProfile
            client = tmt_client.TmtClient(cred, "ap-beijing", clientProfile) 

            req = models.TextTranslateRequest()
            params = {
                "SourceText": text,
                "Source": "zh",
                "Target": "en",
                "ProjectId": 0,
                "UntranslatedText": "#"
            }
            req.from_json_string(json.dumps(params))

            resp = client.TextTranslate(req) 
            json_str = resp.to_json_string()
            j = json.loads(json_str)
            return j['TargetText']

        except TencentCloudSDKException as err: 
            # print('\n', err)
            return None


    def replace(self, text, ents):
        '''
        input: 一条待处理的文本字符串 & 实体位置及类型列表\n
        output: 处理好的文本和实体dict
        '''
        res = {
            'originalText' : None,
            'entities' : []
        }   # 暂时保存处理好的字符串与实体
        t = text    # 暂时保存处理中的字符串

        # 将文本中实体位置替换为同等长度的 $ ，并且为实体出现顺序编号
        ## 考虑到文档中本身就有单个#出现，为不产生混淆使用美元符当作占位符
        for i in range(len(ents)):
            start_pos = ents[i]['start_pos']
            end_pos = ents[i]['end_pos']
            str_ent = t[start_pos:end_pos]        # 要替换的中文实体
            dollar_signs = '$' * (end_pos - start_pos)  # 做填充字符串的井号字符串
            t = t[:start_pos] + dollar_signs + t[end_pos:]
            res['entities'].append({
                '#' : i,
                'entity' : str_ent,
                'label_type' : ents[i]['label_type']
            })
        
        # 将替换结束的文本实体位置的 $ 字符串替换为 #(序号) 序列
        ## 防止美元符干扰翻译，将美元符换为# 和序号的序列
        pattern = r'\$+'
        cnt = 0 # 填充到几号实体的计数器
        prev = 'I will never stop loving you, even though it doesnt make sense anymore.'
        while t != prev:
            substitute = '#({})'.format(str(cnt))
            prev = t    # 保存替换前的字符串
            t = re.sub(pattern, substitute, t, count=1)
            cnt += 1
        
        res['originalText'] = t

        return res


    def pos_into_mark(self, dicts):
        '''
        input: 使用实体起始结束位置标记实体位置的dict列表\n
        output: 将文本中加入实体标记代替实体本身的dict
        '''
        res = []   # 存储处理好的文本和实体dict
        with tqdm(desc='Marking', total=len(dicts)) as tbar:
            for dic in dicts:
                text = dic['originalText']  # 存储待处理的字符串
                ents = dic['entities']      # 存储实体
                res.append(self.replace(text, ents))
                tbar.update(1)


        return res



if __name__ == '__main__':
    translator = Processer(path)
