import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

const VERSION = "0.9.1";
const PUSH_DEBOUNCE_MS = 800;
const HEARTBEAT_INTERVAL_MS = 10_000;
const POLL_PUSH_INTERVAL_MS = 3_000;

function genId(prefix) {
    if (crypto.randomUUID) return crypto.randomUUID();
    return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2)}`;
}

// boot_id is per-page-load (NOT persisted). Used to detect when two tabs share
// the same sessionStorage tab_id (browser tab-duplication / session-restore copies it).
const bootId = genId("boot");

// sessionStorage is per-tab — but the browser COPIES it on duplicate-tab and
// session-restore-of-a-duplicated-session. The server detects that via boot_id
// mismatch and tells us to regenerate.
let tabId = sessionStorage.getItem("mcp_bridge.tab_id");
if (!tabId) {
    tabId = genId("tab");
    sessionStorage.setItem("mcp_bridge.tab_id", tabId);
}

function regenerateTabId() {
    const oldId = tabId;
    tabId = genId("tab");
    sessionStorage.setItem("mcp_bridge.tab_id", tabId);
    console.log(`[mcp_bridge] tab_id collision; regenerated ${oldId} -> ${tabId}`);
}

const trustAgent = localStorage.getItem("mcp_bridge.trust") !== "false";
let pushTimer = null;
let lastSig = null;

function buildLabel(workflow) {
    const nodes = workflow?.nodes || [];
    const types = {};
    for (const n of nodes) {
        if (n.type) types[n.type] = (types[n.type] || 0) + 1;
    }
    const top_types = Object.entries(types)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 6)
        .map(([t, c]) => (c > 1 ? `${t}×${c}` : t));

    let prompt_preview = null;
    const PROMPTY = new Set(["CLIPTextEncode", "CLIPTextEncodeSDXL", "TextEncodeAceStepAudio1.5", "PromptText", "Text", "ImpactWildcardEncode"]);
    for (const n of nodes) {
        if (PROMPTY.has(n.type)) {
            const wv = n.widgets_values || [];
            for (const v of wv) {
                if (typeof v === "string" && v.trim().length > 0) {
                    prompt_preview = v.slice(0, 100).replace(/\s+/g, " ").trim();
                    break;
                }
            }
            if (prompt_preview) break;
        }
    }

    return {
        title: document.title || null,
        url: location.host + location.pathname + (location.hash || ""),
        node_count: nodes.length,
        top_types,
        prompt_preview,
    };
}

async function buildPayload() {
    const workflow = app.graph.serialize();
    let api_workflow = null;
    try {
        const result = await app.graphToPrompt();
        api_workflow = result.output;
    } catch (e) {
        // graph not currently valid; UI format still useful
    }
    return {
        tab_id: tabId,
        boot_id: bootId,
        comfy_client_id: api.clientId,
        workflow,
        api_workflow,
        label: buildLabel(workflow),
    };
}

async function pushNow(_retryDepth = 0) {
    try {
        const payload = await buildPayload();
        const sig = JSON.stringify(payload.workflow);
        if (sig === lastSig) return;
        lastSig = sig;
        const r = await fetch("/mcp_bridge/state", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });
        if (r.status === 409 && _retryDepth < 1) {
            const data = await r.json().catch(() => ({}));
            if (data.regenerate) {
                regenerateTabId();
                lastSig = null;
                return pushNow(_retryDepth + 1);
            }
        }
    } catch (e) {
        console.warn("[mcp_bridge] push failed:", e);
    }
}

function schedulePush() {
    if (pushTimer) clearTimeout(pushTimer);
    pushTimer = setTimeout(pushNow, PUSH_DEBOUNCE_MS);
}

async function heartbeat() {
    try {
        const r = await fetch("/mcp_bridge/heartbeat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ tab_id: tabId, boot_id: bootId }),
        });
        const data = await r.json().catch(() => ({}));
        if (data.regenerate) {
            regenerateTabId();
            lastSig = null;
            await pushNow();
        } else if (data.known === false) {
            // Server doesn't know us (probably restarted) — push full state.
            lastSig = null;
            await pushNow();
        }
    } catch (e) {
        // network blip; next tick will retry
    }
}

function confirmReplace() {
    if (trustAgent) return true;
    return confirm(
        "MCP agent wants to replace this tab's workflow.\n\n" +
        "Click OK to apply, Cancel to skip.\n\n" +
        "(Re-enable auto-apply: `localStorage.removeItem('mcp_bridge.trust')` in the console.)"
    );
}

async function handleLoad(ev) {
    const wf = ev.workflow;
    if (!wf) return;
    if (ev.confirm !== false && !confirmReplace()) {
        console.log("[mcp_bridge] load declined by user");
        return;
    }
    try {
        await app.loadGraphData(wf);
        lastSig = null;
        schedulePush();
        console.log("[mcp_bridge] workflow applied from agent");
    } catch (e) {
        console.error("[mcp_bridge] load failed:", e);
        alert("MCP load failed: " + e.message);
    }
}

async function handleScreenshot(ev) {
    const requestId = ev.request_id;
    if (!requestId) return;
    try {
        const canvas = app.canvas?.canvas || app.canvasEl;
        if (!canvas) throw new Error("LiteGraph canvas not found");
        const dataUrl = canvas.toDataURL("image/png");
        await fetch("/mcp_bridge/screenshot/response", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                request_id: requestId,
                data_url: dataUrl,
                width: canvas.width,
                height: canvas.height,
                tab_id: tabId,
            }),
        });
    } catch (e) {
        console.error("[mcp_bridge] screenshot failed:", e);
        await fetch("/mcp_bridge/screenshot/response", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_id: requestId, error: e.message, tab_id: tabId }),
        });
    }
}

function findOutputSlot(node, slot) {
    if (typeof slot === "number") return slot;
    const outs = node.outputs || [];
    for (let i = 0; i < outs.length; i++) {
        if (outs[i].name === slot) return i;
    }
    for (let i = 0; i < outs.length; i++) {
        if (outs[i].type === slot) return i;
    }
    throw new Error(`output slot ${JSON.stringify(slot)} not found on node ${node.id} (${node.type}); have: ${outs.map(o => o.name).join(",")}`);
}

function findInputSlot(node, slot) {
    if (typeof slot === "number") return slot;
    const ins = node.inputs || [];
    for (let i = 0; i < ins.length; i++) {
        if (ins[i].name === slot) return i;
    }
    throw new Error(`input slot ${JSON.stringify(slot)} not found on node ${node.id} (${node.type}); have: ${ins.map(o => o.name).join(",")}`);
}

function nodeSummary(node) {
    // node.pos may be an Array OR a Float32Array (newer LiteGraph), so don't use Array.isArray
    const hasPos = node.pos && typeof node.pos.length === "number" && node.pos.length >= 2;
    const hasSize = node.size && typeof node.size.length === "number" && node.size.length >= 2;
    return {
        id: node.id,
        type: node.type,
        pos: hasPos ? [node.pos[0], node.pos[1]] : null,
        size: hasSize ? [node.size[0], node.size[1]] : null,
        widgets: (node.widgets || []).map(w => ({ name: w.name, value: w.value })),
    };
}

const OPS = {
    add_node({ class_type, pos, widget_values, id }) {
        const node = LiteGraph.createNode(class_type);
        if (!node) throw new Error(`unknown node class: ${class_type}`);
        if (id != null) node.id = id;
        app.graph.add(node);
        // Set position AFTER add — LiteGraph can normalize/reset pos during graph.add
        if (pos && pos.length >= 2) {
            node.pos = [Number(pos[0]) || 0, Number(pos[1]) || 0];
        }
        if (widget_values) {
            for (const w of node.widgets || []) {
                if (w.name in widget_values) {
                    w.value = widget_values[w.name];
                    if (typeof w.callback === "function") w.callback(w.value);
                }
            }
        }
        return { node: nodeSummary(node) };
    },

    delete_node({ node_id }) {
        const node = app.graph.getNodeById(node_id);
        if (!node) throw new Error(`node ${node_id} not found`);
        app.graph.remove(node);
        return { removed: node_id };
    },

    connect({ from_node_id, from_slot, to_node_id, to_slot }) {
        const fromNode = app.graph.getNodeById(from_node_id);
        if (!fromNode) throw new Error(`node ${from_node_id} not found`);
        const toNode = app.graph.getNodeById(to_node_id);
        if (!toNode) throw new Error(`node ${to_node_id} not found`);
        const fromIdx = findOutputSlot(fromNode, from_slot);
        const toIdx = findInputSlot(toNode, to_slot);
        const link = fromNode.connect(fromIdx, toNode, toIdx);
        if (!link) throw new Error(`connect failed (likely a type mismatch between ${fromNode.outputs[fromIdx]?.type} and ${toNode.inputs[toIdx]?.type})`);
        return { link_id: link.id ?? link, from_idx: fromIdx, to_idx: toIdx };
    },

    connect_many({ connections }) {
        // Atomic-ish batch wiring. Each entry: {from_node_id, from_slot, to_node_id, to_slot}.
        // Continues on individual errors; reports per-connection result so the agent can see
        // which links failed without re-issuing the whole batch.
        const results = [];
        for (const c of connections || []) {
            try {
                const r = OPS.connect(c);
                results.push({ ok: true, ...c, ...r });
            } catch (e) {
                results.push({ ok: false, ...c, error: e.message });
            }
        }
        return { count: results.length, results };
    },

    disconnect({ to_node_id, to_slot }) {
        const node = app.graph.getNodeById(to_node_id);
        if (!node) throw new Error(`node ${to_node_id} not found`);
        const idx = findInputSlot(node, to_slot);
        const ok = node.disconnectInput(idx);
        return { disconnected: !!ok, slot: idx };
    },

    set_widget({ node_id, name, value }) {
        const node = app.graph.getNodeById(node_id);
        if (!node) throw new Error(`node ${node_id} not found`);
        const w = (node.widgets || []).find(w => w.name === name);
        if (!w) throw new Error(`widget ${JSON.stringify(name)} not found on node ${node_id} (${node.type}); have: ${(node.widgets || []).map(w => w.name).join(",")}`);

        // Type-check: catch agents that emit a number where a string was expected
        // (a real qwen failure mode — corrupted CLIPTextEncode.text with a 16-digit int).
        const oldType = typeof w.value;
        const newType = typeof value;
        if (oldType === "string" && newType !== "string") {
            throw new Error(
                `widget '${name}' on node ${node_id} (${node.type}) expects a string; got ${newType} (${JSON.stringify(value).slice(0, 80)}). ` +
                `For prompt text, the value must be a JSON string. Current value: ${JSON.stringify(w.value).slice(0, 80)}`
            );
        }
        if ((oldType === "number" || oldType === "boolean") && newType === "string") {
            // Best-effort coerce: agents sometimes JSON-stringify numbers/bools
            const coerced = oldType === "number" ? Number(value) : (value === "true" || value === true);
            if (oldType === "number" && Number.isNaN(coerced)) {
                throw new Error(
                    `widget '${name}' on node ${node_id} (${node.type}) expects a number; got non-numeric string ${JSON.stringify(value).slice(0, 80)}`
                );
            }
            w.value = coerced;
        } else {
            w.value = value;
        }
        if (typeof w.callback === "function") w.callback(w.value);
        return { node_id: node.id, node_type: node.type, name: w.name, value: w.value };
    },

    move_node({ node_id, x, y }) {
        const node = app.graph.getNodeById(node_id);
        if (!node) throw new Error(`node ${node_id} not found`);
        node.pos = [x, y];
        return { pos: node.pos };
    },

    arrange_layout() {
        if (typeof app.graph.arrange === "function") {
            app.graph.arrange();
            return { arranged: true };
        }
        throw new Error("graph.arrange() not available in this ComfyUI version");
    },
};

async function handleOp(ev) {
    const requestId = ev.request_id;
    const op = ev.op || {};
    let result;
    try {
        const fn = OPS[op.op];
        if (!fn) throw new Error(`unknown op: ${op.op}`);
        result = (await fn(op)) || {};
        result.ok = true;
    } catch (e) {
        console.error("[mcp_bridge] op failed:", op, e);
        result = { ok: false, error: e.message };
    }

    // CRITICAL: push fresh state to the bridge BEFORE acking the op.
    // Without this, set_widget returns ok:true and the agent immediately calls
    // queue_workflow → bridge serves stale cached state → wrong values queued.
    // The 800ms schedulePush debounce was a real race.
    if (result.ok) {
        lastSig = null;
        try {
            await pushNow();
        } catch (e) {
            console.warn("[mcp_bridge] post-op pushNow failed:", e);
        }
    }

    if (requestId) {
        await fetch("/mcp_bridge/op/response", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ request_id: requestId, tab_id: tabId, ...result }),
        });
    }
}

async function handleEvent(ev) {
    if (ev.type === "load") return handleLoad(ev);
    if (ev.type === "screenshot") return handleScreenshot(ev);
    if (ev.type === "op") return handleOp(ev);
    console.warn("[mcp_bridge] unknown event type:", ev.type);
}

async function pollLoop() {
    while (true) {
        try {
            const r = await fetch(`/mcp_bridge/poll?tab_id=${encodeURIComponent(tabId)}`);
            if (!r.ok) {
                await new Promise((res) => setTimeout(res, 2000));
                continue;
            }
            const data = await r.json();
            for (const ev of data.events || []) {
                handleEvent(ev);
            }
        } catch (e) {
            await new Promise((res) => setTimeout(res, 2000));
        }
    }
}

app.registerExtension({
    name: "comfy.mcp_bridge",
    async setup() {
        const orig = app.graph.onAfterChange;
        app.graph.onAfterChange = function (...args) {
            if (orig) orig.apply(this, args);
            schedulePush();
        };

        setTimeout(pushNow, 1500);
        setInterval(heartbeat, HEARTBEAT_INTERVAL_MS);
        // Fallback: re-check the graph every few seconds. onAfterChange misses some
        // edit types (notably widget value tweaks) on this ComfyUI build; pushNow has
        // a JSON signature dedup, so unchanged graphs cost nothing on the wire.
        setInterval(() => { pushNow().catch(() => {}); }, POLL_PUSH_INTERVAL_MS);

        window.addEventListener("beforeunload", () => {
            const blob = new Blob([JSON.stringify({ tab_id: tabId })], { type: "application/json" });
            navigator.sendBeacon("/mcp_bridge/disconnect", blob);
        });

        pollLoop();

        console.log(`[mcp_bridge] v${VERSION} ready (tab_id=${tabId}, comfy_client_id=${api.clientId}, trust=${trustAgent})`);
    },
});
