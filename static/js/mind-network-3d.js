/**
 * MindNetwork3D — real-time center_self graph + clinical edge FX.
 *
 * Renders BlueprintBuilder graph:
 *   - center_self sphere + emotion noun nodes
 *   - solid / dashed edges (sch fragmentation → dashed + scatter)
 *   - ASD fixation → dense cyan local edges around hubs
 *
 * Usage:
 *   const net = new MindNetwork3DScene(containerEl);
 *   net.setDiagnostic(doc);
 *   net.setGraph(BlueprintBuilder.getGraph());
 *   net.resetOrbit();
 */
(function () {
  "use strict";

  var CENTER_ID = "center_self";
  var PARTICLE_COUNT = 80;

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
    ctx.font = "600 22px 'Noto Sans KR', sans-serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText(String(text || "").slice(0, 12), 128, 32);
    var tex = new THREE.CanvasTexture(canvas);
    if (THREE.SRGBColorSpace) tex.colorSpace = THREE.SRGBColorSpace;
    var mat = new THREE.SpriteMaterial({
      map: tex,
      transparent: true,
      depthTest: false,
      opacity: 0.95,
    });
    var sprite = new THREE.Sprite(mat);
    sprite.scale.set(1.35, 0.34, 1);
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
    this._livePulse = 0;

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
    this.scene.add(amb);
    this.scene.add(key);

    // Soft ambient particle field (backdrop)
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
    this.scene.add(this._nodeGroup);
    this.scene.add(this._edgeGroup);

    // Seed center_self immediately
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
      self._dragging = true;
      self._lastX = x;
      self._lastY = y;
      self._autoRotate = false;
    };
    var move = function (x, y) {
      if (!self._dragging) return;
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
    this.material.color.set(this._networkColor());
    this.material.needsUpdate = true;
    // Rebuild edges so dashed/dense reflect latest clinical state
    if (this._graph && this._graph.nodes) {
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
        if (child.material.map) child.material.map.dispose();
        child.material.dispose();
      }
      if (child.children) {
        child.traverse(function (obj) {
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
      var baseX = Number(n.x) || 0;
      var baseY = Number(n.y) || 0;
      var baseZ = Number(n.z) || 0;
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
      var geo = new THREE.BufferGeometry().setFromPoints([
        a.position.clone(),
        b.position.clone(),
      ]);

      var line;
      if (dashed) {
        var dashMat = new THREE.LineDashedMaterial({
          color: new THREE.Color(color),
          dashSize: 0.18,
          gapSize: 0.14,
          transparent: true,
          opacity: opacity,
          linewidth: 1,
        });
        line = new THREE.Line(geo, dashMat);
        line.computeLineDistances();
      } else {
        var solidMat = new THREE.LineBasicMaterial({
          color: new THREE.Color(color),
          transparent: true,
          opacity: opacity,
        });
        line = new THREE.Line(geo, solidMat);
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
      if (line.userData.dashed && line.computeLineDistances) {
        line.computeLineDistances();
      }
    }
  };

  MindNetwork3DScene.prototype.resetOrbit = function () {
    this._azimuth = 0.35;
    this._polar = Math.PI / 2.55;
    this._radius = 8;
    this._autoRotate = false;
  };

  MindNetwork3DScene.prototype.setAutoRotate = function (on) {
    this._autoRotate = !!on;
  };

  MindNetwork3DScene.prototype._animate = function () {
    if (this._disposed) return;
    requestAnimationFrame(this._animate);
    var t = (performance.now() - this._clockStart) / 1000;
    var sch = this.schFragmentation;
    var asd = this.asdRigidity;
    var amp = 1.0 + this.internalizingPressure * 0.5;

    // Backdrop particles
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

    // Node clinical motion
    var ids = Object.keys(this._nodeMeshes);
    for (var n = 0; n < ids.length; n++) {
      var mesh = this._nodeMeshes[ids[n]];
      var ud = mesh.userData || {};
      var base = ud.base || { x: 0, y: 0, z: 0 };
      if (ud.isCenter) {
        mesh.position.set(0, 0, 0);
        mesh.scale.setScalar(1 + Math.sin(t * 2) * 0.04);
        continue;
      }
      if (sch > 0.6) {
        // Fragment: drift away from center, break cohesion
        var scatter = 1 + sch * 0.55 * amp;
        mesh.position.x = base.x * scatter + Math.sin(t * 1.3 + n) * 0.25 * sch;
        mesh.position.y = base.y * scatter + Math.cos(t * 1.1 + n) * 0.25 * sch;
        mesh.position.z = base.z * scatter + Math.sin(t * 0.9 + n) * 0.25 * sch;
      } else if (asd > 0.6) {
        // Fixation: compress toward hub axes / center ring
        var targetR = ud.fixation ? 1.1 : 1.6;
        var len = Math.sqrt(base.x * base.x + base.z * base.z) || 1;
        var tx = (base.x / len) * targetR;
        var tz = (base.z / len) * targetR;
        mesh.position.x = lerp(mesh.position.x, tx, 0.04 * amp);
        mesh.position.y = lerp(mesh.position.y, base.y * 0.35, 0.04 * amp);
        mesh.position.z = lerp(mesh.position.z, tz, 0.04 * amp);
      } else {
        mesh.position.x = lerp(mesh.position.x, base.x, 0.08);
        mesh.position.y = lerp(mesh.position.y, base.y + Math.sin(t + n) * 0.05, 0.08);
        mesh.position.z = lerp(mesh.position.z, base.z, 0.08);
      }
    }

    this._syncEdgeEndpoints();

    if (this._livePulse > 0) {
      this._livePulse = Math.max(0, this._livePulse - 0.02);
    }

    if (this._autoRotate && !this._dragging) {
      this._azimuth += 0.0035;
    }

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
      this._clearGroup(this._nodeGroup);
      this._clearGroup(this._edgeGroup);
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
})();
