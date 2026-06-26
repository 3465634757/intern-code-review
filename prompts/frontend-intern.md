# 前端实习生 - 岗位专项评审标准

> 本文件为岗位叠加层，继承 `_base-template.md` 的通用评审框架。
> 以下内容占据总分的 **25%（岗位专项维度）**。

## 岗位专项评审维度

### 1. 框架使用 (3分)

**React 技术栈：**
- 组件拆分是否合理（单一职责，不过度拆分也不过度耦合）
- State 管理是否得当（避免不必要的全局状态，正确选择 useState/useReducer/Context）
- useEffect 使用是否正确（依赖数组完整、有清理函数、无死循环）
- 是否存在不必要的重渲染（合理使用 memo/useMemo/useCallback）
- Hooks 规则是否遵守（不在条件语句中调用、自Hook命名以use开头）

**Vue 技术栈：**
- 组件通信方式是否合理（props/emit vs provide/inject vs Pinia）
- computed/watch 使用是否正确（避免在computed中产生副作用）
- 响应式数据使用是否正确（ref/reactive 区分、解构丢失响应性）
- 生命周期使用是否合理（onMounted/onUnmounted 配对）

**通用：**
- 是否过度使用第三方库解决简单问题
- 组件API设计是否简洁易用

### 2. 样式与布局 (3分)

- CSS 命名是否遵循团队规范（BEM / CSS Modules / Tailwind / styled-components）
- 是否存在大量内联样式或 `!important`
- 响应式设计是否考虑（移动端适配、断点设置）
- 是否使用设计系统/组件库的 token 和变量（而非硬编码色值/字号）
- 布局方式是否合理（Flex vs Grid 选择、避免过度嵌套）
- 动画/过渡是否流畅（是否使用 transform/opacity 而非触发重排的属性）

### 3. 用户体验意识 (3分)

- **三态处理**：Loading、Empty、Error 状态是否都有处理
- **表单校验**：前端校验是否完善、错误提示是否友好
- **无障碍 (a11y)**：是否使用语义化HTML标签、图片有alt、表单有label
- **国际化**：是否考虑文案长度差异（如果项目需要）
- **性能感知**：骨架屏、懒加载、图片优化是否考虑
- **错误边界**：是否使用 ErrorBoundary 防止局部错误白屏

### 4. TypeScript 与工程化 (3分)

- 类型定义是否准确（是否存在大量 `any`、`@ts-ignore`）
- Props 类型定义是否完整（是否用 interface/type 明确声明）
- 是否合理使用泛型和工具类型（Partial、Pick、Omit 等）
- 组件/工具函数是否有基本测试
- 是否引入了不必要的依赖（检查 package.json 变更）
- 构建产物是否考虑了代码分割

### 5. 前端安全 (3分)

- **XSS 防护**：是否正确处理用户输入、是否滥用 `dangerouslySetInnerHTML` / `v-html`
- **敏感信息**：API Key、Secret 是否硬编码在前端代码中
- **第三方依赖**：是否引入了已知有漏洞的包版本
- **CORS 理解**：是否理解跨域限制，而非盲目使用代理
- **Cookie/Storage**：敏感数据存储是否安全（httpOnly、secure 标记）

---

## 前端专项扣分示例（供AI参考）

| 问题 | 扣分 | 理由 |
|------|------|------|
| 组件超过300行未拆分 | -5 | 单一职责违反 |
| useEffect 缺少依赖项 | -8 | 会导致闭包陷阱 |
| 全是 any 类型 | -10 | 失去 TypeScript 意义 |
| dangerouslySetInnerHTML 未做 sanitize | -10 | XSS 风险 |
| Loading 状态完全没处理 | -5 | 用户体验差 |
| 硬编码色值 #333 散落各处 | -3 | 应使用设计token |
| 图片无 alt、表单无 label | -3 | 无障碍不达标 |
