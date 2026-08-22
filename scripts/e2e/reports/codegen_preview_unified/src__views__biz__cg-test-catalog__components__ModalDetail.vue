--- boot/src/views/biz/cg-test-catalog/components/ModalDetail.vue
+++ fastapi/src/views/biz/cg-test-catalog/components/ModalDetail.vue
@@ -36,7 +36,7 @@
 </script>
 
 <template>
-  <NModal v-model:show="state.showModal" preset="card" draggable :mask-closable="false" title="详情" style="width: 680px">
+  <NModal v-model:show="state.showModal" preset="card" draggable :mask-closable="false" title="CgTestCatalog详情" style="width: 680px">
     <NScrollbar class="max-h-[min(620px,calc(100vh-300px))] pr-16px">
       <NSpin :show="state.loading">
         <NDescriptions label-placement="left" bordered :column="1">
