<script setup lang="ts">import{states}from '../../constants/enums';defineProps<{status:string}>()</script><template><span class="status" :class="status">{{states[status]||status}}</span></template>
