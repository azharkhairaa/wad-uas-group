<script setup>
import { computed } from 'vue'

import { STATUS_BOOKING } from '@/utils/status'

const props = defineProps({ status: { type: String, required: true } })
const info = computed(() => STATUS_BOOKING[props.status] || { label: props.status, nada: '' })
</script>

<template>
  <span class="badge" :class="info.nada">{{ info.label }}</span>
</template>
