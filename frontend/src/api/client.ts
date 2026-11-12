export async function request<T>(path:string,options:RequestInit={}):Promise<T>{
 const response=await fetch('/api'+path,{...options,headers:{'Content-Type':'application/json',Authorization:'Bearer '+localStorage.getItem('currents_token'),...options.headers}});
 if(!response.ok){const data=await response.json().catch(()=>({detail:'连接中断，请重试'})); if(response.status===401){localStorage.removeItem('currents_token');localStorage.removeItem('currents_user');} throw new Error(typeof data.detail==='string'?data.detail:'输入内容未通过校验，请检查取值范围');}
 return response.json();
}
export async function download(path:string,filename:string){const r=await fetch('/api'+path,{headers:{Authorization:'Bearer '+localStorage.getItem('currents_token')}});if(!r.ok)throw new Error('导出失败，请等待计算完成后重试');const url=URL.createObjectURL(await r.blob());const a=document.createElement('a');a.href=url;a.download=filename;a.click();URL.revokeObjectURL(url);}
