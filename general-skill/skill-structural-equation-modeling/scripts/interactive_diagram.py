"""
Generate a self-contained interactive HTML SEM diagram using Cytoscape.js.

Features:
  - Drag any node to reposition
  - Toggle: Full Model (items + errors) ↔ Structural Only (constructs only)
  - Toggle: Standardized ↔ Unstandardized coefficients
  - Export current view as PNG
  - Fit indices shown in toolbar
"""

import json
import os
from collections import defaultdict, deque


# ── HTML template (MODEL_DATA and FIT_TEXT injected at runtime) ──────────────
_HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>SEM Interactive Diagram</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/cytoscape/3.28.1/cytoscape.min.js"></script>
<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
body { font-family: Arial, sans-serif; background: #f0f4f8; height: 100vh; display: flex; flex-direction: column; }

#toolbar {
  background: #1e2d3d;
  padding: 9px 16px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(0,0,0,0.35);
  flex-wrap: wrap;
}
#toolbar h3 { color: #a8d5cf; font-size: 14px; letter-spacing: 0.5px; margin-right: 6px; white-space: nowrap; }

.sep { width: 1px; height: 26px; background: #3a5068; margin: 0 4px; flex-shrink: 0; }

.btn {
  padding: 5px 13px;
  border: 1.5px solid transparent;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
  font-weight: 600;
  transition: all 0.18s;
  white-space: nowrap;
}
.btn-mode  { background: #2e4259; color: #8ba9bf; border-color: #3a5068; }
.btn-mode.active  { background: #3B7A7A; color: #e8f5f5; border-color: #A8D5CF; }
.btn-coeff { background: #2e4259; color: #8ba9bf; border-color: #3a5068; }
.btn-coeff.active { background: #5b4b8a; color: #e8e0f5; border-color: #9b85cc; }
.btn-export { background: #c0392b; color: #fff; border-color: #a93226; margin-left: auto; }
.btn-export:hover { background: #a93226; }
.btn-fit    { background: #2c5f2e; color: #a8d8a8; border-color: #3a7a3c; }
.btn-fit:hover { background: #3a7a3c; }

#fit-box {
  color: #8ba9bf;
  font-size: 11px;
  padding-left: 12px;
  border-left: 1px solid #3a5068;
  line-height: 1.6;
}
#cy { flex: 1; background: #ffffff; }

#hint {
  position: fixed;
  bottom: 10px;
  right: 14px;
  color: #aab;
  font-size: 11px;
  pointer-events: none;
  background: rgba(255,255,255,0.7);
  padding: 3px 7px;
  border-radius: 4px;
}
#legend {
  position: fixed;
  bottom: 10px;
  left: 14px;
  font-size: 11px;
  background: rgba(255,255,255,0.9);
  border: 1px solid #ddd;
  border-radius: 5px;
  padding: 7px 10px;
  line-height: 1.8;
}
.leg-sig   { color: #C0392B; font-weight: bold; }
.leg-ns    { color: #AAAAAA; }
.leg-meas  { color: #3B7A7A; }
</style>
</head>
<body>

<div id="toolbar">
  <h3>⬡ SEM Diagram</h3>

  <button class="btn btn-mode active" id="btn-full"   onclick="setMode('full')">Full Model</button>
  <button class="btn btn-mode"        id="btn-struct" onclick="setMode('structural')">Structural Only</button>

  <div class="sep"></div>

  <button class="btn btn-coeff active" id="btn-std"   onclick="setCoeff('std')">β Standardized</button>
  <button class="btn btn-coeff"       id="btn-unstd" onclick="setCoeff('unstd')">B Unstandardized</button>

  <div class="sep"></div>

  <button class="btn btn-fit" onclick="cy.fit(40)">⊞ Fit View</button>

  <div id="fit-box">FIT_TEXT_PLACEHOLDER</div>

  <button class="btn btn-export" onclick="exportPNG()">↓ Export PNG</button>
</div>

<div id="cy"></div>

<div id="legend">
  <span class="leg-sig">─── Significant path (p&lt;.05)</span><br>
  <span class="leg-ns">─── Non-significant path</span><br>
  <span class="leg-meas">─── Factor loading</span>
</div>

<div id="hint">Drag nodes · Scroll to zoom · Drag background to pan</div>

<script>
const MODEL_DATA = MODEL_DATA_PLACEHOLDER;
let currentMode  = 'full';
let currentCoeff = 'std';

const cy = cytoscape({
  container: document.getElementById('cy'),
  elements:  MODEL_DATA.elements,

  style: [
    // ── Construct oval ────────────────────────────────────────────────────
    {
      selector: '.construct',
      style: {
        'shape': 'ellipse',
        'background-color': '#A8D5CF',
        'border-color': '#3B7A7A',
        'border-width': 2.5,
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'text-wrap': 'wrap',
        'font-size': '13px',
        'font-weight': 'bold',
        'color': '#1a3a3a',
        'width': 130, 'height': 62,
        'z-index': 10,
        'shadow-blur': 6, 'shadow-color': '#b0cece', 'shadow-offset-x': 2, 'shadow-offset-y': 2
      }
    },
    // ── Item rectangle ────────────────────────────────────────────────────
    {
      selector: '.item',
      style: {
        'shape': 'rectangle',
        'background-color': '#ffffff',
        'border-color': '#5D6D7E',
        'border-width': 1.5,
        'label': 'data(label)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '10px',
        'color': '#2c3e50',
        'width': 68, 'height': 27,
        'z-index': 5
      }
    },
    // ── Error circle ──────────────────────────────────────────────────────
    {
      selector: '.error',
      style: {
        'shape': 'ellipse',
        'background-color': '#f4fcfc',
        'border-color': '#A8D5CF',
        'border-width': 1.2,
        'label': 'data(label_std)',
        'text-valign': 'center',
        'text-halign': 'center',
        'font-size': '8px',
        'color': '#5f9ea0',
        'width': 40, 'height': 40,
        'z-index': 3
      }
    },
    // ── Error edge ────────────────────────────────────────────────────────
    {
      selector: '.error_edge',
      style: {
        'line-color': '#A8D5CF',
        'target-arrow-color': '#A8D5CF',
        'target-arrow-shape': 'triangle',
        'curve-style': 'straight',
        'width': 1.0,
        'arrow-scale': 0.65
      }
    },
    // ── Measurement: significant ──────────────────────────────────────────
    {
      selector: '.measurement.sig_meas',
      style: {
        'line-color': '#3B7A7A',
        'target-arrow-color': '#3B7A7A',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'width': 1.5,
        'arrow-scale': 0.75,
        'label': 'data(label_std)',
        'font-size': '8px',
        'color': '#2a5a5a',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.85,
        'text-background-padding': '1px',
        'text-wrap': 'wrap'
      }
    },
    // ── Measurement: non-significant / ref ────────────────────────────────
    {
      selector: '.measurement.nonsig',
      style: {
        'line-color': '#AAAAAA',
        'target-arrow-color': '#AAAAAA',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'width': 1.0,
        'arrow-scale': 0.65,
        'label': 'data(label_std)',
        'font-size': '8px',
        'color': '#999999',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.85,
        'text-background-padding': '1px',
        'text-wrap': 'wrap'
      }
    },
    // ── Structural: significant ───────────────────────────────────────────
    {
      selector: '.structural.sig_struct',
      style: {
        'line-color': '#C0392B',
        'target-arrow-color': '#C0392B',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'width': 3.2,
        'arrow-scale': 1.2,
        'label': 'data(label_std)',
        'font-size': '11px',
        'font-weight': 'bold',
        'color': '#922b21',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.9,
        'text-background-padding': '2px',
        'text-wrap': 'wrap',
        'z-index': 20
      }
    },
    // ── Structural: non-significant ───────────────────────────────────────
    {
      selector: '.structural.nonsig_struct',
      style: {
        'line-color': '#AAAAAA',
        'target-arrow-color': '#AAAAAA',
        'target-arrow-shape': 'triangle',
        'curve-style': 'bezier',
        'width': 2.0,
        'arrow-scale': 1.0,
        'label': 'data(label_std)',
        'font-size': '11px',
        'color': '#999999',
        'text-background-color': '#ffffff',
        'text-background-opacity': 0.9,
        'text-background-padding': '2px',
        'text-wrap': 'wrap',
        'z-index': 20
      }
    }
  ],

  layout: { name: 'preset' },
  userZoomingEnabled:  true,
  userPanningEnabled:  true,
  boxSelectionEnabled: false
});

// ── Mode toggle ──────────────────────────────────────────────────────────────
function setMode(mode) {
  currentMode = mode;
  document.getElementById('btn-full').classList.toggle('active', mode === 'full');
  document.getElementById('btn-struct').classList.toggle('active', mode === 'structural');
  if (mode === 'structural') {
    cy.elements('.item, .error, .error_edge, .measurement').hide();
  } else {
    cy.elements('.item, .error, .error_edge, .measurement').show();
  }
}

// ── Coefficient toggle ───────────────────────────────────────────────────────
function setCoeff(coeff) {
  currentCoeff = coeff;
  document.getElementById('btn-std').classList.toggle('active',   coeff === 'std');
  document.getElementById('btn-unstd').classList.toggle('active', coeff === 'unstd');

  const labelKey = coeff === 'std' ? 'label_std' : 'label_unstd';
  const errKey   = coeff === 'std' ? 'label_std' : 'label_unstd';

  cy.elements('.measurement').style('label', ele => ele.data(labelKey));
  cy.elements('.structural').style('label',  ele => ele.data(labelKey));
  cy.elements('.error').style('label',       ele => ele.data(errKey));
}

// ── Export PNG ───────────────────────────────────────────────────────────────
function exportPNG() {
  const uri = cy.png({ scale: 2.5, bg: 'white', full: true, output: 'base64uri' });
  const a   = document.createElement('a');
  a.href     = uri;
  a.download = 'sem_diagram.png';
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
}

// ── Linked movement: drag construct → items + errors follow ──────────────────
const _prevPos = {};

cy.on('grab', '.construct', evt => {
  const n = evt.target;
  _prevPos[n.id()] = { x: n.position('x'), y: n.position('y') };
});

cy.on('drag', '.construct', evt => {
  const n  = evt.target;
  const id = n.id();
  if (!_prevPos[id]) return;

  const dx = n.position('x') - _prevPos[id].x;
  const dy = n.position('y') - _prevPos[id].y;
  if (dx === 0 && dy === 0) return;

  // Move all items belonging to this construct
  cy.nodes('.item')
    .filter(node => node.data('construct') === id)
    .forEach(item => item.shift({ x: dx, y: dy }));

  // Move all errors whose item belongs to this construct
  cy.nodes('.error')
    .filter(node => {
      const owner = cy.getElementById(node.data('item'));
      return owner.length > 0 && owner.data('construct') === id;
    })
    .forEach(err => err.shift({ x: dx, y: dy }));

  _prevPos[id] = { x: n.position('x'), y: n.position('y') };
});

cy.on('free', '.construct', evt => {
  delete _prevPos[evt.target.id()];
});

cy.fit(50);
</script>
</body>
</html>
"""


def generate(params, model_spec: str, output_path: str,
             stats_df=None, std_ests: bool = True) -> None:
    """
    Build a self-contained interactive HTML SEM diagram and write to output_path.

    Parameters
    ----------
    params      : semopy inspect() DataFrame (std_est=True)
    model_spec  : semopy model specification string
    output_path : where to write the .html file
    stats_df    : calc_stats() DataFrame (optional, for fit indices)
    std_ests    : if True use 'Est. Std' column, else 'Estimate'
    """
    # ── Parse spec ────────────────────────────────────────────────────────────
    latent_vars, measurement_map = [], {}
    for line in model_spec.strip().split("\n"):
        line = line.strip()
        if "=~" in line:
            lv, items_str = line.split("=~", 1)
            lv    = lv.strip()
            items = [i.strip() for i in items_str.split("+")]
            latent_vars.append(lv)
            measurement_map[lv] = items
    latent_set = set(latent_vars)
    est_col = "Est. Std" if std_ests else "Estimate"

    structural = params[
        (params["op"] == "~") &
        (params["lval"].isin(latent_set)) &
        (params["rval"].isin(latent_set))
    ]

    # ── Param helpers ─────────────────────────────────────────────────────────
    def pval(lval, rval):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            return float(row["p-value"].values[0])
        except (TypeError, ValueError):
            return None

    def pcol(lval, rval, col):
        row = params[(params["lval"] == lval) & (params["rval"] == rval)]
        if len(row) == 0:
            return None
        try:
            v = row[col].values[0]
            return None if str(v) in ("-", "", "nan") else float(v)
        except (TypeError, ValueError):
            return None

    def stars(p):
        if p is None:
            return ""
        return "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else ""))

    def edge_label(b, se, p, is_ref=False):
        if b is None:
            return ""
        s = stars(p)
        se_str = f"\nSE={se:.3f}" if se is not None else ""
        if is_ref:
            return f"β={b:.3f}(ref)"
        return f"β={b:.3f}{s}{se_str}"

    # Residual variances
    ev_std, ev_unstd = {}, {}
    for _, row in params[params["op"] == "~~"].iterrows():
        if row["lval"] == row["rval"]:
            try:
                ev_std[row["lval"]]   = round(float(row["Est. Std"]), 3)
                ev_unstd[row["lval"]] = round(float(row["Estimate"]), 3)
            except (TypeError, ValueError, KeyError):
                pass

    # ── Topological sort → positions ─────────────────────────────────────────
    adj    = defaultdict(list)
    in_deg = {lv: 0 for lv in latent_vars}
    for _, row in structural.iterrows():
        pred, out = row["rval"], row["lval"]
        if pred in latent_set and out in latent_set:
            adj[pred].append(out)
            in_deg[out] += 1

    level  = {lv: 0 for lv in latent_vars if in_deg[lv] == 0}
    queue  = deque(level.keys())
    while queue:
        node = queue.popleft()
        for child in adj[node]:
            level[child] = max(level.get(child, 0), level[node] + 1)
            in_deg[child] -= 1
            if in_deg[child] == 0:
                queue.append(child)
    for lv in latent_vars:
        level.setdefault(lv, 0)

    level_groups = defaultdict(list)
    for lv in latent_vars:
        level_groups[level[lv]].append(lv)

    # Pixel positions (Cytoscape uses px)
    LV_H  = 420   # horizontal gap between construct levels
    LV_V  = 260   # vertical gap between constructs at same level
    IT_H  = 130   # horizontal gap between items within construct
    IT_V  = 130   # construct → items drop
    ER_V  = 85    # items → ε drop

    c_pos = {}
    for lvl, nodes in sorted(level_groups.items()):
        n  = len(nodes)
        ys = [-(n - 1) * LV_V / 2 + i * LV_V for i in range(n)]
        for node, y in zip(nodes, ys):
            c_pos[node] = (lvl * LV_H, y)

    i_pos = {}
    for lv, items in measurement_map.items():
        cx, cy_ = c_pos[lv]
        n  = len(items)
        xs = [cx - (n - 1) * IT_H / 2 + i * IT_H for i in range(n)]
        for item, x in zip(items, xs):
            i_pos[item] = (x, cy_ + IT_V)

    # ── Build Cytoscape elements ──────────────────────────────────────────────
    elements = []

    # Construct nodes
    for lv in latent_vars:
        x, y = c_pos[lv]
        n_it = len(measurement_map.get(lv, []))
        elements.append({
            "data":     {"id": lv, "label": f"{lv}\n({n_it} items)", "type": "construct"},
            "position": {"x": x, "y": y},
            "classes":  "construct"
        })

    # Item + error nodes + measurement edges
    for lv, items in measurement_map.items():
        for i, item in enumerate(items):
            ix, iy  = i_pos[item]
            is_ref  = (i == 0)
            p       = pval(item, lv)
            b_std   = pcol(item, lv, "Est. Std")
            b_unst  = pcol(item, lv, "Estimate")
            se      = pcol(item, lv, "Std. Err")
            sig     = (is_ref) or (p is not None and p < 0.05)

            # Item node
            elements.append({
                "data":     {"id": item, "label": item, "type": "item", "construct": lv},
                "position": {"x": ix, "y": iy},
                "classes":  "item"
            })

            # Error node
            err = f"e_{item}"
            es  = ev_std.get(item, "")
            eu  = ev_unstd.get(item, "")
            elements.append({
                "data": {
                    "id": err, "type": "error", "item": item,
                    "label_std":   f"ε={es}" if es != "" else "ε",
                    "label_unstd": f"ε={eu}" if eu != "" else "ε"
                },
                "position": {"x": ix, "y": iy + ER_V},
                "classes": "error"
            })

            # Error → item edge
            elements.append({
                "data":    {"id": f"eedge_{item}", "source": err, "target": item, "type": "error_edge"},
                "classes": "error_edge"
            })

            # Construct → item (measurement)
            lbl_std  = edge_label(b_std,  se, p, is_ref)
            lbl_unst = edge_label(b_unst, se, p, is_ref)
            elements.append({
                "data": {
                    "id": f"meas_{lv}_{item}",
                    "source": lv, "target": item, "type": "measurement",
                    "label_std": lbl_std, "label_unstd": lbl_unst,
                    "sig": sig, "is_ref": is_ref
                },
                "classes": f"measurement {'sig_meas' if sig else 'nonsig'}"
            })

    # Structural edges
    for _, row in structural.iterrows():
        out, pred = row["lval"], row["rval"]
        p      = pval(out, pred)
        b_std  = pcol(out, pred, "Est. Std")
        b_unst = pcol(out, pred, "Estimate")
        se     = pcol(out, pred, "Std. Err")
        sig    = p is not None and p < 0.05
        elements.append({
            "data": {
                "id": f"struct_{pred}_{out}",
                "source": pred, "target": out, "type": "structural",
                "label_std":   edge_label(b_std,  se, p),
                "label_unstd": edge_label(b_unst, se, p),
                "sig": sig
            },
            "classes": f"structural {'sig_struct' if sig else 'nonsig_struct'}"
        })

    # ── Fit indices ───────────────────────────────────────────────────────────
    fit_info = {}
    fit_text = ""
    if stats_df is not None:
        try:
            fit_info = {
                "chi2":  round(float(stats_df.loc["Value", "chi2"]), 2),
                "df":    int(float(stats_df.loc["Value", "DoF"])),
                "p":     round(float(stats_df.loc["Value", "chi2 p-value"]), 3),
                "CFI":   round(float(stats_df.loc["Value", "CFI"]), 3),
                "TLI":   round(float(stats_df.loc["Value", "TLI"]), 3),
                "RMSEA": round(float(stats_df.loc["Value", "RMSEA"]), 3),
            }
            fit_text = (f"χ²({fit_info['df']})={fit_info['chi2']}, p={fit_info['p']} &nbsp;|&nbsp; "
                        f"CFI={fit_info['CFI']} &nbsp;|&nbsp; "
                        f"TLI={fit_info['TLI']} &nbsp;|&nbsp; "
                        f"RMSEA={fit_info['RMSEA']}")
        except Exception:
            pass

    model_data = {"elements": elements, "fit": fit_info}

    # ── Write HTML ────────────────────────────────────────────────────────────
    html = _HTML
    html = html.replace("MODEL_DATA_PLACEHOLDER", json.dumps(model_data, indent=2))
    html = html.replace("FIT_TEXT_PLACEHOLDER",   fit_text)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"  Interactive diagram saved: {output_path}")
