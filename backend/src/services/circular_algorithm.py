import numpy as np
from scipy.special import i0e,i1e
from scipy.optimize import brentq
from scipy.stats import vonmises
EPS=1e-8
def concentration(r):
    if not np.isfinite(r) or r<0 or r>1:raise ValueError('合向量长度R须在[0,1]')
    if r<EPS:return 0.0
    if 1-r<EPS:return None
    upper=2.0
    while float(i1e(upper)/i0e(upper))<r:upper*=2
    return float(brentq(lambda k:float(i1e(k)/i0e(k))-r,0,upper,xtol=1e-11))
def summarize(values):
    values=np.asarray(values,dtype=float)
    if values.ndim!=1 or len(values)<2 or not np.isfinite(values).all():raise ValueError('圆周统计至少两个有限角度')
    if ((values<0)|(values>=360)).any():raise ValueError('角度须在[0,360)')
    theta=np.deg2rad(values);c=float(np.cos(theta).mean());s=float(np.sin(theta).mean());r=float(np.clip(np.hypot(c,s),0,1));r2=float(abs(np.exp(2j*theta).mean()))
    mean=None if r<EPS else float(np.rad2deg(np.arctan2(s,c))%360)
    if mean is not None and (mean<1e-10 or 360-mean<1e-10):mean=0.0
    kappa=concentration(r);edges=np.arange(0,361,30);counts,_=np.histogram(values,bins=edges)
    fitted=None
    if mean is not None and kappa is not None:
        cdf=vonmises.cdf(np.deg2rad(edges),kappa,loc=np.deg2rad(mean));fitted=np.diff(cdf).tolist()
    status='mean_undefined' if mean is None else 'concentration_degenerate' if kappa is None else 'estimated'
    return {'n':len(values),'mean_bearing':mean,'resultant':r,'second_resultant':r2,'circular_variance':1-r,'kappa':kappa,'fit_status':status,'histogram':[{'lower':int(lo),'upper':int(hi),'count':int(n),'proportion':float(n/len(values)),'fitted_probability':None if fitted is None else fitted[i]} for i,(lo,hi,n) in enumerate(zip(edges[:-1],edges[1:],counts))],'warning':'一阶合向量弱而二阶强；单峰von Mises不能概括此分布' if r<.2 and r2>.5 else 'von Mises为单峰描述模型，未作拟合优度保证'}
