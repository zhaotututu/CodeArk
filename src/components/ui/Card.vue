<script setup lang="ts">
import { type ClassValue, clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

const props = defineProps<{
  class?: ClassValue
}>()

function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}
</script>

<template>
  <div :class="cn('rounded-xl border bg-card text-card-foreground shadow', props.class)">
    <slot />
  </div>
</template>

