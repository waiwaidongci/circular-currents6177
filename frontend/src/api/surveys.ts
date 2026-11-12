import{request}from './client';import type{Survey}from '../types/domain';export const list=()=>request<Survey[]>('/surveys');
export const create=(data:unknown)=>request<Survey>('/surveys',{method:'POST',body:JSON.stringify(data)});
export const patch=(id:number,data:unknown)=>request<Survey>('/surveys/'+id,{method:'PATCH',body:JSON.stringify(data)});
