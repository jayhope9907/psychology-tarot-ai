/**
 * MindNetwork3D (vanilla three.js port of static/components/MindNetwork3D.tsx)
 *
 * DSM5IntegratedDiagnostic 또는 IntegratedDiagnosticModel을 받아
 * 200개 파티클 신경망을 렌더링한다.
 *   - schFragmentation > 0.6 → 파편화 산란 (보라 #a855f7)
 *   - asdRigidity > 0.6 → 고정축 압축 (시안 #06b6d4)
 *   - else → 부드러운 신경망 파동 (에메랄드 #10b981)
 *
 * 사용: const net = new MindNetwork3DScene(containerEl); net.setDiagnostic(doc);
 */
(function () {
  "use strict";

  var PARTICLE_COUNT = 200;

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function clamp01(n) {
    return Math.min(1, Math.max(0, n));
  }

  function parseNetworkMetrics(data) {
    var doc = data || {};
    if (doc.clinicalProfile && doc.threeRenderMetrics) {
      var cp = doc.clinicalProfile || {};
      var tm = doc.threeRenderMetrics || {};
      var asdRaw = Number(cp.asd_stimming_index);
      var asdRigidity = clamp01(
        Number.isFinite(asdRaw) && asdRaw > 0
          ? asdRaw / 100
          : (Number(tm.cluster_density) || 0) / 100
      );
      var schFragmentation = clamp01((Number(cp.schizophrenia_index) || 0) / 100);
      return { asdRigidity: asdRigidity, schFragmentation: schFragmentation };
    }
    var dims = doc.dimensions || {};
    var sch = dims.schizophrenia_spectrum || {};
    return {
      asdRigidity: clamp01((Number(dims.obsessive_compulsive) || 0) / 100),
      schFragmentation: clamp01((Number(sch.ego_boundary_loss) || 0) / 100),
    };
  }

  function buildSpherePositions() {
    var pos = new Float32Array(PARTICLE_COUNT * 3);
    for (var i = 0; i < PARTICLE_COUNT * 3; i += 3) {
      var u = Math.random();
      var v = Math.random();
      var theta = u * 2.0 * Math.PI;
      var phi = Math.acos(2.0 * v - 1.0);
      var r = 3.0 * Math.cbrt(Math.random());
      pos[i] = r * Math.sin(phi) * Math.cos(theta);
      pos[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i + 2] = r * Math.cos(phi);
    }
    return pos;
  }

  function MindNetwork3DScene(container) {
    if (typeof THREE === "undefined") throw new Error("THREE not loaded");
    this.container = container;
    this.asdRigidity = 0;
    this.schFragmentation = 0;
    this.internalizingPressure = 0; // 0..1
    this._disposed = false;

    var width = container.clientWidth || 560;
    var height = container.clientHeight || 500;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#0b0f19");
    this.camera = new THREE.PerspectiveCamera(60, width / height, 0.1, 100);
    this.camera.position.set(0, 0, 7);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(width, height);
    this.renderer.setClearColor(0x0b0f19, 1);
    container.appendChild(this.renderer.domElement);

    this.positions = buildSpherePositions();
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute(
      "position",
      new THREE.BufferAttribute(this.positions, 3)
    );
    this.material = new THREE.PointsMaterial({
      size: 0.12,
      color: new THREE.Color("#10b981"),
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.8,
    });
    this.points = new THREE.Points(this.geometry, this.material);
    this.scene.add(this.points);

    // 궤도 조작계 (줌 허용) — OrbitControls 미탑재 환경용 경량 구현
    this._azimuth = 0;
    this._polar = Math.PI / 2.4;
    this._radius = 7;
    this._dragging = false;
    this._lastX = 0;
    this._lastY = 0;
    this._bindControls();

    this._clockStart = performance.now();
    this._animate = this._animate.bind(this);
    requestAnimationFrame(this._animate);
  }

  MindNetwork3DScene.prototype._bindControls = function () {
    var el = this.renderer.domElement;
    var self = this;
    var start = function (x, y) {
      self._dragging = true;
      self._lastX = x;
      self._lastY = y;
    };
    var move = function (x, y) {
      if (!self._dragging) return;
      var dx = x - self._lastX;
      var dy = y - self._lastY;
      self._lastX = x;
      self._lastY = y;
      self._azimuth -= dx * 0.005;
      self._polar -= dy * 0.005;
      var minPolar = 0.2;
      var maxPolar = Math.PI - 0.2;
      self._polar = Math.min(maxPolar, Math.max(minPolar, self._polar));
    };
    var end = function () {
      self._dragging = false;
    };
    el.addEventListener("pointerdown", function (e) {
      start(e.clientX, e.clientY);
    });
    window.addEventListener("pointermove", function (e) {
      move(e.clientX, e.clientY);
    });
    window.addEventListener("pointerup", end);
    el.addEventListener(
      "wheel",
      function (e) {
        e.preventDefault();
        self._radius = Math.min(18, Math.max(3, self._radius + e.deltaY * 0.01));
      },
      { passive: false }
    );
    el.addEventListener(
      "touchstart",
      function (e) {
        if (e.touches[0]) start(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: true }
    );
    el.addEventListener(
      "touchmove",
      function (e) {
        if (e.touches[0]) move(e.touches[0].clientX, e.touches[0].clientY);
      },
      { passive: true }
    );
    el.addEventListener("touchend", end);
  };

  MindNetwork3DScene.prototype._networkColor = function () {
    if (this.internalizingPressure > 0.75) return "#ff3333";
    if (this.schFragmentation > 0.6) return "#a855f7";
    if (this.asdRigidity > 0.6) return "#06b6d4";
    return "#10b981";
  };

  MindNetwork3DScene.prototype.setDiagnostic = function (data) {
    var m = parseNetworkMetrics(data);
    this.asdRigidity = m.asdRigidity;
    this.schFragmentation = m.schFragmentation;
    var coreScore = NaN;
    if (data && data.internalizing_core && data.internalizing_core.total_internalizing_score != null) {
      coreScore = Number(data.internalizing_core.total_internalizing_score);
    } else if (data && data.total_internalizing_score != null) {
      coreScore = Number(data.total_internalizing_score);
    }
    this.internalizingPressure = clamp01(Number.isFinite(coreScore) ? coreScore / 100 : 0);
    // 모드 전환 시 구형 레이아웃 재시드 (파편화가 누적된 경우 리셋)
    this.positions = buildSpherePositions();
    this.geometry.setAttribute(
      "position",
      new THREE.BufferAttribute(this.positions, 3)
    );
    this.material.color.set(this._networkColor());
    this.material.needsUpdate = true;
  };

  MindNetwork3DScene.prototype._animate = function () {
    if (this._disposed) return;
    requestAnimationFrame(this._animate);
    var t = (performance.now() - this._clockStart) / 1000;
    var positions = this.geometry.attributes.position.array;
    var sch = this.schFragmentation;
    var asd = this.asdRigidity;
    var amp = 1.0 + this.internalizingPressure * 0.5;

    for (var i = 0; i < positions.length; i += 3) {
      if (sch > 0.6) {
        positions[i] += Math.sin(t + i) * 0.05 * sch * amp;
        positions[i + 1] += Math.cos(t + i) * 0.05 * sch * amp;
        positions[i + 2] += Math.sin(t * 0.5 + i) * 0.05 * sch * amp;
      } else if (asd > 0.6) {
        positions[i] = lerp(positions[i], Math.sin(i) * 0.5, 0.02 * amp);
        positions[i + 1] = lerp(positions[i + 1], Math.cos(i) * 0.5, 0.02 * amp);
      } else {
        positions[i + 1] += Math.sin(t + positions[i]) * 0.005 * amp;
      }
    }
    this.geometry.attributes.position.needsUpdate = true;

    var sinP = Math.sin(this._polar);
    this.camera.position.set(
      this._radius * sinP * Math.sin(this._azimuth),
      this._radius * Math.cos(this._polar),
      this._radius * sinP * Math.cos(this._azimuth)
    );
    this.camera.lookAt(0, 0, 0);

    this.renderer.render(this.scene, this.camera);
  };

  MindNetwork3DScene.prototype.resize = function () {
    var width = this.container.clientWidth || 560;
    var height = this.container.clientHeight || 500;
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(width, height);
  };

  MindNetwork3DScene.prototype.dispose = function () {
    this._disposed = true;
    try {
      this.renderer.dispose();
      this.geometry.dispose();
      this.material.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    } catch (_) {}
  };

  window.MindNetwork3DScene = MindNetwork3DScene;
})();
