/**
 * BlueprintBuilder (vanilla port of static/hooks/use3DBlueprintBuilder.ts)
 *
 * On each user message:
 *   - extractKeyEmotionWord → 우울 궤적 / 자율신경 과활성 / 무의식 조각
 *   - NetworkNode sized by total_internalizing_score (>70 → val 15 else 8)
 *   - color HIGH_ALERT → #ff3333 else #10b981
 *   - link from center_self; ego_boundary_loss > 50 → #a855f7 else #06b6d4
 *   - dashed if loose_association > 60
 *
 * Usage:
 *   BlueprintBuilder.ingest(message, diagnostic, behaviorLog?)
 *   BlueprintBuilder.getGraph()
 *   BlueprintBuilder.reset()
 */
(function () {
  "use strict";

  var CENTER_ID = "center_self";
  var MAX_HISTORY = 40;

  var DEPRESSIVE_RE =
    /우울|가라앉|무기력|공허|슬프|희망\s*없|눈물|depress|sad|hopeless|empty/i;
  var AUTONOMIC_RE =
    /불안|초조|긴장|두근|공황|숨\s*막|자율신경|과활성|심박|anxiety|panic|nervous|jitter/i;
  var UNCONSCIOUS_RE =
    /꿈|무의식|환상|해리|와해|파편|연상|망상|이상한\s*생각|fragment|dream|dissoc|delusion/i;

  function isIntegratedModel(data) {
    return !!(data && typeof data === "object" && data.clinicalProfile);
  }

  function isDsm5(data) {
    return !!(
      data &&
      typeof data === "object" &&
      "total_internalizing_score" in data &&
      data.dimensions
    );
  }

  function parseBlueprintMetrics(diagnostic) {
    var doc = diagnostic || {};

    if (isIntegratedModel(doc)) {
      var core = doc.internalizing_core || {};
      var total =
        Number(core.total_internalizing_score) ||
        Number(doc.total_internalizing_score) ||
        0;
      var risk =
        core.internalizing_risk_level ||
        (total > 70 ? "HIGH_ALERT" : total > 40 ? "MONITOR" : "NORMAL");
      var sch = Number((doc.clinicalProfile || {}).schizophrenia_index) || 0;
      return {
        totalInternalizing: total,
        riskLevel: risk,
        egoBoundaryLoss: sch,
        looseAssociation: sch,
      };
    }

    if (isDsm5(doc)) {
      var spectrum = (doc.dimensions && doc.dimensions.schizophrenia_spectrum) || {};
      return {
        totalInternalizing: Number(doc.total_internalizing_score) || 0,
        riskLevel: doc.internalizing_risk_level || "NORMAL",
        egoBoundaryLoss: Number(spectrum.ego_boundary_loss) || 0,
        looseAssociation: Number(spectrum.loose_association) || 0,
      };
    }

    // neurodevelopmental_matrix / unknown
    var mapping = doc.spectrum_mapping || {};
    var frag =
      Number(mapping.cognitive_fragmentation) ||
      Number(doc.cognitive_disorganization_score) ||
      0;
    var totalLoose =
      Number(doc.total_internalizing_score) ||
      (doc.internalizing_core && Number(doc.internalizing_core.total_internalizing_score)) ||
      frag;
    var riskLoose =
      doc.internalizing_risk_level ||
      (totalLoose > 70 ? "HIGH_ALERT" : totalLoose > 40 ? "MONITOR" : "NORMAL");

    return {
      totalInternalizing: totalLoose,
      riskLevel: riskLoose,
      egoBoundaryLoss: frag,
      looseAssociation: frag,
    };
  }

  function extractKeyEmotionWord(userChatMessage, behaviorLog, diagnostic) {
    var text = String(userChatMessage || "");
    var metrics = parseBlueprintMetrics(diagnostic);
    var log = behaviorLog || {};
    var hesitation = Number(log.hesitation_index) || 0;
    var backspaces = Number(log.backspace_count) || 0;

    if (UNCONSCIOUS_RE.test(text) || metrics.looseAssociation > 55 || metrics.egoBoundaryLoss > 55) {
      return "무의식 조각";
    }
    if (AUTONOMIC_RE.test(text) || hesitation > 0.45 || backspaces >= 8) {
      return "자율신경 과활성";
    }
    if (DEPRESSIVE_RE.test(text) || metrics.totalInternalizing > 55) {
      return "우울 궤적";
    }
    if (metrics.egoBoundaryLoss >= metrics.totalInternalizing) return "무의식 조각";
    if (hesitation > 0.25) return "자율신경 과활성";
    return "우울 궤적";
  }

  function makeCenter() {
    return {
      id: CENTER_ID,
      label: "self",
      val: 20,
      color: "#f8fafc",
      x: 0,
      y: 0,
      z: 0,
    };
  }

  function ensureCenter(nodes) {
    var list = Array.isArray(nodes) ? nodes.slice() : [];
    if (list.some(function (n) { return n && n.id === CENTER_ID; })) return list;
    return [makeCenter()].concat(list);
  }

  function capHistory(graph) {
    var nodes = ensureCenter(graph.nodes || []);
    var links = Array.isArray(graph.links) ? graph.links.slice() : [];
    var center = nodes.filter(function (n) { return n.id === CENTER_ID; })[0];
    var others = nodes.filter(function (n) { return n.id !== CENTER_ID; });
    if (others.length <= MAX_HISTORY) {
      return { nodes: ensureCenter(nodes), links: links };
    }
    var kept = others.slice(-MAX_HISTORY);
    var keepIds = {};
    keepIds[CENTER_ID] = true;
    for (var i = 0; i < kept.length; i++) keepIds[kept[i].id] = true;
    var filteredLinks = links.filter(function (l) {
      return keepIds[String(l.source)] && keepIds[String(l.target)];
    });
    return {
      nodes: ensureCenter(center ? [center].concat(kept) : kept),
      links: filteredLinks,
    };
  }

  function BlueprintBuilderState() {
    this.seq = 0;
    this.lastLabel = "";
    this.lastDashed = false;
    this.lastBehaviorLog = null;
    this.graph = { nodes: ensureCenter([]), links: [] };
  }

  BlueprintBuilderState.prototype.build = function (message, diagnostic, behaviorLog) {
    var metrics = parseBlueprintMetrics(diagnostic);
    var label = extractKeyEmotionWord(message, behaviorLog, diagnostic);
    var val = metrics.totalInternalizing > 70 ? 15 : 8;
    var color = metrics.riskLevel === "HIGH_ALERT" ? "#ff3333" : "#10b981";
    var linkColor = metrics.egoBoundaryLoss > 50 ? "#a855f7" : "#06b6d4";
    var dashed = metrics.looseAssociation > 60;
    var seq = this.seq++;
    var id = "emo_" + seq + "_" + Date.now().toString(36);
    var angle = (seq % 12) * ((Math.PI * 2) / 12);
    var radius = 2.2 + (seq % 5) * 0.35;

    return {
      label: label,
      node: {
        id: id,
        label: label,
        val: val,
        color: color,
        x: Math.cos(angle) * radius,
        y: (seq % 3) - 1,
        z: Math.sin(angle) * radius,
      },
      link: {
        source: CENTER_ID,
        target: id,
        color: linkColor,
        dashed: dashed,
      },
    };
  };

  BlueprintBuilderState.prototype.ingest = function (message, diagnostic, behaviorLog) {
    var log = behaviorLog != null ? behaviorLog : this.lastBehaviorLog;
    var built = this.build(message, diagnostic, log);
    this.lastLabel = built.label;
    this.lastDashed = !!built.link.dashed;
    this.graph = capHistory({
      nodes: ensureCenter(this.graph.nodes).concat([built.node]),
      links: (this.graph.links || []).concat([built.link]),
    });
    return built;
  };

  BlueprintBuilderState.prototype.rememberBehavior = function (behaviorLog) {
    this.lastBehaviorLog = behaviorLog || null;
  };

  BlueprintBuilderState.prototype.getGraph = function () {
    return {
      nodes: (this.graph.nodes || []).slice(),
      links: (this.graph.links || []).slice(),
    };
  };

  BlueprintBuilderState.prototype.reset = function () {
    this.seq = 0;
    this.lastLabel = "";
    this.lastDashed = false;
    this.lastBehaviorLog = null;
    this.graph = { nodes: ensureCenter([]), links: [] };
  };

  BlueprintBuilderState.prototype.getLastStatus = function () {
    return {
      label: this.lastLabel || "",
      dashed: !!this.lastDashed,
      nodeCount: Math.max(0, (this.graph.nodes || []).length - 1),
    };
  };

  var api = new BlueprintBuilderState();
  api.parseBlueprintMetrics = parseBlueprintMetrics;
  api.extractKeyEmotionWord = extractKeyEmotionWord;
  api.CENTER_ID = CENTER_ID;
  api.MAX_HISTORY = MAX_HISTORY;

  var root = typeof window !== "undefined" ? window : typeof globalThis !== "undefined" ? globalThis : this;
  root.BlueprintBuilder = api;
})();
