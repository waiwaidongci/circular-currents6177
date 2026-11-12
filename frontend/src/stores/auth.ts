import {reactive,computed} from 'vue';import{login}from '../api/auth';import type{User}from '../types/domain';
let saved:User|null=null;try{saved=JSON.parse(localStorage.getItem('currents_user')||'null')}catch{}
export const auth=reactive({user:saved});export const canEdit=computed(()=>auth.user?.role==='admin'||auth.user?.role==='analyst');export const isAdmin=computed(()=>auth.user?.role==='admin');
export async function signIn(email:string,password:string){const data=await login(email,password);localStorage.setItem('currents_token',data.access_token);localStorage.setItem('currents_user',JSON.stringify(data.user));auth.user=data.user;}
export function signOut(){localStorage.removeItem('currents_token');localStorage.removeItem('currents_user');auth.user=null;}
