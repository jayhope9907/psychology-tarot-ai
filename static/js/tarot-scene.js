/**
 * Three.js tarot — top-down table view, circular archetype spread, custom camera.
 */
(function (global) {
  const CARD_W = 0.36;
  const CARD_H = 0.58;
  const CARD_DEPTH = 0.022;
  const TABLE_RADIUS = 6.4;
  const TABLE_TOP_Y = 0.68;
  const TABLE_CENTER_Z = 0;
  const RING_RADII = [5.05, 3.85, 2.65];
  const CAMERA_DEFAULTS = { height: 12.2, fov: 38, zoom: 1, orbit: 0 };
  const CAMERA_LOOK = { x: 0, y: TABLE_TOP_Y, z: TABLE_CENTER_Z };
  const STORAGE_KEY = "psychology_ai_tarot_camera";
  const textureCache = new Map();

  function loadCameraPrefs() {
    try {
      const raw = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{}");
      return {
        height: Math.min(18, Math.max(7, Number(raw.height) || CAMERA_DEFAULTS.height)),
        fov: Math.min(60, Math.max(24, Number(raw.fov) || CAMERA_DEFAULTS.fov)),
        zoom: Math.min(1.45, Math.max(0.7, Number(raw.zoom) || CAMERA_DEFAULTS.zoom)),
        orbit: Number.isFinite(Number(raw.orbit)) ? Number(raw.orbit) : 0,
      };
    } catch (e) {
      return { ...CAMERA_DEFAULTS };
    }
  }

  function saveCameraPrefs(prefs) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prefs));
    } catch (e) {}
  }

  function archetypeHint(card) {
    if (!card) return "";
    const theme = (card.psychology_theme || "").trim();
    const kw = Array.isArray(card.keywords_ko) ? card.keywords_ko.filter(Boolean).slice(0, 2).join(" · ") : "";
    const detail = theme || kw || (card.upright_ko || "").split(/[.。]/)[0] || "";
    return detail ? `${card.name_ko} — ${detail}` : (card.name_ko || "");
  }

  function drawFallbackFace(ctx, card) {
    const colors = (card && card.gradient) || ["#1e3a5f", "#5b9bd5"];
    const grad = ctx.createLinearGradient(0, 0, 512, 800);
    grad.addColorStop(0, colors[0]);
    grad.addColorStop(1, colors[1]);
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 800);
    ctx.strokeStyle = "rgba(255,252,247,0.85)";
    ctx.lineWidth = 6;
    ctx.strokeRect(20, 20, 472, 760);
    ctx.fillStyle = "#f4f1eb";
    ctx.font = "bold 120px serif";
    ctx.textAlign = "center";
    ctx.fillText((card && card.symbol) || "✦", 256, 300);
    ctx.font = "600 40px 'Noto Sans KR', sans-serif";
    ctx.fillText((card && card.name_ko) || "타로", 256, 460);
  }

  function drawBackFace(ctx) {
    const grad = ctx.createLinearGradient(0, 0, 512, 800);
    grad.addColorStop(0, "#1a2822");
    grad.addColorStop(0.5, "#0f1714");
    grad.addColorStop(1, "#1e2d26");
    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, 512, 800);
    ctx.strokeStyle = "#c4a574";
    ctx.lineWidth = 8;
    ctx.strokeRect(24, 24, 464, 752);
    ctx.fillStyle = "#c4a574";
    ctx.font = "bold 100px serif";
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillText("✦", 256, 400);
    ctx.font = "500 26px 'Noto Sans KR', sans-serif";
    ctx.fillStyle = "rgba(244,241,235,0.7)";
    ctx.fillText("마음쉼터 타로", 256, 520);
  }

  function createCanvasTexture(drawFn) {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 800;
    drawFn(canvas.getContext("2d"));
    const texture = new THREE.CanvasTexture(canvas);
    texture.anisotropy = 8;
    if (THREE.SRGBColorSpace) texture.colorSpace = THREE.SRGBColorSpace;
    return texture;
  }

  function loadCardFrontTexture(card) {
    const key = `${card?.id || "unknown"}_${card?.reversed ? "rev" : "up"}`;
    if (textureCache.has(key)) return Promise.resolve(textureCache.get(key));

    const hidden = global.TarotImageSettings?.getMode?.() === "hidden";

    if (hidden || !card?.image_url) {
      const tex = createCanvasTexture((ctx) => drawFallbackFace(ctx, card));
      textureCache.set(key, tex);
      return Promise.resolve(tex);
    }

    return new Promise((resolve) => {
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        const tex = createCanvasTexture((ctx) => {
          ctx.fillStyle = "#0f1714";
          ctx.fillRect(0, 0, 512, 800);
          if (card.reversed) {
            ctx.save();
            ctx.translate(256, 400);
            ctx.rotate(Math.PI);
            ctx.drawImage(img, -236, -370, 472, 740);
            ctx.restore();
            ctx.fillStyle = "rgba(180,40,40,0.85)";
            ctx.font = "600 28px 'Noto Sans KR', sans-serif";
            ctx.textAlign = "center";
            ctx.fillText("역방향", 256, 56);
          } else {
            ctx.drawImage(img, 20, 20, 472, 740);
          }
          ctx.strokeStyle = "rgba(255,252,247,0.9)";
          ctx.lineWidth = 6;
          ctx.strokeRect(20, 20, 472, 760);
          ctx.fillStyle = "rgba(15,23,20,0.82)";
          ctx.fillRect(20, 700, 472, 80);
          ctx.fillStyle = "#f4f1eb";
          ctx.font = "600 30px 'Noto Sans KR', sans-serif";
          ctx.textAlign = "center";
          ctx.fillText(card.name_ko || "", 256, 748);
        });
        textureCache.set(key, tex);
        resolve(tex);
      };
      img.onerror = () => {
        const tex = createCanvasTexture((ctx) => drawFallbackFace(ctx, card));
        textureCache.set(key, tex);
        resolve(tex);
      };
      img.src = card.image_url;
    });
  }

  function createBackTexture() {
    if (!textureCache.has("__back__")) {
      textureCache.set("__back__", createCanvasTexture(drawBackFace));
    }
    return textureCache.get("__back__");
  }

  function easeInOutCubic(t) {
    return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  }

  class TarotScene {
    constructor(container) {
      this.container = container;
      this.deckData = [];
      this.drawnCards = [];
      this.meshes = [];
      this.phase = "idle";
      this.flippedCount = 0;
      this.onCardFlip = null;
      this.onPhaseChange = null;
      this.onPick = null;
      this.onPickComplete = null;
      this.onCameraChange = null;

      this.pickMode = false;
      this.maxPicks = 3;
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.contextMeshes = [];
      this.hoveredMesh = null;
      this.circleRotation = 0;
      this.circleRadiusScale = 1;
      this._animToken = 0;
      this.cameraPrefs = loadCameraPrefs();
      this.onHover = null;
      this._pointers = new Map();
      this._gesture = {
        mode: null,
        startX: 0,
        startY: 0,
        moved: false,
        pendingPick: null,
        orbitStart: 0,
        pinchDist: 0,
        pinchZoom: 1,
      };

      this.raycaster = new THREE.Raycaster();
      this.pointer = new THREE.Vector2();

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(this.cameraPrefs.fov, 1, 0.1, 100);
      this._updateCamera();

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setClearColor(0x000000, 0);
      this.renderer.shadowMap.enabled = true;
      container.appendChild(this.renderer.domElement);
      this.renderer.domElement.style.touchAction = "none";
      this.renderer.domElement.style.cursor = "grab";

      this.scene.add(new THREE.AmbientLight(0xf4f1eb, 0.72));
      const key = new THREE.DirectionalLight(0xffffff, 0.85);
      key.position.set(1.5, 16, 2);
      key.castShadow = true;
      key.shadow.mapSize.set(1024, 1024);
      this.scene.add(key);
      const rim = new THREE.PointLight(0xc4a574, 0.45, 36);
      rim.position.set(-2, 8, -2);
      this.scene.add(rim);
      const fill = new THREE.PointLight(0x5a8f78, 0.28, 28);
      fill.position.set(3, 6, 3);
      this.scene.add(fill);

      this._addTable();
      this._addTableRing();
      this._addParticles();
      this._resize();
      this._onResize = () => this._resize();
      this._onPointerDown = (e) => this._gesturePointerDown(e);
      this._onPointerMove = (e) => this._gesturePointerMove(e);
      this._onPointerUp = (e) => this._gesturePointerUp(e);
      this._onWheel = (e) => this._gestureWheel(e);
      window.addEventListener("resize", this._onResize);
      const el = this.renderer.domElement;
      this._onPointerLeave = (e) => {
        this._setHover(null);
        this._onPointerUp(e);
      };
      el.addEventListener("pointerdown", this._onPointerDown);
      el.addEventListener("pointermove", this._onPointerMove);
      el.addEventListener("pointerup", this._onPointerUp);
      el.addEventListener("pointercancel", this._onPointerUp);
      el.addEventListener("pointerleave", this._onPointerLeave);
      el.addEventListener("wheel", this._onWheel, { passive: false });
      this._animate = this._animate.bind(this);
      requestAnimationFrame(this._animate);
    }

    getCameraPrefs() {
      return { ...this.cameraPrefs };
    }

    setCameraPrefs(partial = {}) {
      this.cameraPrefs = {
        height: Math.min(18, Math.max(7, Number(partial.height ?? this.cameraPrefs.height))),
        fov: Math.min(60, Math.max(24, Number(partial.fov ?? this.cameraPrefs.fov))),
        zoom: Math.min(1.45, Math.max(0.7, Number(partial.zoom ?? this.cameraPrefs.zoom))),
        orbit: Number(partial.orbit ?? this.cameraPrefs.orbit) || 0,
      };
      saveCameraPrefs(this.cameraPrefs);
      this._updateCamera();
      if (this.onCameraChange) this.onCameraChange(this.getCameraPrefs());
      return this.getCameraPrefs();
    }

    resetCameraPrefs() {
      return this.setCameraPrefs({ ...CAMERA_DEFAULTS });
    }

    nudgeZoom(factor) {
      const next = Math.min(1.45, Math.max(0.7, this.cameraPrefs.zoom * factor));
      return this.setCameraPrefs({ zoom: next });
    }

    nudgeOrbit(deltaRad) {
      return this.setCameraPrefs({ orbit: (this.cameraPrefs.orbit || 0) + deltaRad });
    }

    _eventToNDC(event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      return rect;
    }

    _hitMeshes(filterFn) {
      this.raycaster.setFromCamera(this.pointer, this.camera);
      const pool = filterFn ? this.meshes.filter(filterFn) : this.meshes;
      const hits = this.raycaster.intersectObjects(pool, false);
      return hits.length ? hits[0].object : null;
    }

    _pointerDistance(a, b) {
      const dx = a.x - b.x;
      const dy = a.y - b.y;
      return Math.hypot(dx, dy);
    }

    _gestureWheel(event) {
      event.preventDefault();
      const factor = event.deltaY > 0 ? 0.94 : 1.06;
      this.nudgeZoom(factor);
    }

    _gesturePointerDown(event) {
      try {
        this.renderer.domElement.setPointerCapture(event.pointerId);
      } catch (_) {}
      this._pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      this._eventToNDC(event);

      if (this._pointers.size === 2) {
        const pts = [...this._pointers.values()];
        this._gesture.mode = "pinch";
        this._gesture.pendingPick = null;
        this._gesture.pinchDist = this._pointerDistance(pts[0], pts[1]);
        this._gesture.pinchZoom = this.cameraPrefs.zoom;
        this.renderer.domElement.style.cursor = "grabbing";
        return;
      }

      this._gesture.mode = "pending";
      this._gesture.moved = false;
      this._gesture.startX = event.clientX;
      this._gesture.startY = event.clientY;
      this._gesture.orbitStart = this.cameraPrefs.orbit || 0;

      if (this.pickMode) {
        const mesh = this._hitMeshes((m) => m.userData.selectable && !m.userData.selected);
        this._gesture.pendingPick = mesh || null;
      } else if (this.phase === "reveal") {
        this._gesture.pendingPick = this._hitMeshes((m) => m.userData.slot && !m.userData.flipped);
      } else {
        this._gesture.pendingPick = null;
      }
    }

    _gesturePointerMove(event) {
      if (this._pointers.has(event.pointerId)) {
        this._pointers.set(event.pointerId, { x: event.clientX, y: event.clientY });
      }

      if (this._pointers.size >= 2 && this._gesture.mode === "pinch") {
        const pts = [...this._pointers.values()];
        const dist = this._pointerDistance(pts[0], pts[1]);
        if (this._gesture.pinchDist > 0) {
          const ratio = dist / this._gesture.pinchDist;
          this.setCameraPrefs({ zoom: Math.min(1.45, Math.max(0.7, this._gesture.pinchZoom * ratio)) });
        }
        this._setHover(null);
        return;
      }

      if (!this._pointers.has(event.pointerId)) {
        // hover-only move
        this._eventToNDC(event);
        this._updateHoverFromPointer();
        return;
      }

      const dx = event.clientX - this._gesture.startX;
      const dy = event.clientY - this._gesture.startY;
      const dist = Math.hypot(dx, dy);
      if (dist > 10) {
        this._gesture.moved = true;
        if (this._gesture.mode === "pending") {
          this._gesture.mode = "orbit";
          this._gesture.pendingPick = null;
          this.renderer.domElement.style.cursor = "grabbing";
        }
      }

      if (this._gesture.mode === "orbit") {
        // horizontal drag rotates table view; vertical nudges height slightly
        const orbit = this._gesture.orbitStart - (dx / 180) * Math.PI;
        const height = Math.min(18, Math.max(7, this.cameraPrefs.height + dy * -0.01));
        this.setCameraPrefs({ orbit, height });
        this._setHover(null);
        return;
      }

      this._eventToNDC(event);
      this._updateHoverFromPointer();
    }

    _gesturePointerUp(event) {
      const wasPending = this._gesture.mode === "pending" && !this._gesture.moved;
      const pending = this._gesture.pendingPick;
      this._pointers.delete(event.pointerId);
      try {
        this.renderer.domElement.releasePointerCapture(event.pointerId);
      } catch (_) {}

      if (this._pointers.size < 2 && this._gesture.mode === "pinch") {
        this._gesture.mode = null;
      }
      if (this._pointers.size === 0) {
        if (wasPending && pending) {
          if (this.pickMode && pending.userData.selectable) {
            this._togglePick(pending);
          } else if (this.phase === "reveal" && pending.userData.slot && !pending.userData.flipped) {
            this.flipCard(pending.userData.index);
          }
        }
        this._gesture.mode = null;
        this._gesture.pendingPick = null;
        this._gesture.moved = false;
        this.renderer.domElement.style.cursor = this.pickMode ? "pointer" : "grab";
      }
    }

    _updateHoverFromPointer() {
      if (this._gesture.mode === "orbit" || this._gesture.mode === "pinch") {
        this._setHover(null);
        return;
      }
      let mesh = null;
      if (this.pickMode) {
        mesh = this._hitMeshes((m) => m.userData.selectable && !m.userData.selected);
      } else if (this.phase === "ready" || this.phase === "picking") {
        mesh = this._hitMeshes((m) => !m.userData.selected);
      } else if (this.phase === "reveal" || this.phase === "complete") {
        mesh = this._hitMeshes((m) => !!m.userData.slot || m.userData.selected);
      }
      this._setHover(mesh);
    }

    _addTable() {
      const wood = new THREE.MeshStandardMaterial({
        color: 0x4a3424,
        roughness: 0.82,
        metalness: 0.06,
      });
      const table = new THREE.Mesh(new THREE.CylinderGeometry(TABLE_RADIUS, TABLE_RADIUS * 0.96, 0.18, 72), wood);
      table.position.set(0, TABLE_TOP_Y - 0.09, TABLE_CENTER_Z);
      table.receiveShadow = true;
      table.castShadow = true;
      this.scene.add(table);

      const rim = new THREE.Mesh(
        new THREE.TorusGeometry(TABLE_RADIUS - 0.04, 0.05, 12, 96),
        new THREE.MeshStandardMaterial({ color: 0xc4a574, roughness: 0.45, metalness: 0.35 })
      );
      rim.rotation.x = Math.PI / 2;
      rim.position.set(0, TABLE_TOP_Y + 0.01, TABLE_CENTER_Z);
      this.scene.add(rim);

      const floor = new THREE.Mesh(
        new THREE.CircleGeometry(11, 48),
        new THREE.MeshStandardMaterial({ color: 0x0a100e, roughness: 1 })
      );
      floor.rotation.x = -Math.PI / 2;
      floor.position.set(0, -0.02, TABLE_CENTER_Z);
      floor.receiveShadow = true;
      this.scene.add(floor);
    }

    _addTableRing() {
      RING_RADII.forEach((radius, idx) => {
        const ring = new THREE.Mesh(
          new THREE.RingGeometry(radius - 0.04, radius + 0.04, 128),
          new THREE.MeshBasicMaterial({
            color: 0xc4a574,
            transparent: true,
            opacity: 0.16 - idx * 0.03,
            side: THREE.DoubleSide,
          })
        );
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(0, TABLE_TOP_Y + 0.012, TABLE_CENTER_Z);
        this.scene.add(ring);
      });

      const inner = new THREE.Mesh(
        new THREE.CircleGeometry(RING_RADII[2] - 0.2, 120),
        new THREE.MeshBasicMaterial({
          color: 0x0f1714,
          transparent: true,
          opacity: 0.28,
          side: THREE.DoubleSide,
        })
      );
      inner.rotation.x = -Math.PI / 2;
      inner.position.set(0, TABLE_TOP_Y + 0.011, TABLE_CENTER_Z);
      this.scene.add(inner);
    }

    _updateCamera() {
      const prefs = this.cameraPrefs;
      this.camera.fov = prefs.fov;
      const orbit = prefs.orbit || 0;
      const height = prefs.height / prefs.zoom;
      const bias = 0.35 / prefs.zoom;
      this.camera.position.set(
        Math.sin(orbit) * bias,
        height,
        Math.cos(orbit) * bias + TABLE_CENTER_Z
      );
      this.camera.lookAt(CAMERA_LOOK.x, CAMERA_LOOK.y, CAMERA_LOOK.z);
      this.camera.up.set(0, 0, -1);
      this.camera.updateProjectionMatrix();
    }

    _resize() {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight || 480;
      this.camera.aspect = w / h;
      this._updateCamera();
      this.renderer.setSize(w, h);
    }

    _addParticles() {
      const count = 90;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const a = (i / count) * Math.PI * 2;
        const r = RING_RADII[0] + 0.2 + Math.random() * 0.4;
        positions[i * 3] = Math.sin(a) * r;
        positions[i * 3 + 1] = TABLE_TOP_Y + 0.04 + Math.random() * 0.08;
        positions[i * 3 + 2] = Math.cos(a) * r + TABLE_CENTER_Z;
      }
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      this.particles = new THREE.Points(
        geo,
        new THREE.PointsMaterial({ color: 0xc4a574, size: 0.028, transparent: true, opacity: 0.32 })
      );
      this.scene.add(this.particles);
    }

    _makeCardMesh(card) {
      const geo = new THREE.BoxGeometry(CARD_W, CARD_H, CARD_DEPTH);
      const backTex = createBackTexture();
      const frontTex = createCanvasTexture((ctx) => drawFallbackFace(ctx, card));
      const mats = [
        new THREE.MeshStandardMaterial({ color: 0x222222 }),
        new THREE.MeshStandardMaterial({ color: 0x222222 }),
        new THREE.MeshStandardMaterial({ color: 0x222222 }),
        new THREE.MeshStandardMaterial({ color: 0x222222 }),
        new THREE.MeshStandardMaterial({ map: backTex, emissive: 0x000000, emissiveIntensity: 0 }),
        new THREE.MeshStandardMaterial({ map: frontTex }),
      ];
      const mesh = new THREE.Mesh(geo, mats);
      mesh.castShadow = true;
      mesh.userData.card = card;
      mesh.userData.flipped = false;
      mesh.userData.selected = false;
      mesh.userData.selectable = true;
      mesh.userData.baseAngle = 0;
      mesh.userData.circleIndex = 0;
      return mesh;
    }

    async _applyFrontTexture(mesh, card) {
      const tex = await loadCardFrontTexture(card);
      mesh.material[5].map = tex;
      mesh.material[5].needsUpdate = true;
    }

    _circleAngleFor(mesh) {
      return mesh.userData.baseAngle + this.circleRotation;
    }

    _faceDownRx() {
      return Math.PI / 2;
    }

    _faceUpRx() {
      return -Math.PI / 2;
    }

    _circlePose(angle, radius, lift) {
      const r = radius;
      return {
        x: Math.sin(angle) * r,
        y: TABLE_TOP_Y + CARD_DEPTH / 2 + lift,
        z: Math.cos(angle) * r + TABLE_CENTER_Z,
        rx: this._faceDownRx(),
        ry: 0,
        rz: -angle,
      };
    }

    _applyCirclePose(mesh, radiusScale, lift) {
      if (mesh.userData.selected && mesh.userData.drawPose) {
        const p = mesh.userData.drawPose;
        mesh.position.set(p.x, p.y, p.z);
        mesh.rotation.set(p.rx ?? this._faceDownRx(), p.ry ?? 0, p.rz ?? 0);
        return;
      }
      const baseRadius = mesh.userData.ringRadius || RING_RADII[0];
      const hoverLift = mesh.userData.hoverLift || 0;
      const pose = this._circlePose(
        this._circleAngleFor(mesh),
        baseRadius * radiusScale,
        lift + hoverLift
      );
      mesh.position.set(pose.x, pose.y, pose.z);
      mesh.rotation.set(pose.rx, pose.ry, pose.rz);
    }

    _layoutCircle() {
      const majorMeshes = this.meshes.filter((m) => !m.userData.card?.suit);
      const minorMeshes = this.meshes.filter((m) => m.userData.card?.suit);
      const mid = Math.ceil(minorMeshes.length / 2);
      const rings = [
        { meshes: majorMeshes, radius: RING_RADII[0] },
        { meshes: minorMeshes.slice(0, mid), radius: RING_RADII[1] },
        { meshes: minorMeshes.slice(mid), radius: RING_RADII[2] },
      ];

      rings.forEach(({ meshes: ringMeshes, radius }) => {
        ringMeshes.forEach((mesh, i) => {
          mesh.userData.ringRadius = radius;
          mesh.userData.baseAngle = (i / Math.max(1, ringMeshes.length)) * Math.PI * 2 - Math.PI / 2;
          mesh.userData.circleIndex = i;
          mesh.userData.drawPose = null;
          mesh.userData.selected = false;
          mesh.userData.selectable = true;
          mesh.userData.dimmed = false;
          mesh.userData.hoverLift = 0;
          mesh.scale.set(1, 1, 1);
          mesh.material[4].emissive.setHex(0x000000);
          mesh.material[4].emissiveIntensity = 0;
          mesh.material.forEach((mat) => {
            mat.transparent = false;
            mat.opacity = 1;
          });
          this._applyCirclePose(mesh, this.circleRadiusScale, 0);
        });
      });
    }

    buildDeck(catalog) {
      this.clear();
      this.deckData = (catalog || []).slice();
      // Fisher–Yates so visual ring order is not the fixed catalog order.
      for (let i = this.deckData.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const tmp = this.deckData[i];
        this.deckData[i] = this.deckData[j];
        this.deckData[j] = tmp;
      }
      this.deckData.forEach((card) => {
        const mesh = this._makeCardMesh(card);
        this.scene.add(mesh);
        this.meshes.push(mesh);
      });
      this.circleRotation = 0;
      this.circleRadiusScale = 1;
      this._layoutCircle();
      this.phase = "ready";
      this._emitPhase();
    }

    async shuffle() {
      if (!this.meshes.length) {
        this.phase = "shuffling";
        this._emitPhase();
        await new Promise((r) => setTimeout(r, 900));
        this.phase = "ready";
        this._emitPhase();
        return;
      }

      this.phase = "shuffling";
      this._emitPhase();
      const token = ++this._animToken;
      // Re-shuffle mesh order on rings for fair pick positions.
      for (let i = this.meshes.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        const tmp = this.meshes[i];
        this.meshes[i] = this.meshes[j];
        this.meshes[j] = tmp;
      }
      this._layoutCircle();
      const startRot = this.circleRotation;
      const endRot = startRot + Math.PI * 2 * 2.2;
      const duration = 2800;
      const start = performance.now();

      await new Promise((resolve) => {
        const tick = (now) => {
          if (token !== this._animToken) {
            resolve();
            return;
          }
          const t = Math.min((now - start) / duration, 1);
          const ease = easeInOutCubic(t);
          this.circleRotation = THREE.MathUtils.lerp(startRot, endRot, ease);
          this.circleRadiusScale = 1 - Math.sin(ease * Math.PI) * 0.05;
          this.meshes.forEach((mesh) => {
            if (!mesh.userData.selected) {
              const wobble = Math.sin(this._circleAngleFor(mesh) * 3 + ease * Math.PI * 4) * 0.01 * (1 - t);
              this._applyCirclePose(mesh, this.circleRadiusScale, wobble);
            }
          });
          if (t < 1) requestAnimationFrame(tick);
          else {
            this.circleRadiusScale = 1;
            this.meshes.forEach((mesh) => {
              if (!mesh.userData.selected) this._applyCirclePose(mesh, 1, 0);
            });
            this.phase = "ready";
            this._emitPhase();
            resolve();
          }
        };
        requestAnimationFrame(tick);
      });
    }

    clear() {
      [...this.meshes, ...this.contextMeshes].forEach((m) => {
        if (m.parent) this.scene.remove(m);
      });
      this.meshes = [];
      this.contextMeshes = [];
      this.drawnCards = [];
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.flippedCount = 0;
      this.pickMode = false;
      this.hoveredMesh = null;
      this.circleRotation = 0;
      this.circleRadiusScale = 1;
      if (this.onHover) this.onHover("", null);
    }

    _spreadSlots(count) {
      const y = TABLE_TOP_Y + CARD_DEPTH / 2 + 0.02;
      if (count <= 1) return [{ x: 0, y, z: TABLE_CENTER_Z, ry: 0, rx: this._faceDownRx(), rz: 0 }];
      if (count === 2) {
        return [
          { x: -0.55, y, z: TABLE_CENTER_Z, ry: 0, rx: this._faceDownRx(), rz: 0.04 },
          { x: 0.55, y, z: TABLE_CENTER_Z, ry: 0, rx: this._faceDownRx(), rz: -0.04 },
        ];
      }
      return [
        { x: -0.78, y, z: TABLE_CENTER_Z + 0.08, ry: 0, rx: this._faceDownRx(), rz: 0.06 },
        { x: 0, y, z: TABLE_CENTER_Z - 0.05, ry: 0, rx: this._faceDownRx(), rz: 0 },
        { x: 0.78, y, z: TABLE_CENTER_Z + 0.08, ry: 0, rx: this._faceDownRx(), rz: -0.06 },
      ];
    }

    _drawHoldPose(pickIndex) {
      const slots = [
        { x: 0, y: TABLE_TOP_Y + 0.08, z: TABLE_CENTER_Z, ry: 0, rx: this._faceDownRx(), rz: 0 },
        { x: -0.42, y: TABLE_TOP_Y + 0.08, z: TABLE_CENTER_Z + 0.12, ry: 0, rx: this._faceDownRx(), rz: 0.05 },
        { x: 0.42, y: TABLE_TOP_Y + 0.08, z: TABLE_CENTER_Z + 0.12, ry: 0, rx: this._faceDownRx(), rz: -0.05 },
      ];
      return slots[pickIndex] || slots[0];
    }

    startPickMode(maxPicks) {
      this.maxPicks = maxPicks;
      this.pickMode = true;
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.phase = "picking";
      this._emitPhase();
      this.meshes.forEach((m) => {
        m.userData.selectable = !m.userData.selected;
      });
    }

    _setHover(mesh) {
      if (this.hoveredMesh && this.hoveredMesh !== mesh) {
        this.hoveredMesh.userData.hoverLift = 0;
        if (!this.hoveredMesh.userData.selected && !this.hoveredMesh.userData.dimmed) {
          this.hoveredMesh.material[4].emissive.setHex(0x000000);
          this.hoveredMesh.material[4].emissiveIntensity = 0;
        }
      }
      this.hoveredMesh = mesh;
      if (mesh && !mesh.userData.selected && !mesh.userData.dimmed) {
        mesh.userData.hoverLift = this.pickMode ? 0.06 : 0.03;
        mesh.material[4].emissive.setHex(0x8a7348);
        mesh.material[4].emissiveIntensity = this.pickMode ? 0.28 : 0.16;
      }
      if (this.onHover) {
        const card = mesh?.userData?.card;
        this.onHover(card ? archetypeHint(card) : "", card || null);
      }
    }

    // legacy aliases kept for safety
    _handlePointerMove(event) {
      this._gesturePointerMove(event);
    }

    _handlePointer(event) {
      this._gesturePointerDown(event);
    }

    _animateMeshTo(mesh, target, duration) {
      const token = this._animToken;
      const start = performance.now();
      const from = {
        x: mesh.position.x,
        y: mesh.position.y,
        z: mesh.position.z,
        rx: mesh.rotation.x,
        ry: mesh.rotation.y,
        rz: mesh.rotation.z,
      };
      return new Promise((resolve) => {
        const tick = (now) => {
          if (token !== this._animToken) {
            resolve();
            return;
          }
          const t = Math.min((now - start) / duration, 1);
          const ease = easeInOutCubic(t);
          mesh.position.x = THREE.MathUtils.lerp(from.x, target.x, ease);
          mesh.position.y = THREE.MathUtils.lerp(from.y, target.y, ease);
          mesh.position.z = THREE.MathUtils.lerp(from.z, target.z, ease);
          mesh.rotation.x = THREE.MathUtils.lerp(from.rx, target.rx ?? this._faceDownRx(), ease);
          mesh.rotation.y = THREE.MathUtils.lerp(from.ry, target.ry ?? 0, ease);
          mesh.rotation.z = THREE.MathUtils.lerp(from.rz, target.rz ?? 0, ease);
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });
    }

    async _drawCardFromCircle(mesh, pickIndex) {
      const startAngle = this._circleAngleFor(mesh);
      const midR = (mesh.userData.ringRadius || RING_RADII[0]) * 0.45;
      const mid = {
        x: Math.sin(startAngle) * midR,
        y: TABLE_TOP_Y + 0.12,
        z: Math.cos(startAngle) * midR + TABLE_CENTER_Z,
        rx: this._faceDownRx(),
        ry: 0,
        rz: -startAngle,
      };
      const hold = this._drawHoldPose(pickIndex);
      mesh.userData.drawPose = null;
      await this._animateMeshTo(mesh, mid, 380);
      await this._animateMeshTo(mesh, hold, 480);
      mesh.userData.drawPose = { ...hold };
      mesh.material[4].emissive.setHex(0xc4a574);
      mesh.material[4].emissiveIntensity = 0.42;
    }

    async _returnCardToCircle(mesh) {
      mesh.userData.drawPose = null;
      const pose = this._circlePose(
        this._circleAngleFor(mesh),
        mesh.userData.ringRadius || RING_RADII[0],
        0
      );
      await this._animateMeshTo(mesh, pose, 420);
      mesh.material[4].emissive.setHex(0x000000);
      mesh.material[4].emissiveIntensity = 0;
    }

    _togglePick(mesh) {
      if (mesh.userData.selected) {
        mesh.userData.selected = false;
        mesh.userData.selectable = true;
        this.selectedMeshes = this.selectedMeshes.filter((m) => m !== mesh);
        this.pickedCardIds = this.selectedMeshes.map((m) => m.userData.card.id);
        this._returnCardToCircle(mesh).then(() => {
          if (this.onPick) this.onPick(this.pickedCardIds.length, this.maxPicks);
        });
        return;
      }
      if (this.selectedMeshes.length >= this.maxPicks) return;

      mesh.userData.selected = true;
      mesh.userData.selectable = false;
      const pickIndex = this.selectedMeshes.length;
      this.selectedMeshes.push(mesh);
      this.pickedCardIds = this.selectedMeshes.map((m) => m.userData.card.id);
      if (this.onPick) this.onPick(this.pickedCardIds.length, this.maxPicks);

      this._drawCardFromCircle(mesh, pickIndex).then(() => {
        if (this.selectedMeshes.length >= this.maxPicks) {
          this.pickMode = false;
          this._setHover(null);
          if (this.onPickComplete) this.onPickComplete(this.pickedCardIds.slice());
        }
      });
    }

    pickCardById(cardId) {
      const mesh = this.meshes.find((m) => m.userData.card?.id === cardId && m.userData.selectable);
      if (mesh) this._togglePick(mesh);
    }

    async layoutSelected(cards) {
      this.drawnCards = cards || [];
      const token = ++this._animToken;
      const unselected = this.meshes.filter((m) => !m.userData.selected);

      unselected.forEach((mesh) => {
        mesh.userData.selectable = false;
        mesh.userData.dimmed = true;
      });

      const fadeStart = performance.now();
      const fadeDuration = 650;
      await new Promise((resolve) => {
        const tick = (now) => {
          if (token !== this._animToken) {
            resolve();
            return;
          }
          const t = Math.min((now - fadeStart) / fadeDuration, 1);
          unselected.forEach((mesh) => {
            mesh.material.forEach((mat) => {
              mat.transparent = true;
              // Keep ring context visible (fade, don't remove).
              mat.opacity = 1 - t * 0.72;
            });
            mesh.scale.setScalar(1 - t * 0.08);
          });
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });

      this.contextMeshes = unselected.slice();

      const slots = this._spreadSlots(this.selectedMeshes.length);
      this.phase = "spreading";
      this._emitPhase();

      const anims = this.selectedMeshes.map((mesh, i) => {
        mesh.userData.drawPose = null;
        mesh.userData.slot = slots[i];
        mesh.userData.index = i;
        mesh.userData.card = this.drawnCards[i] || mesh.userData.card;
        mesh.userData.dimmed = false;
        mesh.material.forEach((mat) => {
          mat.transparent = false;
          mat.opacity = 1;
        });
        mesh.scale.set(1, 1, 1);
        this._applyFrontTexture(mesh, mesh.userData.card);
        const slot = slots[i];
        return this._animateMeshTo(mesh, {
          x: slot.x,
          y: slot.y + 0.03,
          z: slot.z,
          ry: slot.ry,
          rx: slot.rx ?? this._faceDownRx(),
          rz: slot.rz ?? 0,
        }, 780);
      });

      await Promise.all(anims);
      this.meshes = this.selectedMeshes.slice();
      this.phase = "reveal";
      this._emitPhase();
    }

    flipCard(index) {
      const mesh = this.meshes[index];
      if (!mesh || mesh.userData.flipped) return Promise.resolve();
      mesh.userData.flipped = true;
      this.flippedCount += 1;
      const card = mesh.userData.card;
      if (this.onCardFlip) this.onCardFlip(card, index);
      return this._applyFrontTexture(mesh, card).then(() => this._animateFlip(mesh)).then(() => {
        if (this.flippedCount >= this.meshes.length) {
          this.phase = "complete";
          this._emitPhase();
        }
      });
    }

    refreshImageMode() {
      textureCache.clear();
      createBackTexture();
      this.meshes.forEach((mesh) => {
        if (mesh.userData.flipped && mesh.userData.card) {
          this._applyFrontTexture(mesh, mesh.userData.card);
        } else {
          mesh.material[4].map = createBackTexture();
          mesh.material[4].needsUpdate = true;
        }
      });
    }

    _animateFlip(mesh) {
      const duration = 680;
      const start = performance.now();
      const startX = mesh.rotation.x;
      const endX = this._faceUpRx();
      const startY = mesh.position.y;
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = easeInOutCubic(t);
          mesh.rotation.x = THREE.MathUtils.lerp(startX, endX, ease);
          mesh.position.y = startY + Math.sin(ease * Math.PI) * 0.22;
          if (t < 1) requestAnimationFrame(tick);
          else {
            mesh.position.y = startY;
            resolve();
          }
        };
        requestAnimationFrame(tick);
      });
    }

    _emitPhase() {
      if (this.onPhaseChange) this.onPhaseChange(this.phase);
    }

    _animate() {
      requestAnimationFrame(this._animate);
      const now = performance.now();
      if (this.particles) this.particles.rotation.y += 0.00035;

      if (this.phase === "picking" && this.pickMode) {
        this.meshes.forEach((mesh) => {
          if (!mesh.userData.selected && !mesh.userData.drawPose) {
            const lift = Math.sin(now * 0.0018 + mesh.userData.circleIndex * 0.4) * 0.006;
            this._applyCirclePose(mesh, this.circleRadiusScale, lift);
          }
        });
      }

      this.renderer.render(this.scene, this.camera);
    }

    dispose() {
      window.removeEventListener("resize", this._onResize);
      const el = this.renderer.domElement;
      el.removeEventListener("pointerdown", this._onPointerDown);
      el.removeEventListener("pointermove", this._onPointerMove);
      el.removeEventListener("pointerup", this._onPointerUp);
      el.removeEventListener("pointercancel", this._onPointerUp);
      el.removeEventListener("pointerleave", this._onPointerLeave);
      el.removeEventListener("wheel", this._onWheel);
      this.renderer.dispose();
    }
  }

  global.TarotScene = TarotScene;
  global.TarotCameraDefaults = CAMERA_DEFAULTS;
  global.tarotArchetypeHint = archetypeHint;
  global.loadCardFrontTexture = loadCardFrontTexture;
})(typeof window !== "undefined" ? window : globalThis);
