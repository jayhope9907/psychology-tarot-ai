/**
 * BlueprintBuilder — real-time emotion-noun → NetworkNode/Edge pipeline.
 *
 * On each user message:
 *   - extractEmotionNouns → contextual emotion nouns (fallback category labels)
 *   - each noun → node linked from center_self
 *   - sch / loose_association high → dashed purple edges + scatter cue
 *   - ASD stimming high → dense local edges around fixation hubs
 *
 * Usage:
 *   BlueprintBuilder.ingest(message, diagnostic, behaviorLog?)
 *   BlueprintBuilder.applyClinicalEffects(diagnostic)
 *   BlueprintBuilder.getGraph()
 *   BlueprintBuilder.reset()
 */
(function () {
  "use strict";

  var CENTER_ID = "center_self";
  var MAX_HISTORY = 40;
  var MAX_NOUNS_PER_TURN = 4;

  var DEPRESSIVE_RE =
    /우울|가라앉|무기력|공허|슬프|희망\s*없|눈물|depress|sad|hopeless|empty/i;
  var AUTONOMIC_RE =
    /불안|초조|긴장|두근|공황|숨\s*막|자율신경|과활성|심박|anxiety|panic|nervous|jitter/i;
  var UNCONSCIOUS_RE =
    /꿈|무의식|환상|해리|와해|파편|연상|망상|이상한\s*생각|fragment|dream|dissoc|delusion/i;

  var EMOTION_NOUNS = [
    "우울", "불안", "공포", "분노", "죄책", "수치", "수치심", "외로움", "고독", "공허",
    "무기력", "절망", "희망", "기쁨", "안도", "긴장", "초조", "공황", "자책", "혐오",
    "질투", "슬픔", "고립", "압박", "스트레스", "피로", "지침", "혼란", "와해", "해리",
    "망상", "환청", "집착", "반복", "루틴", "강박", "자존감", "애착", "거절", "배신",
    "불신", "수치감", "shame", "guilt", "fear", "anger", "sadness", "anxiety", "panic",
    "loneliness", "emptiness", "stress", "fatigue", "obsession", "attachment", "rejection",
  ];

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
      var cp = doc.clinicalProfile || {};
      var sch = Number(cp.schizophrenia_index) || 0;
      var asd = Number(cp.asd_stimming_index) || 0;
      var tm = doc.threeRenderMetrics || {};
      if (!asd && tm.cluster_density) asd = Number(tm.cluster_density) || 0;
      return {
        totalInternalizing: total,
        riskLevel: risk,
        egoBoundaryLoss: sch,
        looseAssociation: sch,
        schizophreniaIndex: sch,
        asdStimmingIndex: asd,
      };
    }

    if (isDsm5(doc)) {
      var spectrum = (doc.dimensions && doc.dimensions.schizophrenia_spectrum) || {};
      var loose = Number(spectrum.loose_association) || 0;
      var ego = Number(spectrum.ego_boundary_loss) || 0;
      return {
        totalInternalizing: Number(doc.total_internalizing_score) || 0,
        riskLevel: doc.internalizing_risk_level || "NORMAL",
        egoBoundaryLoss: ego,
        looseAssociation: loose,
        schizophreniaIndex: (loose + ego) / 2,
        asdStimmingIndex: Number(doc.dimensions && doc.dimensions.obsessive_compulsive) || 0,
      };
    }

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
      schizophreniaIndex: frag,
      asdStimmingIndex: Number(mapping.asd_rigidity) || 0,
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

  function extractEmotionNouns(userChatMessage, behaviorLog, diagnostic) {
    var text = String(userChatMessage || "");
    var found = [];
    var seen = {};
    var lower = text.toLowerCase();

    for (var i = 0; i < EMOTION_NOUNS.length; i++) {
      var noun = EMOTION_NOUNS[i];
      var key = noun.toLowerCase();
      if (seen[key]) continue;
      if (lower.indexOf(key) >= 0 || text.indexOf(noun) >= 0) {
        seen[key] = true;
        found.push(noun);
        if (found.length >= MAX_NOUNS_PER_TURN) break;
      }
    }

    if (!found.length) {
      found.push(extractKeyEmotionWord(userChatMessage, behaviorLog, diagnostic));
    }
    return found;
  }

  function makeCenter() {
    return {
      id: CENTER_ID,
      label: "self",
      val: 20,
      color: "#f8fafc",
      kind: "center",
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

  function buildDenseHubLinks(nodes, hubId, asdIndex, linkColor) {
    var dense = [];
    if (!(asdIndex > 60)) return dense;
    var others = (nodes || []).filter(function (n) {
      return n && n.id !== CENTER_ID && n.id !== hubId;
    });
    var maxExtra = Math.min(8, Math.max(2, Math.floor((asdIndex - 60) / 5)));
    for (var i = 0; i < others.length && dense.length < maxExtra; i++) {
      dense.push({
        source: hubId,
        target: others[i].id,
        color: linkColor || "#06b6d4",
        dashed: false,
        dense: true,
        strength: 0.35 + asdIndex / 200,
      });
    }
    return dense;
  }

  function BlueprintBuilderState() {
    this.seq = 0;
    this.lastLabel = "";
    this.lastLabels = [];
    this.lastDashed = false;
    this.lastBehaviorLog = null;
    this.lastMetrics = null;
    this.graph = { nodes: ensureCenter([]), links: [] };
  }

  BlueprintBuilderState.prototype.buildTurn = function (message, diagnostic, behaviorLog) {
    var metrics = parseBlueprintMetrics(diagnostic);
    var nouns = extractEmotionNouns(message, behaviorLog, diagnostic);
    var val = metrics.totalInternalizing > 70 ? 15 : 8;
    var color = metrics.riskLevel === "HIGH_ALERT" ? "#ff3333" : "#10b981";
    var schHigh = metrics.schizophreniaIndex > 60 || metrics.looseAssociation > 60;
    var linkColor =
      metrics.egoBoundaryLoss > 50 || metrics.schizophreniaIndex > 50 ? "#a855f7" : "#06b6d4";
    var dashed = schHigh;
    var nodes = [];
    var links = [];
    var baseSeq = this.seq;

    for (var i = 0; i < nouns.length; i++) {
      var seq = baseSeq + i;
      var id = "emo_" + seq + "_" + Date.now().toString(36) + "_" + i;
      var angle = (seq % 12) * ((Math.PI * 2) / 12) + i * 0.15;
      var radius = 2.2 + (seq % 5) * 0.35;
      nodes.push({
        id: id,
        label: nouns[i],
        val: val,
        color: color,
        kind: "emotion",
        fixation: /집착|반복|루틴|강박|obsession/i.test(nouns[i]),
        x: Math.cos(angle) * radius,
        y: ((seq + i) % 3) - 1,
        z: Math.sin(angle) * radius,
      });
      links.push({
        source: CENTER_ID,
        target: id,
        color: linkColor,
        dashed: dashed,
        dense: false,
      });
    }

    var hub = nodes.find(function (n) { return n.fixation; }) || nodes[0];
    if (hub && metrics.asdStimmingIndex > 60) {
      var provisional = ensureCenter((this.graph.nodes || []).concat(nodes));
      links = links.concat(
        buildDenseHubLinks(provisional, hub.id, metrics.asdStimmingIndex, "#06b6d4")
      );
      hub.val = Math.max(hub.val, 12 + Math.floor(metrics.asdStimmingIndex / 20));
      hub.color = "#06b6d4";
    }

    this.seq = baseSeq + nouns.length;
    return {
      labels: nouns,
      label: nouns[0] || "",
      nodes: nodes,
      links: links,
      metrics: metrics,
      dashed: dashed,
    };
  };

  BlueprintBuilderState.prototype.ingest = function (message, diagnostic, behaviorLog) {
    var log = behaviorLog != null ? behaviorLog : this.lastBehaviorLog;
    var built = this.buildTurn(message, diagnostic, log);
    this.lastLabel = built.label;
    this.lastLabels = built.labels.slice();
    this.lastDashed = !!built.dashed;
    this.lastMetrics = built.metrics;
    this.graph = capHistory({
      nodes: ensureCenter(this.graph.nodes).concat(built.nodes),
      links: (this.graph.links || []).concat(built.links),
    });

    if (built.metrics && built.metrics.asdStimmingIndex > 60) {
      var hubNode =
        this.graph.nodes.find(function (n) { return n.fixation; }) ||
        this.graph.nodes.filter(function (n) { return n.id !== CENTER_ID; }).slice(-1)[0];
      if (hubNode) {
        var extras = buildDenseHubLinks(
          this.graph.nodes,
          hubNode.id,
          built.metrics.asdStimmingIndex,
          "#06b6d4"
        );
        var existing = {};
        (this.graph.links || []).forEach(function (l) {
          existing[String(l.source) + ">" + String(l.target)] = true;
        });
        for (var e = 0; e < extras.length; e++) {
          var key = String(extras[e].source) + ">" + String(extras[e].target);
          if (!existing[key]) this.graph.links.push(extras[e]);
        }
      }
    }

    return {
      label: built.label,
      labels: built.labels,
      node: built.nodes[0] || null,
      nodes: built.nodes,
      links: built.links,
      link: built.links[0] || null,
      metrics: built.metrics,
    };
  };

  BlueprintBuilderState.prototype.applyClinicalEffects = function (diagnostic) {
    var metrics = parseBlueprintMetrics(diagnostic);
    this.lastMetrics = metrics;
    var schHigh = metrics.schizophreniaIndex > 60 || metrics.looseAssociation > 60;
    var linkColor =
      metrics.egoBoundaryLoss > 50 || metrics.schizophreniaIndex > 50 ? "#a855f7" : "#06b6d4";
    this.lastDashed = schHigh;
    (this.graph.links || []).forEach(function (l) {
      if (l.dense) {
        l.color = "#06b6d4";
        l.dashed = false;
        return;
      }
      if (String(l.source) === CENTER_ID || String(l.target) === CENTER_ID) {
        l.dashed = schHigh;
        l.color = linkColor;
      }
    });
    return this.getGraph();
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
    this.lastLabels = [];
    this.lastDashed = false;
    this.lastBehaviorLog = null;
    this.lastMetrics = null;
    this.graph = { nodes: ensureCenter([]), links: [] };
  };

  BlueprintBuilderState.prototype.getLastStatus = function () {
    var m = this.lastMetrics || {};
    return {
      label: this.lastLabel || "",
      labels: (this.lastLabels || []).slice(),
      dashed: !!this.lastDashed,
      nodeCount: Math.max(0, (this.graph.nodes || []).length - 1),
      linkCount: (this.graph.links || []).length,
      schizophreniaIndex: Number(m.schizophreniaIndex) || 0,
      asdStimmingIndex: Number(m.asdStimmingIndex) || 0,
    };
  };

  var api = new BlueprintBuilderState();
  api.parseBlueprintMetrics = parseBlueprintMetrics;
  api.extractKeyEmotionWord = extractKeyEmotionWord;
  api.extractEmotionNouns = extractEmotionNouns;
  api.CENTER_ID = CENTER_ID;
  api.MAX_HISTORY = MAX_HISTORY;
  api.EMOTION_NOUNS = EMOTION_NOUNS;

  var root = typeof window !== "undefined" ? window : typeof globalThis !== "undefined" ? globalThis : this;
  root.BlueprintBuilder = api;
})();
