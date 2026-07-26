/**
 * MindRoom3D (vanilla three.js port of static/components/MindRoom3D.tsx)
 *
 * DSM5IntegratedDiagnostic을 받아 심리 상태가 투사되는 가상 3D 방을 렌더링한다.
 *   - 내재화 점수 ↑ → 천장 수축(Y 스케일 최대 50%) + 조도 차단(최대 80%)
 *   - 와해성(schTotal) > 0.5 → 방이 기괴하게 뒤틀리는 회전 왜곡
 *   - schTotal > 0.6 → 와이어프레임(프레임 깨짐) 효과
 *   - 낱말카드/마인드맵 노드 → 방 안 떠다니는 소품(스프라이트)으로 배치
 *   - 드래그/터치로 360도 회전 (줌 금지, 상하각 클램프)
 *
 * Dual-support: DSM5IntegratedDiagnostic | IntegratedDiagnosticModel | neurodevelopmental_matrix
 *
 * 사용:
 *   const room = new MindRoom3DScene(containerEl);
 *   room.setDiagnostic(doc);
 *   room.setMindmap(mindmap);
 */
(function () {
  "use strict";

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function clamp01(n) {
    return Math.min(1, Math.max(0, n));
  }

  function makeLabelSprite(text, fill) {
    var canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 96;
    var ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, 256, 96);
    ctx.fillStyle = fill || "rgba(244,235,208,0.92)";
    ctx.beginPath();
    ctx.moveTo(16, 8);
    ctx.lineTo(240, 8);
    ctx.quadraticCurveTo(248, 8, 248, 16);
    ctx.lineTo(248, 72);
    ctx.quadraticCurveTo(248, 80, 240, 80);
    ctx.lineTo(16, 80);
    ctx.quadraticCurveTo(8, 80, 8, 72);
    ctx.lineTo(8, 16);
    ctx.quadraticCurveTo(8, 8, 16, 8);
    ctx.closePath();
    ctx.fill();
    ctx.strokeStyle = "rgba(40,36,28,0.35)";
    ctx.lineWidth = 2;
    ctx.stroke();
    ctx.fillStyle = "#2a2418";
    ctx.font = "bold 28px sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    var label = String(text || "").slice(0, 12);
    ctx.fillText(label, 128, 44);
    var tex = new THREE.CanvasTexture(canvas);
    tex.needsUpdate = true;
    var mat = new THREE.SpriteMaterial({ map: tex, transparent: true, depthTest: true });
    var sprite = new THREE.Sprite(mat);
    sprite.scale.set(1.6, 0.6, 1);
    return sprite;
  }

  function MindRoom3DScene(container) {
    if (typeof THREE === "undefined") throw new Error("THREE not loaded");
    this.container = container;
    this.internalizingFactor = 0;
    this.schTotal = 0;
    this._wallTextureOverride = false;
    this._disposed = false;
    this._propCount = 0;

    const width = container.clientWidth || 560;
    const height = container.clientHeight || 500;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#1a1814");
    this.camera = new THREE.PerspectiveCamera(70, width / height, 0.1, 100);
    // 방 안쪽에서 내부를 바라봄 (BackSide 벽이 보이도록)
    this.camera.position.set(0, 0.4, 2.4);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(width, height);
    this.renderer.setClearColor(0x1a1814, 1);
    container.appendChild(this.renderer.domElement);

    this.ambient = new THREE.AmbientLight(0xfff2d6, 0.85);
    this.scene.add(this.ambient);
    this.pointLight = new THREE.PointLight(0xffe8b0, 0.7);
    this.pointLight.position.set(0, 2.2, 0);
    this.scene.add(this.pointLight);
    this.fillLight = new THREE.PointLight(0xa8c4ff, 0.25);
    this.fillLight.position.set(-2, 1, 2);
    this.scene.add(this.fillLight);

    this.material = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#f4ebd0"),
      side: THREE.BackSide,
      wireframe: false,
      roughness: 0.85,
      metalness: 0.05,
    });
    this.room = new THREE.Mesh(new THREE.BoxGeometry(10, 8, 10), this.material);
    this.scene.add(this.room);

    // 바닥 대비 — 빈 공간처럼 보이지 않게
    this.floor = new THREE.Mesh(
      new THREE.CircleGeometry(4.2, 48),
      new THREE.MeshStandardMaterial({
        color: new THREE.Color("#cbb89a"),
        roughness: 0.95,
        side: THREE.DoubleSide,
      })
    );
    this.floor.rotation.x = -Math.PI / 2;
    this.floor.position.y = -3.85;
    this.scene.add(this.floor);

    // 기본 소품(테이블·램프) — 마인드맵 없어도 방이 '비어' 보이지 않음
    this.furniture = new THREE.Group();
    var table = new THREE.Mesh(
      new THREE.CylinderGeometry(0.9, 1.0, 0.12, 24),
      new THREE.MeshStandardMaterial({ color: 0x8b6914, roughness: 0.7 })
    );
    table.position.set(0, -2.8, -1.5);
    this.furniture.add(table);
    var lamp = new THREE.Mesh(
      new THREE.SphereGeometry(0.22, 16, 16),
      new THREE.MeshStandardMaterial({
        color: 0xffe6a8,
        emissive: 0xffc857,
        emissiveIntensity: 0.55,
      })
    );
    lamp.position.set(0, -2.2, -1.5);
    this.furniture.add(lamp);
    this.scene.add(this.furniture);

    this.propsGroup = new THREE.Group();
    this.scene.add(this.propsGroup);

    // 궤도: 방 안쪽 반지름
    this._azimuth = 0.35;
    this._polar = Math.PI / 2.2;
    this._radius = 2.6;
    this._dragging = false;
    this._lastX = 0;
    this._lastY = 0;
    this._bindControls();

    this._clockStart = performance.now();
    this._animate = this._animate.bind(this);
    requestAnimationFrame(this._animate);
  }

  MindRoom3DScene.prototype._bindControls = function () {
    const el = this.renderer.domElement;
    const start = (x, y) => {
      this._dragging = true;
      this._lastX = x;
      this._lastY = y;
    };
    const move = (x, y) => {
      if (!this._dragging) return;
      const dx = x - this._lastX;
      const dy = y - this._lastY;
      this._lastX = x;
      this._lastY = y;
      this._azimuth -= dx * 0.005;
      this._polar -= dy * 0.005;
      const minPolar = Math.PI / 3.2;
      const maxPolar = Math.PI / 1.85;
      this._polar = Math.min(maxPolar, Math.max(minPolar, this._polar));
    };
    const end = () => {
      this._dragging = false;
    };
    el.addEventListener("pointerdown", (e) => start(e.clientX, e.clientY));
    window.addEventListener("pointermove", (e) => move(e.clientX, e.clientY));
    window.addEventListener("pointerup", end);
    el.addEventListener(
      "touchstart",
      (e) => {
        if (e.touches[0]) start(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: true }
    );
    el.addEventListener(
      "touchmove",
      (e) => {
        if (e.touches[0]) move(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: true }
    );
    el.addEventListener("touchend", end);
  };

  MindRoom3DScene.prototype._roomColor = function () {
    if (this._projColor) return this._projColor;
    if (this.schTotal > 0.5) return "#4a2c5e";
    if (this.internalizingFactor >= 0.8) return "#2b2b2b";
    if (this.internalizingFactor >= 0.5) return "#d8dee6";
    return "#f4ebd0";
  };

  MindRoom3DScene.prototype._applyRoomProjection = function (proj) {
    if (!proj || !proj.color_tone) return;
    var tone = proj.color_tone;
    var toneMap = {
      "fractured-distorted": "#4a2c5e",
      "dark-gray": "#1a1c20",
      "cold-white": "#d8dee6",
      "warm-yellow": "#f4ebd0",
    };
    this._projColor = toneMap[tone] || null;
    if (typeof proj.lighting_level === "number") {
      this._projLighting = Math.max(0, Math.min(100, Number(proj.lighting_level))) / 100;
    } else {
      this._projLighting = null;
    }
    this.material.wireframe = tone === "fractured-distorted" || this.schTotal > 0.6;
    if (tone === "dark-gray") {
      this.pointLight.intensity = Math.max(0.12, 0.45 * (this._projLighting != null ? this._projLighting : 0.2));
    }
    if (this.scene && this._projColor) {
      var bg = new THREE.Color(this._projColor).multiplyScalar(0.25);
      this.scene.background = bg;
      this.renderer.setClearColor(bg.getHex(), 1);
    }
  };

  MindRoom3DScene.prototype._clearProps = function () {
    if (!this.propsGroup) return;
    while (this.propsGroup.children.length) {
      var child = this.propsGroup.children[0];
      this.propsGroup.remove(child);
      if (child.material) {
        if (child.material.map) child.material.map.dispose();
        child.material.dispose();
      }
      if (child.geometry) child.geometry.dispose();
    }
    this._propCount = 0;
  };

  /**
   * 낱말카드/마인드맵 노드를 방 안 소품으로 배치.
   * mindmap: { nodes: [{ id, label, kind, layer, x?, y? }], links? }
   */
  MindRoom3DScene.prototype.setMindmap = function (mindmap) {
    this._clearProps();
    var mm = mindmap || {};
    var nodes = Array.isArray(mm.nodes) ? mm.nodes : [];
    if (!nodes.length) return;

    var usable = nodes.filter(function (n) {
      return n && n.kind !== "center";
    });
    if (!usable.length) usable = nodes.slice(0, 12);
    usable = usable.slice(0, 16);

    var colors = {
      keyword: 0xf2b96b,
      branch: 0xd8cbb8,
      stress: 0x8fd6a8,
      conscious: 0x7cb8f2,
      default: 0xb393e8,
    };

    for (var i = 0; i < usable.length; i++) {
      var n = usable[i];
      var angle = (i / usable.length) * Math.PI * 2;
      var radius = 1.6 + (i % 3) * 0.35;
      var y = -1.2 + (i % 4) * 0.55;
      var fillHex = colors[n.kind] || (n.layer === "conscious" ? colors.conscious : colors.default);
      var orb = new THREE.Mesh(
        new THREE.SphereGeometry(0.18, 16, 16),
        new THREE.MeshStandardMaterial({
          color: fillHex,
          emissive: fillHex,
          emissiveIntensity: 0.25,
          roughness: 0.4,
        })
      );
      orb.position.set(Math.cos(angle) * radius, y, Math.sin(angle) * radius - 0.4);
      this.propsGroup.add(orb);

      var label = n.label || n.id || ("카드" + (i + 1));
      var sprite = makeLabelSprite(label, n.kind === "stress" ? "rgba(143,214,168,0.92)" : "rgba(244,235,208,0.92)");
      sprite.position.copy(orb.position);
      sprite.position.y += 0.38;
      this.propsGroup.add(sprite);
    }
    this._propCount = usable.length;
  };

  MindRoom3DScene.prototype.getPropCount = function () {
    return this._propCount || 0;
  };

  MindRoom3DScene.prototype.setDiagnostic = function (data) {
    const doc = data || {};
    this._wallTextureOverride = false;
    this._projColor = null;
    this._projLighting = null;

    var proj =
      (doc.clinical_meta && doc.clinical_meta.room_projection) ||
      doc.mind_room ||
      doc.room_projection ||
      null;
    if (proj && proj.color_tone) {
      this._applyRoomProjection(proj);
    }

    if (doc.three_d_room_fx) {
      var fx = doc.three_d_room_fx;
      var tex = fx.wall_texture || "rigid-grid";
      this._wallTextureOverride = true;
      if (tex === "rigid-grid") {
        this.material.wireframe = false;
        this.material.color.set("#e8e2d4");
      } else if (tex === "wireframe-dissolve") {
        this.material.wireframe = true;
        this.material.color.set("#4a2c5e");
      } else if (tex === "isolated-island") {
        this.material.wireframe = false;
        this.material.color.set("#0d1b2a");
      }
      this.material.needsUpdate = true;
      var muffling = Number(fx.sound_muffling_factor) || 0;
      this.pointLight.intensity = Math.max(0.15, 0.7 * (1.0 - muffling));
      var sm = doc.spectrum_mapping || {};
      this.schTotal = clamp01(
        ((Number(sm.cognitive_fragmentation) || 0) + (Number(sm.reality_detachment) || 0)) / 200
      );
      this.internalizingFactor = clamp01((Number(doc.cognitive_disorganization_score) || 0) / 100);
      if (doc.mindmap) this.setMindmap(doc.mindmap);
      return;
    }

    if (doc.threeRenderMetrics && doc.clinicalProfile) {
      const cp = doc.clinicalProfile || {};
      var coreScore =
        doc.internalizing_core && doc.internalizing_core.total_internalizing_score != null
          ? Number(doc.internalizing_core.total_internalizing_score)
          : NaN;
      var rawInternal = Number.isFinite(coreScore) ? coreScore : Number(cp.depression_index) || 0;
      this.internalizingFactor = clamp01(rawInternal / 100);
      this.schTotal = clamp01((Number(cp.schizophrenia_index) || 0) / 100);
    } else {
      const dims = doc.dimensions || {};
      const sch = dims.schizophrenia_spectrum || {};
      this.internalizingFactor = clamp01((Number(doc.total_internalizing_score) || 0) / 100);
      this.schTotal = clamp01(
        ((Number(sch.loose_association) || 0) + (Number(sch.ego_boundary_loss) || 0)) / 200
      );
    }
    this.material.color.set(this._roomColor());
    if (!this._projColor) {
      this.material.wireframe = this.schTotal > 0.6;
    }
    this.material.needsUpdate = true;
    this.pointLight.color.set(this.internalizingFactor >= 0.8 ? "#ff6666" : "#ffe8b0");
    if (this._projLighting == null) {
      this.pointLight.intensity = Math.max(0.25, 0.75 * (1 - this.internalizingFactor * 0.6));
    }
    if (doc.mindmap) this.setMindmap(doc.mindmap);
  };

  MindRoom3DScene.prototype._animate = function () {
    if (this._disposed) return;
    requestAnimationFrame(this._animate);
    const t = (performance.now() - this._clockStart) / 1000;

    const targetYScale = 1.0 - this.internalizingFactor * 0.5;
    this.room.scale.y = lerp(this.room.scale.y, targetYScale, 0.05);
    this.room.scale.x = lerp(this.room.scale.x, 1.0, 0.05);
    this.room.scale.z = lerp(this.room.scale.z, 1.0, 0.05);

    if (this.schTotal > 0.5) {
      this.room.rotation.x = Math.sin(t) * (this.schTotal * 0.1);
      this.room.rotation.z = Math.cos(t) * (this.schTotal * 0.1);
    } else {
      this.room.rotation.set(0, 0, 0);
    }

    const lightingFloor =
      this._projLighting != null ? this._projLighting : 1.0 - this.internalizingFactor * 0.8;
    this.ambient.intensity = lerp(this.ambient.intensity, Math.max(0.2, lightingFloor), 0.05);

    // 소품 살짝 부유
    if (this.propsGroup && this.propsGroup.children.length) {
      this.propsGroup.children.forEach(function (child, idx) {
        if (child.isSprite) return;
        child.position.y += Math.sin(t * 1.4 + idx) * 0.0015;
      });
    }

    const sinP = Math.sin(this._polar);
    this.camera.position.set(
      this._radius * sinP * Math.sin(this._azimuth),
      this._radius * Math.cos(this._polar) * 0.55 + 0.2,
      this._radius * sinP * Math.cos(this._azimuth)
    );
    this.camera.lookAt(0, -0.4, -0.6);

    this.renderer.render(this.scene, this.camera);
  };

  MindRoom3DScene.prototype.resize = function () {
    const width = this.container.clientWidth || 560;
    const height = this.container.clientHeight || 500;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };

  MindRoom3DScene.prototype.dispose = function () {
    this._disposed = true;
    try {
      this._clearProps();
      this.renderer.dispose();
      this.room.geometry.dispose();
      this.material.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    } catch (_) {}
  };

  window.MindRoom3DScene = MindRoom3DScene;
})();
