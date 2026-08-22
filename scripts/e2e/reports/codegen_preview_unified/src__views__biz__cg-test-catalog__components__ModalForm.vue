--- boot/src/views/biz/cg-test-catalog/components/ModalForm.vue
+++ fastapi/src/views/biz/cg-test-catalog/components/ModalForm.vue
@@ -24,7 +24,7 @@
   formModel: normalizeFormData(),
 })
 
-const modalTitle = computed(() => state.dataId ? '编辑' : '新增')
+const modalTitle = computed(() => state.dataId ? '编辑CgTestCatalog' : '新增CgTestCatalog')
 const rules = computed<FormRules>(() => ({
 }))
 
