import{request}from './client';import type{Run}from '../types/domain';export const list=()=>request<Run[]>('/runs');
export const create=(data:unknown)=>request<Run>('/runs',{method:'POST',body:JSON.stringify(data)});
