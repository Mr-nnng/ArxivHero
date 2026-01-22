<script setup lang="ts">
import { darkTheme, dateZhCN, zhCN, NConfigProvider } from 'naive-ui'

</script>

<template>
  <n-config-provider :locale="zhCN" :date-locale="dateZhCN" :theme="darkTheme">
    <router-view />
  </n-config-provider>
</template>
