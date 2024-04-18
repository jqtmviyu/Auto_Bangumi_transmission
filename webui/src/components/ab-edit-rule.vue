<script lang="ts" setup>
import type { BangumiRule } from '#/bangumi';

const emit = defineEmits<{
  (e: 'update', rule: BangumiRule): void;
  (e: 'enable', id: number): void;
  (e: 'disable', id: number): void;
  (
    e: 'deleteFile',
    opts: { id: number; deleteFile: boolean }
  ): void;
}>();

const { t } = useMyI18n();

const show = defineModel('show', { default: false });
const rule = defineModel<BangumiRule>('rule', {
  required: true,
});

const deleteFileDialogShow = ref<boolean>(false);
watch(show, (val) => {
  if (!val) {
    deleteFileDialogShow.value = false;
  }
});

function showDeleteFileDialog() {
  deleteFileDialogShow.value = true;
}

function emitdeleteFile(deleteFile: boolean) {
  emit('deleteFile', {
    id: rule.value.id,
    deleteFile,
  });
}

function emitUpdate() {
  emit('update', rule.value);
}

function emitEnable() {
  emit('enable', rule.value.id);
}

function emitDisable() {
  emit('disable', rule.value.id);
}

</script>

<template>
  <ab-popup v-model:show="show" :title="t('homepage.rule.edit_rule')" css="w-380">

    <div space-y-12>
      <ab-rule v-model:rule="rule"></ab-rule>

      <div fx-cer justify-end gap-x-10>
        <ab-button size="small" type="warn" @click="showDeleteFileDialog">
          {{ $t('homepage.rule.delete') }}
        </ab-button>
        <ab-button v-if="rule.deleted" size="small" @click="emitEnable">
          {{ $t('homepage.rule.enable') }}
        </ab-button>
        <ab-button v-else size="small" @click="emitDisable">
          {{ $t('homepage.rule.disable') }}
        </ab-button>
        <ab-button size="small" @click="emitUpdate">
          {{ $t('homepage.rule.update') }}
        </ab-button>
      </div>
    </div>

    <ab-popup
      v-model:show="deleteFileDialogShow"
      :title="$t('homepage.rule.delete')"
    >
      <div>{{ $t('homepage.rule.delete_hit') }}</div>
      <div line my-8></div>

      <div f-cer gap-x-10>
        <ab-button size="small" type="warn" @click="() => emitdeleteFile(true)">
          {{ $t('homepage.rule.yes_btn') }}
        </ab-button>
        <ab-button size="small" @click="() => emitdeleteFile(false)">
          {{ $t('homepage.rule.no_btn') }}
        </ab-button>
      </div>
    </ab-popup>
  </ab-popup>
</template>
