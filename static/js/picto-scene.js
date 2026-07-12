/**
 * 그림마음 3D 장면 — 캔버스 아이소메트릭/입체 일러스트 (Three.js 없이 경량).
 * window.PictoScene.paint(canvas, sceneId, options)
 */
(function (global) {
  const SCENES = {
    // moods
    mood_happy: { sky: ["#ffe9a8", "#ffb347"], ground: "#7ec850", accent: "#ffd54f", symbol: "sun" },
    mood_calm: { sky: ["#c8e6f5", "#a8d5e5"], ground: "#8fbc8f", accent: "#81c784", symbol: "lake" },
    mood_ok: { sky: ["#dfe6ee", "#c5ced8"], ground: "#9aa7b5", accent: "#90a4ae", symbol: "cloud" },
    mood_sad: { sky: ["#8ba4c4", "#5a7290"], ground: "#6b7c8f", accent: "#64b5f6", symbol: "rain" },
    mood_angry: { sky: ["#ff8a65", "#e53935"], ground: "#8d6e63", accent: "#ff5252", symbol: "fire" },
    mood_scared: { sky: ["#7e57c2", "#4527a0"], ground: "#4a3f5c", accent: "#ce93d8", symbol: "storm" },
    mood_tired: { sky: ["#90a4ae", "#607d8b"], ground: "#546e7a", accent: "#b0bec5", symbol: "moon" },
    mood_confused: { sky: ["#b39ddb", "#9575cd"], ground: "#7e57c2", accent: "#e1bee7", symbol: "swirl" },
    // talk
    talk_want_chat: { sky: ["#e3f2fd", "#90caf9"], ground: "#81c784", accent: "#42a5f5", symbol: "speech" },
    talk_want_hug: { sky: ["#fce4ec", "#f8bbd0"], ground: "#a5d6a7", accent: "#f06292", symbol: "hug" },
    talk_want_quiet: { sky: ["#eceff1", "#cfd8dc"], ground: "#b0bec5", accent: "#78909c", symbol: "quiet" },
    talk_want_walk: { sky: ["#fff8e1", "#ffe082"], ground: "#66bb6a", accent: "#ffca28", symbol: "path" },
    talk_want_home: { sky: ["#e8f5e9", "#a5d6a7"], ground: "#81c784", accent: "#ef6c00", symbol: "house" },
    talk_hurt: { sky: ["#ffebee", "#ffcdd2"], ground: "#ef9a9a", accent: "#e53935", symbol: "band" },
    talk_hungry: { sky: ["#fff3e0", "#ffcc80"], ground: "#aed581", accent: "#ff7043", symbol: "fruit" },
    talk_thirsty: { sky: ["#e1f5fe", "#81d4fa"], ground: "#4fc3f7", accent: "#0288d1", symbol: "drop" },
    talk_alone: { sky: ["#eceff1", "#b0bec5"], ground: "#90a4ae", accent: "#607d8b", symbol: "solo" },
    talk_together: { sky: ["#e8f5e9", "#c8e6c9"], ground: "#81c784", accent: "#43a047", symbol: "duo" },
    talk_yes: { sky: ["#e8f5e9", "#a5d6a7"], ground: "#66bb6a", accent: "#2e7d32", symbol: "check" },
    talk_no: { sky: ["#ffebee", "#ef9a9a"], ground: "#e57373", accent: "#c62828", symbol: "cross" },
    talk_stop: { sky: ["#fff3e0", "#ffcc80"], ground: "#ffb74d", accent: "#e65100", symbol: "hand" },
    talk_wait: { sky: ["#e3f2fd", "#bbdefb"], ground: "#90caf9", accent: "#1565c0", symbol: "hour" },
    talk_thanks: { sky: ["#f3e5f5", "#e1bee7"], ground: "#ce93d8", accent: "#8e24aa", symbol: "bow" },
    talk_help_me: { sky: ["#ffebee", "#ffcdd2"], ground: "#ef9a9a", accent: "#d32f2f", symbol: "sos" },
    talk_scared: { sky: ["#ede7f6", "#b39ddb"], ground: "#7e57c2", accent: "#5e35b1", symbol: "storm" },
    talk_bored: { sky: ["#eceff1", "#cfd8dc"], ground: "#9e9e9e", accent: "#757575", symbol: "flat" },
    talk_rest: { sky: ["#e8eaf6", "#9fa8da"], ground: "#5c6bc0", accent: "#3949ab", symbol: "bed" },
    talk_love: { sky: ["#fce4ec", "#f48fb1"], ground: "#f06292", accent: "#e91e63", symbol: "heart" },
    // cards
    card_sun: { sky: ["#fff59d", "#ffb300"], ground: "#ffcc02", accent: "#ff6f00", symbol: "sun" },
    card_moon: { sky: ["#1a237e", "#3949ab"], ground: "#283593", accent: "#c5cae9", symbol: "moon" },
    card_star: { sky: ["#0d1b2a", "#1b3a4b"], ground: "#415a77", accent: "#ffd54f", symbol: "star" },
    card_heart: { sky: ["#fce4ec", "#f48fb1"], ground: "#ef9a9a", accent: "#e91e63", symbol: "heart" },
    card_tree: { sky: ["#e8f5e9", "#81c784"], ground: "#558b2f", accent: "#2e7d32", symbol: "tree" },
    card_path: { sky: ["#fff8e1", "#ffe082"], ground: "#8d6e63", accent: "#ffb300", symbol: "path" },
    // nav / help
    nav_mood: { sky: ["#e8f5e9", "#a5d6a7"], ground: "#66bb6a", accent: "#2e7d32", symbol: "heart" },
    nav_talk: { sky: ["#e3f2fd", "#90caf9"], ground: "#64b5f6", accent: "#1565c0", symbol: "speech" },
    nav_cards: { sky: ["#fff8e1", "#ffe082"], ground: "#ffca28", accent: "#f57f17", symbol: "star" },
    nav_help: { sky: ["#ffebee", "#ef9a9a"], ground: "#e57373", accent: "#c62828", symbol: "sos" },
    nav_history: { sky: ["#e8eaf6", "#9fa8da"], ground: "#7986cb", accent: "#3949ab", symbol: "cal" },
    help_1393: { sky: ["#e3f2fd", "#90caf9"], ground: "#42a5f5", accent: "#0d47a1", symbol: "phone" },
    help_119: { sky: ["#ffebee", "#ef9a9a"], ground: "#e53935", accent: "#b71c1c", symbol: "ambulance" },
    help_129: { sky: ["#e8f5e9", "#a5d6a7"], ground: "#66bb6a", accent: "#1b5e20", symbol: "phone" },
    help_caregiver: { sky: ["#fff3e0", "#ffcc80"], ground: "#ffb74d", accent: "#ef6c00", symbol: "duo" },
  };

  function hexToRgb(hex) {
    const h = (hex || "#888").replace("#", "");
    const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
    return { r: (n >> 16) & 255, g: (n >> 8) & 255, b: n & 255 };
  }

  function shade(hex, amt) {
    const { r, g, b } = hexToRgb(hex);
    const c = (v) => Math.max(0, Math.min(255, v + amt));
    return `rgb(${c(r)},${c(g)},${c(b)})`;
  }

  function isoBox(ctx, x, y, w, h, d, top, left, right) {
    // top
    ctx.beginPath();
    ctx.moveTo(x, y - h);
    ctx.lineTo(x + w, y - h - w * 0.35);
    ctx.lineTo(x + w + d, y - h - w * 0.35 + d * 0.35);
    ctx.lineTo(x + d, y - h + d * 0.35);
    ctx.closePath();
    ctx.fillStyle = top;
    ctx.fill();
    // left
    ctx.beginPath();
    ctx.moveTo(x, y - h);
    ctx.lineTo(x + d, y - h + d * 0.35);
    ctx.lineTo(x + d, y + d * 0.35);
    ctx.lineTo(x, y);
    ctx.closePath();
    ctx.fillStyle = left;
    ctx.fill();
    // right
    ctx.beginPath();
    ctx.moveTo(x + d, y - h + d * 0.35);
    ctx.lineTo(x + w + d, y - h - w * 0.35 + d * 0.35);
    ctx.lineTo(x + w + d, y - w * 0.35 + d * 0.35);
    ctx.lineTo(x + d, y + d * 0.35);
    ctx.closePath();
    ctx.fillStyle = right;
    ctx.fill();
  }

  function drawFigure(ctx, cx, cy, color, scale) {
    const s = scale || 1;
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(cx, cy - 18 * s, 8 * s, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillRect(cx - 5 * s, cy - 10 * s, 10 * s, 16 * s);
    ctx.strokeStyle = shade(color, -40);
    ctx.lineWidth = 2.5 * s;
    ctx.beginPath();
    ctx.moveTo(cx, cy + 6 * s);
    ctx.lineTo(cx - 8 * s, cy + 16 * s);
    ctx.moveTo(cx, cy + 6 * s);
    ctx.lineTo(cx + 8 * s, cy + 16 * s);
    ctx.stroke();
  }

  function drawSymbol(ctx, W, H, symbol, accent) {
    const cx = W * 0.52;
    const cy = H * 0.48;
    ctx.save();
    if (symbol === "sun") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(cx, cy - 10, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      for (let i = 0; i < 8; i++) {
        const a = (i / 8) * Math.PI * 2;
        ctx.beginPath();
        ctx.moveTo(cx + Math.cos(a) * 28, cy - 10 + Math.sin(a) * 28);
        ctx.lineTo(cx + Math.cos(a) * 38, cy - 10 + Math.sin(a) * 38);
        ctx.stroke();
      }
      drawFigure(ctx, cx - 30, cy + 40, "#5d4037", 1.1);
    } else if (symbol === "lake") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.ellipse(cx, cy + 20, 50, 14, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = shade(accent, 40);
      ctx.beginPath();
      ctx.ellipse(cx - 8, cy + 16, 20, 5, 0, 0, Math.PI * 2);
      ctx.fill();
      drawFigure(ctx, cx + 25, cy + 5, "#455a64", 1);
    } else if (symbol === "rain") {
      ctx.fillStyle = "#90a4ae";
      ctx.beginPath();
      ctx.ellipse(cx, cy - 20, 40, 16, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = accent;
      ctx.lineWidth = 2;
      for (let i = 0; i < 6; i++) {
        ctx.beginPath();
        ctx.moveTo(cx - 25 + i * 10, cy);
        ctx.lineTo(cx - 20 + i * 10, cy + 25);
        ctx.stroke();
      }
      drawFigure(ctx, cx, cy + 40, "#37474f", 1);
    } else if (symbol === "fire") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.moveTo(cx, cy + 20);
      ctx.quadraticCurveTo(cx - 30, cy, cx - 10, cy - 30);
      ctx.quadraticCurveTo(cx, cy - 10, cx + 10, cy - 35);
      ctx.quadraticCurveTo(cx + 30, cy, cx, cy + 20);
      ctx.fill();
      drawFigure(ctx, cx - 35, cy + 35, "#3e2723", 1);
    } else if (symbol === "storm") {
      ctx.fillStyle = "#5e35b1";
      ctx.beginPath();
      ctx.ellipse(cx, cy - 15, 42, 18, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.moveTo(cx - 5, cy);
      ctx.lineTo(cx + 12, cy + 5);
      ctx.lineTo(cx - 2, cy + 18);
      ctx.lineTo(cx + 15, cy + 40);
      ctx.lineTo(cx - 18, cy + 12);
      ctx.lineTo(cx + 2, cy + 8);
      ctx.closePath();
      ctx.fill();
    } else if (symbol === "moon") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(cx + 10, cy - 15, 24, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = SCENES.mood_tired.sky[1];
      ctx.beginPath();
      ctx.arc(cx + 20, cy - 18, 18, 0, Math.PI * 2);
      ctx.fill();
      drawFigure(ctx, cx - 20, cy + 35, "#455a64", 0.95);
    } else if (symbol === "swirl") {
      ctx.strokeStyle = accent;
      ctx.lineWidth = 4;
      for (let i = 0; i < 3; i++) {
        ctx.beginPath();
        ctx.arc(cx, cy, 12 + i * 10, 0, Math.PI * 1.5);
        ctx.stroke();
      }
      drawFigure(ctx, cx, cy + 40, "#5e35b1", 1);
    } else if (symbol === "cloud") {
      ctx.fillStyle = "#eceff1";
      ctx.beginPath();
      ctx.arc(cx - 16, cy - 5, 16, 0, Math.PI * 2);
      ctx.arc(cx + 8, cy - 10, 20, 0, Math.PI * 2);
      ctx.arc(cx + 24, cy, 14, 0, Math.PI * 2);
      ctx.fill();
      drawFigure(ctx, cx - 5, cy + 40, "#607d8b", 1);
    } else if (symbol === "speech") {
      isoBox(ctx, cx - 30, cy + 10, 50, 28, 18, "#fff", shade(accent, -20), shade(accent, -40));
      ctx.fillStyle = "#fff";
      ctx.beginPath();
      ctx.moveTo(cx - 10, cy + 10);
      ctx.lineTo(cx - 25, cy + 28);
      ctx.lineTo(cx + 5, cy + 10);
      ctx.fill();
      drawFigure(ctx, cx + 35, cy + 30, "#1565c0", 1);
    } else if (symbol === "hug") {
      drawFigure(ctx, cx - 14, cy + 20, "#ad1457", 1.05);
      drawFigure(ctx, cx + 14, cy + 20, "#6a1b9a", 1.05);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(cx, cy + 8, 22, 0.2, Math.PI - 0.2);
      ctx.stroke();
    } else if (symbol === "quiet") {
      ctx.fillStyle = shade(accent, 30);
      ctx.beginPath();
      ctx.arc(cx, cy, 28, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 28px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("shh", cx, cy + 8);
    } else if (symbol === "path") {
      ctx.fillStyle = "#8d6e63";
      ctx.beginPath();
      ctx.moveTo(cx - 18, cy + 45);
      ctx.lineTo(cx - 6, cy - 20);
      ctx.lineTo(cx + 10, cy - 20);
      ctx.lineTo(cx + 22, cy + 45);
      ctx.closePath();
      ctx.fill();
      drawFigure(ctx, cx, cy + 10, "#5d4037", 1);
    } else if (symbol === "house") {
      isoBox(ctx, cx - 28, cy + 25, 40, 30, 22, "#ffe0b2", "#ef6c00", "#e65100");
      ctx.fillStyle = "#bf360c";
      ctx.beginPath();
      ctx.moveTo(cx - 32, cy - 5);
      ctx.lineTo(cx - 5, cy - 35);
      ctx.lineTo(cx + 38, cy - 10);
      ctx.lineTo(cx + 12, cy + 18);
      ctx.closePath();
      ctx.fill();
    } else if (symbol === "band") {
      drawFigure(ctx, cx, cy + 20, "#c62828", 1.1);
      ctx.fillStyle = "#fff";
      ctx.fillRect(cx - 8, cy - 5, 16, 10);
      ctx.strokeStyle = "#e53935";
      ctx.lineWidth = 2;
      ctx.strokeRect(cx - 8, cy - 5, 16, 10);
    } else if (symbol === "fruit") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(cx, cy + 5, 22, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#2e7d32";
      ctx.fillRect(cx - 2, cy - 22, 4, 12);
    } else if (symbol === "drop") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.moveTo(cx, cy - 28);
      ctx.quadraticCurveTo(cx + 24, cy + 5, cx, cy + 28);
      ctx.quadraticCurveTo(cx - 24, cy + 5, cx, cy - 28);
      ctx.fill();
    } else if (symbol === "solo") {
      drawFigure(ctx, cx, cy + 15, "#546e7a", 1.2);
      ctx.strokeStyle = "rgba(255,255,255,0.35)";
      ctx.lineWidth = 2;
      ctx.setLineDash([4, 4]);
      ctx.strokeRect(cx - 40, cy - 40, 80, 90);
      ctx.setLineDash([]);
    } else if (symbol === "duo") {
      drawFigure(ctx, cx - 16, cy + 18, "#ef6c00", 1.05);
      drawFigure(ctx, cx + 16, cy + 18, "#1565c0", 1.05);
    } else if (symbol === "check") {
      ctx.strokeStyle = accent;
      ctx.lineWidth = 8;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(cx - 22, cy);
      ctx.lineTo(cx - 4, cy + 18);
      ctx.lineTo(cx + 26, cy - 20);
      ctx.stroke();
    } else if (symbol === "cross") {
      ctx.strokeStyle = accent;
      ctx.lineWidth = 8;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(cx - 20, cy - 20);
      ctx.lineTo(cx + 20, cy + 20);
      ctx.moveTo(cx + 20, cy - 20);
      ctx.lineTo(cx - 20, cy + 20);
      ctx.stroke();
    } else if (symbol === "hand") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.roundRect?.(cx - 18, cy - 20, 36, 50, 10);
      if (!ctx.roundRect) ctx.fillRect(cx - 18, cy - 20, 36, 50);
      else ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 22px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("STOP", cx, cy + 8);
    } else if (symbol === "hour") {
      ctx.strokeStyle = accent;
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(cx - 16, cy - 28);
      ctx.lineTo(cx + 16, cy - 28);
      ctx.lineTo(cx + 10, cy);
      ctx.lineTo(cx + 16, cy + 28);
      ctx.lineTo(cx - 16, cy + 28);
      ctx.lineTo(cx - 10, cy);
      ctx.closePath();
      ctx.stroke();
      ctx.fillStyle = shade(accent, 60);
      ctx.fill();
    } else if (symbol === "bow") {
      drawFigure(ctx, cx, cy + 10, "#6a1b9a", 1.1);
      ctx.strokeStyle = accent;
      ctx.lineWidth = 3;
      ctx.beginPath();
      ctx.arc(cx, cy + 30, 18, 0.2, Math.PI - 0.2);
      ctx.stroke();
    } else if (symbol === "sos") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(cx, cy, 30, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#fff";
      ctx.font = "bold 20px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("SOS", cx, cy + 7);
    } else if (symbol === "flat") {
      ctx.fillStyle = accent;
      ctx.fillRect(cx - 35, cy - 8, 70, 16);
      drawFigure(ctx, cx, cy + 30, "#757575", 1);
    } else if (symbol === "bed") {
      isoBox(ctx, cx - 40, cy + 30, 60, 12, 28, "#e8eaf6", "#5c6bc0", "#3949ab");
      drawFigure(ctx, cx - 5, cy + 5, "#1a237e", 0.9);
    } else if (symbol === "heart") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      const x = cx, y = cy;
      ctx.moveTo(x, y + 16);
      ctx.bezierCurveTo(x, y + 6, x - 28, y - 18, x - 28, y - 4);
      ctx.bezierCurveTo(x - 28, y - 22, x, y - 18, x, y - 2);
      ctx.bezierCurveTo(x, y - 18, x + 28, y - 22, x + 28, y - 4);
      ctx.bezierCurveTo(x + 28, y - 18, x, y + 6, x, y + 16);
      ctx.fill();
    } else if (symbol === "star") {
      ctx.fillStyle = accent;
      ctx.beginPath();
      for (let i = 0; i < 5; i++) {
        const a = -Math.PI / 2 + (i * 2 * Math.PI) / 5;
        const b = a + Math.PI / 5;
        ctx.lineTo(cx + Math.cos(a) * 28, cy + Math.sin(a) * 28);
        ctx.lineTo(cx + Math.cos(b) * 12, cy + Math.sin(b) * 12);
      }
      ctx.closePath();
      ctx.fill();
    } else if (symbol === "tree") {
      ctx.fillStyle = "#6d4c41";
      ctx.fillRect(cx - 6, cy + 5, 12, 35);
      ctx.fillStyle = accent;
      ctx.beginPath();
      ctx.arc(cx, cy - 5, 28, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = shade(accent, 30);
      ctx.beginPath();
      ctx.arc(cx - 12, cy - 15, 16, 0, Math.PI * 2);
      ctx.fill();
    } else if (symbol === "phone") {
      isoBox(ctx, cx - 12, cy + 20, 22, 40, 10, "#e3f2fd", accent, shade(accent, -30));
      ctx.fillStyle = "#fff";
      ctx.fillRect(cx - 6, cy - 10, 14, 22);
    } else if (symbol === "ambulance") {
      isoBox(ctx, cx - 40, cy + 25, 55, 22, 24, "#fff", accent, shade(accent, -25));
      ctx.fillStyle = "#fff";
      ctx.font = "bold 18px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("+", cx, cy + 5);
    } else if (symbol === "cal") {
      isoBox(ctx, cx - 28, cy + 20, 45, 35, 16, "#e8eaf6", "#5c6bc0", "#3949ab");
      ctx.fillStyle = "#fff";
      ctx.font = "bold 16px sans-serif";
      ctx.textAlign = "center";
      ctx.fillText("7", cx + 2, cy + 5);
    } else {
      drawFigure(ctx, cx, cy + 15, accent, 1.15);
    }
    ctx.restore();
  }

  function paint(canvas, sceneId, options) {
    const opts = options || {};
    const conf = SCENES[sceneId] || SCENES.mood_ok;
    const dpr = Math.min(2, global.devicePixelRatio || 1);
    const cssW = canvas.clientWidth || opts.width || 160;
    const cssH = canvas.clientHeight || opts.height || 140;
    canvas.width = Math.max(1, Math.floor(cssW * dpr));
    canvas.height = Math.max(1, Math.floor(cssH * dpr));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    const W = cssW;
    const H = cssH;

    const sky = ctx.createLinearGradient(0, 0, 0, H * 0.62);
    sky.addColorStop(0, conf.sky[0]);
    sky.addColorStop(1, conf.sky[1]);
    ctx.fillStyle = sky;
    ctx.fillRect(0, 0, W, H);

    // ground plane (perspective)
    ctx.fillStyle = conf.ground;
    ctx.beginPath();
    ctx.moveTo(0, H * 0.58);
    ctx.lineTo(W, H * 0.52);
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fill();
    ctx.fillStyle = shade(conf.ground, -25);
    ctx.beginPath();
    ctx.moveTo(0, H * 0.72);
    ctx.lineTo(W, H * 0.66);
    ctx.lineTo(W, H);
    ctx.lineTo(0, H);
    ctx.closePath();
    ctx.fill();

    // floating platform
    isoBox(
      ctx,
      W * 0.22,
      H * 0.78,
      W * 0.38,
      H * 0.06,
      W * 0.18,
      shade(conf.ground, 35),
      shade(conf.ground, -10),
      shade(conf.ground, -30)
    );

    drawSymbol(ctx, W, H, conf.symbol, conf.accent);

    // depth vignette
    const vig = ctx.createRadialGradient(W / 2, H / 2, W * 0.2, W / 2, H / 2, W * 0.75);
    vig.addColorStop(0, "rgba(0,0,0,0)");
    vig.addColorStop(1, "rgba(0,0,0,0.18)");
    ctx.fillStyle = vig;
    ctx.fillRect(0, 0, W, H);

    return conf;
  }

  global.PictoScene = { paint, SCENES };
})(typeof window !== "undefined" ? window : globalThis);
