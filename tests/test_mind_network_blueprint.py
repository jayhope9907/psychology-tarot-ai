"""Smoke tests for BlueprintBuilder emotion-noun → center_self edge pipeline."""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BB_JS = ROOT / "static" / "js" / "blueprint-builder.js"
MN_JS = ROOT / "static" / "js" / "mind-network-3d.js"
CHAT = ROOT / "static" / "chat.html"


def test_blueprint_builder_file_has_realtime_noun_api():
    text = BB_JS.read_text(encoding="utf-8")
    assert "extractEmotionNouns" in text
    assert "center_self" in text
    assert "applyClinicalEffects" in text
    assert "asdStimmingIndex" in text
    assert "buildDenseHubLinks" in text


def test_mind_network_draws_graph_edges():
    text = MN_JS.read_text(encoding="utf-8")
    assert "setGraph" in text
    assert "LineDashedMaterial" in text
    assert "center_self" in text
    assert "resetOrbit" in text
    assert "setAutoRotate" in text
    assert "schFragmentation" in text
    assert "fixation" in text


def test_chat_clinician_viewer_wired():
    text = CHAT.read_text(encoding="utf-8")
    assert "임상의 3D 무의식 도면" in text
    assert "ingestBlueprintRealtime" in text
    assert "syncMindNetworkGraph" in text
    assert "maybeOfferClinicianMindNetwork" in text
    assert "mn3dResetOrbit" in text
    assert "mn3dAutoRotate" in text
    assert "mn-live" in text
    assert "#mind-network" in text
    assert "mind-network-3d.js?v=2" in text


@pytest.mark.skipif(not shutil.which("node"), reason="node not available")
def test_blueprint_builder_runtime_nouns_and_clinical():
    script = r"""
const fs = require('fs');
const vm = require('vm');
const src = fs.readFileSync(process.argv[2], 'utf8');
const ctx = { console, window: {} };
vm.createContext(ctx);
vm.runInContext(src, ctx);
const BB = ctx.window.BlueprintBuilder;
const nouns = BB.extractEmotionNouns('요즘 불안과 우울이 반복되고 집착이 커져요');
if (!nouns.includes('불안') || !nouns.includes('우울')) process.exit(2);
BB.reset();
const schDoc = {
  clinicalProfile: { schizophrenia_index: 72, asd_stimming_index: 20, depression_index: 40 },
  threeRenderMetrics: { backbone_tension: 50, cluster_density: 20 },
  internalizing_core: { total_internalizing_score: 55, internalizing_risk_level: 'MONITOR' },
};
BB.ingest('와해되는 느낌과 불안', schDoc, {});
const g1 = BB.getGraph();
if (!g1.nodes.some(n => n.id === 'center_self')) process.exit(3);
if (!g1.links.some(l => l.dashed)) process.exit(4);

BB.reset();
const asdDoc = {
  clinicalProfile: { schizophrenia_index: 10, asd_stimming_index: 78, depression_index: 20 },
  threeRenderMetrics: { backbone_tension: 40, cluster_density: 78 },
  internalizing_core: { total_internalizing_score: 40, internalizing_risk_level: 'NORMAL' },
};
BB.ingest('불안', asdDoc, {});
BB.ingest('집착과 반복 루틴', asdDoc, {});
const g2 = BB.getGraph();
if (!g2.links.some(l => l.dense)) process.exit(5);
console.log(JSON.stringify({ nouns, n1: g1.nodes.length, e1: g1.links.length, n2: g2.nodes.length, dense: g2.links.filter(l=>l.dense).length }));
"""
    with tempfile.NamedTemporaryFile("w", suffix=".cjs", delete=False, encoding="utf-8") as fh:
        fh.write(script)
        runner = fh.name
    try:
        proc = subprocess.run(
            ["node", runner, str(BB_JS)],
            capture_output=True,
            timeout=20,
            check=False,
        )
    finally:
        Path(runner).unlink(missing_ok=True)
    stdout = (proc.stdout or b"").decode("utf-8", errors="replace")
    stderr = (proc.stderr or b"").decode("utf-8", errors="replace")
    assert proc.returncode == 0, stderr or stdout
    payload = json.loads(stdout.strip().splitlines()[-1])
    assert "불안" in payload["nouns"]
    assert payload["dense"] >= 1
