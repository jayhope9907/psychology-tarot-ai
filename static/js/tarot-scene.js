/**
 * Three.js tarot — user shuffle, pick, and flip with card artwork.
 */
(function (global) {
  const CARD_W = 0.72;
  const CARD_H = 1.15;
  const CARD_DEPTH = 0.035;
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

    if (!card?.image_url) {
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

      this.raycaster = new THREE.Raycaster();
      this.pointer = new THREE.Vector2();

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      this.camera.position.set(0, 3.8, 9.5);
      this.camera.lookAt(0, 0.4, 0);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setClearColor(0x000000, 0);
      this.renderer.shadowMap.enabled = true;
      container.appendChild(this.renderer.domElement);

      this.scene.add(new THREE.AmbientLight(0xf4f1eb, 0.6));
      const key = new THREE.DirectionalLight(0xffffff, 0.95);
      key.position.set(4, 10, 6);
      key.castShadow = true;
      this.scene.add(key);
      const rim = new THREE.PointLight(0xc4a574, 0.55, 24);
      rim.position.set(-3, 3, 5);
      this.scene.add(rim);

      this._addParticles();
      this._resize();
      this._onResize = () => this._resize();
      this._onPointerDown = (e) => this._handlePointer(e);
      window.addEventListener("resize", this._onResize);
      this.renderer.domElement.addEventListener("pointerdown", this._onPointerDown);
      this._animate = this._animate.bind(this);
      requestAnimationFrame(this._animate);
    }

    _resize() {
      const w = this.container.clientWidth;
      const h = this.container.clientHeight || 480;
      this.camera.aspect = w / h;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(w, h);
    }

    _addParticles() {
      const count = 160;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 24;
        positions[i * 3 + 1] = Math.random() * 10 - 1;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 16 - 4;
      }
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      this.particles = new THREE.Points(
        geo,
        new THREE.PointsMaterial({ color: 0xc4a574, size: 0.035, transparent: true, opacity: 0.5 })
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
        new THREE.MeshStandardMaterial({ map: backTex }),
      ];
      const mesh = new THREE.Mesh(geo, mats);
      mesh.castShadow = true;
      mesh.userData.card = card;
      mesh.userData.flipped = false;
      mesh.userData.selected = false;
      mesh.userData.selectable = true;
      mesh.rotation.x = -0.15;
      return mesh;
    }

    async _applyFrontTexture(mesh, card) {
      const tex = await loadCardFrontTexture(card);
      mesh.material[4].map = tex;
      mesh.material[4].needsUpdate = true;
    }

    buildDeck(catalog) {
      this.clear();
      this.deckData = (catalog || []).slice();
      this._layoutFan();
      this.phase = "ready";
      this._emitPhase();
    }

    _layoutFan() {
      const total = this.deckData.length;
      const arc = Math.PI * 1.35;
      const start = -arc / 2;
      const radius = 5.2;
      this.deckData.forEach((card, i) => {
        const mesh = this._makeCardMesh(card);
        const t = total <= 1 ? 0.5 : i / (total - 1);
        const angle = start + arc * t;
        mesh.position.set(Math.sin(angle) * radius, 0.15, Math.cos(angle) * radius - 2.8);
        mesh.rotation.y = -angle;
        mesh.userData.fanIndex = i;
        mesh.userData.fanAngle = angle;
        mesh.userData.fanRadius = radius;
        this.scene.add(mesh);
        this.meshes.push(mesh);
      });
    }

    clear() {
      this.meshes.forEach((m) => this.scene.remove(m));
      this.meshes = [];
      this.drawnCards = [];
      this.selectedMeshes = [];
      this.pickedCardIds = [];
      this.flippedCount = 0;
      this.pickMode = false;
    }

    _spreadSlots(count) {
      if (count <= 1) return [{ x: 0, y: 0.35, z: 0.6 }];
      if (count === 2) {
        return [
          { x: -1.1, y: 0.3, z: 0.45 },
          { x: 1.1, y: 0.3, z: 0.45 },
        ];
      }
      return [
        { x: -1.8, y: 0.25, z: 0.2 },
        { x: 0, y: 0.4, z: 0.7 },
        { x: 1.8, y: 0.25, z: 0.2 },
      ];
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
      const duration = 2000;
      const start = performance.now();
      const origins = this.meshes.map((m) => ({
        pos: m.position.clone(),
        rotY: m.rotation.y,
      }));

      await new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = 1 - Math.pow(1 - t, 3);
          this.meshes.forEach((mesh, i) => {
            const angle = ease * Math.PI * 5 + i * 0.35;
            const radius = 2.2 * Math.sin(ease * Math.PI);
            mesh.position.x = Math.cos(angle) * radius;
            mesh.position.z = Math.sin(angle) * radius - 2;
            mesh.position.y = 0.4 + Math.sin(angle * 2) * 0.25;
            mesh.rotation.y = angle;
          });
          if (t < 1) requestAnimationFrame(tick);
          else {
            this.meshes.forEach((mesh, i) => {
              mesh.position.copy(origins[i].pos);
              mesh.rotation.y = origins[i].rotY;
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
        m.userData.selectable = true;
        m.userData.selected = false;
      });
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
        const idx = mesh.userData.index;
        this.flipCard(idx);
      }
    }

    _togglePick(mesh) {
      if (mesh.userData.selected) {
        mesh.userData.selected = false;
        mesh.position.y -= 0.25;
        mesh.material[5].emissive = new THREE.Color(0x000000);
        this.selectedMeshes = this.selectedMeshes.filter((m) => m !== mesh);
        this.pickedCardIds = this.selectedMeshes.map((m) => m.userData.card.id);
        if (this.onPick) this.onPick(this.pickedCardIds.length, this.maxPicks);
        return;
      }
      if (this.selectedMeshes.length >= this.maxPicks) return;

      mesh.userData.selected = true;
      mesh.position.y += 0.25;
      mesh.material[5].emissive = new THREE.Color(0xc4a574);
      mesh.material[5].emissiveIntensity = 0.35;
      this.selectedMeshes.push(mesh);
      this.pickedCardIds = this.selectedMeshes.map((m) => m.userData.card.id);
      if (this.onPick) this.onPick(this.pickedCardIds.length, this.maxPicks);

      if (this.selectedMeshes.length >= this.maxPicks) {
        this.pickMode = false;
        if (this.onPickComplete) this.onPickComplete(this.pickedCardIds.slice());
      }
    }

    pickCardById(cardId) {
      const mesh = this.meshes.find((m) => m.userData.card?.id === cardId && m.userData.selectable);
      if (mesh) this._togglePick(mesh);
    }

    async layoutSelected(cards) {
      this.drawnCards = cards || [];
      const unselected = this.meshes.filter((m) => !m.userData.selected);
      unselected.forEach((mesh) => {
        mesh.userData.selectable = false;
        mesh.position.y -= 0.6;
        mesh.material.forEach((mat) => {
          mat.transparent = true;
          mat.opacity = 0.15;
        });
      });

      const slots = this._spreadSlots(this.selectedMeshes.length);
      this.phase = "spreading";
      this._emitPhase();

      this.selectedMeshes.forEach((mesh, i) => {
        mesh.userData.slot = slots[i];
        mesh.userData.index = i;
        mesh.userData.card = this.drawnCards[i] || mesh.userData.card;
        mesh.rotation.y = 0;
        this._applyFrontTexture(mesh, mesh.userData.card);
      });

      await this._animateToSlots(this.selectedMeshes, slots);
      this.meshes = this.selectedMeshes.slice();
      this.phase = "reveal";
      this._emitPhase();
    }

    _animateToSlots(meshes, slots) {
      const duration = 1200;
      const start = performance.now();
      const origins = meshes.map((m) => m.position.clone());
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = 1 - Math.pow(1 - t, 3);
          meshes.forEach((mesh, i) => {
            const slot = slots[i];
            mesh.position.x = THREE.MathUtils.lerp(origins[i].x, slot.x, ease);
            mesh.position.y = THREE.MathUtils.lerp(origins[i].y, slot.y, ease);
            mesh.position.z = THREE.MathUtils.lerp(origins[i].z, slot.z, ease);
            mesh.rotation.x = THREE.MathUtils.lerp(mesh.rotation.x, -0.12, ease);
          });
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });
    }

    flipCard(index) {
      const mesh = this.meshes[index];
      if (!mesh || mesh.userData.flipped) return Promise.resolve();
      mesh.userData.flipped = true;
      this.flippedCount += 1;
      const card = mesh.userData.card;
      if (this.onCardFlip) this.onCardFlip(card, index);
      return this._animateFlip(mesh).then(() => {
        if (this.flippedCount >= this.meshes.length) {
          this.phase = "complete";
          this._emitPhase();
        }
      });
    }

    _animateFlip(mesh) {
      const duration = 650;
      const start = performance.now();
      const startY = mesh.rotation.y;
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
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
      if (this.particles) this.particles.rotation.y += 0.0007;
      this.meshes.forEach((mesh, i) => {
        if (this.phase === "reveal" && mesh.userData.slot && !mesh.userData.flipped) {
          mesh.position.y = mesh.userData.slot.y + Math.sin(performance.now() * 0.002 + i) * 0.025;
        }
      });
      this.renderer.render(this.scene, this.camera);
    }

    dispose() {
      window.removeEventListener("resize", this._onResize);
      this.renderer.domElement.removeEventListener("pointerdown", this._onPointerDown);
      this.renderer.dispose();
    }
  }

  global.TarotScene = TarotScene;
  global.loadCardFrontTexture = loadCardFrontTexture;
})(window);
