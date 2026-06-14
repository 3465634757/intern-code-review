# 实习生周度评审报告

### 📋 基本信息

- **实习生姓名**：张三
- **岗位**：前端实习生
- **审查周期**：2026-W24（2026-06-08 ~ 2026-06-12）
- **本周提交数**：12次
- **涉及仓库**：company/web-app, company/component-lib
- **涉及模块**：用户个人中心页面重构、通用 Button 组件优化

---

### 📊 评分总览

| 维度 | 得分(/100) | 权重 | 加权得分 | 扣分原因 |
|------|-----------|------|----------|----------|
| 代码规范 | 78 | 15% | 11.7 | 部分组件命名不一致，混用 camelCase 和 PascalCase |
| 逻辑正确性 | 65 | 25% | 16.3 | 用户头像上传未处理网络超时，表单校验有遗漏 |
| 学习成长 | 82 | 20% | 16.4 | 相比上周明显进步，开始主动使用 TypeScript 泛型 |
| 工程实践 | 72 | 15% | 10.8 | commit message 不够规范，部分提交信息为 "fix" |
| 沟通协作 | 88 | 10% | 8.8 | PR 描述详细，主动在 review 中提出问题 |
| 岗位专项 | 58 | 15% | 8.7 | useEffect 依赖数组缺失、Loading 状态未处理 |
| **总分** | | | **72.7** | |

**等级**：🟡 C（合格）

---

### 🏆 本周亮点

1. **TypeScript 类型意识提升**：在 `UserProfile.tsx` 中主动使用了 `Partial<User>` 和 `Pick<User, 'name' | 'avatar'>` 工具类型，比上周到处写 `any` 有明显进步。

2. **组件设计思维萌芽**：`Button` 组件的重构中，考虑了 `variant`、`size`、`disabled`、`loading` 等 Props，API 设计趋于合理。

3. **主动沟通**：在 PR #234 中主动询问了"这里应该用 `useCallback` 吗？"，说明开始思考性能优化。

---

### ⚠️ 待改进项

🔴 **高优先级**

1. **useEffect 缺少依赖项导致闭包陷阱**
   - 文件：`src/pages/UserProfile.tsx:45-52`
   - 问题：
     ```tsx
     useEffect(() => {
       fetchUser(userId).then(setUser);
     }, []);  // ❌ 缺少 userId 依赖
     ```
   - 建议：将 `userId` 加入依赖数组，或使用 `useCallback` 包裹：
     ```tsx
     useEffect(() => {
       fetchUser(userId).then(setUser);
     }, [userId]);  // ✅
     ```

2. **Loading/Empty/Error 三态未处理**
   - 文件：`src/components/UserList.tsx`
   - 问题：列表组件只有正常渲染逻辑，无 loading 骨架屏、无空状态提示、无错误兜底
   - 建议：增加三态处理：
     ```tsx
     if (loading) return <Skeleton />;
     if (error) return <ErrorRetry onRetry={refetch} />;
     if (list.length === 0) return <Empty description="暂无用户" />;
     ```

🟡 **中优先级**

3. **Commit message 不规范**
   - 问题：12次提交中有4次信息为 "fix"、"update"、"改了"，无法从 git log 理解变更内容
   - 建议：遵循 Conventional Commits 规范，如 `fix(user): 修复头像上传超时未提示用户`

4. **表单校验不完整**
   - 文件：`src/pages/ProfileEdit.tsx:78`
   - 问题：手机号输入框只校验了非空，未校验格式
   - 建议：增加正则校验 `/^1[3-9]\d{9}$/`

🟢 **低优先级**

5. **CSS 命名不一致**
   - 问题：新写的组件用了 BEM（`.user-card__avatar`），旧组件是驼峰（`.userAvatar`），风格不统一
   - 建议：新代码统一使用 CSS Modules 或 Tailwind，逐步迁移旧代码

---

### 📈 成长趋势

| 维度 | 上周得分 | 本周得分 | 变化 | 趋势 |
|------|---------|---------|------|------|
| 代码规范 | 75 | 78 | +3 | 📈 |
| 逻辑正确性 | 68 | 65 | -3 | 📉 |
| 学习成长 | 70 | 82 | +12 | 📈 |
| 工程实践 | 70 | 72 | +2 | ➡️ |
| 沟通协作 | 85 | 88 | +3 | 📈 |
| 岗位专项 | 45 | 58 | +13 | 📈 |
| **总分** | **68.5** | **72.7** | **+4.2** | **📈** |

**总结**：本周整体进步明显，尤其是岗位专项维度提升13分，说明开始有意识地学习框架最佳实践。但逻辑正确性略有下降，需要在提交前多做自测。

---

### 🎯 下周改进目标

1. **必须完成**：修复 `UserProfile.tsx` 中的 useEffect 依赖问题，并为所有涉及异步数据获取的组件添加 Loading/Empty/Error 三态处理。

2. **努力达成**：所有 commit message 遵循 Conventional Commits 格式（`type(scope): description`），目标是下周12次提交全部规范。

3. **挑战目标**：为 `UserList` 组件编写一个基本的单元测试（用 `@testing-library/react`），验证空状态和错误状态的渲染。

---

### 💬 导师寄语

张三，这周你的进步肉眼可见，尤其是 TypeScript 类型的使用从"全是 any"到开始用泛型工具类型，这个转变很好。但前端开发最怕的就是"功能跑通了就行"——useEffect 的依赖数组、表单校验、三态处理这些细节，才是真正区分"会写页面"和"写好页面"的分水岭。下周把这三块补上，你的代码质量会上一个台阶。加油 💪

---
