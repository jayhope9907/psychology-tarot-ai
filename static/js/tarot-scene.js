/**
 * Three.js tarot — circular spread, human-like shuffle & draw.
 */
(function (global) {
  const CARD_W = 0.54;
  const CARD_H = 0.87;
  const CARD_DEPTH = 0.028;
  const CIRCLE_RADIUS_OUTER = 4.55;
  const CIRCLE_RADIUS_INNER = 2.85;
  const INNER_RING_SCALE = 0.76;
  const CIRCLE_Y = 0.1;
  const CIRCLE_CENTER_Z = 0.55;
  const CAMERA_FOV = 48;
  const CAMERA_BASE = { x: 0, y: 4.4, z: 6.4 };
  const CAMERA_LOOK = { x: 0, y: 0.12, z: CIRCLE_CENTER_Z };
  const textureCache = new Map();

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

      this.pickMode = false;
      this.maxPicks = 3;
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.hoveredMesh = null;
      this.circleRotation = 0;
      this.circleRadiusScale = 1;
      this._animToken = 0;

      this.raycaster = new THREE.Raycaster();
      this.pointer = new THREE.Vector2();

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(CAMERA_FOV, 1, 0.1, 100);
      this._updateCamera();

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setClearColor(0x000000, 0);
      this.renderer.shadowMap.enabled = true;
      container.appendChild(this.renderer.domElement);

      this.scene.add(new THREE.AmbientLight(0xf4f1eb, 0.62));
      const key = new THREE.DirectionalLight(0xffffff, 0.9);
      key.position.set(2, 12, 8);
      key.castShadow = true;
      this.scene.add(key);
      const rim = new THREE.PointLight(0xc4a574, 0.45, 28);
      rim.position.set(-2, 4, 6);
      this.scene.add(rim);

      this._addTableRing();
      this._addParticles();
      this._resize();
      this._onResize = () => this._resize();
      this._onPointerDown = (e) => this._handlePointer(e);
      this._onPointerMove = (e) => this._handlePointerMove(e);
      window.addEventListener("resize", this._onResize);
      this.renderer.domElement.addEventListener("pointerdown", this._onPointerDown);
      this.renderer.domElement.addEventListener("pointermove", this._onPointerMove);
      this._animate = this._animate.bind(this);
      requestAnimationFrame(this._animate);
    }

    _addTableRing() {
      for (const [radius, opacity] of [[CIRCLE_RADIUS_OUTER, 0.14], [CIRCLE_RADIUS_INNER, 0.1]]) {
        const ring = new THREE.Mesh(
          new THREE.RingGeometry(radius - 0.05, radius + 0.05, 120),
          new THREE.MeshBasicMaterial({
            color: 0xc4a574,
            transparent: true,
            opacity,
            side: THREE.DoubleSide,
          })
        );
        ring.rotation.x = -Math.PI / 2;
        ring.position.set(0, 0.02, CIRCLE_CENTER_Z);
        this.scene.add(ring);
      }

      const inner = new THREE.Mesh(
        new THREE.CircleGeometry(CIRCLE_RADIUS_INNER - 0.06, 120),
        new THREE.MeshBasicMaterial({
          color: 0x0f1714,
          transparent: true,
          opacity: 0.32,
          side: THREE.DoubleSide,
        })
      );
      inner.rotation.x = -Math.PI / 2;
      inner.position.set(0, 0.015, CIRCLE_CENTER_Z);
      this.scene.add(inner);
    }

    _updateCamera() {
      const w = this.container.clientWidth || 640;
      const h = this.container.clientHeight || 480;
      const aspect = w / h;
      const narrow = aspect < 0.92;
      const z = narrow ? CAMERA_BASE.z * 0.88 : CAMERA_BASE.z;
      const y = narrow ? CAMERA_BASE.y * 0.92 : CAMERA_BASE.y + (aspect > 1.2 ? 0.35 : 0);
      this.camera.position.set(CAMERA_BASE.x, y, z);
      this.camera.lookAt(CAMERA_LOOK.x, CAMERA_LOOK.y, CAMERA_LOOK.z);
    }

    _resize() {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight || 480;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this._updateCamera();
      this.renderer.setSize(w, h);
    }

    _addParticles() {
      const count = 80;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        const a = (i / count) * Math.PI * 2;
        const r = CIRCLE_RADIUS_OUTER + 0.25 + Math.random() * 0.35;
        positions[i * 3] = Math.sin(a) * r;
        positions[i * 3 + 1] = 0.05 + Math.random() * 0.12;
        positions[i * 3 + 2] = Math.cos(a) * r + CIRCLE_CENTER_Z;
      }
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      this.particles = new THREE.Points(
        geo,
        new THREE.PointsMaterial({ color: 0xc4a574, size: 0.028, transparent: true, opacity: 0.35 })
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
        new THREE.MeshStandardMaterial({ map: frontTex }),
        new THREE.MeshStandardMaterial({ map: backTex, emissive: 0x000000, emissiveIntensity: 0 }),
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
      mesh.material[4].map = tex;
      mesh.material[4].needsUpdate = true;
    }

    _circleAngleFor(mesh) {
      return mesh.userData.baseAngle + this.circleRotation;
    }

    _circlePose(angle, radius, lift) {
      const r = radius;
      return {
        x: Math.sin(angle) * r,
        y: CIRCLE_Y + lift,
        z: Math.cos(angle) * r + CIRCLE_CENTER_Z,
        ry: -angle + Math.PI,
        rx: -0.05,
      };
    }

    _applyCirclePose(mesh, radiusScale, lift) {
      if (mesh.userData.selected && mesh.userData.drawPose) {
        const p = mesh.userData.drawPose;
        mesh.position.set(p.x, p.y, p.z);
        mesh.rotation.y = p.ry;
        mesh.rotation.x = p.rx ?? -0.08;
        return;
      }
      const baseRadius = mesh.userData.ringRadius || CIRCLE_RADIUS_OUTER;
      const hoverLift = mesh.userData.hoverLift || 0;
      const pose = this._circlePose(
        this._circleAngleFor(mesh),
        baseRadius * radiusScale,
        lift + hoverLift
      );
      mesh.position.set(pose.x, pose.y, pose.z);
      mesh.rotation.y = pose.ry;
      mesh.rotation.x = pose.rx;
    }

    _layoutCircle() {
      const majorMeshes = this.meshes.filter((m) => !m.userData.card?.suit);
      const minorMeshes = this.meshes.filter((m) => m.userData.card?.suit);

      const placeRing = (ringMeshes, radius, innerRing) => {
        ringMeshes.forEach((mesh, i) => {
          mesh.userData.ringRadius = radius;
          mesh.userData.innerRing = innerRing;
          mesh.userData.baseAngle = (i / ringMeshes.length) * Math.PI * 2 - Math.PI / 2;
          mesh.userData.circleIndex = i;
          mesh.userData.drawPose = null;
          mesh.userData.selected = false;
          mesh.userData.selectable = true;
          mesh.userData.hoverLift = 0;
          const ringScale = innerRing ? INNER_RING_SCALE : 1;
          mesh.scale.set(ringScale, ringScale, 1);
          mesh.material[5].emissive.setHex(0x000000);
          mesh.material[5].emissiveIntensity = 0;
          mesh.material.forEach((mat) => {
            mat.transparent = false;
            mat.opacity = 1;
          });
          this._applyCirclePose(mesh, this.circleRadiusScale, 0);
        });
      };

      placeRing(majorMeshes, CIRCLE_RADIUS_OUTER, false);
      placeRing(minorMeshes, CIRCLE_RADIUS_INNER, true);
    }

    buildDeck(catalog) {
      this.clear();
      this.deckData = (catalog || []).slice();
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

    clear() {
      this.meshes.forEach((m) => this.scene.remove(m));
      this.meshes = [];
      this.drawnCards = [];
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.flippedCount = 0;
      this.pickMode = false;
      this.hoveredMesh = null;
      this.circleRotation = 0;
      this.circleRadiusScale = 1;
    }

    _spreadSlots(count) {
      if (count <= 1) return [{ x: 0, y: 0.48, z: 1.55, ry: 0 }];
      if (count === 2) {
        return [
          { x: -1.05, y: 0.44, z: 1.35, ry: 0.12 },
          { x: 1.05, y: 0.44, z: 1.35, ry: -0.12 },
        ];
      }
      return [
        { x: -1.65, y: 0.38, z: 1.15, ry: 0.18 },
        { x: 0, y: 0.52, z: 1.65, ry: 0 },
        { x: 1.65, y: 0.38, z: 1.15, ry: -0.18 },
      ];
    }

    _drawHoldPose(pickIndex) {
      const slots = [
        { x: 0, y: 0.62, z: 1.45, ry: 0, rx: -0.1 },
        { x: -0.92, y: 0.56, z: 1.52, ry: 0.14, rx: -0.1 },
        { x: 0.92, y: 0.56, z: 1.52, ry: -0.14, rx: -0.1 },
      ];
      return slots[pickIndex] || slots[0];
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
      const startRot = this.circleRotation;
      const endRot = startRot + Math.PI * 2 * 2.2;
      const duration = 3200;
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
          this.circleRadiusScale = 1 - Math.sin(ease * Math.PI) * 0.07;
          this.meshes.forEach((mesh) => {
            if (!mesh.userData.selected) {
              const wobble = Math.sin(this._circleAngleFor(mesh) * 3 + ease * Math.PI * 4) * 0.012 * (1 - t);
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
        if (!this.hoveredMesh.userData.selected) {
          this.hoveredMesh.material[5].emissive.setHex(0x000000);
          this.hoveredMesh.material[5].emissiveIntensity = 0;
        }
      }
      this.hoveredMesh = mesh;
      if (mesh && this.pickMode && !mesh.userData.selected) {
        mesh.userData.hoverLift = 0.1;
        mesh.material[5].emissive.setHex(0x8a7348);
        mesh.material[5].emissiveIntensity = 0.22;
      }
    }

    _handlePointerMove(event) {
      if (!this.pickMode) {
        this._setHover(null);
        return;
      }
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      this.raycaster.setFromCamera(this.pointer, this.camera);
      const hits = this.raycaster.intersectObjects(
        this.meshes.filter((m) => m.userData.selectable && !m.userData.selected),
        false
      );
      this._setHover(hits.length ? hits[0].object : null);
    }

    _handlePointer(event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      this.raycaster.setFromCamera(this.pointer, this.camera);
      const hits = this.raycaster.intersectObjects(this.meshes, false);
      if (!hits.length) return;
      const mesh = hits[0].object;

      if (this.pickMode && mesh.userData.selectable) {
        this._togglePick(mesh);
        return;
      }

      if (this.phase === "reveal" && mesh.userData.slot && !mesh.userData.flipped) {
        this.flipCard(mesh.userData.index);
      }
    }

    _animateMeshTo(mesh, target, duration) {
      const token = this._animToken;
      const start = performance.now();
      const from = {
        x: mesh.position.x,
        y: mesh.position.y,
        z: mesh.position.z,
        ry: mesh.rotation.y,
        rx: mesh.rotation.x,
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
          mesh.rotation.y = THREE.MathUtils.lerp(from.ry, target.ry, ease);
          mesh.rotation.x = THREE.MathUtils.lerp(from.rx, target.rx ?? -0.08, ease);
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });
    }

    async _drawCardFromCircle(mesh, pickIndex) {
      const startAngle = this._circleAngleFor(mesh);
      const midR = (mesh.userData.ringRadius || CIRCLE_RADIUS_OUTER) * 0.55;
      const mid = {
        x: Math.sin(startAngle) * midR,
        y: CIRCLE_Y + 0.35,
        z: Math.cos(startAngle) * midR + CIRCLE_CENTER_Z,
        ry: -startAngle + Math.PI,
        rx: -0.12,
      };
      const hold = this._drawHoldPose(pickIndex);
      mesh.userData.drawPose = null;
      await this._animateMeshTo(mesh, mid, 420);
      await this._animateMeshTo(mesh, hold, 520);
      mesh.userData.drawPose = { ...hold };
      mesh.material[5].emissive.setHex(0xc4a574);
      mesh.material[5].emissiveIntensity = 0.38;
    }

    async _returnCardToCircle(mesh) {
      mesh.userData.drawPose = null;
      const pose = this._circlePose(
        this._circleAngleFor(mesh),
        mesh.userData.ringRadius || CIRCLE_RADIUS_OUTER,
        0
      );
      await this._animateMeshTo(mesh, pose, 480);
      mesh.material[5].emissive.setHex(0x000000);
      mesh.material[5].emissiveIntensity = 0;
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
      });

      const fadeStart = performance.now();
      const fadeDuration = 700;
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
              mat.opacity = 1 - t * 0.88;
            });
            mesh.position.y = CIRCLE_Y - t * 0.35;
          });
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });

      unselected.forEach((mesh) => this.scene.remove(mesh));

      const slots = this._spreadSlots(this.selectedMeshes.length);
      this.phase = "spreading";
      this._emitPhase();

      const anims = this.selectedMeshes.map((mesh, i) => {
        mesh.userData.drawPose = null;
        mesh.userData.slot = slots[i];
        mesh.userData.index = i;
        mesh.userData.card = this.drawnCards[i] || mesh.userData.card;
        this._applyFrontTexture(mesh, mesh.userData.card);
        const slot = slots[i];
        return this._animateMeshTo(mesh, {
          x: slot.x,
          y: slot.y,
          z: slot.z,
          ry: slot.ry,
          rx: -0.1,
        }, 900);
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
        }
      });
    }

    _animateFlip(mesh) {
      const duration = 680;
      const start = performance.now();
      const startY = mesh.rotation.y;
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = easeInOutCubic(t);
          mesh.rotation.y = THREE.MathUtils.lerp(startY, Math.PI, ease);
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
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
      if (this.particles) this.particles.rotation.y += 0.0004;

      if (this.phase === "picking" && this.pickMode) {
        this.meshes.forEach((mesh) => {
          if (!mesh.userData.selected && !mesh.userData.drawPose) {
            const lift = Math.sin(now * 0.0018 + mesh.userData.circleIndex * 0.4) * 0.008;
            this._applyCirclePose(mesh, this.circleRadiusScale, lift);
          }
        });
      }

      this.meshes.forEach((mesh, i) => {
        if (this.phase === "reveal" && mesh.userData.slot && !mesh.userData.flipped) {
          mesh.position.y = mesh.userData.slot.y + Math.sin(now * 0.002 + i) * 0.018;
        }
      });

      this.renderer.render(this.scene, this.camera);
    }

    dispose() {
      window.removeEventListener("resize", this._onResize);
      this.renderer.domElement.removeEventListener("pointerdown", this._onPointerDown);
      this.renderer.domElement.removeEventListener("pointermove", this._onPointerMove);
      this.renderer.dispose();
    }
  }

  global.TarotScene = TarotScene;
  global.loadCardFrontTexture = loadCardFrontTexture;
})(window);
