/**
 * Three.js tarot deck — shuffle, spread, flip animations.
 */
(function (global) {
  const CARD_W = 1.4;
  const CARD_H = 2.2;
  const CARD_DEPTH = 0.04;

  function createCardTexture(card, face) {
    const canvas = document.createElement("canvas");
    canvas.width = 512;
    canvas.height = 800;
    const ctx = canvas.getContext("2d");

    if (face === "back") {
      const grad = ctx.createLinearGradient(0, 0, 512, 800);
      grad.addColorStop(0, "#1a2822");
      grad.addColorStop(0.5, "#0f1714");
      grad.addColorStop(1, "#1e2d26");
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, 512, 800);
      ctx.strokeStyle = "#c4a574";
      ctx.lineWidth = 8;
      ctx.strokeRect(24, 24, 464, 752);
      ctx.strokeStyle = "rgba(196,165,116,0.35)";
      ctx.lineWidth = 2;
      for (let i = 0; i < 6; i++) {
        ctx.beginPath();
        ctx.arc(256, 400, 60 + i * 28, 0, Math.PI * 2);
        ctx.stroke();
      }
      ctx.fillStyle = "#c4a574";
      ctx.font = "bold 120px serif";
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText("✦", 256, 400);
      ctx.font = "500 28px 'Noto Sans KR', sans-serif";
      ctx.fillStyle = "rgba(244,241,235,0.7)";
      ctx.fillText("마음쉼터 타로", 256, 520);
    } else {
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
      ctx.font = "bold 140px serif";
      ctx.textAlign = "center";
      ctx.fillText((card && card.symbol) || "✦", 256, 300);
      ctx.font = "600 44px 'Noto Sans KR', sans-serif";
      ctx.fillText((card && card.name_ko) || "타로", 256, 460);
      ctx.font = "400 26px 'Cormorant Garamond', serif";
      ctx.fillStyle = "rgba(244,241,235,0.85)";
      ctx.fillText((card && card.name_en) || "", 256, 520);
      if (card && card.reversed) {
        ctx.save();
        ctx.translate(256, 640);
        ctx.rotate(Math.PI);
        ctx.font = "500 24px 'Noto Sans KR', sans-serif";
        ctx.fillStyle = "rgba(255,200,200,0.9)";
        ctx.fillText("역방향", 0, 0);
        ctx.restore();
      }
      ctx.font = "400 22px 'Noto Sans KR', sans-serif";
      ctx.fillStyle = "rgba(244,241,235,0.75)";
      const kw = ((card && card.keywords_ko) || []).join(" · ");
      ctx.fillText(kw, 256, 620);
    }

    const texture = new THREE.CanvasTexture(canvas);
    texture.anisotropy = 8;
    return texture;
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

      this.scene = new THREE.Scene();
      this.camera = new THREE.PerspectiveCamera(42, 1, 0.1, 100);
      this.camera.position.set(0, 2.2, 7.5);
      this.camera.lookAt(0, 0.2, 0);

      this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
      this.renderer.setClearColor(0x000000, 0);
      this.renderer.shadowMap.enabled = true;
      container.appendChild(this.renderer.domElement);

      this.scene.add(new THREE.AmbientLight(0xf4f1eb, 0.55));
      const key = new THREE.DirectionalLight(0xffffff, 0.9);
      key.position.set(4, 8, 6);
      key.castShadow = true;
      this.scene.add(key);
      const rim = new THREE.PointLight(0xc4a574, 0.6, 20);
      rim.position.set(-3, 2, 4);
      this.scene.add(rim);

      this._addParticles();
      this._resize();
      window.addEventListener("resize", () => this._resize());
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
      const count = 180;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      for (let i = 0; i < count; i++) {
        positions[i * 3] = (Math.random() - 0.5) * 24;
        positions[i * 3 + 1] = Math.random() * 10 - 2;
        positions[i * 3 + 2] = (Math.random() - 0.5) * 16 - 4;
      }
      geo.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      const mat = new THREE.PointsMaterial({
        color: 0xc4a574,
        size: 0.04,
        transparent: true,
        opacity: 0.55,
      });
      this.particles = new THREE.Points(geo, mat);
      this.scene.add(this.particles);
    }

    _makeCardMesh(card, face) {
      const geo = new THREE.BoxGeometry(CARD_W, CARD_H, CARD_DEPTH);
      const frontTex = createCardTexture(card, "front");
      const backTex = createCardTexture(null, "back");
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
      mesh.userData.face = face;
      mesh.userData.targetRotY = 0;
      mesh.userData.targetPos = new THREE.Vector3();
      mesh.userData.flipped = false;
      return mesh;
    }

    buildDeck(catalog) {
      this.clear();
      this.deckData = catalog || [];
      const stack = this.deckData.slice(0, 12);
      stack.forEach((card, i) => {
        const mesh = this._makeCardMesh(card, "back");
        mesh.position.set(0, i * 0.018, -i * 0.01);
        mesh.rotation.x = -0.08;
        mesh.userData.targetPos.copy(mesh.position);
        mesh.userData.stackIndex = i;
        this.scene.add(mesh);
        this.meshes.push(mesh);
      });
      this.phase = "ready";
      this._emitPhase();
    }

    clear() {
      this.meshes.forEach((m) => this.scene.remove(m));
      this.meshes = [];
      this.drawnCards = [];
      this.flippedCount = 0;
    }

    _spreadSlots(count) {
      if (count <= 1) return [{ x: 0, y: 0.2, z: 0.25 }];
      if (count === 2) {
        return [
          { x: -1.5, y: 0.15, z: 0.1 },
          { x: 1.5, y: 0.15, z: 0.1 },
        ];
      }
      return [
        { x: -2.4, y: 0.1, z: 0 },
        { x: 0, y: 0.25, z: 0.3 },
        { x: 2.4, y: 0.1, z: 0 },
      ];
    }

    async shuffle() {
      if (!this.meshes.length) {
        this.phase = "shuffling";
        this._emitPhase();
        await new Promise((resolve) => setTimeout(resolve, 1200));
        this.phase = "ready";
        this._emitPhase();
        return;
      }
      this.phase = "shuffling";
      this._emitPhase();
      const duration = 2200;
      const start = performance.now();
      const origins = this.meshes.map((m) => m.position.clone());

      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = 1 - Math.pow(1 - t, 3);
          this.meshes.forEach((mesh, i) => {
            const angle = ease * Math.PI * 4 + i * 0.4;
            const radius = 1.8 * Math.sin(ease * Math.PI);
            mesh.position.x = Math.cos(angle) * radius;
            mesh.position.z = Math.sin(angle) * radius - 1.5;
            mesh.position.y = origins[i].y + Math.sin(angle * 2) * 0.35;
            mesh.rotation.y = angle;
            mesh.rotation.x = -0.08 + Math.sin(angle) * 0.25;
          });
          if (t < 1) requestAnimationFrame(tick);
          else {
            this.meshes.forEach((mesh, i) => {
              mesh.position.copy(origins[i]);
              mesh.rotation.set(-0.08, 0, 0);
            });
            this.phase = "ready";
            this._emitPhase();
            resolve();
          }
        };
        requestAnimationFrame(tick);
      });
    }

    async spread(drawnCards) {
      this.drawnCards = drawnCards || [];
      if (!this.drawnCards.length) {
        throw new Error("뽑힌 카드가 없습니다.");
      }
      this.clear();
      const count = this.drawnCards.length;
      const slots = this._spreadSlots(count);

      this.phase = "spreading";
      this._emitPhase();

      for (let i = 0; i < count; i++) {
        const card = this.drawnCards[i];
        const mesh = this._makeCardMesh(card, "back");
        const slot = slots[i] || slots[slots.length - 1];
        mesh.position.set(0, 2.5, -2);
        mesh.rotation.x = -0.5;
        mesh.userData.slot = slot;
        mesh.userData.index = i;
        this.scene.add(mesh);
        this.meshes.push(mesh);
      }

      await this._animateSpread(slots.slice(0, count));
      this.phase = "reveal";
      this._emitPhase();
    }

    _animateSpread(slots) {
      const duration = 1400;
      const start = performance.now();
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = 1 - Math.pow(1 - t, 3);
          this.meshes.forEach((mesh, i) => {
            const slot = mesh.userData.slot || slots[i] || { x: 0, y: 0.2, z: 0 };
            mesh.position.x = THREE.MathUtils.lerp(0, slot.x, ease);
            mesh.position.y = THREE.MathUtils.lerp(2.5, slot.y, ease);
            mesh.position.z = THREE.MathUtils.lerp(-2, slot.z, ease);
            mesh.rotation.x = THREE.MathUtils.lerp(-0.5, -0.12, ease);
          });
          if (t < 1) requestAnimationFrame(tick);
          else resolve();
        };
        requestAnimationFrame(tick);
      });
    }

    async flipAll() {
      for (let i = 0; i < this.meshes.length; i++) {
        await this.flipCard(i);
        await new Promise((r) => setTimeout(r, 450));
      }
      this.phase = "complete";
      this._emitPhase();
    }

    flipCard(index) {
      const mesh = this.meshes[index];
      if (!mesh || mesh.userData.flipped) return Promise.resolve();
      mesh.userData.flipped = true;
      mesh.userData.targetRotY = Math.PI;
      this.flippedCount += 1;
      if (this.onCardFlip) this.onCardFlip(mesh.userData.card, index);
      return this._animateFlip(mesh);
    }

    _animateFlip(mesh) {
      const duration = 700;
      const start = performance.now();
      const startY = mesh.rotation.y;
      return new Promise((resolve) => {
        const tick = (now) => {
          const t = Math.min((now - start) / duration, 1);
          const ease = t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
          mesh.rotation.y = THREE.MathUtils.lerp(startY, Math.PI, ease);
          mesh.position.y += Math.sin(t * Math.PI) * 0.004;
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
      if (this.particles) {
        this.particles.rotation.y += 0.0008;
      }
      this.meshes.forEach((mesh, i) => {
        if (this.phase === "reveal" && mesh.userData.slot && !mesh.userData.flipped) {
          mesh.position.y = mesh.userData.slot.y + Math.sin(performance.now() * 0.002 + i) * 0.03;
        }
      });
      this.renderer.render(this.scene, this.camera);
    }

    dispose() {
      window.removeEventListener("resize", () => this._resize());
      this.renderer.dispose();
    }
  }

  global.TarotScene = TarotScene;
})(window);
