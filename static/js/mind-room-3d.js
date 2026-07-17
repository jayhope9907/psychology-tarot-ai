/**
 * MindRoom3D (vanilla three.js port of static/components/MindRoom3D.tsx)
 *
 * DSM5IntegratedDiagnostic을 받아 심리 상태가 투사되는 가상 3D 방을 렌더링한다.
 *   - 내재화 점수 ↑ → 천장 수축(Y 스케일 최대 50%) + 조도 차단(최대 80%)
 *   - 와해성(schTotal) > 0.5 → 방이 기괴하게 뒤틀리는 회전 왜곡
 *   - schTotal > 0.6 → 와이어프레임(프레임 깨짐) 효과
 *   - 드래그/터치로 360도 회전 (줌 금지, 상하각 PI/3 ~ PI/2 클램프)
 *
 * 사용: const room = new MindRoom3DScene(containerEl); room.setDiagnostic(doc);
 */
(function () {
  "use strict";

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function MindRoom3DScene(container) {
    if (typeof THREE === "undefined") throw new Error("THREE not loaded");
    this.container = container;
    this.internalizingFactor = 0;
    this.schTotal = 0;
    this._disposed = false;

    const width = container.clientWidth || 560;
    const height = container.clientHeight || 500;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
    this.camera.position.set(0, 0, 8);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(width, height);
    container.appendChild(this.renderer.domElement);

    this.ambient = new THREE.AmbientLight(0xffffff, 0.8);
    this.scene.add(this.ambient);
    this.pointLight = new THREE.PointLight(0xffffff, 0.5);
    this.pointLight.position.set(0, 5, 0);
    this.scene.add(this.pointLight);

    this.material = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#f4ebd0"),
      side: THREE.BackSide, // 큐브 '내부' 벽면 렌더
      wireframe: false,
    });
    this.room = new THREE.Mesh(new THREE.BoxGeometry(10, 8, 10), this.material);
    this.scene.add(this.room);

    // 궤도 조작계 (줌 금지, 상하각 클램프) — OrbitControls 미탑재 환경용 경량 구현
    this._azimuth = 0;
    this._polar = Math.PI / 2.4; // PI/3 ~ PI/2 사이 시작값
    this._radius = 8;
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
      const minPolar = Math.PI / 3;
      const maxPolar = Math.PI / 2;
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

  // 임상 상태에 따른 컬러 매핑 변환
  MindRoom3DScene.prototype._roomColor = function () {
    if (this.schTotal > 0.5) return "#4a2c5e"; // 기괴하고 몽환적인 보라색 톤
    if (this.internalizingFactor >= 0.8) return "#2b2b2b"; // 극도의 우울 잿빛
    return "#f4ebd0"; // 안정: 따뜻한 샌드 옐로우 톤
  };

  MindRoom3DScene.prototype.setDiagnostic = function (data) {
    const doc = data || {};
    const dims = doc.dimensions || {};
    const sch = dims.schizophrenia_spectrum || {};
    this.internalizingFactor = Math.min(
      Math.max((Number(doc.total_internalizing_score) || 0) / 100, 0),
      1
    );
    this.schTotal = Math.min(
      Math.max(
        ((Number(sch.loose_association) || 0) + (Number(sch.ego_boundary_loss) || 0)) / 200,
        0
      ),
      1
    );
    this.material.color.set(this._roomColor());
    this.material.wireframe = this.schTotal > 0.6; // 프레임 깨짐 효과
    this.material.needsUpdate = true;
    this.pointLight.color.set(this.internalizingFactor >= 0.8 ? "#ff3333" : "#ffffff");
  };

  MindRoom3DScene.prototype._animate = function () {
    if (this._disposed) return;
    requestAnimationFrame(this._animate);
    const t = (performance.now() - this._clockStart) / 1000;

    // 1. [내재화 반영] 점수가 높을수록 천장이 낮아지고 공간이 수축 (최대 50%)
    const targetYScale = 1.0 - this.internalizingFactor * 0.5;
    this.room.scale.y = lerp(this.room.scale.y, targetYScale, 0.05);

    // 2. [와해성 반영] 방이 기괴하게 회전·뒤틀림
    if (this.schTotal > 0.5) {
      this.room.rotation.x = Math.sin(t) * (this.schTotal * 0.1);
      this.room.rotation.z = Math.cos(t) * (this.schTotal * 0.1);
    } else {
      this.room.rotation.set(0, 0, 0);
    }

    // 3. [우울/공황 반영] 조도 차단 (최대 80% 어두워짐)
    const targetIntensity = 1.0 - this.internalizingFactor * 0.8;
    this.ambient.intensity = lerp(this.ambient.intensity, targetIntensity, 0.05);

    // 궤도 카메라
    const sinP = Math.sin(this._polar);
    this.camera.position.set(
      this._radius * sinP * Math.sin(this._azimuth),
      this._radius * Math.cos(this._polar),
      this._radius * sinP * Math.cos(this._azimuth)
    );
    this.camera.lookAt(0, 0, 0);

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
