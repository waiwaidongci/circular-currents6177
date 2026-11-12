import numpy as np
def chord_matrix(a,b):
    angles=np.deg2rad(np.r_[a,b]);xy=np.column_stack([np.cos(angles),np.sin(angles)])
    return np.sqrt(np.maximum(0,((xy[:,None]-xy[None,:])**2).sum(axis=2)))
def statistic(distance,left,right):
    n=len(left);m=len(right)
    return max(0.0,float(2*distance[np.ix_(left,right)].sum()/(n*m)-distance[np.ix_(left,left)].sum()/n**2-distance[np.ix_(right,right)].sum()/m**2))
def compare(a,b,repetitions,seed):
    a=np.asarray(a,float);b=np.asarray(b,float)
    if min(len(a),len(b))<2 or max(len(a),len(b))>250:raise ValueError('每组须有2–250个观测')
    if not np.isfinite(a).all() or not np.isfinite(b).all() or ((np.r_[a,b]<0)|(np.r_[a,b]>=360)).any():raise ValueError('角度须在[0,360)')
    if not 1<=repetitions<=999:raise ValueError('置换次数无效')
    d=chord_matrix(a,b);n=len(a);order=np.arange(n+len(b));observed=statistic(d,order[:n],order[n:]);rng=np.random.default_rng(seed);null=[]
    for _ in range(repetitions):
        perm=rng.permutation(order);null.append(statistic(d,perm[:n],perm[n:]))
    extreme=sum(x>=observed-1e-12 for x in null)
    return {'statistic':observed,'p_value':(extreme+1)/(repetitions+1),'extreme':extreme,'permutations':repetitions,'seed':seed,'null_statistics':null,'null_quantiles':np.quantile(null,[.025,.5,.975]).tolist(),'definition':'V-energy: 2 mean cross chord distance - mean within A (diagonal included) - mean within B; upper-tail label permutation with +1 correction'}
