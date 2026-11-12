import{request}from './client';import type{Mooring}from '../types/domain';export const list=()=>request<Mooring[]>('/moorings');
export const patch=(id:number,data:unknown)=>request<Mooring>('/moorings/'+id,{method:'PATCH',body:JSON.stringify(data)});
