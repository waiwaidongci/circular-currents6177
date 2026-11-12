import{onUnmounted}from 'vue';export function usePolling(callback:()=>void,delay=2000){const id=setInterval(callback,delay);onUnmounted(()=>clearInterval(id));}
