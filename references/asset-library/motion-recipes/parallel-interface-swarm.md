# Parallel Interface Swarm

`Parallel Interface Swarm（并行界面群）` 用六至九个真实工作界面建立一个不规则三维工作空间，让“多个任务正在同时运行”在两至三秒内被看见。它不是卡片墙，也不是把截图排满画面。

## 解决的问题

当内容要表达并行生产、多个代理协作、多条工作流同时推进或系统吞吐量时，单个录屏只能证明“一件事正在做”。并行界面群通过真实界面、错落纵深和连续运镜，把“同时发生”变成一个空间关系。

## 必须保留的结构

- 使用至少六个可辨认的真实界面；一张主界面最清楚，其余承担规模与空间，不要求等权可读。
- 每张界面独立设置 `x / y / z / rotationX / rotationY / rotationZ`，允许局部出画和互相遮挡，但不能形成等距网格。
- 界面按不同时间、方向和深度进入；混乱来自受控的不对称，不来自随机乱飞。
- 摄像机沿斜线穿过空间，先完成一次方向反转，再缓慢向主界面落稳；结尾保持画面充满。
- 界面内部至少有一种真实或诚实的运行信号，例如视频播放、时间线游标、状态脉冲或素材微视差。
- 每个界面用径向遮罩柔化边缘，并按深度分配轻度虚焦、亮度和饱和度；不要用统一高斯模糊糊住所有内容。

## 不要使用

- 素材不足六份，或几张界面只是同一截图的复制。
- 观众必须逐字阅读每个界面，或某个界面承载关键事实但会被遮挡。
- 规则九宫格、同角度同速度飞入、霓虹紫蓝边框、持续发光和无意义粒子。
- 把第三方软件截图、用户录屏或单期 B-roll 作为模板资产重新分发；共享库只保存运动骨架和获批参考帧。

## HTML 约定

```html
<div id="work-world">
  <article class="work-panel" data-x="0" data-y="0" data-z="120"
    data-rx="-4" data-ry="-7" data-rz="-2">
    <div class="panel-shell">
      <video class="media" muted playsinline></video>
      <span class="playhead"></span>
      <span class="edit-pulse"></span>
    </div>
  </article>
</div>
```

每期必须按真实素材重新设置目标位置和倾角。`.panel-shell` 可使用类似下面的边缘遮罩；半径、阴影和色彩跟随当期视觉系统。

```css
.panel-shell {
  overflow: hidden;
  border-radius: 22px;
  mask-image: radial-gradient(ellipse 92% 88% at 50% 50%,
    #000 0 57%, rgba(0,0,0,.97) 70%, rgba(0,0,0,.68) 84%, transparent 100%);
}
```

## GSAP 调用

实现：`references/asset-library/motion-recipes/gsap-cinematic-shots.js#parallelInterfaceSwarm`

```js
HFShotLanguage.parallelInterfaceSwarm(
  tl,
  ".work-panel",
  0,
  {
    stage: "#work-world",
    duration: 2.4,
    perspective: 1560,
    starts: episodeSpecificEntrances,
    drifts: episodeSpecificDrifts,
  },
);
```

默认入口与漂移是确定性的九界面参考值；正式使用时应根据当期素材比例、主体位置和安全区重新设计。声音默认保持干净；只有存在清楚可见的镜头穿越或落点时，才另配有许可的空气划过或短冲击声。

函数默认要求至少六个界面；若确有更少界面的表达任务，应改用卡片环绕或另行设计，而不是降低 `minPanels` 来伪装规模。状态脉冲的颜色可通过 `pulseBoxShadow` 跟随当期强调色。

批准参考：`library/references/reference.ui.parallel-interface-swarm.v1/reference.yaml`。
