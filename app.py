from __future__ import annotations

import json
import os
import shutil
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlparse

import yaml


APP_DIR = Path(
    os.environ.get("CLASH_VERGE_APP_DIR")
    or Path(os.environ.get("APPDATA", "")) / "io.github.clash-verge-rev.clash-verge-rev"
)
PROFILES_YAML = APP_DIR / "profiles.yaml"
PROFILES_DIR = APP_DIR / "profiles"
HOST = "127.0.0.1"
PORT = int(os.environ.get("CLASH_VERGE_CONFIG_UI_PORT", "8787"))
IDLE_TIMEOUT_SECONDS = int(os.environ.get("CLASH_UI_IDLE_TIMEOUT", "1800"))
LAST_ACCESS = time.time()

SECTION_TITLES = {
    "groups": "代理组",
    "proxies": "代理节点",
    "rules": "规则",
}


HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Clash Verge 可视化增强配置</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #17191e;
      --surface: #22262d;
      --surface-2: #2b3039;
      --surface-3: #343a45;
      --line: #464e5c;
      --line-soft: #343a44;
      --text: #f3f5f8;
      --muted: #aeb6c2;
      --accent: #1687ff;
      --accent-soft: #153f68;
      --danger: #ff5b52;
      --ok: #42c47a;
      --warn: #f0b84b;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      height: 100vh;
      overflow: hidden;
      background: var(--bg);
      color: var(--text);
      font: 14px/1.5 system-ui, -apple-system, "Segoe UI", "Microsoft YaHei", sans-serif;
    }
    button, input, select, textarea {
      font: inherit;
      color: var(--text);
      background: var(--surface-2);
      border: 1px solid var(--line);
      border-radius: 6px;
    }
    button {
      min-height: 34px;
      padding: 0 12px;
      cursor: pointer;
      white-space: nowrap;
    }
    button:hover { border-color: #6a7485; }
    button.primary {
      background: var(--accent);
      border-color: var(--accent);
      font-weight: 650;
    }
    button.ghost { background: transparent; }
    button.choice.added {
      background: rgba(66, 196, 122, .18);
      border-color: var(--ok);
      color: #bff6d4;
    }
    button.choice .state {
      color: var(--muted);
      margin-left: 6px;
      font-size: 12px;
    }
    button.choice.added .state { color: #d6ffe4; }
    button.danger { color: #ffbeb9; border-color: #7b3a3a; }
    button:disabled { opacity: .45; cursor: not-allowed; }
    input, select { height: 34px; padding: 0 10px; min-width: 0; }
    textarea {
      width: 100%;
      min-height: 86px;
      padding: 10px;
      resize: vertical;
      line-height: 1.45;
    }
    header {
      height: 58px;
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 0 18px;
      background: #20242b;
      border-bottom: 1px solid var(--line-soft);
    }
    header h1 { margin: 0; font-size: 18px; }
    main {
      height: calc(100vh - 58px);
      display: grid;
      grid-template-columns: 300px minmax(360px, 1fr);
      min-height: 0;
      overflow: hidden;
    }
    aside {
      padding: 14px;
      overflow: auto;
      background: #1e2229;
      border-right: 1px solid var(--line-soft);
    }
    .workspace {
      min-width: 0;
      min-height: 0;
      display: grid;
      grid-template-rows: auto 1fr;
      overflow: hidden;
    }
    .topbar {
      padding: 14px 16px 10px;
      border-bottom: 1px solid var(--line-soft);
      background: #20242b;
    }
    .tabs, .segments, .toolbar {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      gap: 8px;
    }
    .tabs { margin-bottom: 10px; }
    .tab.active, .segment.active {
      background: var(--accent);
      border-color: var(--accent);
      color: white;
    }
    .editor-layout {
      min-height: 0;
      display: grid;
      grid-template-columns: minmax(320px, 42%) minmax(360px, 1fr);
      overflow: hidden;
    }
    .list-pane, .detail-pane {
      min-width: 0;
      min-height: 0;
      overflow: auto;
      padding: 14px;
    }
    .list-pane { border-right: 1px solid var(--line-soft); }
    .profile {
      width: 100%;
      min-height: 56px;
      display: block;
      text-align: left;
      margin-bottom: 8px;
      background: var(--surface);
      border-color: transparent;
    }
    .profile.active {
      background: var(--accent-soft);
      border-color: var(--accent);
    }
    .profile strong {
      display: block;
      font-size: 14px;
      overflow-wrap: anywhere;
    }
    .meta {
      display: block;
      margin-top: 3px;
      color: var(--muted);
      font-size: 12px;
      overflow-wrap: anywhere;
    }
    .row {
      display: grid;
      grid-template-columns: 126px minmax(0, 1fr);
      gap: 8px 10px;
      align-items: center;
      margin-bottom: 9px;
    }
    .row label { color: var(--muted); }
    .row.wide {
      display: block;
      margin-top: 12px;
    }
    .row.wide label {
      display: block;
      margin-bottom: 6px;
    }
    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    .section-title h2 {
      margin: 0;
      font-size: 16px;
    }
    .item {
      width: 100%;
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      align-items: center;
      text-align: left;
      padding: 10px;
      margin-bottom: 8px;
      background: var(--surface);
      border-color: transparent;
    }
    .item.active {
      background: #263b4f;
      border-color: var(--accent);
    }
    .item-title {
      font-weight: 700;
      overflow-wrap: anywhere;
    }
    .item-sub {
      display: block;
      color: var(--muted);
      font-size: 12px;
      margin-top: 2px;
      overflow-wrap: anywhere;
    }
    .pill {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 22px;
      padding: 0 8px;
      border-radius: 999px;
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 12px;
    }
    .status {
      margin-left: auto;
      min-width: 120px;
      text-align: right;
      color: var(--muted);
      overflow-wrap: anywhere;
    }
    .empty {
      color: var(--muted);
      border: 1px dashed var(--line);
      border-radius: 8px;
      padding: 20px;
      background: rgba(255,255,255,.02);
    }
    .hint {
      color: var(--muted);
      font-size: 12px;
      margin-top: 6px;
    }
    .split {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .danger-text { color: var(--danger); }
    .warn-text { color: var(--warn); }
    .ok-text { color: var(--ok); }
    .choice-panel {
      max-height: 320px;
      overflow: auto;
      align-content: flex-start;
      padding: 8px;
      border: 1px solid var(--line-soft);
      border-radius: 8px;
      background: rgba(255,255,255,.025);
    }
    @media (max-width: 980px) {
      body { overflow: auto; }
      main { grid-template-columns: 1fr; height: auto; min-height: calc(100vh - 58px); overflow: visible; }
      aside { max-height: 260px; border-right: 0; border-bottom: 1px solid var(--line-soft); }
      .workspace, .editor-layout { overflow: visible; }
      .editor-layout { grid-template-columns: 1fr; }
      .list-pane { border-right: 0; border-bottom: 1px solid var(--line-soft); }
    }
    @media (max-width: 620px) {
      header { height: auto; min-height: 58px; flex-wrap: wrap; padding: 12px; }
      .row { grid-template-columns: 1fr; }
      .split { grid-template-columns: 1fr; }
    }
  </style>
</head>
<body>
  <header>
    <h1>Clash Verge 可视化增强配置</h1>
    <span class="pill" id="currentProfile">未选择</span>
    <span class="status" id="status"></span>
  </header>
  <main>
    <aside>
      <div class="toolbar" style="margin-bottom: 10px">
        <button id="reloadProfiles">刷新配置</button>
      </div>
      <div id="profiles"></div>
    </aside>
    <section class="workspace">
      <div class="topbar">
        <div class="tabs">
          <button class="tab active" data-tab="groups">代理组</button>
          <button class="tab" data-tab="proxies">代理节点</button>
          <button class="tab" data-tab="rules">规则</button>
        </div>
        <div class="toolbar">
          <div class="segments">
            <button class="segment active" data-bucket="prepend">前置</button>
            <button class="segment" data-bucket="append">后置</button>
            <button class="segment" data-bucket="delete">删除</button>
          </div>
          <input id="filter" placeholder="筛选当前列表">
          <button id="addPrepend">添加前置</button>
          <button id="addAppend">添加后置</button>
          <button id="addItem">新增当前</button>
          <button id="toPrepend">移到前置</button>
          <button id="toAppend">移到后置</button>
          <button id="moveUp">上移</button>
          <button id="moveDown">下移</button>
          <button class="danger" id="deleteItem">删除</button>
          <button class="primary" id="save">保存</button>
          <span class="pill" id="fileInfo">未加载文件</span>
        </div>
      </div>
      <div class="editor-layout">
        <div class="list-pane">
          <div class="section-title">
            <h2 id="listTitle">项目</h2>
            <span class="pill" id="countInfo">0 项</span>
          </div>
          <div id="items"></div>
        </div>
        <div class="detail-pane">
          <div id="detail"></div>
        </div>
      </div>
    </section>
  </main>

  <script>
    const state = {
      profiles: [],
      profile: null,
      data: null,
      tab: "groups",
      bucket: "prepend",
      selected: -1,
      filter: ""
    };

    const $ = (id) => document.getElementById(id);

    function status(message, ok = true) {
      $("status").textContent = message;
      $("status").style.color = ok ? "var(--ok)" : "var(--danger)";
      if (message) setTimeout(() => {
        if ($("status").textContent === message) $("status").textContent = "";
      }, 3500);
    }

    async function api(path, options) {
      const res = await fetch(path, options);
      const body = await res.json();
      if (!res.ok) throw new Error(body.error || res.statusText);
      return body;
    }

    async function loadProfiles() {
      state.profiles = (await api("/api/profiles")).profiles;
      renderProfiles();
      const current = state.profiles.find(p => p.current) || state.profiles[0];
      if (current) await loadProfile(current.uid);
      else renderAll();
    }

    async function loadProfile(uid) {
      state.data = await api(`/api/profile/${encodeURIComponent(uid)}`);
      state.profile = state.data.profile;
      state.selected = -1;
      $("currentProfile").textContent = state.profile.name || state.profile.uid;
      renderAll();
    }

    function currentSection() {
      if (!state.data) return { file: "", prepend: [], append: [], delete: [] };
      return state.data.sections[state.tab] || { file: "", prepend: [], append: [], delete: [] };
    }

    function currentList() {
      const section = currentSection();
      if (!Array.isArray(section[state.bucket])) section[state.bucket] = [];
      return section[state.bucket];
    }

    function choices() {
      return state.data?.choices || { proxies: [], groups: [], policies: [] };
    }

    function renderAll() {
      renderProfiles();
      renderTopbar();
      renderList();
      renderDetail();
    }

    function renderProfiles() {
      $("profiles").innerHTML = state.profiles.length
        ? state.profiles.map(p => `
          <button class="profile ${state.profile?.uid === p.uid ? "active" : ""}" data-uid="${escapeHtml(p.uid)}">
            <strong>${escapeHtml(p.name || p.uid)}${p.current ? " · 当前" : ""}</strong>
            <span class="meta">${escapeHtml(p.type)} · ${escapeHtml(p.file || "")}</span>
          </button>`).join("")
        : `<div class="empty">没有找到 Clash Verge Rev 配置。</div>`;
      document.querySelectorAll(".profile").forEach(btn => {
        btn.onclick = () => loadProfile(btn.dataset.uid).catch(err => status(err.message, false));
      });
    }

    function renderTopbar() {
      document.querySelectorAll(".tab").forEach(btn => btn.classList.toggle("active", btn.dataset.tab === state.tab));
      document.querySelectorAll(".segment").forEach(btn => btn.classList.toggle("active", btn.dataset.bucket === state.bucket));
      const sec = currentSection();
      $("fileInfo").textContent = sec.file ? sec.file : "此项未绑定增强文件";
      $("filter").value = state.filter;
    }

    function renderList() {
      const list = currentList();
      const filtered = list
        .map((item, index) => ({ item, index, text: itemSearchText(item).toLowerCase() }))
        .filter(row => !state.filter || row.text.includes(state.filter.toLowerCase()));
      $("listTitle").textContent = `${tabName()} · ${bucketName()}`;
      $("countInfo").textContent = `${filtered.length} / ${list.length} 项`;
      if (!state.profile) {
        $("items").innerHTML = `<div class="empty">请选择左侧订阅。</div>`;
        return;
      }
      if (!filtered.length) {
        $("items").innerHTML = `<div class="empty">当前列表为空。</div>`;
        return;
      }
      $("items").innerHTML = filtered.map(({ item, index }) => `
        <button class="item ${state.selected === index ? "active" : ""}" data-index="${index}">
          <span>
            <span class="item-title">${escapeHtml(itemTitle(item))}</span>
            <span class="item-sub">${escapeHtml(itemSubtitle(item))}</span>
          </span>
          <span class="pill">${index + 1}</span>
        </button>`).join("");
      document.querySelectorAll(".item").forEach(btn => {
        btn.onclick = () => {
          state.selected = Number(btn.dataset.index);
          renderList();
          renderDetail();
        };
      });
    }

    function renderDetail() {
      const list = currentList();
      const item = list[state.selected];
      $("moveUp").disabled = state.selected <= 0;
      $("moveDown").disabled = state.selected < 0 || state.selected >= list.length - 1;
      $("deleteItem").disabled = state.selected < 0;
      $("toPrepend").disabled = state.selected < 0 || state.bucket === "prepend";
      $("toAppend").disabled = state.selected < 0 || state.bucket === "append";
      $("save").disabled = !state.profile;
      if (!state.profile) {
        $("detail").innerHTML = `<div class="empty">请选择左侧订阅后开始编辑。</div>`;
        return;
      }
      if (!currentSection().file) {
        $("detail").innerHTML = `<div class="empty">当前订阅没有绑定 ${tabName()} 增强文件。请先在 Clash Verge Rev 里打开一次“编辑${tabName()}”创建文件。</div>`;
        return;
      }
      if (!item) {
        $("detail").innerHTML = `<div class="empty">选择左侧项目，或点击“添加前置 / 添加后置”。</div>`;
        return;
      }
      if (state.bucket === "delete") renderDeleteForm(item);
      else if (state.tab === "groups") renderGroupForm(item);
      else if (state.tab === "proxies") renderProxyForm(item);
      else renderRuleForm(item);
    }

    function renderGroupForm(group) {
      $("detail").innerHTML = `
        <div class="section-title"><h2>编辑代理组</h2><span class="pill">${escapeHtml(group.type || "select")}</span></div>
        ${field("名称", input("name", group.name))}
        ${field("类型", select("type", ["select","url-test","fallback","load-balance","relay"], group.type || "select"))}
        ${field("测试地址", input("url", group.url || "", "http://www.gstatic.com/generate_204"))}
        <div class="split">
          ${field("间隔秒", input("interval", group.interval ?? ""))}
          ${field("容差", input("tolerance", group.tolerance ?? ""))}
        </div>
        ${field("包含全部节点", select("include-all", ["","true","false"], group["include-all"] === true ? "true" : group["include-all"] === false ? "false" : ""))}
        ${field("节点过滤", input("filter", group.filter || ""))}
        ${field("排除过滤", input("exclude-filter", group["exclude-filter"] || ""))}
        ${fieldWide("选择/填写节点", textarea("proxies", listToText(group.proxies)))}
        ${choiceButtons("proxies", groupMemberChoices(group.name), group.proxies || [])}
        ${fieldWide("保留的其他字段 JSON", textarea("__extra", extraJson(group, ["name","type","url","interval","tolerance","include-all","filter","exclude-filter","proxies"])) )}`;
      bindInputs();
      bindChoiceButtons("proxies", "proxies");
    }

    function renderProxyForm(proxy) {
      $("detail").innerHTML = `
        <div class="section-title"><h2>编辑代理节点</h2><span class="pill">${escapeHtml(proxy.type || "socks5")}</span></div>
        ${field("名称", input("name", proxy.name))}
        ${field("类型", select("type", ["socks5","http","ss","trojan","vmess","vless","hysteria2","hysteria","tuic","wireguard"], proxy.type || "socks5"))}
        ${field("服务器", input("server", proxy.server))}
        ${field("端口", input("port", proxy.port ?? ""))}
        ${field("用户名", input("username", proxy.username || ""))}
        ${field("密码", input("password", proxy.password || ""))}
        ${field("加密方式", input("cipher", proxy.cipher || ""))}
        ${field("UUID", input("uuid", proxy.uuid || ""))}
        ${field("前置代理", selectWithCustom("dialer-proxy", choices().policies, proxy["dialer-proxy"] || ""))}
        <div class="split">
          ${field("UDP", select("udp", ["","true","false"], boolValue(proxy.udp)))}
          ${field("TLS", select("tls", ["","true","false"], boolValue(proxy.tls)))}
        </div>
        ${fieldWide("保留的其他字段 JSON", textarea("__extra", extraJson(proxy, ["name","type","server","port","username","password","cipher","uuid","dialer-proxy","udp","tls"])) )}`;
      bindInputs();
    }

    function renderRuleForm(raw) {
      const rule = parseRule(raw);
      $("detail").innerHTML = `
        <div class="section-title"><h2>编辑规则</h2><span class="pill">${escapeHtml(rule.type)}</span></div>
        ${field("规则类型", select("ruleType", ["DOMAIN","DOMAIN-SUFFIX","DOMAIN-KEYWORD","IP-CIDR","IP-CIDR6","GEOIP","GEOSITE","PROCESS-NAME","RULE-SET","MATCH"], rule.type))}
        ${field("匹配内容", input("value", rule.value, "example.com"))}
        ${field("策略", selectWithCustom("policy", choices().policies, rule.policy || "DIRECT"))}
        ${field("附加参数", input("options", rule.options || "", "no-resolve 等"))}
        ${fieldWide("规则原文", textarea("rawRule", raw))}
        <div class="hint">修改上面的结构化字段会自动生成规则原文；直接编辑规则原文也可以。</div>`;
      bindInputs();
    }

    function renderDeleteForm(item) {
      $("detail").innerHTML = `
        <div class="section-title"><h2>编辑删除项</h2><span class="pill">delete</span></div>
        ${fieldWide("删除匹配内容", textarea("deleteRaw", typeof item === "string" ? item : JSON.stringify(item, null, 2)))}
        <div class="hint">删除项按 Clash Verge Rev 增强配置的 delete 语义保存。规则通常填完整规则行，节点/代理组通常填名称。</div>`;
      bindInputs();
    }

    function bindInputs() {
      document.querySelectorAll("[data-k]").forEach(el => {
        el.oninput = applyInput;
        el.onchange = applyInput;
      });
    }

    function applyInput(event) {
      const key = event.target.dataset.k;
      const list = currentList();
      let item = list[state.selected];
      if (state.bucket === "delete") {
        list[state.selected] = event.target.value;
        renderList();
        return;
      }
      if (state.tab === "rules") {
        if (key === "rawRule") list[state.selected] = event.target.value;
        else {
          const rule = parseRule(item);
          if (key === "ruleType") rule.type = event.target.value;
          if (key === "value") rule.value = event.target.value.trim();
          if (key === "policy") rule.policy = event.target.value.trim();
          if (key === "options") rule.options = event.target.value.trim();
          list[state.selected] = buildRule(rule);
        }
        renderList();
        return;
      }
      if (key === "__extra") {
        try {
          const parsed = event.target.value.trim() ? JSON.parse(event.target.value) : {};
          const keep = state.tab === "groups"
            ? ["name","type","url","interval","tolerance","include-all","filter","exclude-filter","proxies"]
            : ["name","type","server","port","username","password","cipher","uuid","dialer-proxy","udp","tls"];
          for (const k of Object.keys(item)) if (!keep.includes(k)) delete item[k];
          Object.assign(item, parsed);
          status("其他字段已更新");
        } catch {
          status("其他字段 JSON 格式不正确", false);
        }
        renderList();
        return;
      }
      setValue(item, key, event.target.value);
      renderList();
    }

    function setValue(item, key, value) {
      const text = String(value ?? "").trim();
      if (key === "proxies") {
        item.proxies = String(value).split(/\r?\n/).map(v => v.trim()).filter(Boolean);
        return;
      }
      if (["port","interval","tolerance","timeout","max-failed-times"].includes(key)) {
        if (text === "") delete item[key];
        else item[key] = Number(text);
        return;
      }
      if (["udp","tls","include-all"].includes(key)) {
        if (text === "") delete item[key];
        else item[key] = text === "true";
        return;
      }
      if (text === "") delete item[key];
      else item[key] = value;
    }

    function addItem(bucket = state.bucket) {
      if (!state.profile) return;
      state.bucket = bucket;
      const list = currentList();
      let item;
      if (state.bucket === "delete") item = "";
      else if (state.tab === "groups") item = { name: "新代理组", type: "select", proxies: [] };
      else if (state.tab === "proxies") item = { name: "新 SOCKS5 节点", type: "socks5", server: "", port: 1080 };
      else item = "DOMAIN-SUFFIX,example.com,DIRECT";
      list.unshift(item);
      state.selected = 0;
      renderAll();
    }

    function deleteItem() {
      const list = currentList();
      if (state.selected < 0) return;
      list.splice(state.selected, 1);
      state.selected = Math.min(state.selected, list.length - 1);
      renderList();
      renderDetail();
    }

    function moveSelected(delta) {
      const list = currentList();
      const next = state.selected + delta;
      if (state.selected < 0 || next < 0 || next >= list.length) return;
      [list[state.selected], list[next]] = [list[next], list[state.selected]];
      state.selected = next;
      renderList();
      renderDetail();
    }

    function moveToBucket(targetBucket) {
      if (!state.profile || state.selected < 0 || state.bucket === targetBucket) return;
      const section = currentSection();
      const source = currentList();
      if (!Array.isArray(section[targetBucket])) section[targetBucket] = [];
      const target = section[targetBucket];
      const [item] = source.splice(state.selected, 1);
      target.unshift(item);
      state.bucket = targetBucket;
      state.selected = 0;
      renderAll();
    }

    async function saveCurrent() {
      if (!state.profile) return;
      await api(`/api/profile/${encodeURIComponent(state.profile.uid)}/${state.tab}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify({ data: currentSection() })
      });
      status("已保存，回到 Clash Verge Rev 重新应用订阅后生效");
      await loadProfile(state.profile.uid);
    }

    function field(label, control) {
      return `<div class="row"><label>${escapeHtml(label)}</label>${control}</div>`;
    }

    function fieldWide(label, control) {
      return `<div class="row wide"><label>${escapeHtml(label)}</label>${control}</div>`;
    }

    function input(key, value = "", placeholder = "") {
      return `<input data-k="${escapeHtml(key)}" value="${escapeAttr(value ?? "")}" placeholder="${escapeAttr(placeholder)}">`;
    }

    function textarea(key, value = "") {
      return `<textarea data-k="${escapeHtml(key)}">${escapeHtml(value ?? "")}</textarea>`;
    }

    function select(key, options, value = "") {
      return `<select data-k="${escapeHtml(key)}">${options.map(opt => `<option value="${escapeAttr(opt)}" ${String(opt) === String(value) ? "selected" : ""}>${escapeHtml(labelFor(opt))}</option>`).join("")}</select>`;
    }

    function selectWithCustom(key, options, value = "") {
      const unique = Array.from(new Set(["", ...options, value].filter(v => v !== undefined && v !== null)));
      return select(key, unique, value);
    }

    function groupMemberChoices(currentGroupName = "") {
      const c = choices();
      const groups = c.groups
        .filter(v => v && v !== currentGroupName)
        .map(v => ({ value: v, kind: "组" }));
      const proxies = c.proxies.map(v => ({ value: v, kind: "节点" }));
      const defaults = ["DIRECT", "REJECT"].map(v => ({ value: v, kind: "策略" }));
      const seen = new Set();
      return [...defaults, ...groups, ...proxies].filter(item => {
        if (seen.has(item.value)) return false;
        seen.add(item.value);
        return true;
      });
    }

    function choiceButtons(targetKey, values, selectedValues = []) {
      if (!values.length) return `<div class="hint">未从当前订阅中读取到可选节点或代理组。</div>`;
      const selected = new Set(selectedValues || []);
      return `<div class="hint">点击候选项可自动添加/移除；绿色为已添加。</div>
        <div class="toolbar choice-panel" style="margin: 8px 0 12px">${
          values.slice(0, 160).map(item => {
            const value = typeof item === "string" ? item : item.value;
            const kind = typeof item === "string" ? "" : item.kind;
            const added = selected.has(value);
            return `<button class="ghost choice ${added ? "added" : ""}" data-target="${targetKey}" data-value="${escapeAttr(value)}">
              ${kind ? `<span class="pill">${escapeHtml(kind)}</span> ` : ""}${escapeHtml(value)}
              <span class="state">${added ? "已添加" : "未添加"}</span>
            </button>`;
          }).join("")
        }</div>`;
    }

    function bindChoiceButtons(targetKey, textareaKey) {
      document.querySelectorAll(`.choice[data-target="${targetKey}"]`).forEach(btn => {
        btn.onclick = () => {
          const area = document.querySelector(`[data-k="${textareaKey}"]`);
          const current = area.value.split(/\r?\n/).map(v => v.trim()).filter(Boolean);
          const index = current.indexOf(btn.dataset.value);
          if (index >= 0) current.splice(index, 1);
          else current.push(btn.dataset.value);
          area.value = current.join("\n");
          area.dispatchEvent(new Event("input", { bubbles: true }));
          renderDetail();
        };
      });
    }

    function parseRule(raw) {
      if (!raw || typeof raw !== "string") return { type: "DOMAIN-SUFFIX", value: "", policy: "DIRECT", options: "" };
      const parts = raw.split(",");
      const type = parts[0] || "DOMAIN-SUFFIX";
      if (type === "MATCH") return { type, value: "", policy: parts[1] || "DIRECT", options: parts.slice(2).join(",") };
      return { type, value: parts[1] || "", policy: parts[2] || "DIRECT", options: parts.slice(3).join(",") };
    }

    function buildRule(rule) {
      const options = rule.options ? `,${rule.options}` : "";
      if (rule.type === "MATCH") return `MATCH,${rule.policy || "DIRECT"}${options}`;
      return `${rule.type || "DOMAIN-SUFFIX"},${rule.value || ""},${rule.policy || "DIRECT"}${options}`;
    }

    function extraJson(item, knownKeys) {
      const extra = {};
      for (const [key, value] of Object.entries(item || {})) {
        if (!knownKeys.includes(key)) extra[key] = value;
      }
      return JSON.stringify(extra, null, 2);
    }

    function itemTitle(item) {
      if (typeof item === "string") {
        if (state.tab === "rules") return parseRule(item).type + " · " + (parseRule(item).value || parseRule(item).policy || item);
        return item || "空删除项";
      }
      return item?.name || "未命名项目";
    }

    function itemSubtitle(item) {
      if (typeof item === "string") return item;
      if (state.tab === "groups") return `${item.type || "select"} · ${(item.proxies || []).length} 个节点`;
      if (state.tab === "proxies") return `${item.type || ""} · ${item.server || ""}:${item.port || ""}`;
      return JSON.stringify(item);
    }

    function itemSearchText(item) {
      return typeof item === "string" ? item : JSON.stringify(item);
    }

    function tabName() {
      return ({ groups: "代理组", proxies: "代理节点", rules: "规则" })[state.tab] || state.tab;
    }

    function bucketName() {
      return ({ prepend: "前置", append: "后置", delete: "删除" })[state.bucket] || state.bucket;
    }

    function listToText(value) {
      return Array.isArray(value) ? value.join("\n") : "";
    }

    function boolValue(value) {
      if (value === true) return "true";
      if (value === false) return "false";
      return "";
    }

    function labelFor(value) {
      if (value === "") return "未设置";
      if (value === "true") return "开启";
      if (value === "false") return "关闭";
      return value;
    }

    function escapeHtml(value) {
      return String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
    }
    const escapeAttr = escapeHtml;

    $("reloadProfiles").onclick = () => loadProfiles().catch(err => status(err.message, false));
    $("addPrepend").onclick = () => addItem("prepend");
    $("addAppend").onclick = () => addItem("append");
    $("addItem").onclick = () => addItem();
    $("toPrepend").onclick = () => moveToBucket("prepend");
    $("toAppend").onclick = () => moveToBucket("append");
    $("deleteItem").onclick = deleteItem;
    $("moveUp").onclick = () => moveSelected(-1);
    $("moveDown").onclick = () => moveSelected(1);
    $("save").onclick = () => saveCurrent().catch(err => status(err.message, false));
    $("filter").oninput = (event) => {
      state.filter = event.target.value;
      renderList();
    };
    document.querySelectorAll(".tab").forEach(btn => {
      btn.onclick = () => {
        state.tab = btn.dataset.tab;
        state.selected = -1;
        renderAll();
      };
    });
    document.querySelectorAll(".segment").forEach(btn => {
      btn.onclick = () => {
        state.bucket = btn.dataset.bucket;
        state.selected = -1;
        renderAll();
      };
    });

    loadProfiles().catch(err => status(err.message, false));
  </script>
</body>
</html>"""


def read_yaml(path: Path):
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        return None
    return yaml.safe_load(text)


def write_yaml(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        backup = path.with_suffix(path.suffix + f".bak-{time.strftime('%Y%m%d-%H%M%S')}")
        shutil.copy2(path, backup)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False, width=1000),
        encoding="utf-8",
    )


def load_profiles_file():
    data = read_yaml(PROFILES_YAML)
    if not isinstance(data, dict):
        raise RuntimeError(f"无法读取 Clash Verge Rev 配置：{PROFILES_YAML}")
    return data


def profile_items():
    data = load_profiles_file()
    items = data.get("items") or []
    by_uid = {item.get("uid"): item for item in items if isinstance(item, dict)}
    profiles = []
    for item in items:
        if not isinstance(item, dict) or item.get("type") not in {"remote", "local"}:
            continue
        option = item.get("option") or {}
        profiles.append(
            {
                "uid": item.get("uid"),
                "name": item.get("name") or item.get("uid"),
                "type": item.get("type"),
                "file": item.get("file"),
                "current": item.get("uid") == data.get("current"),
                "enhancements": {
                    key: by_uid.get(option.get(key), {}).get("file")
                    for key in ("groups", "proxies", "rules", "merge", "script")
                },
            }
        )
    return profiles


def find_profile(uid: str):
    for profile in profile_items():
        if profile["uid"] == uid:
            return profile
    raise KeyError(f"未找到订阅：{uid}")


def profile_file_path(profile: dict) -> Path | None:
    filename = profile.get("file")
    if not filename:
        return None
    return PROFILES_DIR / filename


def enhancement_path(profile: dict, section: str) -> Path | None:
    filename = profile.get("enhancements", {}).get(section)
    if not filename:
        return None
    return PROFILES_DIR / filename


def load_section(profile: dict, section: str):
    path = enhancement_path(profile, section)
    if not path:
        return {"file": "", "prepend": [], "append": [], "delete": []}
    data = read_yaml(path)
    if not isinstance(data, dict):
        data = {}
    return {
        "file": path.name,
        "prepend": data.get("prepend") if isinstance(data.get("prepend"), list) else [],
        "append": data.get("append") if isinstance(data.get("append"), list) else [],
        "delete": data.get("delete") if isinstance(data.get("delete"), list) else [],
    }


def save_section(profile: dict, section: str, payload: dict):
    path = enhancement_path(profile, section)
    if not path:
        raise RuntimeError(f"当前订阅没有绑定{SECTION_TITLES.get(section, section)}增强文件")
    data = payload.get("data") or {}
    clean = {
        "prepend": data.get("prepend") if isinstance(data.get("prepend"), list) else [],
        "append": data.get("append") if isinstance(data.get("append"), list) else [],
        "delete": data.get("delete") if isinstance(data.get("delete"), list) else [],
    }
    write_yaml(path, clean)


def collect_choices(profile: dict, sections: dict):
    proxies: list[str] = []
    groups: list[str] = []

    base_path = profile_file_path(profile)
    base_data = read_yaml(base_path) if base_path else None
    if isinstance(base_data, dict):
        collect_named(base_data.get("proxies"), proxies)
        collect_named(base_data.get("proxy-groups"), groups)

    collect_named(sections.get("proxies", {}).get("prepend"), proxies)
    collect_named(sections.get("proxies", {}).get("append"), proxies)
    collect_named(sections.get("groups", {}).get("prepend"), groups)
    collect_named(sections.get("groups", {}).get("append"), groups)

    default_policies = ["DIRECT", "REJECT", "PASS"]
    policies = unique(default_policies + groups + proxies)
    return {
        "proxies": unique(proxies),
        "groups": unique(groups),
        "policies": policies,
    }


def collect_named(items, target: list[str]):
    if not isinstance(items, list):
        return
    for item in items:
        if isinstance(item, dict) and item.get("name"):
            target.append(str(item["name"]))


def unique(values: list[str]):
    result = []
    seen = set()
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        touch()
        try:
            parsed = urlparse(self.path)
            if parsed.path == "/":
                self.send_html(HTML)
                return
            if parsed.path == "/api/profiles":
                self.send_json({"profiles": profile_items()})
                return
            if parsed.path.startswith("/api/profile/"):
                uid = unquote(parsed.path.removeprefix("/api/profile/"))
                profile = find_profile(uid)
                sections = {
                    "groups": load_section(profile, "groups"),
                    "proxies": load_section(profile, "proxies"),
                    "rules": load_section(profile, "rules"),
                }
                self.send_json(
                    {
                        "profile": profile,
                        "sections": sections,
                        "choices": collect_choices(profile, sections),
                    }
                )
                return
            self.send_error_json(404, "Not found")
        except Exception as exc:
            self.send_error_json(500, str(exc))

    def do_POST(self):
        touch()
        try:
            parsed = urlparse(self.path)
            parts = parsed.path.strip("/").split("/")
            if len(parts) != 4 or parts[0] != "api" or parts[1] != "profile":
                self.send_error_json(404, "Not found")
                return
            uid = unquote(parts[2])
            section = parts[3]
            if section not in {"groups", "proxies", "rules"}:
                self.send_error_json(400, "无效配置类型")
                return
            length = int(self.headers.get("content-length") or 0)
            payload = json.loads(self.rfile.read(length).decode("utf-8") or "{}")
            profile = find_profile(uid)
            save_section(profile, section, payload)
            self.send_json({"ok": True})
        except Exception as exc:
            self.send_error_json(500, str(exc))

    def log_message(self, fmt, *args):
        return

    def send_html(self, body: str):
        raw = body.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_json(self, data, status=200):
        raw = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("content-type", "application/json; charset=utf-8")
        self.send_header("content-length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def send_error_json(self, status: int, message: str):
        self.send_json({"error": message}, status=status)


def touch():
    global LAST_ACCESS
    LAST_ACCESS = time.time()


def idle_shutdown(server: ThreadingHTTPServer):
    while True:
        time.sleep(30)
        if time.time() - LAST_ACCESS > IDLE_TIMEOUT_SECONDS:
            print(f"Idle for {IDLE_TIMEOUT_SECONDS} seconds, shutting down.")
            server.shutdown()
            return


def main():
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Clash Verge 可视化增强配置：http://{HOST}:{PORT}")
    print(f"配置目录：{APP_DIR}")
    threading.Thread(target=idle_shutdown, args=(server,), daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
