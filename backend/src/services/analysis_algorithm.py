from src.services.circular_algorithm import summarize
from src.services.energy_algorithm import compare
from src.utils.fingerprint import fingerprint
def analyze(rows_a,rows_b,config):
    a=sorted(rows_a,key=lambda r:r['code']);b=sorted(rows_b,key=lambda r:r['code'])
    result={'a':summarize([r['bearing'] for r in a]),'b':summarize([r['bearing'] for r in b]),'energy':compare([r['bearing'] for r in a],[r['bearing'] for r in b],config['permutations'],config['seed'])}
    result['input_snapshot']={'a':a,'b':b,'config':config}
    result['fingerprint']=fingerprint({'algorithm':'circular-energy-v1','a':a,'b':b,'config':config});result['interpretation']='两组单位圆分布差异；小p不代表差异大小、成因或航行风险。交换性要求观测独立；同浮标连续时间自相关可能破坏置换前提。'
    return result
