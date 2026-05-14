/*
 Navicat Premium Dump SQL

 Source Server         : dev-mysql
 Source Server Type    : MySQL
 Source Server Version : 90600 (9.6.0)
 Source Host           : localhost:3306
 Source Schema         : hei_data

 Target Server Type    : MySQL
 Target Server Version : 90600 (9.6.0)
 File Encoding         : 65001

 Date: 14/05/2026 18:58:47
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for client_user
-- ----------------------------
DROP TABLE IF EXISTS `client_user`;
CREATE TABLE `client_user`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `account` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '账号',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '密码',
  `nickname` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '昵称',
  `avatar` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '头像',
  `motto` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '座右铭',
  `gender` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '性别',
  `birthday` date NULL DEFAULT NULL COMMENT '生日',
  `email` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '电子邮箱',
  `github` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GitHub',
  `phone` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '手机号',
  `org_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属组织ID',
  `position_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属职位ID',
  `group_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属用户组ID',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `last_login_at` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '最后登录IP',
  `login_count` int NULL DEFAULT 0 COMMENT '登录次数',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_account`(`account` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = 'C端用户' ROW_FORMAT = DYNAMIC;


-- ----------------------------
-- Table structure for gen_basic
-- ----------------------------
DROP TABLE IF EXISTS `gen_basic`;
CREATE TABLE `gen_basic`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `db_table` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '主表名称',
  `db_table_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '主表主键',
  `module_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块名',
  `table_prefix` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '移除表前缀',
  `generate_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '生成方式',
  `module` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属模块',
  `menu_pid` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '上级目录',
  `class_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '类名',
  `form_layout` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '表单布局',
  `grid_whether` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '使用栅格',
  `package_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '包名',
  `author_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '作者',
  `gen_type` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'TABLE' COMMENT '生成类型（TABLE/TREE/LEFT_TREE_TABLE/MASTER_DETAIL）',
  `tree_parent_field` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '树父级字段',
  `tree_name_field` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '树显示名称字段',
  `sub_db_table` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表名称',
  `sub_db_table_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表主键',
  `sub_foreign_key` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表外键',
  `sub_class_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表类名',
  `sub_function_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表功能名',
  `sub_bus_name` varchar(200) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '子表业务名',
  `sort_code` int NULL DEFAULT NULL COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '代码生成基础' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of gen_basic
-- ----------------------------

-- ----------------------------
-- Table structure for gen_config
-- ----------------------------
DROP TABLE IF EXISTS `gen_config`;
CREATE TABLE `gen_config`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `basic_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '基础ID',
  `is_table_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '是否主键',
  `field_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字段名',
  `field_remark` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字段注释',
  `field_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '数据库类型',
  `field_language_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '语言数据类型',
  `effect_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '作用类型（input/textarea/select/radio/checkbox/datepicker/etc）',
  `dict_type_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字典编码',
  `whether_table` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'YES' COMMENT '列表显示',
  `whether_retract` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '列省略',
  `whether_add_update` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'YES' COMMENT '是否增改',
  `whether_required` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '必填',
  `whether_unique` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '唯一',
  `query_whether` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '是否查询',
  `query_type` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '查询方式',
  `table_type` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'MAIN' COMMENT '所属表类型（MAIN/SUB）',
  `sort_code` int NULL DEFAULT NULL COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_basic_id`(`basic_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '代码生成配置' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of gen_config
-- ----------------------------

-- ----------------------------
-- Table structure for rel_org_role
-- ----------------------------
DROP TABLE IF EXISTS `rel_org_role`;
CREATE TABLE `rel_org_role`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `org_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '组织ID',
  `role_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色ID',
  `scope` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '数据范围覆盖：ALL-全部，SELF-本人，ORG-本组织，ORG_AND_BELOW-本组织及以下，CUSTOM_ORG-自定义组织，GROUP-本用户组，GROUP_AND_BELOW-本用户组及以下，CUSTOM_GROUP-自定义用户组。为空则继承 rel_role_permission 的配置',
  `custom_scope_group_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义用户组ID列表(JSON数组)，scope=CUSTOM_GROUP时生效',
  `custom_scope_org_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义组织ID列表(JSON数组)，scope=CUSTOM_ORG时生效',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_org_role`(`org_id` ASC, `role_id` ASC) USING BTREE,
  INDEX `idx_role_id`(`role_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '组织-角色关联' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rel_org_role
-- ----------------------------
INSERT INTO `rel_org_role` VALUES ('140001', '10002', '40003', NULL, NULL, NULL);
INSERT INTO `rel_org_role` VALUES ('140002', '10003', '40005', NULL, NULL, NULL);
INSERT INTO `rel_org_role` VALUES ('140003', '10004', '40006', NULL, NULL, NULL);
INSERT INTO `rel_org_role` VALUES ('140004', '10005', '40007', NULL, NULL, NULL);

-- ----------------------------
-- Table structure for rel_role_permission
-- ----------------------------
DROP TABLE IF EXISTS `rel_role_permission`;
CREATE TABLE `rel_role_permission`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `role_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色ID',
  `permission_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '权限编码',
  `scope` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ALL' COMMENT '数据范围：ALL-全部，SELF-本人，ORG-本组织，ORG_AND_BELOW-本组织及以下，CUSTOM_ORG-自定义组织，GROUP-本用户组，GROUP_AND_BELOW-本用户组及以下，CUSTOM_GROUP-自定义用户组',
  `custom_scope_group_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义用户组ID列表(JSON数组)，scope=CUSTOM_GROUP时生效',
  `custom_scope_org_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义组织ID列表(JSON数组)，scope=CUSTOM_ORG时生效',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_role_permission`(`role_id` ASC, `permission_code` ASC) USING BTREE,
  INDEX `idx_permission_code`(`permission_code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色-权限关联' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rel_role_permission
-- ----------------------------
INSERT INTO `rel_role_permission` VALUES ('2000000001', '40001', 'sys:banner:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000002', '40001', 'sys:banner:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000003', '40001', 'sys:banner:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000004', '40001', 'sys:banner:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000005', '40001', 'sys:banner:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000006', '40001', 'sys:banner:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000007', '40001', 'sys:banner:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000008', '40001', 'sys:banner:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000009', '40001', 'sys:config:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000010', '40001', 'sys:config:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000011', '40001', 'sys:config:edit', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000012', '40001', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000013', '40001', 'sys:config:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000014', '40001', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000015', '40001', 'sys:config:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000016', '40001', 'sys:dev:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000017', '40001', 'sys:dev:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000018', '40001', 'sys:dev:gen:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000019', '40001', 'sys:dev:gen:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000020', '40001', 'sys:dev:gen:edit', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000021', '40001', 'sys:dev:gen:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000022', '40001', 'sys:dev:gen:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000023', '40001', 'sys:dev:gen:preview', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000024', '40001', 'sys:dev:gen:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000025', '40001', 'sys:dev:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000026', '40001', 'sys:dev:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000027', '40001', 'sys:dev:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000028', '40001', 'sys:dict:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000029', '40001', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000030', '40001', 'sys:dict:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000031', '40001', 'sys:dict:get-children', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000032', '40001', 'sys:dict:get-label', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000033', '40001', 'sys:dict:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000034', '40001', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000035', '40001', 'sys:dict:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000036', '40001', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000037', '40001', 'sys:dict:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000038', '40001', 'sys:dict:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000039', '40001', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000040', '40001', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000041', '40001', 'sys:file:download', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000042', '40001', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000043', '40001', 'sys:file:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000044', '40001', 'sys:file:upload', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000045', '40001', 'sys:group:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000046', '40001', 'sys:group:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000047', '40001', 'sys:group:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000048', '40001', 'sys:group:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000049', '40001', 'sys:group:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000050', '40001', 'sys:group:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000051', '40001', 'sys:group:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000052', '40001', 'sys:group:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000053', '40001', 'sys:group:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000054', '40001', 'sys:module:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000055', '40001', 'sys:module:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000056', '40001', 'sys:module:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000057', '40001', 'sys:module:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000058', '40001', 'sys:module:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000059', '40001', 'sys:module:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000060', '40001', 'sys:module:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000061', '40001', 'sys:module:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000062', '40001', 'sys:notice:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000063', '40001', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000064', '40001', 'sys:notice:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000065', '40001', 'sys:notice:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000066', '40001', 'sys:notice:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000067', '40001', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000068', '40001', 'sys:notice:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000069', '40001', 'sys:notice:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000070', '40001', 'sys:org:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000071', '40001', 'sys:org:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000072', '40001', 'sys:org:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000073', '40001', 'sys:org:grant-role', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000074', '40001', 'sys:org:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000075', '40001', 'sys:org:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000076', '40001', 'sys:org:own-roles', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000077', '40001', 'sys:org:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000078', '40001', 'sys:org:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000079', '40001', 'sys:org:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000080', '40001', 'sys:org:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000081', '40001', 'sys:permission:by-module', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000082', '40001', 'sys:permission:modules', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000083', '40001', 'sys:position:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000084', '40001', 'sys:position:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000085', '40001', 'sys:position:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000086', '40001', 'sys:position:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000087', '40001', 'sys:position:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000088', '40001', 'sys:position:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000089', '40001', 'sys:position:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000090', '40001', 'sys:position:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000091', '40001', 'sys:resource:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000092', '40001', 'sys:resource:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000093', '40001', 'sys:resource:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000094', '40001', 'sys:resource:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000095', '40001', 'sys:resource:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000096', '40001', 'sys:resource:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000097', '40001', 'sys:resource:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000098', '40001', 'sys:resource:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000099', '40001', 'sys:resource:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000100', '40001', 'sys:role:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000101', '40001', 'sys:role:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000102', '40001', 'sys:role:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000103', '40001', 'sys:role:grant-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000104', '40001', 'sys:role:grant-resource', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000105', '40001', 'sys:role:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000106', '40001', 'sys:role:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000107', '40001', 'sys:role:own-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000108', '40001', 'sys:role:own-resource', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000109', '40001', 'sys:role:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000110', '40001', 'sys:role:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000111', '40001', 'sys:role:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000112', '40001', 'sys:user:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000113', '40001', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000114', '40001', 'sys:user:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000116', '40001', 'sys:user:grant-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000117', '40001', 'sys:user:grant-role', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000118', '40001', 'sys:user:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000119', '40001', 'sys:user:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000121', '40001', 'sys:user:own-permission-detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000122', '40001', 'sys:user:own-roles', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000123', '40001', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000124', '40001', 'sys:user:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000125', '40001', 'sys:user:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000126', '40002', 'sys:banner:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000127', '40002', 'sys:banner:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000128', '40002', 'sys:banner:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000129', '40002', 'sys:banner:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000130', '40002', 'sys:banner:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000131', '40002', 'sys:banner:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000132', '40002', 'sys:banner:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000133', '40002', 'sys:banner:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000134', '40002', 'sys:config:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000135', '40002', 'sys:config:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000136', '40002', 'sys:config:edit', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000137', '40002', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000138', '40002', 'sys:config:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000139', '40002', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000140', '40002', 'sys:config:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000141', '40002', 'sys:dict:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000142', '40002', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000143', '40002', 'sys:dict:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000144', '40002', 'sys:dict:get-children', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000145', '40002', 'sys:dict:get-label', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000146', '40002', 'sys:dict:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000147', '40002', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000148', '40002', 'sys:dict:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000149', '40002', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000150', '40002', 'sys:dict:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000151', '40002', 'sys:dict:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000152', '40002', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000153', '40002', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000154', '40002', 'sys:file:download', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000155', '40002', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000156', '40002', 'sys:file:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000157', '40002', 'sys:file:upload', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000158', '40002', 'sys:group:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000159', '40002', 'sys:group:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000160', '40002', 'sys:group:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000161', '40002', 'sys:group:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000162', '40002', 'sys:group:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000163', '40002', 'sys:group:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000164', '40002', 'sys:group:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000165', '40002', 'sys:group:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000166', '40002', 'sys:group:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000167', '40002', 'sys:module:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000168', '40002', 'sys:module:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000169', '40002', 'sys:module:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000170', '40002', 'sys:module:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000171', '40002', 'sys:module:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000172', '40002', 'sys:module:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000173', '40002', 'sys:module:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000174', '40002', 'sys:module:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000175', '40002', 'sys:notice:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000176', '40002', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000177', '40002', 'sys:notice:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000178', '40002', 'sys:notice:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000179', '40002', 'sys:notice:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000180', '40002', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000181', '40002', 'sys:notice:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000182', '40002', 'sys:notice:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000183', '40002', 'sys:org:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000184', '40002', 'sys:org:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000185', '40002', 'sys:org:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000186', '40002', 'sys:org:grant-role', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000187', '40002', 'sys:org:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000188', '40002', 'sys:org:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000189', '40002', 'sys:org:own-roles', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000190', '40002', 'sys:org:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000191', '40002', 'sys:org:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000192', '40002', 'sys:org:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000193', '40002', 'sys:org:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000194', '40002', 'sys:permission:by-module', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000195', '40002', 'sys:permission:modules', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000196', '40002', 'sys:position:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000197', '40002', 'sys:position:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000198', '40002', 'sys:position:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000199', '40002', 'sys:position:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000200', '40002', 'sys:position:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000201', '40002', 'sys:position:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000202', '40002', 'sys:position:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000203', '40002', 'sys:position:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000204', '40002', 'sys:resource:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000205', '40002', 'sys:resource:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000206', '40002', 'sys:resource:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000207', '40002', 'sys:resource:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000208', '40002', 'sys:resource:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000209', '40002', 'sys:resource:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000210', '40002', 'sys:resource:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000211', '40002', 'sys:resource:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000212', '40002', 'sys:resource:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000213', '40002', 'sys:role:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000214', '40002', 'sys:role:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000215', '40002', 'sys:role:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000216', '40002', 'sys:role:grant-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000217', '40002', 'sys:role:grant-resource', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000218', '40002', 'sys:role:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000219', '40002', 'sys:role:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000220', '40002', 'sys:role:own-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000221', '40002', 'sys:role:own-resource', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000222', '40002', 'sys:role:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000223', '40002', 'sys:role:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000224', '40002', 'sys:role:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000225', '40002', 'sys:user:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000226', '40002', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000227', '40002', 'sys:user:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000229', '40002', 'sys:user:grant-permission', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000230', '40002', 'sys:user:grant-role', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000231', '40002', 'sys:user:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000232', '40002', 'sys:user:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000234', '40002', 'sys:user:own-permission-detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000235', '40002', 'sys:user:own-roles', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000236', '40002', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000237', '40002', 'sys:user:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000238', '40002', 'sys:user:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000239', '40003', 'sys:banner:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000240', '40003', 'sys:banner:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000241', '40003', 'sys:config:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000242', '40003', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000243', '40003', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000244', '40003', 'sys:dev:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000245', '40003', 'sys:dev:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000246', '40003', 'sys:dev:gen:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000247', '40003', 'sys:dev:gen:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000248', '40003', 'sys:dev:gen:edit', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000249', '40003', 'sys:dev:gen:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000250', '40003', 'sys:dev:gen:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000251', '40003', 'sys:dev:gen:preview', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000252', '40003', 'sys:dev:gen:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000253', '40003', 'sys:dev:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000254', '40003', 'sys:dev:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000255', '40003', 'sys:dev:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000256', '40003', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000257', '40003', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000258', '40003', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000259', '40003', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000260', '40003', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000261', '40003', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000262', '40003', 'sys:group:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000263', '40003', 'sys:group:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000264', '40003', 'sys:group:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000265', '40003', 'sys:module:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000266', '40003', 'sys:module:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000267', '40003', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000268', '40003', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000269', '40003', 'sys:org:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000270', '40003', 'sys:org:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000271', '40003', 'sys:org:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000272', '40003', 'sys:permission:by-module', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000273', '40003', 'sys:permission:modules', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000274', '40003', 'sys:position:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000275', '40003', 'sys:position:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000276', '40003', 'sys:resource:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000277', '40003', 'sys:resource:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000278', '40003', 'sys:resource:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000279', '40003', 'sys:role:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000280', '40003', 'sys:role:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000281', '40003', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000282', '40003', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000283', '40004', 'sys:banner:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000284', '40004', 'sys:banner:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000285', '40004', 'sys:config:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000286', '40004', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000287', '40004', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000288', '40004', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000289', '40004', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000290', '40004', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000291', '40004', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000292', '40004', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000293', '40004', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000294', '40004', 'sys:group:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000295', '40004', 'sys:group:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000296', '40004', 'sys:group:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000297', '40004', 'sys:module:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000298', '40004', 'sys:module:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000299', '40004', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000300', '40004', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000301', '40004', 'sys:org:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000302', '40004', 'sys:org:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000303', '40004', 'sys:org:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000304', '40004', 'sys:permission:by-module', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000305', '40004', 'sys:permission:modules', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000306', '40004', 'sys:position:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000307', '40004', 'sys:position:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000308', '40004', 'sys:resource:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000309', '40004', 'sys:resource:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000310', '40004', 'sys:resource:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000311', '40004', 'sys:role:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000312', '40004', 'sys:role:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000313', '40004', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000314', '40004', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000315', '40005', 'sys:banner:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000316', '40005', 'sys:banner:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000317', '40005', 'sys:banner:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000318', '40005', 'sys:banner:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000319', '40005', 'sys:banner:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000320', '40005', 'sys:banner:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000321', '40005', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000322', '40005', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000323', '40005', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000324', '40005', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000325', '40005', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000326', '40005', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000327', '40005', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000328', '40005', 'sys:file:download', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000329', '40005', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000330', '40005', 'sys:file:upload', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000331', '40005', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000332', '40005', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000333', '40005', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000334', '40005', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000335', '40006', 'sys:config:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000336', '40006', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000337', '40006', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000338', '40006', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000339', '40006', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000340', '40006', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000341', '40006', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000342', '40006', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000343', '40006', 'sys:file:download', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000344', '40006', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000345', '40006', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000346', '40006', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000347', '40006', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000348', '40006', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000349', '40007', 'sys:config:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000350', '40007', 'sys:config:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000351', '40007', 'sys:dict:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000352', '40007', 'sys:dict:list', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000353', '40007', 'sys:dict:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000354', '40007', 'sys:dict:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000355', '40007', 'sys:file:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000356', '40007', 'sys:file:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000357', '40007', 'sys:group:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000358', '40007', 'sys:group:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000359', '40007', 'sys:group:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000360', '40007', 'sys:notice:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000361', '40007', 'sys:notice:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000362', '40007', 'sys:org:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000363', '40007', 'sys:org:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000364', '40007', 'sys:org:tree', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000365', '40007', 'sys:position:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000366', '40007', 'sys:position:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000367', '40007', 'sys:user:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000368', '40007', 'sys:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000369', '40007', 'sys:user:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000371', '40007', 'sys:user:grant-role', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000372', '40007', 'sys:user:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000373', '40007', 'sys:user:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000374', '40007', 'sys:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000375', '40001', 'client:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000376', '40001', 'client:user:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000377', '40001', 'client:user:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000378', '40001', 'client:user:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000379', '40001', 'client:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000380', '40001', 'client:user:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000381', '40001', 'client:user:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000382', '40001', 'client:user:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000383', '40002', 'client:user:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000384', '40002', 'client:user:create', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000385', '40002', 'client:user:modify', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000386', '40002', 'client:user:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000387', '40002', 'client:user:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000388', '40002', 'client:user:export', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000389', '40002', 'client:user:template', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000390', '40002', 'client:user:import', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000391', '40001', 'sys:log:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000392', '40001', 'sys:log:detail', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000393', '40001', 'sys:log:remove', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000394', '40001', 'sys:session:page', 'ALL', NULL, NULL);
INSERT INTO `rel_role_permission` VALUES ('2000000395', '40001', 'sys:session:exit', 'ALL', NULL, NULL);

-- ----------------------------
-- Table structure for rel_role_resource
-- ----------------------------
DROP TABLE IF EXISTS `rel_role_resource`;
CREATE TABLE `rel_role_resource`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `role_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色ID',
  `resource_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源ID',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_role_resource`(`role_id` ASC, `resource_id` ASC) USING BTREE,
  INDEX `idx_resource_id`(`resource_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色-资源关联' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rel_role_resource
-- ----------------------------
INSERT INTO `rel_role_resource` VALUES ('7460479666986422274', '40001', '80001');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616637', '40001', '80002');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810889', '40001', '80003');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422273', '40001', '80004');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422285', '40001', '80005');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422296', '40001', '80006');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616581', '40001', '80007');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616591', '40001', '80008');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616600', '40001', '80009');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616611', '40001', '80010');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616620', '40001', '80011');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616627', '40001', '80012');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616636', '40001', '80013');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810883', '40001', '80014');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810888', '40001', '80015');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422272', '40001', '80016');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422275', '40001', '80017');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422276', '40001', '80018');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422277', '40001', '80019');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422278', '40001', '80020');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422279', '40001', '80021');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422280', '40001', '80022');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422281', '40001', '80023');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422282', '40001', '80024');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422284', '40001', '80025');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422286', '40001', '80026');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422287', '40001', '80027');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422288', '40001', '80028');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422289', '40001', '80029');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422290', '40001', '80030');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422291', '40001', '80031');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422292', '40001', '80032');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422295', '40001', '80033');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422297', '40001', '80034');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422298', '40001', '80035');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422299', '40001', '80036');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422300', '40001', '80037');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616580', '40001', '80038');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616582', '40001', '80039');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616583', '40001', '80040');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616584', '40001', '80041');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616585', '40001', '80042');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616586', '40001', '80043');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616590', '40001', '80044');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616592', '40001', '80045');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616593', '40001', '80046');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616594', '40001', '80047');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616595', '40001', '80048');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616599', '40001', '80049');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616601', '40001', '80050');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616602', '40001', '80051');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616603', '40001', '80052');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616604', '40001', '80053');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616605', '40001', '80054');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616610', '40001', '80055');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616612', '40001', '80056');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616613', '40001', '80057');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616614', '40001', '80058');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616615', '40001', '80059');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616619', '40001', '80060');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616621', '40001', '80061');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616622', '40001', '80062');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616623', '40001', '80063');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616624', '40001', '80064');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616626', '40001', '80065');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616628', '40001', '80066');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616629', '40001', '80067');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616630', '40001', '80068');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616631', '40001', '80069');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616635', '40001', '80070');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616638', '40001', '80071');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616639', '40001', '80072');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616640', '40001', '80073');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616641', '40001', '80074');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810882', '40001', '80075');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810884', '40001', '80076');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810885', '40001', '80077');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810886', '40001', '80078');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422283', '40001', '80079');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616587', '40001', '80081');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616588', '40001', '80082');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616589', '40001', '80083');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616596', '40001', '80084');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616597', '40001', '80085');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616598', '40001', '80086');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616606', '40001', '80087');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616608', '40001', '80088');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616609', '40001', '80089');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616616', '40001', '80090');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616617', '40001', '80091');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616618', '40001', '80092');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616625', '40001', '80093');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616632', '40001', '80094');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616633', '40001', '80095');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616634', '40001', '80096');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616642', '40001', '80097');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810880', '40001', '80098');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810881', '40001', '80099');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810887', '40001', '80100');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616576', '40001', '80101');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616577', '40001', '80102');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616579', '40001', '80103');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422294', '40001', '80104');
INSERT INTO `rel_role_resource` VALUES ('7460479666986422293', '40001', '80105');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616607', '40001', '80106');
INSERT INTO `rel_role_resource` VALUES ('7460479666990616578', '40001', '80107');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810890', '40001', '80109');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810891', '40001', '80110');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810892', '40001', '80111');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810893', '40001', '80112');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810894', '40001', '80113');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810895', '40001', '80114');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810896', '40001', '80115');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810897', '40001', '80116');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810898', '40001', '80117');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810899', '40001', '80118');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810900', '40001', '80119');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810901', '40001', '80120');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810914', '40001', '80121');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810915', '40001', '80122');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810916', '40001', '80123');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810917', '40001', '80124');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810918', '40001', '80125');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810919', '40001', '80126');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810920', '40001', '80127');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810921', '40001', '80128');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810922', '40001', '80129');
INSERT INTO `rel_role_resource` VALUES ('7460479666994810923', '40001', '80130');
INSERT INTO `rel_role_resource` VALUES ('3000000104', '40002', '80001');
INSERT INTO `rel_role_resource` VALUES ('3000000105', '40002', '80002');
INSERT INTO `rel_role_resource` VALUES ('3000000106', '40002', '80004');
INSERT INTO `rel_role_resource` VALUES ('3000000107', '40002', '80005');
INSERT INTO `rel_role_resource` VALUES ('3000000108', '40002', '80006');
INSERT INTO `rel_role_resource` VALUES ('3000000109', '40002', '80007');
INSERT INTO `rel_role_resource` VALUES ('3000000110', '40002', '80008');
INSERT INTO `rel_role_resource` VALUES ('3000000111', '40002', '80009');
INSERT INTO `rel_role_resource` VALUES ('3000000112', '40002', '80010');
INSERT INTO `rel_role_resource` VALUES ('3000000113', '40002', '80011');
INSERT INTO `rel_role_resource` VALUES ('3000000114', '40002', '80012');
INSERT INTO `rel_role_resource` VALUES ('3000000115', '40002', '80013');
INSERT INTO `rel_role_resource` VALUES ('3000000116', '40002', '80014');
INSERT INTO `rel_role_resource` VALUES ('3000000117', '40002', '80016');
INSERT INTO `rel_role_resource` VALUES ('3000000118', '40002', '80017');
INSERT INTO `rel_role_resource` VALUES ('3000000119', '40002', '80018');
INSERT INTO `rel_role_resource` VALUES ('3000000120', '40002', '80019');
INSERT INTO `rel_role_resource` VALUES ('3000000121', '40002', '80020');
INSERT INTO `rel_role_resource` VALUES ('3000000122', '40002', '80021');
INSERT INTO `rel_role_resource` VALUES ('3000000123', '40002', '80022');
INSERT INTO `rel_role_resource` VALUES ('3000000124', '40002', '80023');
INSERT INTO `rel_role_resource` VALUES ('3000000125', '40002', '80024');
INSERT INTO `rel_role_resource` VALUES ('3000000126', '40002', '80025');
INSERT INTO `rel_role_resource` VALUES ('3000000127', '40002', '80026');
INSERT INTO `rel_role_resource` VALUES ('3000000128', '40002', '80027');
INSERT INTO `rel_role_resource` VALUES ('3000000129', '40002', '80028');
INSERT INTO `rel_role_resource` VALUES ('3000000130', '40002', '80029');
INSERT INTO `rel_role_resource` VALUES ('3000000131', '40002', '80030');
INSERT INTO `rel_role_resource` VALUES ('3000000132', '40002', '80031');
INSERT INTO `rel_role_resource` VALUES ('3000000133', '40002', '80032');
INSERT INTO `rel_role_resource` VALUES ('3000000134', '40002', '80033');
INSERT INTO `rel_role_resource` VALUES ('3000000135', '40002', '80034');
INSERT INTO `rel_role_resource` VALUES ('3000000136', '40002', '80035');
INSERT INTO `rel_role_resource` VALUES ('3000000137', '40002', '80036');
INSERT INTO `rel_role_resource` VALUES ('3000000138', '40002', '80037');
INSERT INTO `rel_role_resource` VALUES ('3000000139', '40002', '80038');
INSERT INTO `rel_role_resource` VALUES ('3000000140', '40002', '80039');
INSERT INTO `rel_role_resource` VALUES ('3000000141', '40002', '80040');
INSERT INTO `rel_role_resource` VALUES ('3000000142', '40002', '80041');
INSERT INTO `rel_role_resource` VALUES ('3000000143', '40002', '80042');
INSERT INTO `rel_role_resource` VALUES ('3000000144', '40002', '80043');
INSERT INTO `rel_role_resource` VALUES ('3000000145', '40002', '80044');
INSERT INTO `rel_role_resource` VALUES ('3000000146', '40002', '80045');
INSERT INTO `rel_role_resource` VALUES ('3000000147', '40002', '80046');
INSERT INTO `rel_role_resource` VALUES ('3000000148', '40002', '80047');
INSERT INTO `rel_role_resource` VALUES ('3000000149', '40002', '80048');
INSERT INTO `rel_role_resource` VALUES ('3000000150', '40002', '80049');
INSERT INTO `rel_role_resource` VALUES ('3000000151', '40002', '80050');
INSERT INTO `rel_role_resource` VALUES ('3000000152', '40002', '80051');
INSERT INTO `rel_role_resource` VALUES ('3000000153', '40002', '80052');
INSERT INTO `rel_role_resource` VALUES ('3000000154', '40002', '80053');
INSERT INTO `rel_role_resource` VALUES ('3000000155', '40002', '80054');
INSERT INTO `rel_role_resource` VALUES ('3000000156', '40002', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000157', '40002', '80056');
INSERT INTO `rel_role_resource` VALUES ('3000000158', '40002', '80057');
INSERT INTO `rel_role_resource` VALUES ('3000000159', '40002', '80058');
INSERT INTO `rel_role_resource` VALUES ('3000000160', '40002', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000161', '40002', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000162', '40002', '80061');
INSERT INTO `rel_role_resource` VALUES ('3000000163', '40002', '80062');
INSERT INTO `rel_role_resource` VALUES ('3000000164', '40002', '80063');
INSERT INTO `rel_role_resource` VALUES ('3000000165', '40002', '80064');
INSERT INTO `rel_role_resource` VALUES ('3000000166', '40002', '80065');
INSERT INTO `rel_role_resource` VALUES ('3000000167', '40002', '80066');
INSERT INTO `rel_role_resource` VALUES ('3000000168', '40002', '80067');
INSERT INTO `rel_role_resource` VALUES ('3000000169', '40002', '80068');
INSERT INTO `rel_role_resource` VALUES ('3000000170', '40002', '80069');
INSERT INTO `rel_role_resource` VALUES ('3000000171', '40002', '80070');
INSERT INTO `rel_role_resource` VALUES ('3000000172', '40002', '80071');
INSERT INTO `rel_role_resource` VALUES ('3000000173', '40002', '80072');
INSERT INTO `rel_role_resource` VALUES ('3000000174', '40002', '80073');
INSERT INTO `rel_role_resource` VALUES ('3000000175', '40002', '80074');
INSERT INTO `rel_role_resource` VALUES ('3000000176', '40002', '80075');
INSERT INTO `rel_role_resource` VALUES ('3000000177', '40002', '80076');
INSERT INTO `rel_role_resource` VALUES ('3000000178', '40002', '80077');
INSERT INTO `rel_role_resource` VALUES ('3000000179', '40002', '80078');
INSERT INTO `rel_role_resource` VALUES ('3000000180', '40002', '80079');
INSERT INTO `rel_role_resource` VALUES ('3000000181', '40002', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000182', '40002', '80081');
INSERT INTO `rel_role_resource` VALUES ('3000000183', '40002', '80082');
INSERT INTO `rel_role_resource` VALUES ('3000000184', '40002', '80083');
INSERT INTO `rel_role_resource` VALUES ('3000000185', '40002', '80084');
INSERT INTO `rel_role_resource` VALUES ('3000000186', '40002', '80085');
INSERT INTO `rel_role_resource` VALUES ('3000000187', '40002', '80086');
INSERT INTO `rel_role_resource` VALUES ('3000000188', '40002', '80087');
INSERT INTO `rel_role_resource` VALUES ('3000000189', '40002', '80088');
INSERT INTO `rel_role_resource` VALUES ('3000000190', '40002', '80089');
INSERT INTO `rel_role_resource` VALUES ('3000000191', '40002', '80090');
INSERT INTO `rel_role_resource` VALUES ('3000000192', '40002', '80091');
INSERT INTO `rel_role_resource` VALUES ('3000000193', '40002', '80092');
INSERT INTO `rel_role_resource` VALUES ('3000000194', '40002', '80093');
INSERT INTO `rel_role_resource` VALUES ('3000000195', '40002', '80094');
INSERT INTO `rel_role_resource` VALUES ('3000000196', '40002', '80095');
INSERT INTO `rel_role_resource` VALUES ('3000000197', '40002', '80096');
INSERT INTO `rel_role_resource` VALUES ('3000000198', '40002', '80097');
INSERT INTO `rel_role_resource` VALUES ('3000000199', '40002', '80098');
INSERT INTO `rel_role_resource` VALUES ('3000000200', '40002', '80099');
INSERT INTO `rel_role_resource` VALUES ('3000000201', '40002', '80100');
INSERT INTO `rel_role_resource` VALUES ('3000000202', '40002', '80101');
INSERT INTO `rel_role_resource` VALUES ('3000000203', '40002', '80102');
INSERT INTO `rel_role_resource` VALUES ('3000000204', '40002', '80103');
INSERT INTO `rel_role_resource` VALUES ('3000000325', '40002', '80104');
INSERT INTO `rel_role_resource` VALUES ('3000000326', '40002', '80105');
INSERT INTO `rel_role_resource` VALUES ('3000000327', '40002', '80106');
INSERT INTO `rel_role_resource` VALUES ('3000000328', '40002', '80107');
INSERT INTO `rel_role_resource` VALUES ('3000000346', '40002', '80108');
INSERT INTO `rel_role_resource` VALUES ('3000000372', '40002', '80121');
INSERT INTO `rel_role_resource` VALUES ('3000000373', '40002', '80122');
INSERT INTO `rel_role_resource` VALUES ('3000000374', '40002', '80123');
INSERT INTO `rel_role_resource` VALUES ('3000000375', '40002', '80124');
INSERT INTO `rel_role_resource` VALUES ('3000000376', '40002', '80125');
INSERT INTO `rel_role_resource` VALUES ('3000000377', '40002', '80126');
INSERT INTO `rel_role_resource` VALUES ('3000000378', '40002', '80127');
INSERT INTO `rel_role_resource` VALUES ('3000000379', '40002', '80128');
INSERT INTO `rel_role_resource` VALUES ('3000000380', '40002', '80129');
INSERT INTO `rel_role_resource` VALUES ('3000000381', '40002', '80130');
INSERT INTO `rel_role_resource` VALUES ('3000000205', '40003', '80003');
INSERT INTO `rel_role_resource` VALUES ('3000000206', '40003', '80010');
INSERT INTO `rel_role_resource` VALUES ('3000000207', '40003', '80011');
INSERT INTO `rel_role_resource` VALUES ('3000000208', '40003', '80015');
INSERT INTO `rel_role_resource` VALUES ('3000000209', '40003', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000210', '40003', '80056');
INSERT INTO `rel_role_resource` VALUES ('3000000211', '40003', '80057');
INSERT INTO `rel_role_resource` VALUES ('3000000212', '40003', '80058');
INSERT INTO `rel_role_resource` VALUES ('3000000213', '40003', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000214', '40003', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000215', '40003', '80061');
INSERT INTO `rel_role_resource` VALUES ('3000000216', '40003', '80062');
INSERT INTO `rel_role_resource` VALUES ('3000000217', '40003', '80063');
INSERT INTO `rel_role_resource` VALUES ('3000000218', '40003', '80064');
INSERT INTO `rel_role_resource` VALUES ('3000000219', '40003', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000329', '40003', '80104');
INSERT INTO `rel_role_resource` VALUES ('3000000344', '40003', '80105');
INSERT INTO `rel_role_resource` VALUES ('3000000330', '40003', '80106');
INSERT INTO `rel_role_resource` VALUES ('3000000331', '40003', '80107');
INSERT INTO `rel_role_resource` VALUES ('3000000347', '40003', '80108');
INSERT INTO `rel_role_resource` VALUES ('3000000220', '40004', '80004');
INSERT INTO `rel_role_resource` VALUES ('3000000221', '40004', '80005');
INSERT INTO `rel_role_resource` VALUES ('3000000222', '40004', '80006');
INSERT INTO `rel_role_resource` VALUES ('3000000223', '40004', '80007');
INSERT INTO `rel_role_resource` VALUES ('3000000224', '40004', '80010');
INSERT INTO `rel_role_resource` VALUES ('3000000225', '40004', '80011');
INSERT INTO `rel_role_resource` VALUES ('3000000226', '40004', '80012');
INSERT INTO `rel_role_resource` VALUES ('3000000227', '40004', '80013');
INSERT INTO `rel_role_resource` VALUES ('3000000228', '40004', '80014');
INSERT INTO `rel_role_resource` VALUES ('3000000229', '40004', '80016');
INSERT INTO `rel_role_resource` VALUES ('3000000230', '40004', '80020');
INSERT INTO `rel_role_resource` VALUES ('3000000231', '40004', '80025');
INSERT INTO `rel_role_resource` VALUES ('3000000232', '40004', '80029');
INSERT INTO `rel_role_resource` VALUES ('3000000233', '40004', '80033');
INSERT INTO `rel_role_resource` VALUES ('3000000234', '40004', '80037');
INSERT INTO `rel_role_resource` VALUES ('3000000235', '40004', '80038');
INSERT INTO `rel_role_resource` VALUES ('3000000236', '40004', '80042');
INSERT INTO `rel_role_resource` VALUES ('3000000237', '40004', '80044');
INSERT INTO `rel_role_resource` VALUES ('3000000238', '40004', '80048');
INSERT INTO `rel_role_resource` VALUES ('3000000239', '40004', '80049');
INSERT INTO `rel_role_resource` VALUES ('3000000240', '40004', '80053');
INSERT INTO `rel_role_resource` VALUES ('3000000241', '40004', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000242', '40004', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000243', '40004', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000244', '40004', '80064');
INSERT INTO `rel_role_resource` VALUES ('3000000245', '40004', '80065');
INSERT INTO `rel_role_resource` VALUES ('3000000246', '40004', '80069');
INSERT INTO `rel_role_resource` VALUES ('3000000247', '40004', '80070');
INSERT INTO `rel_role_resource` VALUES ('3000000248', '40004', '80074');
INSERT INTO `rel_role_resource` VALUES ('3000000249', '40004', '80077');
INSERT INTO `rel_role_resource` VALUES ('3000000250', '40004', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000251', '40004', '80100');
INSERT INTO `rel_role_resource` VALUES ('3000000332', '40004', '80106');
INSERT INTO `rel_role_resource` VALUES ('3000000333', '40004', '80107');
INSERT INTO `rel_role_resource` VALUES ('3000000348', '40004', '80108');
INSERT INTO `rel_role_resource` VALUES ('3000000252', '40005', '80002');
INSERT INTO `rel_role_resource` VALUES ('3000000253', '40005', '80012');
INSERT INTO `rel_role_resource` VALUES ('3000000254', '40005', '80013');
INSERT INTO `rel_role_resource` VALUES ('3000000255', '40005', '80014');
INSERT INTO `rel_role_resource` VALUES ('3000000256', '40005', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000257', '40005', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000258', '40005', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000259', '40005', '80065');
INSERT INTO `rel_role_resource` VALUES ('3000000260', '40005', '80069');
INSERT INTO `rel_role_resource` VALUES ('3000000261', '40005', '80070');
INSERT INTO `rel_role_resource` VALUES ('3000000262', '40005', '80071');
INSERT INTO `rel_role_resource` VALUES ('3000000263', '40005', '80072');
INSERT INTO `rel_role_resource` VALUES ('3000000264', '40005', '80073');
INSERT INTO `rel_role_resource` VALUES ('3000000265', '40005', '80074');
INSERT INTO `rel_role_resource` VALUES ('3000000266', '40005', '80075');
INSERT INTO `rel_role_resource` VALUES ('3000000267', '40005', '80076');
INSERT INTO `rel_role_resource` VALUES ('3000000268', '40005', '80077');
INSERT INTO `rel_role_resource` VALUES ('3000000269', '40005', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000270', '40005', '80097');
INSERT INTO `rel_role_resource` VALUES ('3000000271', '40005', '80098');
INSERT INTO `rel_role_resource` VALUES ('3000000272', '40005', '80099');
INSERT INTO `rel_role_resource` VALUES ('3000000273', '40005', '80100');
INSERT INTO `rel_role_resource` VALUES ('3000000349', '40005', '80108');
INSERT INTO `rel_role_resource` VALUES ('3000000274', '40006', '80001');
INSERT INTO `rel_role_resource` VALUES ('3000000275', '40006', '80010');
INSERT INTO `rel_role_resource` VALUES ('3000000276', '40006', '80011');
INSERT INTO `rel_role_resource` VALUES ('3000000277', '40006', '80012');
INSERT INTO `rel_role_resource` VALUES ('3000000278', '40006', '80014');
INSERT INTO `rel_role_resource` VALUES ('3000000279', '40006', '80016');
INSERT INTO `rel_role_resource` VALUES ('3000000280', '40006', '80020');
INSERT INTO `rel_role_resource` VALUES ('3000000281', '40006', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000282', '40006', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000283', '40006', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000284', '40006', '80064');
INSERT INTO `rel_role_resource` VALUES ('3000000285', '40006', '80065');
INSERT INTO `rel_role_resource` VALUES ('3000000286', '40006', '80069');
INSERT INTO `rel_role_resource` VALUES ('3000000287', '40006', '80077');
INSERT INTO `rel_role_resource` VALUES ('3000000288', '40006', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000289', '40006', '80100');
INSERT INTO `rel_role_resource` VALUES ('3000000350', '40006', '80108');
INSERT INTO `rel_role_resource` VALUES ('3000000290', '40007', '80001');
INSERT INTO `rel_role_resource` VALUES ('3000000291', '40007', '80004');
INSERT INTO `rel_role_resource` VALUES ('3000000292', '40007', '80007');
INSERT INTO `rel_role_resource` VALUES ('3000000293', '40007', '80008');
INSERT INTO `rel_role_resource` VALUES ('3000000294', '40007', '80009');
INSERT INTO `rel_role_resource` VALUES ('3000000295', '40007', '80010');
INSERT INTO `rel_role_resource` VALUES ('3000000296', '40007', '80011');
INSERT INTO `rel_role_resource` VALUES ('3000000297', '40007', '80012');
INSERT INTO `rel_role_resource` VALUES ('3000000298', '40007', '80014');
INSERT INTO `rel_role_resource` VALUES ('3000000299', '40007', '80016');
INSERT INTO `rel_role_resource` VALUES ('3000000300', '40007', '80017');
INSERT INTO `rel_role_resource` VALUES ('3000000301', '40007', '80018');
INSERT INTO `rel_role_resource` VALUES ('3000000302', '40007', '80020');
INSERT INTO `rel_role_resource` VALUES ('3000000303', '40007', '80021');
INSERT INTO `rel_role_resource` VALUES ('3000000304', '40007', '80022');
INSERT INTO `rel_role_resource` VALUES ('3000000305', '40007', '80023');
INSERT INTO `rel_role_resource` VALUES ('3000000306', '40007', '80024');
INSERT INTO `rel_role_resource` VALUES ('3000000307', '40007', '80038');
INSERT INTO `rel_role_resource` VALUES ('3000000308', '40007', '80042');
INSERT INTO `rel_role_resource` VALUES ('3000000309', '40007', '80044');
INSERT INTO `rel_role_resource` VALUES ('3000000310', '40007', '80048');
INSERT INTO `rel_role_resource` VALUES ('3000000311', '40007', '80049');
INSERT INTO `rel_role_resource` VALUES ('3000000312', '40007', '80053');
INSERT INTO `rel_role_resource` VALUES ('3000000313', '40007', '80055');
INSERT INTO `rel_role_resource` VALUES ('3000000314', '40007', '80059');
INSERT INTO `rel_role_resource` VALUES ('3000000315', '40007', '80060');
INSERT INTO `rel_role_resource` VALUES ('3000000316', '40007', '80065');
INSERT INTO `rel_role_resource` VALUES ('3000000317', '40007', '80069');
INSERT INTO `rel_role_resource` VALUES ('3000000318', '40007', '80077');
INSERT INTO `rel_role_resource` VALUES ('3000000319', '40007', '80080');
INSERT INTO `rel_role_resource` VALUES ('3000000320', '40007', '80100');
INSERT INTO `rel_role_resource` VALUES ('3000000334', '40007', '80106');
INSERT INTO `rel_role_resource` VALUES ('3000000351', '40007', '80108');

-- ----------------------------
-- Table structure for rel_user_permission
-- ----------------------------
DROP TABLE IF EXISTS `rel_user_permission`;
CREATE TABLE `rel_user_permission`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `user_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户ID',
  `permission_code` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '权限编码',
  `scope` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ALL' COMMENT '数据范围：ALL-全部，SELF-本人，ORG-本组织，ORG_AND_BELOW-本组织及以下，CUSTOM_ORG-自定义组织，GROUP-本用户组，GROUP_AND_BELOW-本用户组及以下，CUSTOM_GROUP-自定义用户组',
  `custom_scope_group_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义用户组ID列表(JSON数组)，scope=CUSTOM_GROUP时生效',
  `custom_scope_org_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义组织ID列表(JSON数组)，scope=CUSTOM_ORG时生效',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_permission`(`user_id` ASC, `permission_code` ASC) USING BTREE,
  INDEX `idx_permission_code`(`permission_code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户-权限直关联' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rel_user_permission
-- ----------------------------

-- ----------------------------
-- Table structure for rel_user_role
-- ----------------------------
DROP TABLE IF EXISTS `rel_user_role`;
CREATE TABLE `rel_user_role`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `user_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户ID',
  `role_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色ID',
  `scope` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '数据范围覆盖：ALL-全部，CUSTOM-自定义，ORG-本组织，ORG_AND_BELOW-本组织及以下，SELF-本人。为空则继承 rel_role_permission 的配置',
  `custom_scope_group_ids` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '自定义数据范围组ID列表(JSON数组)，scope=CUSTOM时生效',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_role`(`user_id` ASC, `role_id` ASC) USING BTREE,
  INDEX `idx_role_id`(`role_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户-角色关联' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of rel_user_role
-- ----------------------------
INSERT INTO `rel_user_role` VALUES ('120001', '50001', '40001', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120002', '50002', '40003', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120003', '50003', '40003', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120004', '50004', '40003', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120005', '50005', '40004', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120006', '50006', '40005', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120007', '50007', '40005', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120008', '50008', '40006', 'ALL', NULL);
INSERT INTO `rel_user_role` VALUES ('120009', '50009', '40007', 'ALL', NULL);

-- ----------------------------
-- Table structure for sys_banner
-- ----------------------------
DROP TABLE IF EXISTS `sys_banner`;
CREATE TABLE `sys_banner`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '轮播标题',
  `image` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '轮播图片',
  `url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '跳转地址',
  `link_type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'URL' COMMENT '链接类型',
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '轮播摘要',
  `description` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '轮播描述',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '轮播类别',
  `type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '轮播类型',
  `position` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '展示位置',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `view_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `click_count` int NULL DEFAULT 0 COMMENT '点击次数',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '轮播图' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_banner
-- ----------------------------
INSERT INTO `sys_banner` VALUES ('110001', 'Hei FastAPI 宣传图', 'https://via.placeholder.com/1920x600/1890FF/FFFFFF?text=Hei+FastAPI', 'https://github.com', 'URL', 'Hei FastAPI 框架宣传图', '基于 FastAPI 的企业级后台开发框架', 'INDEX', 'IMAGE', 'INDEX_TOP', 1, 0, 0, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_banner` VALUES ('110002', '系统使用指南', 'https://via.placeholder.com/1920x600/52C41A/FFFFFF?text=使用指南', NULL, 'URL', '新系统使用指南', '快速上手新系统', 'INDEX', 'IMAGE', 'INDEX_TOP', 2, 0, 0, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_banner` VALUES ('110003', '开发团队招募', 'https://via.placeholder.com/1920x600/722ED1/FFFFFF?text=加入我们', NULL, 'URL', '诚聘前后端开发工程师', '如果您对技术充满热情，欢迎加入我们', 'INDEX', 'IMAGE', 'INDEX_TOP', 3, 0, 0, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');

-- ----------------------------
-- Table structure for sys_config
-- ----------------------------
DROP TABLE IF EXISTS `sys_config`;
CREATE TABLE `sys_config`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `config_key` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '配置键',
  `config_value` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '配置值',
  `category` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '分类',
  `remark` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '备注',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序码',
  `extra` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '修改时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '修改用户',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '系统配置' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_config
-- ----------------------------
INSERT INTO `sys_config` VALUES ('1', 'SYS_DEFAULT_FILE_ENGINE', 'LOCAL', 'SYS_BASE', '默认文件引擎', 1, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_config` VALUES ('10', 'SYS_JWT_TOKEN_EXPIRE', '86400', 'SYS_SECURITY', 'JWT Token 过期时间（秒）', 10, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('11', 'SYS_UPLOAD_MAX_SIZE', '10485760', 'SYS_FILE', '文件上传最大大小（字节）', 11, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('12', 'SYS_UPLOAD_ALLOWED_EXTENSIONS', 'jpg,jpeg,png,gif,bmp,doc,docx,xls,xlsx,pdf,txt,zip,rar', 'SYS_FILE', '允许上传的文件后缀', 12, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('2', 'SYS_FILE_LOCAL_FOLDER_FOR_WINDOWS', 'D:/hei-file-upload', 'FILE_LOCAL', '本地文件存储路径(Windows)', 2, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_config` VALUES ('3', 'SYS_FILE_LOCAL_FOLDER_FOR_UNIX', '/data/hei-file-upload', 'FILE_LOCAL', '本地文件存储路径(Unix)', 3, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_config` VALUES ('4', 'SYS_SNOWFLAKE_WORKER_ID', '1', 'SYS_BASE', 'Snowflake 工作节点ID', 4, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('5', 'SYS_SNOWFLAKE_DATACENTER_ID', '1', 'SYS_BASE', 'Snowflake 数据中心ID', 5, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('6', 'SYS_DEFAULT_PASSWORD', '123456', 'SYS_BASE', '默认密码（新增用户时使用）', 6, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('7', 'SYS_USER_INIT_PASSWORD', '123456', 'SYS_BASE', '用户初始密码', 7, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('8', 'SYS_MAX_LOGIN_RETRIES', '5', 'SYS_SECURITY', '最大登录失败次数', 8, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_config` VALUES ('9', 'SYS_LOGIN_LOCK_MINUTES', '30', 'SYS_SECURITY', '登录锁定时间（分钟）', 9, NULL, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');

-- ----------------------------
-- Table structure for sys_dict
-- ----------------------------
DROP TABLE IF EXISTS `sys_dict`;
CREATE TABLE `sys_dict`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '字典编码',
  `label` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字典标签',
  `value` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字典值',
  `color` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字典颜色',
  `category` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '字典分类',
  `parent_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '父字典ID',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '字典' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_dict
-- ----------------------------
INSERT INTO `sys_dict` VALUES ('90001', 'GENDER', '性别', NULL, NULL, 'sys_base', NULL, 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90002', 'GENDER_MALE', '男', 'MALE', 'blue', 'sys_base', '90001', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90003', 'GENDER_FEMALE', '女', 'FEMALE', 'red', 'sys_base', '90001', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90004', 'NOTICE_CATEGORY', '通知分类', NULL, NULL, 'sys_notice', NULL, 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90005', 'NOTICE_CATEGORY_PLATFORM', '平台通知', 'PLATFORM', NULL, 'sys_notice', '90004', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90006', 'NOTICE_CATEGORY_COMPANY', '公司通知', 'COMPANY', NULL, 'sys_notice', '90004', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90007', 'NOTICE_TYPE', '通知类型', NULL, NULL, 'sys_notice', NULL, 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90008', 'NOTICE_TYPE_MAINTENANCE', '维护通知', 'MAINTENANCE', NULL, 'sys_notice', '90007', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90009', 'NOTICE_TYPE_SYSTEM_NOTICE', '系统通知', 'SYSTEM_NOTICE', NULL, 'sys_notice', '90007', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90010', 'NOTICE_TYPE_BUSINESS_NOTICE', '业务通知', 'BUSINESS_NOTICE', NULL, 'sys_notice', '90007', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90011', 'NOTICE_LEVEL', '通知级别', NULL, NULL, 'sys_notice', NULL, 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90012', 'NOTICE_LEVEL_URGENT', '紧急', 'URGENT', 'red', 'sys_notice', '90011', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90013', 'NOTICE_LEVEL_IMPORTANT', '重要', 'IMPORTANT', 'orange', 'sys_notice', '90011', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90014', 'NOTICE_LEVEL_NORMAL', '普通', 'NORMAL', 'blue', 'sys_notice', '90011', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90015', 'NOTICE_POSITION', '通知位置', NULL, NULL, 'sys_notice', NULL, 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90016', 'NOTICE_POSITION_TOP', '顶部通知', 'TOP', 'geekblue', 'sys_notice', '90015', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90017', 'NOTICE_POSITION_POPUP', '弹窗通知', 'POPUP', 'purple', 'sys_notice', '90015', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90018', 'ORG_CATEGORY', '组织类别', NULL, NULL, 'sys_org', NULL, 'ENABLED', 5, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90019', 'ORG_CATEGORY_GROUP', '集团', 'GROUP', NULL, 'sys_org', '90018', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90020', 'ORG_CATEGORY_DEPT', '部门', 'DEPT', NULL, 'sys_org', '90018', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90021', 'GROUP_CATEGORY', '用户组类别', NULL, NULL, 'sys_group', NULL, 'ENABLED', 6, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90022', 'GROUP_CATEGORY_ROLE', '角色组', 'ROLE', NULL, 'sys_group', '90021', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90023', 'GROUP_CATEGORY_DEPT', '部门组', 'DEPT', NULL, 'sys_group', '90021', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90024', 'GROUP_CATEGORY_PROJECT', '项目组', 'PROJECT', NULL, 'sys_group', '90021', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90025', 'POSITION_CATEGORY', '职位类别', NULL, NULL, 'sys_position', NULL, 'ENABLED', 7, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90026', 'POSITION_CATEGORY_MANAGEMENT', '管理', 'MANAGEMENT', NULL, 'sys_position', '90025', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90027', 'POSITION_CATEGORY_TECH', '技术', 'TECH', NULL, 'sys_position', '90025', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90028', 'POSITION_CATEGORY_OPERATIONS', '运营', 'OPERATIONS', NULL, 'sys_position', '90025', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90029', 'POSITION_CATEGORY_SALES', '销售', 'SALES', NULL, 'sys_position', '90025', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90030', 'POSITION_CATEGORY_OTHER', '其他', 'OTHER', NULL, 'sys_position', '90025', 'ENABLED', 5, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90033', 'ROLE_CATEGORY', '角色类别', NULL, NULL, 'sys_role', NULL, 'ENABLED', 8, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90034', 'ROLE_CATEGORY_BACKEND', '后台角色', 'BACKEND', NULL, 'sys_role', '90033', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90035', 'ROLE_CATEGORY_FRONTEND', '前台角色', 'FRONTEND', NULL, 'sys_role', '90033', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90036', 'RESOURCE_CATEGORY', '资源分类', NULL, NULL, 'sys_resource', NULL, 'ENABLED', 9, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90037', 'RESOURCE_CATEGORY_BACKEND_MENU', '后台菜单', 'BACKEND_MENU', NULL, 'sys_resource', '90036', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90038', 'RESOURCE_CATEGORY_FRONTEND_MENU', '前台菜单', 'FRONTEND_MENU', NULL, 'sys_resource', '90036', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90039', 'RESOURCE_CATEGORY_BACKEND_BUTTON', '后台按钮', 'BACKEND_BUTTON', NULL, 'sys_resource', '90036', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90040', 'RESOURCE_CATEGORY_FRONTEND_BUTTON', '前台按钮', 'FRONTEND_BUTTON', NULL, 'sys_resource', '90036', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90041', 'RESOURCE_TYPE', '资源类型', NULL, NULL, 'sys_resource', NULL, 'ENABLED', 10, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90042', 'RESOURCE_TYPE_DIRECTORY', '目录', 'DIRECTORY', NULL, 'sys_resource', '90041', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90043', 'RESOURCE_TYPE_MENU', '菜单', 'MENU', NULL, 'sys_resource', '90041', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90044', 'RESOURCE_TYPE_BUTTON', '按钮', 'BUTTON', NULL, 'sys_resource', '90041', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90045', 'RESOURCE_TYPE_INTERNAL_LINK', '内链', 'INTERNAL_LINK', NULL, 'sys_resource', '90041', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90046', 'RESOURCE_TYPE_EXTERNAL_LINK', '外链', 'EXTERNAL_LINK', NULL, 'sys_resource', '90041', 'ENABLED', 5, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90047', 'SYS_STATUS', '系统状态', NULL, NULL, 'sys_common', NULL, 'ENABLED', 11, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90048', 'SYS_STATUS_ENABLED', '启用', 'ENABLED', 'green', 'sys_common', '90047', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90049', 'SYS_STATUS_DISABLED', '禁用', 'DISABLED', 'red', 'sys_common', '90047', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90050', 'USER_STATUS', '用户状态', NULL, NULL, 'sys_common', NULL, 'ENABLED', 12, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90051', 'USER_STATUS_ACTIVE', '正常', 'ACTIVE', 'green', 'sys_common', '90050', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90052', 'USER_STATUS_INACTIVE', '停用', 'INACTIVE', 'orange', 'sys_common', '90050', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90053', 'USER_STATUS_LOCKED', '锁定', 'LOCKED', 'red', 'sys_common', '90050', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90054', 'SYS_YES_NO', '是否', NULL, NULL, 'sys_common', NULL, 'ENABLED', 13, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90055', 'SYS_YES_NO_YES', '是', 'YES', 'green', 'sys_common', '90054', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90056', 'SYS_YES_NO_NO', '否', 'NO', 'red', 'sys_common', '90054', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90057', 'ORG_CATEGORY_COMPANY', '公司', 'COMPANY', NULL, 'sys_org', '90018', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90058', 'ORG_CATEGORY_UNIT', '单位', 'UNIT', NULL, 'sys_org', '90018', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90059', 'GROUP_CATEGORY_OTHER', '其他', 'OTHER', NULL, 'sys_group', '90021', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90060', 'BANNER_CATEGORY', '横幅类别', NULL, NULL, 'sys_banner', NULL, 'ENABLED', 14, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90061', 'BANNER_CATEGORY_HOME', '首页', 'HOME', NULL, 'sys_banner', '90060', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90062', 'BANNER_CATEGORY_PAGE', '页面', 'PAGE', NULL, 'sys_banner', '90060', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90063', 'BANNER_CATEGORY_APP', '应用', 'APP', NULL, 'sys_banner', '90060', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90064', 'BANNER_TYPE', '横幅类型', NULL, NULL, 'sys_banner', NULL, 'ENABLED', 15, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90065', 'BANNER_TYPE_IMAGE', '图片', 'IMAGE', NULL, 'sys_banner', '90064', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90066', 'BANNER_TYPE_VIDEO', '视频', 'VIDEO', NULL, 'sys_banner', '90064', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90067', 'BANNER_TYPE_TEXT', '文字', 'TEXT', NULL, 'sys_banner', '90064', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90068', 'BANNER_POSITION', '横幅位置', NULL, NULL, 'sys_banner', NULL, 'ENABLED', 16, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90069', 'BANNER_POSITION_TOP', '顶部', 'TOP', NULL, 'sys_banner', '90068', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90070', 'BANNER_POSITION_CENTER', '中间', 'CENTER', NULL, 'sys_banner', '90068', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90071', 'BANNER_POSITION_BOTTOM', '底部', 'BOTTOM', NULL, 'sys_banner', '90068', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90072', 'BANNER_POSITION_SIDEBAR', '侧栏', 'SIDEBAR', NULL, 'sys_banner', '90068', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90073', 'LINK_TYPE', '链接类型', NULL, NULL, 'sys_common', NULL, 'ENABLED', 17, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90074', 'LINK_TYPE_NONE', '无', 'NONE', NULL, 'sys_common', '90073', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90075', 'LINK_TYPE_URL', '链接', 'URL', NULL, 'sys_common', '90073', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90076', 'LINK_TYPE_PAGE', '页面', 'PAGE', NULL, 'sys_common', '90073', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90077', 'LINK_TYPE_ARTICLE', '文章', 'ARTICLE', NULL, 'sys_common', '90073', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90078', 'FILE_ENGINE', '文件引擎', NULL, NULL, 'sys_file', NULL, 'ENABLED', 18, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90079', 'FILE_ENGINE_LOCAL', '本地', 'LOCAL', 'green', 'sys_file', '90078', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90080', 'FILE_ENGINE_MINIO', 'MinIO', 'MINIO', 'blue', 'sys_file', '90078', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90081', 'FILE_ENGINE_ALIYUN', '阿里云', 'ALIYUN', 'red', 'sys_file', '90078', 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90082', 'FILE_ENGINE_TENCENT', '腾讯云', 'TENCENT', 'blue', 'sys_file', '90078', 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90083', 'FILE_ENGINE_S3', 'S3', 'S3', 'purple', 'sys_file', '90078', 'ENABLED', 5, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90084', 'DICT_CATEGORY', '字典分类', NULL, NULL, 'sys_common', NULL, 'ENABLED', 19, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90085', 'DICT_CATEGORY_FRM', '系统字典', 'FRM', 'blue', 'sys_common', '90084', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_dict` VALUES ('90086', 'DICT_CATEGORY_BIZ', '业务字典', 'BIZ', 'green', 'sys_common', '90084', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');

-- ----------------------------
-- Table structure for sys_file
-- ----------------------------
DROP TABLE IF EXISTS `sys_file`;
CREATE TABLE `sys_file`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `engine` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '存储引擎',
  `bucket` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '存储桶',
  `file_key` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件Key',
  `name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件名称',
  `suffix` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件后缀',
  `size_kb` bigint NULL DEFAULT NULL COMMENT '文件大小kb',
  `size_info` varchar(50) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '文件大小（格式化后）',
  `obj_name` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件的对象名（唯一名称）',
  `storage_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件存储路径',
  `download_path` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '文件下载路径',
  `is_download_auth` tinyint(1) NULL DEFAULT NULL COMMENT '文件下载是否需要授权',
  `thumbnail` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '图片缩略图',
  `extra` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '修改时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '修改用户',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '文件' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_file
-- ----------------------------

-- ----------------------------
-- Table structure for sys_group
-- ----------------------------
DROP TABLE IF EXISTS `sys_group`;
CREATE TABLE `sys_group`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户组编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户组名称',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户组类别',
  `parent_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '父用户组ID',
  `org_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '所属组织ID',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '用户组描述',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户组' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_group
-- ----------------------------
INSERT INTO `sys_group` VALUES ('30001', 'ADMIN_GRP', '管理组', 'ADMIN', NULL, '10001', '系统管理组', 'ENABLED', 1, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_group` VALUES ('30002', 'DEV_GRP', '研发组', 'TECH', NULL, '10002', '技术研发组', 'ENABLED', 2, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_group` VALUES ('30003', 'TEST_GRP', '测试组', 'TECH', NULL, '10002', '软件测试组', 'ENABLED', 3, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_group` VALUES ('30004', 'PROD_GRP', '产品组', 'MKT', NULL, '10003', '产品设计组', 'ENABLED', 4, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_group` VALUES ('30005', 'MKT_GRP', '市场组', 'MKT', NULL, '10003', '市场推广组', 'ENABLED', 5, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_log
-- ----------------------------
DROP TABLE IF EXISTS `sys_log`;
CREATE TABLE `sys_log`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `category` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '日志分类',
  `name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '日志名称',
  `exe_status` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '执行状态',
  `exe_message` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '具体消息',
  `op_ip` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作ip',
  `op_address` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作地址',
  `op_browser` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作浏览器',
  `op_os` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作系统',
  `class_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '类名称',
  `method_name` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '方法名称',
  `req_method` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '请求方式',
  `req_url` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '请求地址',
  `param_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '请求参数',
  `result_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '返回结果',
  `op_time` datetime NULL DEFAULT NULL COMMENT '操作时间',
  `trace_id` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '跟踪ID',
  `op_user` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '操作人姓名',
  `sign_data` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '签名数据',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '操作日志' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_log
-- ----------------------------
INSERT INTO `sys_log` VALUES ('7460574111438213120', 'OPERATE', '编辑资源', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', 'modules.sys.resource.api.v1.api', 'resource_modify', 'POST', 'http://localhost:18885/api/v1/sys/resource/modify', '{\"vo\": \"id=\'80109\' code=\'SYS_LOG\' name=\'系统日志\' category=\'BACKEND_MENU\' type=\'DIRECTORY\' description=\'系统日志目录\' parent_id=\'0\' route_path=\'/sys/log\' component_path=None redirect_path=None icon=\'file-text\' color=None is_visible=\'YES\' is_cache=\'NO\' is_affix=\'NO\' is_breadcrumb=\'YES\' external_url=\'\' extra=None status=\'ENABLED\' sort_code=2 is_deleted=\'NO\' created_at=datetime.datetime(2026, 5, 14, 14, 55, 52) created_by=\'50001\' updated_at=datetime.datetime(2026, 5, 14, 8, 3, 25) updated_by=\'50001\'\"}', '{\"code\": 200, \"message\": \"请求成功\", \"data\": null, \"success\": true, \"trace_id\": \"df11249c5cd945788020ab26537e4ec8\"}', '2026-05-14 14:17:59', 'df11249c5cd945788020ab26537e4ec8', 'admin', '445077c3a6b814d61b2d98d0b1c4ac56949bdb7b68e61dd6c11f97249eb0b433', '2026-05-14 14:17:59', NULL, '2026-05-14 14:17:59', NULL);
INSERT INTO `sys_log` VALUES ('7460574398982918144', 'LOGIN', '登录', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', '', '', 'POST', 'http://localhost:18885/api/v1/public/b/login', '', NULL, '2026-05-14 14:19:07', '2293dac2ab29494e938211701f27e0a8', 'admin', '65fb178023eb59fe90264872cf8489662df3db3784c8f1e0a250e054f59e46f3', '2026-05-14 14:19:07', NULL, '2026-05-14 14:19:07', NULL);
INSERT INTO `sys_log` VALUES ('7460574547729715200', 'LOGOUT', '登出', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', '', '', 'POST', 'http://localhost:18885/api/v1/b/logout', '', NULL, '2026-05-14 14:19:43', '35ceae09d7fc47fa9a5c46d56d77591f', 'admin', 'd218c751edac72ac037f719b44aad00e8d43f5d154d56177aa0a5e2bc5e3dd45', '2026-05-14 14:19:43', NULL, '2026-05-14 14:19:43', NULL);
INSERT INTO `sys_log` VALUES ('7460574569590427648', 'LOGIN', '登录', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', '', '', 'POST', 'http://localhost:18885/api/v1/public/b/login', '', NULL, '2026-05-14 14:19:48', '15250291691d40b78d03cf861d03c764', 'admin', '641c6d86fd08f5b1366a0e7c467e2b04e17ea827ef74be536362e068cfa458d6', '2026-05-14 14:19:48', NULL, '2026-05-14 14:19:48', NULL);
INSERT INTO `sys_log` VALUES ('7460597976516268032', 'LOGIN', '登录', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', '', '', 'POST', 'http://localhost:18885/api/v1/public/b/login', '', NULL, '2026-05-14 15:52:49', 'c48b577c89584664a28bf3e254d3b6df', 'admin', '8df85e7d99a8d00b9b5cb772872acf86a379a54abc4cc585f70b759c0d23f0b3', '2026-05-14 15:52:49', NULL, '2026-05-14 15:52:49', NULL);
INSERT INTO `sys_log` VALUES ('7460600988466941952', 'OPERATE', '编辑资源', 'SUCCESS', NULL, '127.0.0.1', '', 'Chrome', 'Windows', 'modules.sys.resource.api.v1.api', 'resource_modify', 'POST', 'http://localhost:18885/api/v1/sys/resource/modify', '{\"vo\": \"id=\'80003\' code=\'DEV_TOOLS\' name=\'系统工具\' category=\'BACKEND_MENU\' type=\'DIRECTORY\' description=\'系统工具目录\' parent_id=None route_path=\'/dev\' component_path=None redirect_path=None icon=\'tool\' color=None is_visible=\'NO\' is_cache=\'NO\' is_affix=\'NO\' is_breadcrumb=\'YES\' external_url=None extra=None status=\'ENABLED\' sort_code=3 is_deleted=\'NO\' created_at=datetime.datetime(2026, 5, 12, 14, 55, 52) created_by=\'50001\' updated_at=datetime.datetime(2026, 5, 14, 7, 42, 53) updated_by=\'50001\'\"}', '{\"code\": 200, \"message\": \"请求成功\", \"data\": null, \"success\": true, \"trace_id\": \"492c2289c61f4fc78e09026bdd3e5f33\"}', '2026-05-14 16:04:47', '492c2289c61f4fc78e09026bdd3e5f33', 'admin', 'a8497db53535c7ed74c3a9a389de56bb4f37895427e4cc7f8afe60ea88116b8a', '2026-05-14 16:04:47', NULL, '2026-05-14 16:04:47', NULL);

-- ----------------------------
-- Table structure for sys_module
-- ----------------------------
DROP TABLE IF EXISTS `sys_module`;
CREATE TABLE `sys_module`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模块编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模块名称',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '模块类别',
  `icon` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块图标',
  `color` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块颜色',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '模块描述',
  `is_visible` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'YES' COMMENT '是否可见',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '模块' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_module
-- ----------------------------
INSERT INTO `sys_module` VALUES ('70001', 'SYS', '系统管理', 'BACKEND_MENU', 'setting', '#1890FF', '系统管理模块', 'YES', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_module` VALUES ('70002', 'CONTENT', '内容管理', 'BACKEND_MENU', 'file-text', '#52C41A', '内容管理模块', 'YES', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_module` VALUES ('70003', 'DEV', '系统工具', 'BACKEND_MENU', 'tool', '#722ED1', '系统工具模块', 'YES', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_module` VALUES ('70004', 'MONITOR', '系统监控', 'BACKEND_MENU', 'dashboard', '#FAAD14', '系统监控模块', 'YES', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_module` VALUES ('70005', 'IM', '即时通讯', 'BACKEND_MENU', 'message', '#FF4D4F', '即时通讯模块', 'YES', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_notice
-- ----------------------------
DROP TABLE IF EXISTS `sys_notice`;
CREATE TABLE `sys_notice`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `title` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '通知标题',
  `summary` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '通知摘要',
  `content` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '通知内容',
  `cover` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '封面图片',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '通知类别',
  `type` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '通知类型',
  `level` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NORMAL' COMMENT '通知级别',
  `view_count` int NULL DEFAULT 0 COMMENT '浏览次数',
  `is_top` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '是否置顶',
  `position` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '通知位置',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_category_type`(`category` ASC, `type` ASC) USING BTREE,
  INDEX `idx_status`(`status` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '通知' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_notice
-- ----------------------------
INSERT INTO `sys_notice` VALUES ('100001', '系统升级维护通知', '系统将于本周六凌晨2:00-6:00进行升级维护', '<h1>系统升级维护</h1><p>为了提供更好的服务，系统将于本周六凌晨2:00-6:00进行升级维护，期间部分功能可能无法正常使用。</p>', NULL, 'PLATFORM', 'MAINTENANCE', 'IMPORTANT', 0, 'YES', 'TOP', 'ENABLED', 1, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_notice` VALUES ('100002', '欢迎使用 Hei FastAPI 系统', '欢迎各位同事使用全新开发的后台管理系统', '<p>Hei FastAPI 是一套基于 FastAPI + SQLAlchemy 2.0 的后台管理系统，欢迎大家体验并提供宝贵意见。</p>', NULL, 'PLATFORM', 'SYSTEM_NOTICE', 'NORMAL', 0, 'NO', 'TOP', 'ENABLED', 2, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_notice` VALUES ('100003', '第三季度工作总结会议通知', '请各部门负责人准备第三季度工作总结报告', '<p>公司将于下周五召开第三季度工作总结会议，请各部门负责人准备相关材料。</p>', NULL, 'COMPANY', 'BUSINESS_NOTICE', 'IMPORTANT', 0, 'NO', NULL, 'ENABLED', 3, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');
INSERT INTO `sys_notice` VALUES ('100004', '关于启用新系统的通知', '即日起正式启用全新后台管理系统', '<p>经过开发团队的不懈努力，全新后台管理系统已于今日正式上线，旧系统将并行运行一个月后下线。</p>', NULL, 'PLATFORM', 'SYSTEM_NOTICE', 'NORMAL', 0, 'NO', NULL, 'ENABLED', 4, '2026-05-12 14:55:53', '50001', '2026-05-12 14:55:53', '50001');

-- ----------------------------
-- Table structure for sys_org
-- ----------------------------
DROP TABLE IF EXISTS `sys_org`;
CREATE TABLE `sys_org`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '组织编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '组织名称',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '组织类别',
  `parent_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '父组织ID',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '组织描述',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE,
  INDEX `idx_parent_id`(`parent_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '组织' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_org
-- ----------------------------
INSERT INTO `sys_org` VALUES ('10001', 'HEI', 'Hei集团', 'GROUP', NULL, '集团总部', 'ENABLED', 1, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10002', 'TECH', '技术部', 'DEPT', '10001', '技术研发部门', 'ENABLED', 2, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10003', 'MKT', '市场部', 'DEPT', '10001', '市场营销部门', 'ENABLED', 3, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10004', 'FIN', '财务部', 'DEPT', '10001', '财务管理部门', 'ENABLED', 4, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10005', 'HR', '人力资源部', 'DEPT', '10001', '人力资源管理部门', 'ENABLED', 5, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10006', 'SALES', '销售部', 'DEPT', '10001', '销售部门', 'ENABLED', 6, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_org` VALUES ('10007', 'OPS', '运维部', 'DEPT', '10001', '运维管理部门', 'ENABLED', 7, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_position
-- ----------------------------
DROP TABLE IF EXISTS `sys_position`;
CREATE TABLE `sys_position`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位名称',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '职位类别',
  `org_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属组织ID',
  `group_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属用户组ID',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '职位描述',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '职位' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_position
-- ----------------------------
INSERT INTO `sys_position` VALUES ('20001', 'CEO', '总经理', 'MGMT', '10001', NULL, '公司总经理', 'ENABLED', 1, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20002', 'CTO', '技术总监', 'TECH', '10002', NULL, '技术部门总监', 'ENABLED', 2, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20003', 'DEV_LEAD', '开发组长', 'TECH', '10002', NULL, '开发团队组长', 'ENABLED', 3, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20004', 'DEV', '开发工程师', 'TECH', '10002', NULL, '软件开发工程师', 'ENABLED', 4, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20005', 'TEST', '测试工程师', 'TECH', '10002', NULL, '软件测试工程师', 'ENABLED', 5, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20006', 'PM', '产品经理', 'MKT', '10003', NULL, '产品经理', 'ENABLED', 6, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20007', 'MKT_DIR', '市场总监', 'MKT', '10003', NULL, '市场部总监', 'ENABLED', 7, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20008', 'FIN_DIR', '财务总监', 'FIN', '10004', NULL, '财务部总监', 'ENABLED', 8, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20009', 'HR_DIR', '人力资源总监', 'HR', '10005', NULL, '人力资源部总监', 'ENABLED', 9, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20010', 'SALES', '销售专员', 'SALES', '10006', NULL, '销售专员', 'ENABLED', 10, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_position` VALUES ('20011', 'OPS', '运维工程师', 'OPS', '10007', NULL, '运维工程师', 'ENABLED', 11, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_quick_action
-- ----------------------------
DROP TABLE IF EXISTS `sys_quick_action`;
CREATE TABLE `sys_quick_action`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `user_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '用户ID',
  `resource_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源ID',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_user_resource`(`user_id` ASC, `resource_id` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户快捷方式' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_quick_action
-- ----------------------------

-- ----------------------------
-- Table structure for sys_resource
-- ----------------------------
DROP TABLE IF EXISTS `sys_resource`;
CREATE TABLE `sys_resource`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源名称',
  `category` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源分类：BACKEND_MENU-后台菜单，FRONTEND_MENU-前台菜单，BACKEND_BUTTON-后台按钮，FRONTEND_BUTTON-前台按钮',
  `type` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '资源类型：DIRECTORY-目录，MENU-菜单，BUTTON-按钮，INTERNAL_LINK-内链，EXTERNAL_LINK-外链',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '资源描述',
  `parent_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '父资源ID',
  `route_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '路由路径',
  `component_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '组件路径',
  `redirect_path` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '重定向路径',
  `icon` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '资源图标',
  `color` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '资源颜色（前台资源使用）',
  `is_visible` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'YES' COMMENT '是否可见',
  `is_cache` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '是否缓存',
  `is_affix` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'NO' COMMENT '是否固定',
  `is_breadcrumb` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'YES' COMMENT '是否显示面包屑',
  `external_url` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '外链地址',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '资源' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_resource
-- ----------------------------
INSERT INTO `sys_resource` VALUES ('80001', 'SYS_ADMIN', '系统管理', 'BACKEND_MENU', 'DIRECTORY', '系统管理目录', NULL, '/sys', NULL, NULL, 'setting', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80002', 'CONTENT_MGR', '内容管理', 'BACKEND_MENU', 'DIRECTORY', '内容管理目录', NULL, '/content', NULL, NULL, 'file-text', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80003', 'DEV_TOOLS', '系统工具', 'BACKEND_MENU', 'DIRECTORY', '系统工具目录', NULL, '/dev', NULL, NULL, 'tool', NULL, 'NO', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-14 16:04:47', '50001');
INSERT INTO `sys_resource` VALUES ('80004', 'SYS_USER', '用户管理', 'BACKEND_MENU', 'MENU', '用户管理菜单', '80001', '/sys/user', 'sys/user/index', NULL, 'user', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80005', 'SYS_ROLE', '角色管理', 'BACKEND_MENU', 'MENU', '角色管理菜单', '80001', '/sys/role', 'sys/role/index', NULL, 'team', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80006', 'SYS_RESOURCE_MGR', '资源管理', 'BACKEND_MENU', 'MENU', '资源管理菜单', '80001', '/sys/resource', 'sys/resource/index', NULL, 'menu', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80007', 'SYS_ORG', '组织管理', 'BACKEND_MENU', 'MENU', '组织管理菜单', '80001', '/sys/org', 'sys/org/index', NULL, 'apartment', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80008', 'SYS_POSITION', '职位管理', 'BACKEND_MENU', 'MENU', '职位管理菜单', '80001', '/sys/org/group/position', 'sys/org/components/group/components/position/index', NULL, 'idcard', NULL, 'NO', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 6, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80009', 'SYS_GROUP', '用户组管理', 'BACKEND_MENU', 'MENU', '用户组管理菜单', '80001', '/sys/org/group', 'sys/org/components/group/index', NULL, 'group', NULL, 'NO', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 7, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80010', 'SYS_DICT', '字典管理', 'BACKEND_MENU', 'MENU', '字典管理菜单', '80001', '/sys/dict', 'sys/dict/index', NULL, 'book', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 8, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80011', 'SYS_CONFIG', '系统配置', 'BACKEND_MENU', 'MENU', '系统配置菜单', '80001', '/sys/config', 'sys/config/index', NULL, 'setting', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 9, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80012', 'SYS_NOTICE', '通知管理', 'BACKEND_MENU', 'MENU', '通知管理菜单', '80001', '/sys/notice', 'sys/notice/index', NULL, 'notification', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 10, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80013', 'SYS_BANNER', '轮播图管理', 'BACKEND_MENU', 'MENU', '轮播图管理菜单', '80002', '/sys/banner', 'sys/banner/index', NULL, 'picture', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80014', 'SYS_FILE', '文件管理', 'BACKEND_MENU', 'MENU', '文件管理菜单', '80002', '/sys/file', 'sys/file/index', NULL, 'file', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80015', 'SYS_DEV', '代码生成', 'BACKEND_MENU', 'MENU', '代码生成菜单', '80003', '/sys/dev', 'sys/dev/index', NULL, 'code', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-14 07:43:12', '50001');
INSERT INTO `sys_resource` VALUES ('80016', 'SYS_USER_PAGE', '用户查询', 'BACKEND_BUTTON', 'BUTTON', '查询用户列表', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80017', 'SYS_USER_CREATE', '用户新增', 'BACKEND_BUTTON', 'BUTTON', '新增用户', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80018', 'SYS_USER_MODIFY', '用户修改', 'BACKEND_BUTTON', 'BUTTON', '修改用户', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80019', 'SYS_USER_REMOVE', '用户删除', 'BACKEND_BUTTON', 'BUTTON', '删除用户', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80020', 'SYS_USER_DETAIL', '用户详情', 'BACKEND_BUTTON', 'BUTTON', '查看用户详情', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80021', 'SYS_USER_EXPORT', '用户导出', 'BACKEND_BUTTON', 'BUTTON', '导出用户数据', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:export\"}', 'ENABLED', 6, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80022', 'SYS_USER_IMPORT', '用户导入', 'BACKEND_BUTTON', 'BUTTON', '导入用户数据', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:import\"}', 'ENABLED', 7, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80023', 'SYS_USER_GRANT_ROLE', '分配角色', 'BACKEND_BUTTON', 'BUTTON', '给用户分配角色', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:grant-role\"}', 'ENABLED', 8, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80025', 'SYS_ROLE_PAGE', '角色查询', 'BACKEND_BUTTON', 'BUTTON', '查询角色列表', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80026', 'SYS_ROLE_CREATE', '角色新增', 'BACKEND_BUTTON', 'BUTTON', '新增角色', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80027', 'SYS_ROLE_MODIFY', '角色修改', 'BACKEND_BUTTON', 'BUTTON', '修改角色', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80028', 'SYS_ROLE_REMOVE', '角色删除', 'BACKEND_BUTTON', 'BUTTON', '删除角色', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80029', 'SYS_ROLE_DETAIL', '角色详情', 'BACKEND_BUTTON', 'BUTTON', '查看角色详情', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:01', '50001');
INSERT INTO `sys_resource` VALUES ('80030', 'SYS_ROLE_EXPORT', '角色导出', 'BACKEND_BUTTON', 'BUTTON', '导出角色数据', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:export\"}', 'ENABLED', 6, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80031', 'SYS_ROLE_GRANT_PERM', '分配权限', 'BACKEND_BUTTON', 'BUTTON', '给角色分配权限', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:grant-permission\"}', 'ENABLED', 7, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80032', 'SYS_ROLE_GRANT_RESOURCE', '分配资源', 'BACKEND_BUTTON', 'BUTTON', '给角色分配资源', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:grant-resource\"}', 'ENABLED', 8, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:02', '50001');
INSERT INTO `sys_resource` VALUES ('80033', 'SYS_RESOURCE_PAGE', '资源查询', 'BACKEND_BUTTON', 'BUTTON', '查询资源列表', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80034', 'SYS_RESOURCE_CREATE', '资源新增', 'BACKEND_BUTTON', 'BUTTON', '新增资源', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80035', 'SYS_RESOURCE_MODIFY', '资源修改', 'BACKEND_BUTTON', 'BUTTON', '修改资源', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80036', 'SYS_RESOURCE_REMOVE', '资源删除', 'BACKEND_BUTTON', 'BUTTON', '删除资源', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80037', 'SYS_RESOURCE_DETAIL', '资源详情', 'BACKEND_BUTTON', 'BUTTON', '查看资源详情', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80038', 'SYS_ORG_PAGE', '组织查询', 'BACKEND_BUTTON', 'BUTTON', '查询组织列表', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80039', 'SYS_ORG_CREATE', '组织新增', 'BACKEND_BUTTON', 'BUTTON', '新增组织', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80040', 'SYS_ORG_MODIFY', '组织修改', 'BACKEND_BUTTON', 'BUTTON', '修改组织', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80041', 'SYS_ORG_REMOVE', '组织删除', 'BACKEND_BUTTON', 'BUTTON', '删除组织', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80042', 'SYS_ORG_DETAIL', '组织详情', 'BACKEND_BUTTON', 'BUTTON', '查看组织详情', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80043', 'SYS_ORG_GRANT_ROLE', '分配角色', 'BACKEND_BUTTON', 'BUTTON', '给组织分配角色', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:grant-role\"}', 'ENABLED', 6, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80044', 'SYS_POSITION_PAGE', '职位查询', 'BACKEND_BUTTON', 'BUTTON', '查询职位列表', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80045', 'SYS_POSITION_CREATE', '职位新增', 'BACKEND_BUTTON', 'BUTTON', '新增职位', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80046', 'SYS_POSITION_MODIFY', '职位修改', 'BACKEND_BUTTON', 'BUTTON', '修改职位', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80047', 'SYS_POSITION_REMOVE', '职位删除', 'BACKEND_BUTTON', 'BUTTON', '删除职位', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80048', 'SYS_POSITION_DETAIL', '职位详情', 'BACKEND_BUTTON', 'BUTTON', '查看职位详情', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80049', 'SYS_GROUP_PAGE', '用户组查询', 'BACKEND_BUTTON', 'BUTTON', '查询用户组列表', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80050', 'SYS_GROUP_CREATE', '用户组新增', 'BACKEND_BUTTON', 'BUTTON', '新增用户组', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80051', 'SYS_GROUP_MODIFY', '用户组修改', 'BACKEND_BUTTON', 'BUTTON', '修改用户组', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80052', 'SYS_GROUP_REMOVE', '用户组删除', 'BACKEND_BUTTON', 'BUTTON', '删除用户组', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80053', 'SYS_GROUP_DETAIL', '用户组详情', 'BACKEND_BUTTON', 'BUTTON', '查看用户组详情', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80054', 'SYS_GROUP_GRANT_ROLE', '分配角色', 'BACKEND_BUTTON', 'BUTTON', '给用户组分配角色', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:create\"}', 'ENABLED', 6, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80055', 'SYS_DICT_PAGE', '字典查询', 'BACKEND_BUTTON', 'BUTTON', '查询字典列表', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80056', 'SYS_DICT_CREATE', '字典新增', 'BACKEND_BUTTON', 'BUTTON', '新增字典', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80057', 'SYS_DICT_MODIFY', '字典修改', 'BACKEND_BUTTON', 'BUTTON', '修改字典', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80058', 'SYS_DICT_REMOVE', '字典删除', 'BACKEND_BUTTON', 'BUTTON', '删除字典', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80059', 'SYS_DICT_DETAIL', '字典详情', 'BACKEND_BUTTON', 'BUTTON', '查看字典详情', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80060', 'SYS_CONFIG_PAGE', '配置查询', 'BACKEND_BUTTON', 'BUTTON', '查询配置列表', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80061', 'SYS_CONFIG_CREATE', '配置新增', 'BACKEND_BUTTON', 'BUTTON', '新增配置', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80062', 'SYS_CONFIG_MODIFY', '配置修改', 'BACKEND_BUTTON', 'BUTTON', '修改配置', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80063', 'SYS_CONFIG_REMOVE', '配置删除', 'BACKEND_BUTTON', 'BUTTON', '删除配置', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80064', 'SYS_CONFIG_DETAIL', '配置详情', 'BACKEND_BUTTON', 'BUTTON', '查看配置详情', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80065', 'SYS_NOTICE_PAGE', '通知查询', 'BACKEND_BUTTON', 'BUTTON', '查询通知列表', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80066', 'SYS_NOTICE_CREATE', '通知新增', 'BACKEND_BUTTON', 'BUTTON', '新增通知', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80067', 'SYS_NOTICE_MODIFY', '通知修改', 'BACKEND_BUTTON', 'BUTTON', '修改通知', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80068', 'SYS_NOTICE_REMOVE', '通知删除', 'BACKEND_BUTTON', 'BUTTON', '删除通知', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80069', 'SYS_NOTICE_DETAIL', '通知详情', 'BACKEND_BUTTON', 'BUTTON', '查看通知详情', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80070', 'SYS_BANNER_PAGE', '轮播查询', 'BACKEND_BUTTON', 'BUTTON', '查询轮播图列表', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:page\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-13 08:19:08', '50001');
INSERT INTO `sys_resource` VALUES ('80071', 'SYS_BANNER_CREATE', '轮播新增', 'BACKEND_BUTTON', 'BUTTON', '新增轮播图', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:create\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-13 08:19:08', '50001');
INSERT INTO `sys_resource` VALUES ('80072', 'SYS_BANNER_MODIFY', '轮播修改', 'BACKEND_BUTTON', 'BUTTON', '修改轮播图', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:modify\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-13 08:19:08', '50001');
INSERT INTO `sys_resource` VALUES ('80073', 'SYS_BANNER_REMOVE', '轮播删除', 'BACKEND_BUTTON', 'BUTTON', '删除轮播图', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-13 08:19:09', '50001');
INSERT INTO `sys_resource` VALUES ('80074', 'SYS_BANNER_DETAIL', '轮播详情', 'BACKEND_BUTTON', 'BUTTON', '查看轮播图详情', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:detail\"}', 'ENABLED', 5, '2026-05-12 14:55:52', '50001', '2026-05-13 08:19:08', '50001');
INSERT INTO `sys_resource` VALUES ('80075', 'SYS_FILE_UPLOAD', '文件上传', 'BACKEND_BUTTON', 'BUTTON', '上传文件', '80014', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:file:upload\"}', 'ENABLED', 1, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:33', '50001');
INSERT INTO `sys_resource` VALUES ('80076', 'SYS_FILE_DOWNLOAD', '文件下载', 'BACKEND_BUTTON', 'BUTTON', '下载文件', '80014', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:file:download\"}', 'ENABLED', 2, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:33', '50001');
INSERT INTO `sys_resource` VALUES ('80077', 'SYS_FILE_PAGE', '文件查询', 'BACKEND_BUTTON', 'BUTTON', '查询文件列表', '80014', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:file:page\"}', 'ENABLED', 3, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:33', '50001');
INSERT INTO `sys_resource` VALUES ('80078', 'SYS_FILE_REMOVE', '文件删除', 'BACKEND_BUTTON', 'BUTTON', '删除文件', '80014', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:file:remove\"}', 'ENABLED', 4, '2026-05-12 14:55:52', '50001', '2026-05-13 10:31:33', '50001');
INSERT INTO `sys_resource` VALUES ('80079', 'SYS_USER_GRANT_PERM', '授权权限', 'BACKEND_BUTTON', 'BUTTON', '给用户授权颗粒度权限', '80004', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:user:grant-permission\"}', 'ENABLED', 10, '2026-05-12 14:55:52', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80080', 'SYS_DASHBOARD', '仪表盘', 'BACKEND_MENU', 'MENU', '仪表盘', NULL, '/dashboard', 'dashboard/index', NULL, 'dashboard', NULL, 'YES', 'NO', 'YES', 'YES', NULL, NULL, 'ENABLED', 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80081', 'SYS_ORG_EXPORT', '组织导出', 'BACKEND_BUTTON', 'BUTTON', '导出组织数据', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:export\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80082', 'SYS_ORG_IMPORT', '组织导入', 'BACKEND_BUTTON', 'BUTTON', '导入组织数据', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:import\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80083', 'SYS_ORG_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载组织导入模板', '80007', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:org:template\"}', 'ENABLED', 9, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80084', 'SYS_POSITION_EXPORT', '职位导出', 'BACKEND_BUTTON', 'BUTTON', '导出职位数据', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:export\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80085', 'SYS_POSITION_IMPORT', '职位导入', 'BACKEND_BUTTON', 'BUTTON', '导入职位数据', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:import\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80086', 'SYS_POSITION_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载职位导入模板', '80008', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:position:template\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80087', 'SYS_GROUP_EXPORT', '用户组导出', 'BACKEND_BUTTON', 'BUTTON', '导出用户组数据', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:export\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80088', 'SYS_GROUP_IMPORT', '用户组导入', 'BACKEND_BUTTON', 'BUTTON', '导入用户组数据', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:import\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80089', 'SYS_GROUP_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载用户组导入模板', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:template\"}', 'ENABLED', 9, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80090', 'SYS_DICT_EXPORT', '字典导出', 'BACKEND_BUTTON', 'BUTTON', '导出字典数据', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:export\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80091', 'SYS_DICT_IMPORT', '字典导入', 'BACKEND_BUTTON', 'BUTTON', '导入字典数据', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:import\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80092', 'SYS_DICT_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载字典导入模板', '80010', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:dict:template\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80093', 'SYS_CONFIG_EDIT_BATCH', '批量编辑', 'BACKEND_BUTTON', 'BUTTON', '批量编辑系统配置', '80011', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:config:edit\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80094', 'SYS_NOTICE_EXPORT', '通知导出', 'BACKEND_BUTTON', 'BUTTON', '导出通知数据', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:export\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80095', 'SYS_NOTICE_IMPORT', '通知导入', 'BACKEND_BUTTON', 'BUTTON', '导入通知数据', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:import\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80096', 'SYS_NOTICE_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载通知导入模板', '80012', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:notice:template\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80097', 'SYS_BANNER_EXPORT', '轮播导出', 'BACKEND_BUTTON', 'BUTTON', '导出轮播图数据', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:export\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80098', 'SYS_BANNER_IMPORT', '轮播导入', 'BACKEND_BUTTON', 'BUTTON', '导入轮播图数据', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:import\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80099', 'SYS_BANNER_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载轮播导入模板', '80013', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:banner:template\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80100', 'SYS_FILE_DETAIL', '文件详情', 'BACKEND_BUTTON', 'BUTTON', '查看文件详情', '80014', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:file:detail\"}', 'ENABLED', 5, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80101', 'SYS_RESOURCE_EXPORT', '资源导出', 'BACKEND_BUTTON', 'BUTTON', '导出资源数据', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:export\"}', 'ENABLED', 6, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80102', 'SYS_RESOURCE_IMPORT', '资源导入', 'BACKEND_BUTTON', 'BUTTON', '导入资源数据', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:import\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80103', 'SYS_RESOURCE_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载资源导入模板', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:template\"}', 'ENABLED', 8, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80104', 'SYS_ROLE_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载角色导入模板', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:template\"}', 'ENABLED', 10, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80105', 'SYS_ROLE_IMPORT', '角色导入', 'BACKEND_BUTTON', 'BUTTON', '导入角色数据', '80005', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:role:import\"}', 'ENABLED', 9, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80106', 'SYS_GROUP_TREE', '用户组树', 'BACKEND_BUTTON', 'BUTTON', '查询用户组树', '80009', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:group:tree\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80107', 'SYS_RESOURCE_TREE', '资源树', 'BACKEND_BUTTON', 'BUTTON', '查询资源树', '80006', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:resource:tree\"}', 'ENABLED', 7, '2026-05-13 10:30:22', '50001', '2026-05-13 10:30:22', '50001');
INSERT INTO `sys_resource` VALUES ('80108', 'SYS_HOME', '首页', 'BACKEND_MENU', 'MENU', '首页', NULL, '/home', 'home/index', NULL, 'home', NULL, 'YES', 'YES', 'NO', 'YES', NULL, NULL, 'ENABLED', 0, '2026-05-13 14:55:52', '50001', '2026-05-14 07:43:59', '50001');
INSERT INTO `sys_resource` VALUES ('80109', 'SYS_LOG', '系统日志', 'BACKEND_MENU', 'DIRECTORY', '系统日志目录', '0', '/sys/log', NULL, NULL, 'file-text', NULL, 'YES', 'NO', 'NO', 'YES', '', NULL, 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:17:59', '50001');
INSERT INTO `sys_resource` VALUES ('80110', 'SYS_OPLOG', '操作日志', 'BACKEND_MENU', 'MENU', '操作日志', '80109', '/sys/log/oplog', 'sys/log/oplog/index', NULL, 'audit', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80111', 'SYS_VISLOG', '访问日志', 'BACKEND_MENU', 'MENU', '访问日志', '80109', '/sys/log/vislog', 'sys/log/vislog/index', NULL, 'eye', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80112', 'SYS_LOG_PAGE', '日志查询', 'BACKEND_BUTTON', 'BUTTON', '查询日志列表', '80110', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:page\"}', 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80113', 'SYS_LOG_DETAIL', '日志详情', 'BACKEND_BUTTON', 'BUTTON', '查看日志详情', '80110', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:detail\"}', 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80114', 'SYS_LOG_REMOVE', '日志删除', 'BACKEND_BUTTON', 'BUTTON', '删除/清空日志', '80110', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:remove\"}', 'ENABLED', 3, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80115', 'SYS_VISLOG_PAGE', '日志查询', 'BACKEND_BUTTON', 'BUTTON', '查询访问日志列表', '80111', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:page\"}', 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80116', 'SYS_VISLOG_DETAIL', '日志详情', 'BACKEND_BUTTON', 'BUTTON', '查看访问日志详情', '80111', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:detail\"}', 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80117', 'SYS_VISLOG_REMOVE', '日志删除', 'BACKEND_BUTTON', 'BUTTON', '删除/清空访问日志', '80111', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:log:remove\"}', 'ENABLED', 3, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80118', 'SYS_SESSION', '会话管理', 'BACKEND_MENU', 'MENU', '会话管理', '80001', '/sys/auth/monitor', 'auth/monitor/index', NULL, 'team', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 11, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80119', 'SYS_SESSION_PAGE', '会话查询', 'BACKEND_BUTTON', 'BUTTON', '查询会话列表', '80118', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:session:page\"}', 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80120', 'SYS_SESSION_EXIT', '强制下线', 'BACKEND_BUTTON', 'BUTTON', '强制用户下线', '80118', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"sys:session:exit\"}', 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80121', 'CLIENT_ADMIN', 'C端管理', 'BACKEND_MENU', 'DIRECTORY', 'C端管理目录', NULL, '/client', NULL, NULL, 'user', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 4, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80122', 'CLIENT_USER', '用户管理', 'BACKEND_MENU', 'MENU', 'C端用户管理菜单', '80121', '/client/user', 'client/user/index', NULL, 'team', NULL, 'YES', 'NO', 'NO', 'YES', NULL, NULL, 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80123', 'CLIENT_USER_PAGE', '用户查询', 'BACKEND_BUTTON', 'BUTTON', '查询C端用户列表', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:page\"}', 'ENABLED', 1, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80124', 'CLIENT_USER_CREATE', '用户新增', 'BACKEND_BUTTON', 'BUTTON', '新增C端用户', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:create\"}', 'ENABLED', 2, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80125', 'CLIENT_USER_MODIFY', '用户修改', 'BACKEND_BUTTON', 'BUTTON', '修改C端用户', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:modify\"}', 'ENABLED', 3, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80126', 'CLIENT_USER_REMOVE', '用户删除', 'BACKEND_BUTTON', 'BUTTON', '删除C端用户', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:remove\"}', 'ENABLED', 4, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80127', 'CLIENT_USER_DETAIL', '用户详情', 'BACKEND_BUTTON', 'BUTTON', '查看C端用户详情', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:detail\"}', 'ENABLED', 5, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80128', 'CLIENT_USER_EXPORT', '用户导出', 'BACKEND_BUTTON', 'BUTTON', '导出C端用户数据', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:export\"}', 'ENABLED', 6, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80129', 'CLIENT_USER_IMPORT', '用户导入', 'BACKEND_BUTTON', 'BUTTON', '导入C端用户数据', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:import\"}', 'ENABLED', 8, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');
INSERT INTO `sys_resource` VALUES ('80130', 'CLIENT_USER_TEMPLATE', '导入模板', 'BACKEND_BUTTON', 'BUTTON', '下载C端用户导入模板', '80122', NULL, NULL, NULL, NULL, NULL, 'YES', 'NO', 'NO', 'YES', NULL, '{\"permission_code\":\"client:user:template\"}', 'ENABLED', 7, '2026-05-14 14:55:52', '50001', '2026-05-14 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_role
-- ----------------------------
DROP TABLE IF EXISTS `sys_role`;
CREATE TABLE `sys_role`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `code` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色编码',
  `name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色名称',
  `category` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '角色类别',
  `description` varchar(500) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '角色描述',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ENABLED' COMMENT '状态',
  `sort_code` int NULL DEFAULT 0 COMMENT '排序',
  `extra` text CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '扩展信息',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  UNIQUE INDEX `uk_code`(`code` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '角色' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_role
-- ----------------------------
INSERT INTO `sys_role` VALUES ('40001', 'SUPER_ADMIN', '超级管理员', 'BACKEND', '系统超级管理员，拥有全部权限', 'ENABLED', 1, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40002', 'ADMIN', '系统管理员', 'BACKEND', '系统管理员', 'ENABLED', 2, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40003', 'DEV', '开发人员', 'BACKEND', '开发人员角色', 'ENABLED', 3, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40004', 'TEST', '测试人员', 'BACKEND', '测试人员角色', 'ENABLED', 4, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40005', 'MKT', '市场人员', 'BACKEND', '市场人员角色', 'ENABLED', 5, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40006', 'FIN', '财务人员', 'BACKEND', '财务人员角色', 'ENABLED', 6, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_role` VALUES ('40007', 'HR', '人力资源', 'BACKEND', '人力资源角色', 'ENABLED', 7, NULL, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

-- ----------------------------
-- Table structure for sys_user
-- ----------------------------
DROP TABLE IF EXISTS `sys_user`;
CREATE TABLE `sys_user`  (
  `id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NOT NULL COMMENT '主键',
  `account` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '账号',
  `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '密码',
  `nickname` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '昵称',
  `avatar` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL COMMENT '头像',
  `motto` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '座右铭',
  `gender` varchar(8) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '性别',
  `birthday` date NULL DEFAULT NULL COMMENT '生日',
  `email` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '电子邮箱',
  `github` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT 'GitHub',
  `phone` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '手机号',
  `org_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属组织ID',
  `position_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属职位ID',
  `group_id` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '所属用户组ID',
  `status` varchar(16) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT 'ACTIVE' COMMENT '状态',
  `last_login_at` datetime NULL DEFAULT NULL COMMENT '最后登录时间',
  `last_login_ip` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '最后登录IP',
  `login_count` int NULL DEFAULT 0 COMMENT '登录次数',
  `created_at` datetime NULL DEFAULT NULL COMMENT '创建时间',
  `created_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '创建用户',
  `updated_at` datetime NULL DEFAULT NULL COMMENT '更新时间',
  `updated_by` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '更新用户',
  PRIMARY KEY (`id`) USING BTREE,
  INDEX `idx_account`(`account` ASC) USING BTREE
) ENGINE = InnoDB CHARACTER SET = utf8mb4 COLLATE = utf8mb4_general_ci COMMENT = '用户' ROW_FORMAT = DYNAMIC;

-- ----------------------------
-- Records of sys_user
-- ----------------------------
INSERT INTO `sys_user` VALUES ('50001', 'admin', '$2b$12$5t3Ey0kGLXaWgmUMYHh8aeh9hOTwpIcKI4M.txQi26Sd3jz4aeEm2', '管理员', NULL, '管理一切', 'MALE', '1990-01-01', 'admin@hei.com', NULL, '13800000001', '10001', '20001', '30001', 'ACTIVE', '2026-05-14 15:52:49', '127.0.0.1', 7, '2026-05-12 14:55:52', '50001', '2026-05-14 15:52:49', '50001');
INSERT INTO `sys_user` VALUES ('50002', 'zhangsan', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '张三', NULL, '代码改变世界', 'MALE', '1995-05-15', 'zhangsan@hei.com', 'https://github.com/zhangsan', '13800000002', '10002', '20004', '30002', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50003', 'lisi', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '李四', NULL, '学无止境', 'MALE', '1993-08-20', 'lisi@hei.com', NULL, '13800000003', '10002', '20004', '30002', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50004', 'wangwu', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '王五', NULL, '追求卓越', 'MALE', '1994-03-10', 'wangwu@hei.com', NULL, '13800000004', '10002', '20003', '30002', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50005', 'zhaoliu', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '赵六', NULL, '质量第一', 'FEMALE', '1996-11-25', 'zhaoliu@hei.com', NULL, '13800000005', '10002', '20005', '30003', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50006', 'sunqi', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '孙七', NULL, '用户至上', 'MALE', '1991-07-07', 'sunqi@hei.com', NULL, '13800000006', '10003', '20006', '30004', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50007', 'zhouba', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '周八', NULL, '市场就是战场', 'FEMALE', '1992-02-14', 'zhouba@hei.com', NULL, '13800000007', '10003', '20007', '30005', 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50008', 'wujiu', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '吴九', NULL, '精打细算', 'MALE', '1988-09-09', 'wujiu@hei.com', NULL, '13800000008', '10004', '20008', NULL, 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50009', 'zhengshi', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '郑十', NULL, '以人为本', 'FEMALE', '1990-12-01', 'zhengshi@hei.com', NULL, '13800000009', '10005', '20009', NULL, 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');
INSERT INTO `sys_user` VALUES ('50010', 'chen十一', '$2b$12$UQFzAxtCkfwFwgrJy0XYm.rO860SX5NIH6zOEm/4SsUdgMA9SkuVC', '陈十一', NULL, '稳定压倒一切', 'MALE', '1993-06-18', 'chen11@hei.com', NULL, '13800000010', '10007', '20011', NULL, 'ACTIVE', NULL, NULL, 0, '2026-05-12 14:55:52', '50001', '2026-05-12 14:55:52', '50001');

SET FOREIGN_KEY_CHECKS = 1;
