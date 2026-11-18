# 发布指南 · 把 dsh-nexus 开源并上架 DSH 插件市场

> 结论先说：**DSH 没有中心化插件市场，也不自带任何索引源。** 所谓「上架」= 你发布一个 format 1 的 JSON 索引文件，用户把它的 URL 加到 **插件 → 发现 → 添加索引源**。谁都能发布索引，没有审核。
>
> 来源：[DSH 官方文档 · Plugin indexes](https://deepseek-harness.github.io/deepseek-harness/en/guide/plugin-market)

---

## 0. 已确定的发布信息

| 项目 | 值 |
|---|---|
| 仓库 | https://github.com/Ronion123/dsh-nexus |
| npm 包名 | `@roninxr/dsh-nexus`（npm 只允许小写，GitHub 名是 `Ronion123`） |
| 索引地址 | `https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.4.1/site/index.json` |
| 版本 tag | `v1.4.1` |

> 索引地址用**固定 tag**（`@v1.4.1`）而不是 `@main`：内容不会被后续提交意外改变。
> 发新版本时打新 tag（如 `v1.4.1`），再把索引地址换成新 tag，或始终把最新版写在 `@main` 的索引里。

包名占位符已全部替换完毕，`tools/publish.py --scope/--owner` 仅在需要改名字时再用。

---

## 1. 开源到 GitHub（已完成）

```bash
cd dsh-nexus
git init
git add .
git commit -m "feat: Nexus desktop pet for DeepSeek Harness"
git branch -M main
git remote add origin https://github.com/<你的名字>/dsh-nexus.git
git push -u origin main
```

> `assets/`（构建中间产物）已在 `.gitignore` 里排除；素材源头由 `tools/build_assets.py` 从你工作区的原图重建。

建议在 GitHub 仓库设置里：
- **About** 填描述 + 勾选 Topics：`dsh`、`dsh-plugin`、`deepseek-harness`、`desktop-pet`
- **Add a license** 选 MIT（LICENSE 已包含，其中单独声明了美术素材不适用 MIT）

---

## 2. 发布到 npm

```bash
npm login                      # 浏览器登录，需要你本人操作
npm publish --access public    # scoped 包首次发布必须带 --access public
```

发布成功后验证：

```bash
npm view @roninxr/dsh-nexus version
```

> `.npmignore` 已排除 `assets/`，包里只含运行时必需的 `pet-pack/`、`index.js`、`locale`、`docs`、图标、LICENSE。
> 实测打包结果：**56 个文件 / 2.59 MB**，35 段动画全部在内。

---

## 3. 发布市场索引（已选定方案 B：jsDelivr）

索引就是仓库里的 `site/` 目录：`index.json` + `icons/dsh-nexus.svg`，**无需任何额外部署**——jsDelivr 直接读 GitHub 仓库文件。

### 你的索引地址（已实测 200）

```
https://raw.githubusercontent.com/Ronion123/dsh-nexus/v1.4.1/site/index.json
```

已验证：

| 资源 | 结果 |
|---|---|
| `site/index.json` | 200, `application/json` |
| `site/icons/dsh-nexus.svg` | 200, `image/svg+xml` |

图标在索引里写的是相对路径 `icons/dsh-nexus.svg`，会按索引 URL 自动解析成上面的绝对地址，验证通过。

**为什么用 `@v1.4.1` 而不是 `@main`**：固定 tag 让索引内容不会被后续提交意外改变。发新版本时打新 tag 并更新地址即可。

**为什么不用 GitHub Pages**：你已把 Pages 配到根目录，方案 B 不依赖它，不影响使用；想关掉可在 Settings → Pages → Source 选 `None`。

索引文件的硬性要求（万一你换托管）：

- UTF-8 JSON、2xx 状态、**不能有重定向**（DSH 拒绝跟随重定向）
- 相对图标路径按索引 URL 解析

### 备选托管方式

- **GitHub Pages**：`Settings → Pages` 选 `main` + `/docs` 目录（需先把 `site/` 内容复制到 `docs/`）
- **对象存储**：把 `site/` 上传到 OSS / S3 / Cloudflare R2，公网 https 直链

---

## 4. 用户怎么安装

用户侧三步：

1. **插件** 页 → 展开 **实验性插件** → 打开 **自定义插件市场**（Custom plugin indexes）
2. 出现 **发现 / Discover** 标签 → **添加索引源** → 粘贴你的索引 URL
3. 浏览卡片 → 点 **安装** → 确认比对来源（npm 包名 + 版本）→ 完成

安装后按桌宠的生效方式：网页刷新，或桌面端右键桌宠 →「重载配置」。

> 用户的索引源是**按 profile 存的**，你更新 `index.json` 里加新版本后，用户刷新即可看到新版本。

---

## 5. 之后发新版本

```bash
# 1. 改版本号（package.json）
# 2. 重新生成索引里的版本条目
python tools/publish.py --index-only
# 3. 发布
npm publish --access public
git add . && git commit -m "chore: release v1.4.1" && git push
```

`site/index.json` 里 `versions` 是数组，可以保留历史版本让用户回退；`publishTimestamp` 用 npm 上该版本的真实发布时间（Unix 秒）。

---

## 6. 发布前检查清单

- [ ] `python tools/publish.py --check` 无未替换占位符
- [ ] `tools/validate_bundle.py` 通过
- [ ] `tools/validate_pack.py` 通过（35 段动画全覆盖、权重 100）
- [ ] `npm pack --dry-run` 里能看到 `pet-pack/` 全部 35 个 webm
- [ ] `site/index.json` 通过官方 `parseMarketIndex`
- [ ] `package.json` 的 `version` 与索引里一致
- [ ] `engines.dsh` 与包实际兼容范围一致（当前写 `>=0.2.0-rc.1`）
- [ ] LICENSE 里美术素材声明保留（奥特曼版权属圆谷，仅个人非商用）

---

## 7. 关于版权与素材（请务必确认）

- **代码**：MIT，随便用。
- **美术素材**：奈克赛斯是圆谷（Tsuburaya Productions）的角色。当前的五张立绘、循环 GIF、九格动作组均是你提供的二创图。作为**个人桌面使用**没问题；但「开源发布让所有人下载」属于再分发，严格说需要权利人许可。

`LICENSE` 里已单独写了一段 ARTWORK NOTICE 说明代码与素材授权范围不同。稳妥做法二选一：

1. **保留现状**，但在 README 与索引描述里明确「素材为同人二创，仅限个人非商业使用，请勿商用」，多数 DSH 桌宠插件都是这个做法；
2. **只开源代码**，让用户自备素材（仓库不放 `pet-pack/` 的图片与动画，附一个说明让用户把自己的图放到对应位置）。这种最干净，但用户装完没有画面，体验差。

如果这是要正式分发，建议先向圆谷或其授权方确认二创再分发的边界。
