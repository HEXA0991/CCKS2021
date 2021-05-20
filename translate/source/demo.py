import json
import os
from tencentcloud.common import credential
from tencentcloud.common.profile.client_profile import ClientProfile
from tencentcloud.common.profile.http_profile import HttpProfile
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
import re
import time

root = os.getcwd() + '\\translate\\'
path = root + 'task1_train.txt'
new_path = root + 'en_task1_train.txt'



secret_id = 'AKIDPct0NYm2uHRBi7CDvSMA0cxCBxS0HejY'
secret_key = 'mLgkOpGTQt6h4UAbstiJ5ey2tpXyBFbg'

from tencentcloud.tmt.v20180321 import tmt_client, models
def translator(text):
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
            print(err) 
            return None

def replace(text, ents):
    '''
    input: 一条待处理的文本字符串 & 实体位置及类型列表\n
    output: 处理好的文本和实体dict
    '''
    res = {
        'originalText' : None,
        'entites' : []
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
        res['entites'].append({
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

def refill_sub(dic):
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
        start_pos = text.index(sign)
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

def write_all(done_corpuses, new_path):
    for item in done_corpuses:
        item['entities'] = str(item['entities'])
    converted_json = json.dumps(done_corpuses, ensure_ascii=False)
    with open(new_path, mode='w', encoding='utf-8') as f:
        f.write(converted_json)

dic = {
    'originalText' : 'One month before admission, because of "# (0), # (1)", # (2) showed: 1, # (3), with # (4). 2. # (5), # (6). After admission, the patients were treated with anti-infection, # (7), inhibition of # (8) enzyme secretion and nutritional support. "# (10)" was located in # (9) on January 16, 2014. The operation went smoothly, the symptoms improved after operation, and the family members asked to be discharged from the hospital. This time for further treatment, we will visit our hospital again, and the outpatient clinic will be admitted to the hospital with "# (11)". Since the spontaneous illness, he has been conscious, depressed, ate little, slept well, and his stool is normal, and his weight has not increased or decreased significantly.',
    'entities' : [{'#': 0, 'entity': 'Cholelithiasis', 'label_type': '疾病和诊断'}, {'#': 1, 'entity': 'Acute cholecystitis', 'label_type': '疾病和诊断'}, {'#': 2, 'entity': 'Lower abdominal CT', 'label_type': '影像检查'}, {'#': 3, 'entity': 'Multiple stones in the upper segment of common bile duct', 'label_type': '疾病和诊断'}, {'#': 4, 'entity': 'Dilatation of intrahepatic and extrahepatic bile duct', 'label_type': '疾病和诊断'}, {'#': 5, 'entity': 'Acute cholecystitis', 'label_type': '疾病和诊断'}, {'#': 6, 'entity': 'Multiple gallbladder stones', 'label_type': '疾病和诊断'}, {'#': 7, 'entity': 'Liver', 'label_type': '解剖部位'}, {'#': 8, 'entity': 'Pancreas', 'label_type': '解剖部位'}, {'#': 9, 'entity': 'B ultrasound', 'label_type': '影像检查'}, {'#': 10, 'entity': 'Puncture cholecystostomy', 'label_type': '手术'}, {'#': 11, 'entity': 'Cholelithiasis after PTCD', 'label_type': '疾病和诊断'}]
}

if __name__ == '__main__':
    # a = translator('缘于入院前1月余因“胆石症、急性胆囊炎”就诊我院，下腹部CT示：1、胆总管上段多发结石，伴肝内外胆管扩张。2、急性胆囊炎，胆囊多发结石。入院后予抗感染，保肝，抑制胰酶分泌，营养支持等治疗，于2014.01.16在B超定位上行“胆囊穿刺造瘘术”，术顺，术后症状好转，家属要求出院。此次为行进一步治疗再次就诊我院，门诊拟“胆石症PTCD术后”收入院，自发病以来神志清，精神不振，饮食少，睡眠可，二便正常，体重未见明显增减。')

    # print(a)
    # a = '缘于入院前1月余因“胆石症、急性胆囊炎”就诊我院，下腹部CT示：1、胆总管上段多发结石，伴肝内外胆管扩张。2、急性胆囊炎，胆囊多发结石。入院后予抗感染，保肝，抑制胰酶分泌，营养支持等治疗，于2014.01.16在B超定位上行“胆囊穿刺造瘘术”，术顺，术后症状好转，家属要求出院。此次为行进一步治疗再次就诊我院，门诊拟“胆石症PTCD术后”收入院，自发病以来神志清，精神不振，饮食少，睡眠可，二便正常，体重未见明显增减。'
    a = refill_sub(dic)
    write_all([a], new_path)
    
    
    pass