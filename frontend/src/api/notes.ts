import{request}from './client';import type{Note}from '../types/domain';export const list=()=>request<Note[]>('/notes');
export const create=(data:unknown)=>request<Note>('/notes',{method:'POST',body:JSON.stringify(data)});
export const review=(id:number,decision:string,comment:string)=>request<Note>('/notes/'+id+'/review',{method:'PATCH',body:JSON.stringify({decision,comment})});
