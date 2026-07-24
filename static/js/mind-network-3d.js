/**
 * MindNetwork3D — confrontation mirror + Future Projection Morphing.
 *
 * Phases:
 *   mirror     — 직면 거울 프레임 안 고착/파편 신경망
 *   shatter    — 유리 균열 glow + glass particle burst
 *   freeze     — 파편 공중 정지 (time freeze)
 *   morph      — CHC 5축 + emerald/gold 건강 신경망으로 lerp 재조립
 *   flythrough — 어두운 거울을 뚫고 미래 도면 안으로 camera fly
 *   future     — 완성된 미래 자아 신경망 idle
 *
 * Usage:
 *   net.setDiagnostic(doc); net.setGraph(graph);
 *   net.enterMirrorPhase();
 *   net.playFutureProjection(doc); // confrontation complete
 */
(function () {
  "use strict";

  var CENTER_ID = "center_self";
  var PARTICLE_COUNT = 80;
  var GLASS_COUNT = 420;
  var CRACK_SEGMENTS = 28;

  var CHC_NODES = [
    { id: "chc_g", label: "g · 전체", key: "g_factor", color: "#fbbf24", pearl: "#fff7d6" },
    { id: "chc_gc", label: "Gc · 언어", key: "crystallized_gc", color: "#34d399", pearl: "#d1fae5" },
    { id: "chc_gf", label: "Gf · 유동", key: "fluid_gf", color: "#10b981", pearl: "#a7f3d0" },
    { id: "chc_gwm", label: "Gwm · 작업기억", key: "working_memory_gwm", color: "#059669", pearl: "#6ee7b7" },
    { id: "chc_gs", label: "Gs · 처리속도", key: "processing_speed_gs", color: "#eab308", pearl: "#fde68a" },
    { id: "chc_gv", label: "Gv · 시공간", key: "visual_processing_gv", color: "#f59e0b", pearl: "#fcd34d" },
  ];

  function lerp(a, b, t) {
    return a + (b - a) * t;
  }

  function clamp01(n) {
    return Math.min(1, Math.max(0, n));
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
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

  function parseCognitiveProfile(data) {
    var doc = data || {};
    if (doc.cognitiveProfile) return doc.cognitiveProfile;
    // DSM5 fallback proxies from dimensions
    var dims = doc.dimensions || {};
    var total = Number(doc.total_internalizing_score) || 50;
    var base = Math.max(70, 130 - total * 0.45);
    return {
      g_factor: base,
      crystallized_gc: base - 2,
      fluid_gf: base - 4,
      working_memory_gwm: base - 6,
      processing_speed_gs: base - (Number(dims.obsessive_compulsive) || 0) * 0.15,
      visual_processing_gv: base - 3,
    };
  }

  function buildSpherePositions() {
    var pos = new Float32Array(PARTICLE_COUNT * 3);
    for (var i = 0; i < PARTICLE_COUNT * 3; i += 3) {
      var u = Math.random();
      var v = Math.random();
      var theta = u * 2.0 * Math.PI;
      var phi = Math.acos(2.0 * v - 1.0);
      var r = 4.2 * Math.cbrt(Math.random());
      pos[i] = r * Math.sin(phi) * Math.cos(theta);
      pos[i + 1] = r * Math.sin(phi) * Math.sin(theta);
      pos[i + 2] = r * Math.cos(phi);
    }
    return pos;
  }

  function makeLabelSprite(text, colorHex) {
    var canvas = document.createElement("canvas");
    canvas.width = 256;
    canvas.height = 64;
    var ctx = canvas.getContext("2d");
    ctx.clearRect(0, 0, 256, 64);
    ctx.fillStyle = "rgba(11,15,25,0.55)";
    ctx.fillRect(8, 12, 240, 40);
    ctx.fillStyle = colorHex || "#e2e8f0";
    ctx.font = "600 20px 'Noto Sans KR', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(text || "").slice(0, 14), 128, 32);
    var tex = new THREE.CanvasTexture(canvas);
    if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
    var mat = new THREE.SpriteMaterial({
      map: tex,
      transparent: true,
      depthTest: false,
      opacity: 0.95,
    });
    var sprite = new THREE.Sprite(mat);
    sprite.scale.set(1.45, 0.36, 1);
    return sprite;
  }

  function MindNetwork3DScene(container) {
    if (typeof THREE === "undefined") throw new Error("THREE not loaded");
    this.container = container;
    this.asdRigidity = 0;
    this.schFragmentation = 0;
    this.internalizingPressure = 0;
    this._disposed = false;
    this._graph = { nodes: [], links: [] };
    this._nodeMeshes = {};
    this._edgeGroup = null;
    this._nodeGroup = null;
    this._mirrorGroup = null;
    this._fxGroup = null;
    this._futureGroup = null;
    this._livePulse = 0;
    this._phase = "mirror"; // mirror|shatter|freeze|morph|flythrough|future
    this._phaseT = 0;
    this._phaseStart = 0;
    this._projectionActive = false;
    this._onPhaseChange = null;
    this._lastDiagnostic = null;
    this._cognitive = null;
    this._glassVel = null;
    this._glassStart = null;
    this._glassTarget = null;
    this._camFrom = null;
    this._camTo = null;
    this._lookFrom = null;
    this._lookTo = null;

    var width = container.clientWidth || 560;
    var height = container.clientHeight || 500;

    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color("#0b0f19");
    this.camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 100);
    this.camera.position.set(0, 1.2, 8);

    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.setSize(width, height);
    this.renderer.setClearColor(0x0b0f19, 1);
    container.appendChild(this.renderer.domElement);

    var amb = new THREE.AmbientLight(0xffffff, 0.55);
    var key = new THREE.DirectionalLight(0xffffff, 0.85);
    key.position.set(4, 8, 6);
    this._rimLight = new THREE.PointLight(0x34d399, 0, 18);
    this._rimLight.position.set(0, 0, -2);
    this.scene.add(amb);
    this.scene.add(key);
    this.scene.add(this._rimLight);

    this.positions = buildSpherePositions();
    this.geometry = new THREE.BufferGeometry();
    this.geometry.setAttribute("position", new THREE.BufferAttribute(this.positions, 3));
    this.material = new THREE.PointsMaterial({
      size: 0.06,
      color: new THREE.Color("#1e293b"),
      sizeAttenuation: true,
      transparent: true,
      opacity: 0.45,
    });
    this.points = new THREE.Points(this.geometry, this.material);
    this.scene.add(this.points);

    this._nodeGroup = new THREE.Group();
    this._edgeGroup = new THREE.Group();
    this._mirrorGroup = new THREE.Group();
    this._fxGroup = new THREE.Group();
    this._futureGroup = new THREE.Group();
    this._futureGroup.visible = false;
    this.scene.add(this._nodeGroup);
    this.scene.add(this._edgeGroup);
    this.scene.add(this._mirrorGroup);
    this.scene.add(this._fxGroup);
    this.scene.add(this._futureGroup);

    this._buildMirrorFrame();
    this.setGraph({
      nodes: [
        {
          id: CENTER_ID,
          label: "self",
          val: 20,
          color: "#f8fafc",
          kind: "center",
          x: 0,
          y: 0,
          z: 0,
        },
      ],
      links: [],
    });

    this._azimuth = 0.35;
    this._polar = Math.PI / 2.55;
    this._radius = 8;
    this._dragging = false;
    this._lastX = 0;
    this._lastY = 0;
    this._autoRotate = false;
    this._bindControls();

    this._clockStart = performance.now();
    this._animate = this._animate.bind(this);
    requestAnimationFrame(this._animate);
  }

  MindNetwork3DScene.prototype._bindControls = function () {
    var el = this.renderer.domElement;
    var self = this;
    var start = function (x, y) {
      if (self._projectionActive) return;
      self._dragging = true;
      self._lastX = x;
      self._lastY = y;
      self._autoRotate = false;
    };
    var move = function (x, y) {
      if (!self._dragging || self._projectionActive) return;
      var dx = x - self._lastX;
      var dy = y - self._lastY;
      self._lastX = x;
      self._lastY = y;
      self._azimuth -= dx * 0.005;
      self._polar -= dy * 0.005;
      self._polar = Math.min(Math.PI - 0.2, Math.max(0.2, self._polar));
    };
    var end = function () {
      self._dragging = false;
    };
    el.addEventListener("pointerdown", function (e) {
      start(e.clientX, e.clientY);
      try {
        el.setPointerCapture(e.pointerId);
      } catch (_) {}
    });
    el.addEventListener("pointermove", function (e) {
      move(e.clientX, e.clientY);
    });
    el.addEventListener("pointerup", end);
    el.addEventListener("pointercancel", end);
    el.addEventListener(
      "wheel",
      function (e) {
        if (self._projectionActive) return;
        e.preventDefault();
        self._radius = Math.min(18, Math.max(3.5, self._radius + e.deltaY * 0.01));
      },
      { passive: false }
    );
    el.style.touchAction = "none";
    el.style.cursor = "grab";
    el.addEventListener("pointerdown", function () {
      el.style.cursor = "grabbing";
    });
    el.addEventListener("pointerup", function () {
      el.style.cursor = "grab";
    });
  };

  /** 직면 거울 프레임 — 중앙 반투명 유리 + 금테 */
  MindNetwork3DScene.prototype._buildMirrorFrame = function () {
    this._clearGroup(this._mirrorGroup);

    var frameMat = new THREE.MeshStandardMaterial({
      color: new THREE.Color("#c4a574"),
      metalness: 0.75,
      roughness: 0.28,
      emissive: new THREE.Color("#3b2f1a"),
      emissiveIntensity: 0.25,
    });
    var outer = new THREE.Mesh(new THREE.BoxGeometry(3.4, 4.6, 0.12), frameMat);
    outer.position.z = -0.35;
    this._mirrorGroup.add(outer);

    var glassMat =
      typeof THREE.MeshPhysicalMaterial === "function"
        ? new THREE.MeshPhysicalMaterial({
            color: new THREE.Color("#9ec9ff"),
            metalness: 0.05,
            roughness: 0.08,
            transmission: 0.72,
            thickness: 0.4,
            transparent: true,
            opacity: 0.55,
            side: THREE.DoubleSide,
          })
        : new THREE.MeshStandardMaterial({
            color: new THREE.Color("#7eb6ff"),
            metalness: 0.2,
            roughness: 0.15,
            transparent: true,
            opacity: 0.35,
            side: THREE.DoubleSide,
          });
    this._glassMesh = new THREE.Mesh(new THREE.PlaneGeometry(2.85, 4.0), glassMat);
    this._glassMesh.position.z = -0.28;
    this._mirrorGroup.add(this._glassMesh);

    // Inner rim
    var rim = new THREE.Mesh(
      new THREE.BoxGeometry(3.05, 4.2, 0.06),
      new THREE.MeshStandardMaterial({
        color: "#1e293b",
        metalness: 0.4,
        roughness: 0.5,
      })
    );
    rim.position.z = -0.4;
    this._mirrorGroup.add(rim);

    this._crackLines = null;
  };

  MindNetwork3DScene.prototype._networkColor = function () {
    if (this.internalizingPressure > 0.75) return "#ff3333";
    if (this.schFragmentation > 0.6) return "#a855f7";
    if (this.asdRigidity > 0.6) return "#06b6d4";
    return "#10b981";
  };

  MindNetwork3DScene.prototype.setDiagnostic = function (data) {
    this._lastDiagnostic = data || null;
    var m = parseNetworkMetrics(data);
    this.asdRigidity = m.asdRigidity;
    this.schFragmentation = m.schFragmentation;
    this._cognitive = parseCognitiveProfile(data);
    var coreScore = NaN;
    if (data && data.internalizing_core && data.internalizing_core.total_internalizing_score != null) {
      coreScore = Number(data.internalizing_core.total_internalizing_score);
    } else if (data && data.total_internalizing_score != null) {
      coreScore = Number(data.total_internalizing_score);
    }
    this.internalizingPressure = clamp01(Number.isFinite(coreScore) ? coreScore / 100 : 0);
    this.material.color.set(this._networkColor());
    this.material.needsUpdate = true;
    if (this._phase === "mirror" && this._graph && this._graph.nodes) {
      this.setGraph(this._graph);
    }
  };

  MindNetwork3DScene.prototype._clearGroup = function (group) {
    if (!group) return;
    while (group.children.length) {
      var child = group.children[0];
      group.remove(child);
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(function (m) {
            if (m.map) m.map.dispose();
            m.dispose();
          });
        } else {
          if (child.material.map) child.material.map.dispose();
          child.material.dispose();
        }
      }
      if (child.children) {
        child.traverse(function (obj) {
          if (obj === child) return;
          if (obj.geometry) obj.geometry.dispose();
          if (obj.material) {
            if (obj.material.map) obj.material.map.dispose();
            obj.material.dispose();
          }
        });
      }
    }
  };

  MindNetwork3DScene.prototype.setGraph = function (graph) {
    if (this._projectionActive && this._phase !== "mirror") return;
    var g = graph || { nodes: [], links: [] };
    this._graph = {
      nodes: (g.nodes || []).slice(),
      links: (g.links || []).slice(),
    };
    this._livePulse = 1;
    this._rebuildNodes();
    this._rebuildEdges();
  };

  MindNetwork3DScene.prototype._rebuildNodes = function () {
    this._clearGroup(this._nodeGroup);
    this._nodeMeshes = {};
    var nodes = this._graph.nodes || [];
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (!n || !n.id) continue;
      var isCenter = n.id === CENTER_ID || n.kind === "center";
      var radius = isCenter ? 0.28 : 0.08 + Math.min(0.22, (Number(n.val) || 8) / 80);
      var geo = new THREE.SphereGeometry(radius, isCenter ? 24 : 16, isCenter ? 24 : 16);
      var mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(n.color || (isCenter ? "#f8fafc" : "#10b981")),
        emissive: new THREE.Color(n.color || "#10b981"),
        emissiveIntensity: isCenter ? 0.35 : 0.22,
        roughness: 0.45,
        metalness: 0.15,
      });
      var mesh = new THREE.Mesh(geo, mat);
      // Keep clinical nodes slightly inside the mirror glass (negative Z)
      var baseX = Number(n.x) || 0;
      var baseY = Number(n.y) || 0;
      var baseZ = (Number(n.z) || 0) * 0.35 - 0.55;
      mesh.position.set(baseX, baseY, baseZ);
      mesh.userData = {
        id: n.id,
        label: n.label,
        base: { x: baseX, y: baseY, z: baseZ },
        isCenter: isCenter,
        fixation: !!n.fixation,
      };
      this._nodeGroup.add(mesh);
      this._nodeMeshes[n.id] = mesh;

      if (!isCenter && n.label) {
        var sprite = makeLabelSprite(n.label, n.color || "#e2e8f0");
        sprite.position.set(0, radius + 0.28, 0);
        mesh.add(sprite);
      }
    }
  };

  MindNetwork3DScene.prototype._rebuildEdges = function () {
    this._clearGroup(this._edgeGroup);
    var links = this._graph.links || [];
    var sch = this.schFragmentation;
    var forceDashed = sch > 0.6;

    for (var i = 0; i < links.length; i++) {
      var link = links[i];
      if (!link) continue;
      var a = this._nodeMeshes[String(link.source)];
      var b = this._nodeMeshes[String(link.target)];
      if (!a || !b) continue;

      var dashed = forceDashed || !!link.dashed;
      var color = link.color || (dashed ? "#a855f7" : "#06b6d4");
      var opacity = link.dense ? 0.55 : dashed ? 0.7 : 0.85;
      var geo = new THREE.BufferGeometry().setFromPoints([a.position.clone(), b.position.clone()]);

      var line;
      if (dashed) {
        var dashMat = new THREE.LineDashedMaterial({
          color: new THREE.Color(color),
          dashSize: 0.18,
          gapSize: 0.14,
          transparent: true,
          opacity: opacity,
        });
        line = new THREE.Line(geo, dashMat);
        line.computeLineDistances();
      } else {
        line = new THREE.Line(
          geo,
          new THREE.LineBasicMaterial({
            color: new THREE.Color(color),
            transparent: true,
            opacity: opacity,
          })
        );
      }
      line.userData = {
        source: String(link.source),
        target: String(link.target),
        dashed: dashed,
        dense: !!link.dense,
      };
      this._edgeGroup.add(line);
    }
  };

  MindNetwork3DScene.prototype._syncEdgeEndpoints = function () {
    var children = this._edgeGroup ? this._edgeGroup.children : [];
    for (var i = 0; i < children.length; i++) {
      var line = children[i];
      var a = this._nodeMeshes[line.userData.source];
      var b = this._nodeMeshes[line.userData.target];
      if (!a || !b || !line.geometry) continue;
      var arr = line.geometry.attributes.position.array;
      arr[0] = a.position.x;
      arr[1] = a.position.y;
      arr[2] = a.position.z;
      arr[3] = b.position.x;
      arr[4] = b.position.y;
      arr[5] = b.position.z;
      line.geometry.attributes.position.needsUpdate = true;
      if (line.userData.dashed && line.computeLineDistances) line.computeLineDistances();
    }
  };

  MindNetwork3DScene.prototype._setPhase = function (phase) {
    this._phase = phase;
    this._phaseStart = performance.now();
    this._phaseT = 0;
    if (typeof this._onPhaseChange === "function") {
      try {
        this._onPhaseChange(phase);
      } catch (_) {}
    }
  };

  MindNetwork3DScene.prototype.getPhase = function () {
    return this._phase;
  };

  MindNetwork3DScene.prototype.onPhaseChange = function (fn) {
    this._onPhaseChange = fn;
  };

  MindNetwork3DScene.prototype.enterMirrorPhase = function () {
    this._projectionActive = false;
    this._clearGroup(this._fxGroup);
    this._clearGroup(this._futureGroup);
    this._futureGroup.visible = false;
    this._mirrorGroup.visible = true;
    this._nodeGroup.visible = true;
    this._edgeGroup.visible = true;
    if (this._glassMesh) this._glassMesh.visible = true;
    this._rimLight.intensity = 0;
    this.scene.background.set("#0b0f19");
    this._setPhase("mirror");
    this.resetOrbit();
  };

  /** Spawn glow cracks on the glass plane */
  MindNetwork3DScene.prototype._spawnCracks = function () {
    var positions = [];
    var origin = new THREE.Vector3(0, 0, -0.27);
    for (var i = 0; i < CRACK_SEGMENTS; i++) {
      var ang = (i / CRACK_SEGMENTS) * Math.PI * 2 + Math.random() * 0.2;
      var len = 0.6 + Math.random() * 1.6;
      var mid = 0.35 + Math.random() * 0.5;
      positions.push(origin.x, origin.y, origin.z);
      positions.push(
        Math.cos(ang) * len * mid,
        Math.sin(ang) * len * mid * 1.15,
        origin.z
      );
      positions.push(
        Math.cos(ang) * len * mid,
        Math.sin(ang) * len * mid * 1.15,
        origin.z
      );
      positions.push(Math.cos(ang) * len, Math.sin(ang) * len * 1.15, origin.z);
      // Branch
      var bang = ang + (Math.random() - 0.5) * 0.8;
      positions.push(Math.cos(ang) * len * mid, Math.sin(ang) * len * mid * 1.15, origin.z);
      positions.push(
        Math.cos(bang) * len * (mid + 0.35),
        Math.sin(bang) * len * (mid + 0.35) * 1.15,
        origin.z
      );
    }
    var geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    var mat = new THREE.LineBasicMaterial({
      color: new THREE.Color("#fef9c3"),
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
    });
    this._crackLines = new THREE.LineSegments(geo, mat);
    this._fxGroup.add(this._crackLines);

    // Soft flash plane
    var flash = new THREE.Mesh(
      new THREE.PlaneGeometry(2.85, 4.0),
      new THREE.MeshBasicMaterial({
        color: "#fff7ed",
        transparent: true,
        opacity: 0.55,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      })
    );
    flash.position.z = -0.26;
    flash.userData.kind = "flash";
    this._fxGroup.add(flash);
  };

  /** Glass particle burst from mirror */
  MindNetwork3DScene.prototype._spawnGlassBurst = function () {
    var pos = new Float32Array(GLASS_COUNT * 3);
    var vel = new Float32Array(GLASS_COUNT * 3);
    var start = new Float32Array(GLASS_COUNT * 3);
    var target = new Float32Array(GLASS_COUNT * 3);
    var colors = new Float32Array(GLASS_COUNT * 3);
    var cGold = new THREE.Color("#fbbf24");
    var cEm = new THREE.Color("#34d399");
    var cIce = new THREE.Color("#e0f2fe");

    for (var i = 0; i < GLASS_COUNT; i++) {
      var ix = i * 3;
      var sx = (Math.random() - 0.5) * 2.6;
      var sy = (Math.random() - 0.5) * 3.6;
      var sz = -0.28;
      start[ix] = sx;
      start[ix + 1] = sy;
      start[ix + 2] = sz;
      pos[ix] = sx;
      pos[ix + 1] = sy;
      pos[ix + 2] = sz;
      vel[ix] = (Math.random() - 0.5) * 4.5;
      vel[ix + 1] = (Math.random() - 0.2) * 4.2;
      vel[ix + 2] = 1.2 + Math.random() * 3.8;

      // Future target near CHC layout (assigned later in morph)
      target[ix] = sx;
      target[ix + 1] = sy;
      target[ix + 2] = sz;

      var pick = Math.random();
      var col = pick < 0.4 ? cEm : pick < 0.75 ? cGold : cIce;
      colors[ix] = col.r;
      colors[ix + 1] = col.g;
      colors[ix + 2] = col.b;
    }

    this._glassStart = start;
    this._glassVel = vel;
    this._glassTarget = target;

    var geo = new THREE.BufferGeometry();
    geo.setAttribute("position", new THREE.BufferAttribute(pos, 3));
    geo.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    var mat = new THREE.PointsMaterial({
      size: 0.07,
      vertexColors: true,
      transparent: true,
      opacity: 0.95,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      sizeAttenuation: true,
    });
    this._glassPoints = new THREE.Points(geo, mat);
    this._fxGroup.add(this._glassPoints);
  };

  MindNetwork3DScene.prototype._chcLayout = function (cognitive) {
    var cog = cognitive || {};
    var layout = [];
    // g at center of future space (behind shattered mirror)
    layout.push({
      id: CHC_NODES[0].id,
      label: CHC_NODES[0].label,
      color: CHC_NODES[0].color,
      pearl: CHC_NODES[0].pearl,
      score: Number(cog.g_factor) || 100,
      x: 0,
      y: 0,
      z: -3.2,
      val: 22,
    });
    for (var i = 1; i < CHC_NODES.length; i++) {
      var def = CHC_NODES[i];
      var ang = ((i - 1) / (CHC_NODES.length - 1)) * Math.PI * 2 - Math.PI / 2;
      var score = Number(cog[def.key]) || 100;
      var radius = 1.55 + (score / 150) * 0.55;
      layout.push({
        id: def.id,
        label: def.label,
        color: def.color,
        pearl: def.pearl,
        score: score,
        x: Math.cos(ang) * radius,
        y: Math.sin(ang) * radius * 0.85,
        z: -3.2 + Math.sin(ang * 2) * 0.35,
        val: 10 + score / 20,
      });
    }
    return layout;
  };

  MindNetwork3DScene.prototype._assignMorphTargets = function () {
    var layout = this._chcLayout(this._cognitive);
    this._futureLayout = layout;
    if (!this._glassTarget) return;
    for (var i = 0; i < GLASS_COUNT; i++) {
      var node = layout[i % layout.length];
      var ix = i * 3;
      var jitter = 0.35;
      this._glassTarget[ix] = node.x + (Math.random() - 0.5) * jitter;
      this._glassTarget[ix + 1] = node.y + (Math.random() - 0.5) * jitter;
      this._glassTarget[ix + 2] = node.z + (Math.random() - 0.5) * jitter;
    }
  };

  MindNetwork3DScene.prototype._buildFutureNetwork = function () {
    this._clearGroup(this._futureGroup);
    var layout = this._futureLayout || this._chcLayout(this._cognitive);
    this._futureMeshes = {};

    for (var i = 0; i < layout.length; i++) {
      var n = layout[i];
      var isG = n.id === "chc_g";
      var radius = isG ? 0.38 : 0.14 + Math.min(0.2, n.val / 90);
      var mat = new THREE.MeshStandardMaterial({
        color: new THREE.Color(n.pearl || n.color),
        emissive: new THREE.Color(n.color),
        emissiveIntensity: isG ? 0.65 : 0.45,
        roughness: 0.18,
        metalness: 0.55,
      });
      var mesh = new THREE.Mesh(new THREE.SphereGeometry(radius, 28, 28), mat);
      mesh.position.set(n.x, n.y, n.z);
      mesh.scale.setScalar(0.01);
      mesh.userData = { id: n.id, targetScale: 1 };
      this._futureGroup.add(mesh);
      this._futureMeshes[n.id] = mesh;

      var sprite = makeLabelSprite(n.label, n.color);
      sprite.position.set(0, radius + 0.32, 0);
      mesh.add(sprite);
    }

    // Emerald/gold edges between g and satellites + ring
    var g = layout[0];
    for (var j = 1; j < layout.length; j++) {
      var a = layout[j];
      var geo = new THREE.BufferGeometry().setFromPoints([
        new THREE.Vector3(g.x, g.y, g.z),
        new THREE.Vector3(a.x, a.y, a.z),
      ]);
      this._futureGroup.add(
        new THREE.Line(
          geo,
          new THREE.LineBasicMaterial({
            color: new THREE.Color(j % 2 ? "#34d399" : "#fbbf24"),
            transparent: true,
            opacity: 0.75,
          })
        )
      );
      var next = layout[j + 1] || layout[1];
      if (j < layout.length - 1 || layout.length > 2) {
        var ring = new THREE.BufferGeometry().setFromPoints([
          new THREE.Vector3(a.x, a.y, a.z),
          new THREE.Vector3(next.x, next.y, next.z),
        ]);
        this._futureGroup.add(
          new THREE.Line(
            ring,
            new THREE.LineBasicMaterial({
              color: new THREE.Color("#6ee7b7"),
              transparent: true,
              opacity: 0.4,
            })
          )
        );
      }
    }

    this._futureGroup.visible = true;
  };

  /**
   * Confrontation session complete → Now You See Me style Future Projection.
   * @param {object} [diagnostic] optional latest DSM5 / IntegratedDiagnosticModel
   */
  MindNetwork3DScene.prototype.playFutureProjection = function (diagnostic) {
    if (diagnostic) this.setDiagnostic(diagnostic);
    if (!this._cognitive) this._cognitive = parseCognitiveProfile(this._lastDiagnostic);
    this._projectionActive = true;
    this._autoRotate = false;
    this._clearGroup(this._fxGroup);
    this._spawnCracks();
    this._spawnGlassBurst();
    this._assignMorphTargets();
    this._buildFutureNetwork();
    // Hide live clinical graph during cinematic
    this._nodeGroup.visible = false;
    this._edgeGroup.visible = false;
    if (this._glassMesh) this._glassMesh.visible = false;
    this._rimLight.intensity = 2.2;
    this._rimLight.color.set("#fbbf24");
    this._setPhase("shatter");
  };

  // Alias for event naming in product copy
  MindNetwork3DScene.prototype.onConfrontationComplete = function (diagnostic) {
    return this.playFutureProjection(diagnostic);
  };

  MindNetwork3DScene.prototype.resetOrbit = function () {
    this._azimuth = 0.35;
    this._polar = Math.PI / 2.55;
    this._radius = 8;
    this._autoRotate = false;
  };

  MindNetwork3DScene.prototype.setAutoRotate = function (on) {
    if (this._projectionActive) return;
    this._autoRotate = !!on;
  };

  MindNetwork3DScene.prototype._updateProjection = function (now) {
    var elapsed = (now - this._phaseStart) / 1000;
    this._phaseT = elapsed;

    if (this._phase === "shatter") {
      this._updateShatter(elapsed);
      if (elapsed >= 0.85) this._setPhase("freeze");
      return;
    }
    if (this._phase === "freeze") {
      // Soft hold — particles nearly still
      if (this._crackLines && this._crackLines.material) {
        this._crackLines.material.opacity = Math.max(0, 0.9 - elapsed * 0.35);
      }
      if (elapsed >= 0.75) {
        this._captureGlassAsStart();
        this._setPhase("morph");
      }
      return;
    }
    if (this._phase === "morph") {
      this._updateMorph(elapsed);
      if (elapsed >= 1.9) {
        this._prepareFlythrough();
        this._setPhase("flythrough");
      }
      return;
    }
    if (this._phase === "flythrough") {
      this._updateFlythrough(elapsed);
      if (elapsed >= 2.1) {
        this._finishFuture();
      }
    }
  };

  MindNetwork3DScene.prototype._updateShatter = function (elapsed) {
    var dt = Math.min(elapsed, 1.2);
    if (!this._glassPoints) return;
    var arr = this._glassPoints.geometry.attributes.position.array;
    for (var i = 0; i < GLASS_COUNT; i++) {
      var ix = i * 3;
      arr[ix] = this._glassStart[ix] + this._glassVel[ix] * dt;
      arr[ix + 1] = this._glassStart[ix + 1] + this._glassVel[ix + 1] * dt - 0.9 * dt * dt;
      arr[ix + 2] = this._glassStart[ix + 2] + this._glassVel[ix + 2] * dt;
    }
    this._glassPoints.geometry.attributes.position.needsUpdate = true;

    // Fade flash
    this._fxGroup.children.forEach(function (c) {
      if (c.userData && c.userData.kind === "flash" && c.material) {
        c.material.opacity = Math.max(0, 0.55 - elapsed * 0.7);
      }
    });
    if (this._crackLines && this._crackLines.material) {
      this._crackLines.material.opacity = 0.7 + Math.sin(elapsed * 30) * 0.25;
    }
    this._rimLight.intensity = 3.5 - elapsed * 1.5;
  };

  MindNetwork3DScene.prototype._captureGlassAsStart = function () {
    if (!this._glassPoints) return;
    var arr = this._glassPoints.geometry.attributes.position.array;
    for (var i = 0; i < arr.length; i++) this._glassStart[i] = arr[i];
  };

  MindNetwork3DScene.prototype._updateMorph = function (elapsed) {
    var t = easeInOutCubic(clamp01(elapsed / 1.85));
    if (!this._glassPoints) return;
    var arr = this._glassPoints.geometry.attributes.position.array;
    for (var i = 0; i < GLASS_COUNT; i++) {
      var ix = i * 3;
      arr[ix] = lerp(this._glassStart[ix], this._glassTarget[ix], t);
      arr[ix + 1] = lerp(this._glassStart[ix + 1], this._glassTarget[ix + 1], t);
      arr[ix + 2] = lerp(this._glassStart[ix + 2], this._glassTarget[ix + 2], t);
    }
    this._glassPoints.geometry.attributes.position.needsUpdate = true;
    this._glassPoints.material.opacity = 0.95 - t * 0.55;

    // Scale in future CHC nodes
    var ids = Object.keys(this._futureMeshes || {});
    for (var n = 0; n < ids.length; n++) {
      var mesh = this._futureMeshes[ids[n]];
      mesh.scale.setScalar(lerp(0.01, 1, t));
    }
    this._rimLight.intensity = 1.2 + t * 2.5;
    this._rimLight.color.set(t > 0.5 ? "#34d399" : "#fbbf24");
    this.scene.background.lerp(new THREE.Color("#071510"), t * 0.15);

    if (this._crackLines) this._crackLines.visible = t < 0.4;
    this._mirrorGroup.visible = t < 0.85;
  };

  MindNetwork3DScene.prototype._prepareFlythrough = function () {
    var sinP = Math.sin(this._polar);
    this._camFrom = {
      x: this._radius * sinP * Math.sin(this._azimuth),
      y: this._radius * Math.cos(this._polar),
      z: this._radius * sinP * Math.cos(this._azimuth),
    };
    this._lookFrom = { x: 0, y: 0, z: -0.3 };
    // Dive through mirror into future CHC core
    this._camTo = { x: 0.15, y: 0.35, z: -1.15 };
    this._lookTo = { x: 0, y: 0, z: -3.2 };
    if (this._glassPoints) this._glassPoints.visible = false;
    this._mirrorGroup.visible = false;
    this._futureGroup.visible = true;
    var ids = Object.keys(this._futureMeshes || {});
    for (var i = 0; i < ids.length; i++) this._futureMeshes[ids[i]].scale.setScalar(1);
  };

  MindNetwork3DScene.prototype._updateFlythrough = function (elapsed) {
    var t = easeInOutCubic(clamp01(elapsed / 2.0));
    if (!this._camFrom || !this._camTo) return;
    this.camera.position.set(
      lerp(this._camFrom.x, this._camTo.x, t),
      lerp(this._camFrom.y, this._camTo.y, t),
      lerp(this._camFrom.z, this._camTo.z, t)
    );
    this.camera.lookAt(
      lerp(this._lookFrom.x, this._lookTo.x, t),
      lerp(this._lookFrom.y, this._lookTo.y, t),
      lerp(this._lookFrom.z, this._lookTo.z, t)
    );
    this._rimLight.intensity = 2.8 + Math.sin(elapsed * 4) * 0.4;
    // Gentle pulse on future nodes
    var ids = Object.keys(this._futureMeshes || {});
    for (var i = 0; i < ids.length; i++) {
      var mesh = this._futureMeshes[ids[i]];
      var pulse = 1 + Math.sin(elapsed * 3 + i) * 0.04;
      mesh.scale.setScalar(pulse);
    }
  };

  MindNetwork3DScene.prototype._finishFuture = function () {
    this._setPhase("future");
    this._projectionActive = false;
    this._azimuth = 0.2;
    this._polar = Math.PI / 2.3;
    this._radius = 5.2;
    this._autoRotate = true;
    this.scene.background.set("#071510");
    this._rimLight.intensity = 2.4;
    this._rimLight.color.set("#34d399");
  };

  MindNetwork3DScene.prototype._animate = function () {
    if (this._disposed) return;
    requestAnimationFrame(this._animate);
    var now = performance.now();
    var t = (now - this._clockStart) / 1000;

    if (this._projectionActive || this._phase === "flythrough" || this._phase === "morph" || this._phase === "shatter" || this._phase === "freeze") {
      this._updateProjection(now);
      // During projection, camera may be controlled by flythrough; otherwise hold
      if (this._phase !== "flythrough" && this._phase !== "future") {
        var sinPHold = Math.sin(this._polar);
        this.camera.position.set(
          this._radius * sinPHold * Math.sin(this._azimuth),
          this._radius * Math.cos(this._polar),
          this._radius * sinPHold * Math.cos(this._azimuth)
        );
        this.camera.lookAt(0, 0, -0.4);
      }
      this.renderer.render(this.scene, this.camera);
      return;
    }

    if (this._phase === "future") {
      if (this._autoRotate && !this._dragging) this._azimuth += 0.004;
      var idsF = Object.keys(this._futureMeshes || {});
      for (var f = 0; f < idsF.length; f++) {
        var fm = this._futureMeshes[idsF[f]];
        fm.scale.setScalar(1 + Math.sin(t * 2.2 + f) * 0.035);
      }
      var sinPF = Math.sin(this._polar);
      this.camera.position.set(
        this._radius * sinPF * Math.sin(this._azimuth),
        this._radius * Math.cos(this._polar),
        this._radius * sinPF * Math.cos(this._azimuth) - 2.4
      );
      this.camera.lookAt(0, 0, -3.0);
      this.renderer.render(this.scene, this.camera);
      return;
    }

    // ── mirror / clinical idle ──
    var sch = this.schFragmentation;
    var asd = this.asdRigidity;
    var amp = 1.0 + this.internalizingPressure * 0.5;

    var positions = this.geometry.attributes.position.array;
    for (var i = 0; i < positions.length; i += 3) {
      if (sch > 0.6) {
        positions[i] += Math.sin(t + i) * 0.03 * sch * amp;
        positions[i + 1] += Math.cos(t + i) * 0.03 * sch * amp;
        positions[i + 2] += Math.sin(t * 0.5 + i) * 0.03 * sch * amp;
      } else if (asd > 0.6) {
        positions[i] = lerp(positions[i], Math.sin(i) * 0.4, 0.015 * amp);
        positions[i + 1] = lerp(positions[i + 1], Math.cos(i) * 0.4, 0.015 * amp);
      } else {
        positions[i + 1] += Math.sin(t + positions[i]) * 0.003 * amp;
      }
    }
    this.geometry.attributes.position.needsUpdate = true;

    var ids = Object.keys(this._nodeMeshes);
    for (var n = 0; n < ids.length; n++) {
      var mesh = this._nodeMeshes[ids[n]];
      var ud = mesh.userData || {};
      var base = ud.base || { x: 0, y: 0, z: 0 };
      if (ud.isCenter) {
        mesh.position.set(0, 0, base.z || -0.55);
        mesh.scale.setScalar(1 + Math.sin(t * 2) * 0.04);
        continue;
      }
      if (sch > 0.6) {
        var scatter = 1 + sch * 0.55 * amp;
        mesh.position.x = base.x * scatter + Math.sin(t * 1.3 + n) * 0.25 * sch;
        mesh.position.y = base.y * scatter + Math.cos(t * 1.1 + n) * 0.25 * sch;
        mesh.position.z = base.z * scatter + Math.sin(t * 0.9 + n) * 0.15 * sch;
      } else if (asd > 0.6) {
        var targetR = ud.fixation ? 0.85 : 1.25;
        var len = Math.sqrt(base.x * base.x + base.y * base.y) || 1;
        var tx = (base.x / len) * targetR;
        var ty = (base.y / len) * targetR;
        mesh.position.x = lerp(mesh.position.x, tx, 0.04 * amp);
        mesh.position.y = lerp(mesh.position.y, ty, 0.04 * amp);
        mesh.position.z = lerp(mesh.position.z, base.z, 0.04 * amp);
      } else {
        mesh.position.x = lerp(mesh.position.x, base.x, 0.08);
        mesh.position.y = lerp(mesh.position.y, base.y + Math.sin(t + n) * 0.05, 0.08);
        mesh.position.z = lerp(mesh.position.z, base.z, 0.08);
      }
    }

    this._syncEdgeEndpoints();
    if (this._livePulse > 0) this._livePulse = Math.max(0, this._livePulse - 0.02);
    if (this._autoRotate && !this._dragging) this._azimuth += 0.0035;

    var sinP = Math.sin(this._polar);
    this.camera.position.set(
      this._radius * sinP * Math.sin(this._azimuth),
      this._radius * Math.cos(this._polar),
      this._radius * sinP * Math.cos(this._azimuth)
    );
    this.camera.lookAt(0, 0, -0.4);
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
      this._clearGroup(this._nodeGroup);
      this._clearGroup(this._edgeGroup);
      this._clearGroup(this._mirrorGroup);
      this._clearGroup(this._fxGroup);
      this._clearGroup(this._futureGroup);
      this.renderer.dispose();
      this.geometry.dispose();
      this.material.dispose();
      if (this.renderer.domElement && this.renderer.domElement.parentNode) {
        this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
      }
    } catch (_) {}
  };

  window.MindNetwork3DScene = MindNetwork3DScene;
  window.parseNetworkMetrics = parseNetworkMetrics;
  window.MIND_NETWORK_CHC_NODES = CHC_NODES;
})();
