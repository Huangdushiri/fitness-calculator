"use strict";

/* ==================== 内置食物库（每 100g：碳水 / 蛋白质 / 脂肪） ==================== */
const DEFAULT_FOODS = [
  { name: "猪肉肥瘦", carbs: 2.4, protein: 13.2, fat: 37.0 },
  { name: "猪肉里脊", carbs: 0.0, protein: 20.2, fat: 7.9 },
  { name: "猪肉后臀尖", carbs: 0.0, protein: 20.4, fat: 9.8 },
  { name: "牛肉肥瘦", carbs: 2.0, protein: 19.9, fat: 4.2 },
  { name: "牛肉里脊", carbs: 2.4, protein: 22.2, fat: 0.9 },
  { name: "牛肉后腱", carbs: 2.2, protein: 20.1, fat: 1.0 },
  { name: "牛肉前腿", carbs: 2.9, protein: 19.2, fat: 1.8 },
  { name: "牛肉后腿", carbs: 1.1, protein: 20.9, fat: 2.0 },
  { name: "牛肉腑肋", carbs: 0.0, protein: 18.6, fat: 5.4 },
  { name: "鸡胸脯肉", carbs: 0.0, protein: 24.6, fat: 1.9 },
  { name: "鸡腿", carbs: 0.0, protein: 20.2, fat: 7.2 },
  { name: "鸡翅", carbs: 0.0, protein: 19.0, fat: 11.5 },
  { name: "鸡蛋", carbs: 2.8, protein: 13.3, fat: 8.8 },
  { name: "米饭", carbs: 25.9, protein: 2.6, fat: 0.3 },
  { name: "馒头", carbs: 45.6, protein: 6.8, fat: 1.1 },
  { name: "面条", carbs: 60.7, protein: 8.7, fat: 1.7 },
  { name: "玉米", carbs: 22.7, protein: 4.0, fat: 1.2 },
  { name: "红薯", carbs: 24.7, protein: 1.1, fat: 0.2 },
  { name: "南瓜", carbs: 4.4, protein: 0.7, fat: 0.1 },
  { name: "虾", carbs: 1.6, protein: 18.3, fat: 0.5 },
  { name: "西兰花", carbs: 4.3, protein: 4.1, fat: 0.6 },
  { name: "豆腐均值", carbs: 3.8, protein: 8.1, fat: 3.7 },
  { name: "北豆腐", carbs: 1.5, protein: 12.0, fat: 4.8 },
  { name: "南豆腐", carbs: 2.4, protein: 6.2, fat: 2.5 },
  { name: "香蕉", carbs: 22.0, protein: 1.4, fat: 0.2 },
];

/* ==================== 存储（localStorage） ==================== */
const LS_FOODS = "fitness_custom_foods";
const LS_RECORDS = "fitness_records";

function getCustomFoods() {
  try { return JSON.parse(localStorage.getItem(LS_FOODS) || "[]"); }
  catch (e) { return []; }
}
function setCustomFoods(list) { localStorage.setItem(LS_FOODS, JSON.stringify(list)); }

function getRecords() {
  try { return JSON.parse(localStorage.getItem(LS_RECORDS) || "[]"); }
  catch (e) { return []; }
}
function setRecords(list) { localStorage.setItem(LS_RECORDS, JSON.stringify(list)); }

function allFoods() { return DEFAULT_FOODS.concat(getCustomFoods()); }

/* ==================== 计算逻辑（与桌面版 nutrition.py 一致） ==================== */
function fmt(v, nd) {
  nd = (nd === undefined) ? 1 : nd;
  const x = Number(v).toFixed(nd);
  return x;
}

function readFloat(text, label) {
  const v = parseFloat(String(text).trim());
  if (isNaN(v)) throw "「" + label + "」请输入有效数字";
  if (v < 0) throw "「" + label + "」不能为负数";
  return v;
}

function bmr(gender, weight, height, age) {
  return gender === "男"
    ? 10 * weight + 6.25 * height - 5 * age + 5
    : 10 * weight + 6.25 * height - 5 * age - 161;
}

function foodNutrition(weight, c100, p100, f100) {
  const k = weight / 100;
  const carbs = c100 * k, protein = p100 * k, fat = f100 * k;
  return { kcal: 4 * carbs + 4 * protein + 9 * fat, carbs, protein, fat };
}

function split532(total) {
  return { carbs: total * 0.5 / 4, protein: total * 0.3 / 4, fat: total * 0.2 / 9 };
}

const CARB_RATIOS = { "高碳日": 50 / 35, "中碳日": 1.0, "低碳日": 15 / 35 };
const FAT_RATIOS = { "高碳日": 15 / 35, "中碳日": 1.0, "低碳日": 50 / 35 };
const CYCLE_COUNTS = { "高碳日": 2, "中碳日": 3, "低碳日": 2 };
const CYCLE_ORDER = ["高碳日", "中碳日", "低碳日"];

function weekNorm(ratios) {
  let total = 0;
  for (const d of CYCLE_ORDER) total += CYCLE_COUNTS[d] * ratios[d];
  return 7 / total;
}

function carbCycling(weight, carbsKg, proteinKg, fatKg) {
  const protein = proteinKg * weight;
  const carbsMid = carbsKg * weight * weekNorm(CARB_RATIOS);
  const fatMid = fatKg * weight * weekNorm(FAT_RATIOS);
  const daily = {};
  const weekly = { total_kcal: 0, carbs: 0, protein: 0, fat: 0 };
  for (const name of CYCLE_ORDER) {
    const carbs = carbsMid * CARB_RATIOS[name];
    const fat = fatMid * FAT_RATIOS[name];
    const total_kcal = 4 * carbs + 4 * protein + 9 * fat;
    daily[name] = { total_kcal, carbs, protein, fat };
    weekly.total_kcal += total_kcal * CYCLE_COUNTS[name];
    weekly.carbs += carbs * CYCLE_COUNTS[name];
    weekly.protein += protein * CYCLE_COUNTS[name];
    weekly.fat += fat * CYCLE_COUNTS[name];
  }
  return { daily, weekly };
}

function nowStr() {
  const d = new Date();
  const p = n => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`;
}

/* ==================== 工具 ==================== */
const $ = id => document.getElementById(id);
const esc = s => String(s).replace(/[&<>"']/g, c => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));

/* ==================== 标签页导航 ==================== */
function switchScreen(name) {
  document.querySelectorAll(".screen").forEach(s => s.classList.remove("active"));
  $("screen-" + name).classList.add("active");
  document.querySelectorAll(".tab").forEach(t => t.classList.toggle("active", t.dataset.screen === name));
  window.scrollTo(0, 0);
}

/* ==================== 状态 ==================== */
let currentGender = "男";
let items = [];           // 本次清单
let currentDate = null;   // 当前选中的记录日期（null = 全部）

/* ==================== 基础代谢 ==================== */
function calcBmr() {
  try {
    const age = readFloat($("bmr-age").value, "年龄");
    const height = readFloat($("bmr-height").value, "身高");
    const weight = readFloat($("bmr-weight").value, "体重");
    const r = bmr(currentGender, weight, height, age);
    $("bmr-result").textContent =
      `性别：${currentGender}\n基础代谢（BMR）：约 ${fmt(r, 0)} kcal / 天\n\n` +
      `说明：Mifflin-St Jeor 公式，为静息状态下维持生命所需的每日热量。\n` +
      `TDEE ≈ BMR × 活动系数（久坐 1.2 / 轻度 1.375 / 中度 1.55 / 高强度 1.725）`;
  } catch (e) {
    $("bmr-result").textContent = e;
  }
}

/* ==================== 食物下拉 / 食物库 ==================== */
function renderFoodSelect() {
  const sel = $("food-select");
  sel.innerHTML = "";
  for (const f of allFoods()) {
    const o = document.createElement("option");
    o.value = f.name; o.textContent = f.name;
    sel.appendChild(o);
  }
  updateFoodInfo();
}

function updateFoodInfo() {
  const f = allFoods().find(x => x.name === $("food-select").value);
  $("food-info").textContent = f
    ? `每 100g：碳水 ${fmt(f.carbs)}g · 蛋白质 ${fmt(f.protein)}g · 脂肪 ${fmt(f.fat)}g`
    : "";
}

function renderFoodLibrary() {
  const ul = $("food-library");
  ul.innerHTML = "";
  for (const f of allFoods()) {
    const li = document.createElement("li");
    li.innerHTML = `<div>${esc(f.name)}</div><div class="meta">碳水 ${fmt(f.carbs)}g · 蛋白质 ${fmt(f.protein)}g · 脂肪 ${fmt(f.fat)}g</div>`;
    li.onclick = () => {
      $("m-name").value = f.name;
      $("m-carbs").value = f.carbs;
      $("m-protein").value = f.protein;
      $("m-fat").value = f.fat;
    };
    ul.appendChild(li);
  }
}

/* ==================== 饮食热量（多食物 + 确认记录） ==================== */
function addItem() {
  const name = $("food-select").value;
  const f = allFoods().find(x => x.name === name);
  if (!f) { alert("请先选择一种食物"); return; }
  let weight;
  try { weight = readFloat($("food-weight").value, "重量"); }
  catch (e) { alert(e); return; }
  const r = foodNutrition(weight, f.carbs, f.protein, f.fat);
  items.push({ name, weight, kcal: r.kcal, carbs: r.carbs, protein: r.protein, fat: r.fat });
  $("food-weight").value = "";
  renderItems();
}

function renderItems() {
  const ul = $("item-list");
  ul.innerHTML = "";
  let tk = 0, tc = 0, tp = 0, tf = 0;
  items.forEach((it, i) => {
    tk += it.kcal; tc += it.carbs; tp += it.protein; tf += it.fat;
    const li = document.createElement("li");
    li.innerHTML =
      `<div><div>${esc(it.name)}</div><div class="meta">${fmt(it.weight, 0)}g · 碳水 ${fmt(it.carbs)}g · 蛋白质 ${fmt(it.protein)}g · 脂肪 ${fmt(it.fat)}g</div></div>` +
      `<button class="rm" data-i="${i}">✕</button>`;
    li.querySelector(".rm").onclick = () => { items.splice(i, 1); renderItems(); };
    ul.appendChild(li);
  });
  $("item-total").textContent =
    `合计：热量 ${fmt(tk, 0)} kcal · 碳水 ${fmt(tc)} g · 蛋白质 ${fmt(tp)} g · 脂肪 ${fmt(tf)} g`;
}

function clearItems() { items = []; renderItems(); }

function saveRecord() {
  if (items.length === 0) { alert("清单为空，请先加入食物"); return; }
  const tk = items.reduce((s, i) => s + i.kcal, 0);
  const tc = items.reduce((s, i) => s + i.carbs, 0);
  const tp = items.reduce((s, i) => s + i.protein, 0);
  const tf = items.reduce((s, i) => s + i.fat, 0);
  const rec = {
    id: Date.now(),
    datetime: nowStr(),
    mealPeriod: $("meal-period").value,
    kcal: tk, carbs: tc, protein: tp, fat: tf,
    items: items.map(i => ({ ...i }))
  };
  const all = getRecords();
  all.push(rec);
  setRecords(all);
  items = []; renderItems();
  alert(`已记录「${rec.mealPeriod}」\n${rec.datetime}`);
  renderDates(); // 日期列表同步更新
}

/* ==================== 食物管理 ==================== */
function saveFood() {
  const name = $("m-name").value.trim();
  if (!name) { alert("请输入食物名称"); return; }
  let carbs, protein, fat;
  try {
    carbs = readFloat($("m-carbs").value, "碳水");
    protein = readFloat($("m-protein").value, "蛋白质");
    fat = readFloat($("m-fat").value, "脂肪");
  } catch (e) { alert(e); return; }

  const list = getCustomFoods();
  const i = list.findIndex(x => x.name === name);
  if (i >= 0) list[i] = { name, carbs, protein, fat };
  else list.push({ name, carbs, protein, fat });
  setCustomFoods(list);
  renderFoodLibrary(); renderFoodSelect();
  $("m-name").value = ""; $("m-carbs").value = ""; $("m-protein").value = ""; $("m-fat").value = "";
}

function deleteFood() {
  const name = $("m-name").value.trim() || prompt("请输入要删除的食物名称：");
  if (!name) return;
  if (!confirm(`确定删除食物「${name}」吗？`)) return;
  const list = getCustomFoods().filter(x => x.name !== name);
  setCustomFoods(list);
  renderFoodLibrary(); renderFoodSelect();
  $("m-name").value = "";
}

/* ==================== 饮食结构 ==================== */
function calc532() {
  try {
    const total = readFloat($("d-total").value, "每日总热量");
    const r = split532(total);
    $("d-532-result").textContent =
      `每日总热量：${fmt(total, 0)} kcal\n碳水（50%）：${fmt(r.carbs)} g\n蛋白质（30%）：${fmt(r.protein)} g\n脂肪（20%）：${fmt(r.fat)} g`;
  } catch (e) { $("d-532-result").textContent = e; }
}

function calcCycle() {
  try {
    const w = readFloat($("d-weight").value, "体重");
    const c = readFloat($("d-carbs").value, "碳水");
    const p = readFloat($("d-protein").value, "蛋白质");
    const f = readFloat($("d-fat").value, "脂肪");
    const { daily, weekly } = carbCycling(w, c, p, f);
    const lines = [];
    for (const n of CYCLE_ORDER) {
      const d = daily[n];
      lines.push(`【${n}】(每周 ${CYCLE_COUNTS[n]} 天)`);
      lines.push(`  总热量：${fmt(d.total_kcal, 0)} kcal`);
      lines.push(`  碳水：${fmt(d.carbs)} g（${fmt(d.carbs / w, 2)} g/kg）`);
      lines.push(`  蛋白质：${fmt(d.protein)} g（${fmt(d.protein / w, 2)} g/kg）`);
      lines.push(`  脂肪：${fmt(d.fat)} g（${fmt(d.fat / w, 2)} g/kg）`);
    }
    lines.push("");
    lines.push("【每周合计】(2 高碳日 + 3 中碳日 + 2 低碳日)");
    lines.push(`  总热量：${fmt(weekly.total_kcal, 0)} kcal`);
    lines.push(`  碳水：${fmt(weekly.carbs)} g · 蛋白质：${fmt(weekly.protein)} g · 脂肪：${fmt(weekly.fat)} g`);
    $("d-cycle-result").textContent = lines.join("\n");
  } catch (e) { $("d-cycle-result").textContent = e; }
}

/* ==================== 饮食记录 ==================== */
function renderDates() {
  const recs = getRecords();
  const dates = [...new Set(recs.map(r => r.datetime.slice(0, 10)))].sort().reverse();
  const ul = $("date-list");
  ul.innerHTML = "";
  const entries = [null, ...dates]; // null 表示「全部」
  entries.forEach(d => {
    const li = document.createElement("li");
    li.textContent = d === null ? "全部" : d;
    const isActive = (d === null && currentDate === null) || d === currentDate;
    if (isActive) li.classList.add("active");
    li.onclick = () => { currentDate = d; renderDates(); renderRecords(); };
    ul.appendChild(li);
  });
  renderRecords();
}

function renderRecords() {
  const recs = getRecords();
  const filtered = currentDate === null ? recs : recs.filter(r => r.datetime.slice(0, 10) === currentDate);
  filtered.sort((a, b) => (a.datetime < b.datetime ? 1 : -1));

  $("record-title").textContent = currentDate === null ? "全部记录" : `${currentDate} 本日总摄入`;

  const ul = $("record-list");
  ul.innerHTML = "";
  let tk = 0, tc = 0, tp = 0, tf = 0;
  for (const r of filtered) {
    tk += r.kcal; tc += r.carbs; tp += r.protein; tf += r.fat;
    const li = document.createElement("li");
    const itemsHtml = r.items.map(it =>
      `· ${esc(it.name)} ${fmt(it.weight, 0)}g → ${fmt(it.kcal, 0)} kcal / 碳水 ${fmt(it.carbs)}g / 蛋白质 ${fmt(it.protein)}g / 脂肪 ${fmt(it.fat)}g`
    ).join("<br>");
    li.innerHTML =
      `<div class="head"><span>${esc(r.datetime)} · ${esc(r.mealPeriod)}</span><span>${fmt(r.kcal, 0)} kcal</span></div>` +
      `<div class="items">${itemsHtml}</div>` +
      `<button class="del" data-id="${r.id}">删除</button>`;
    li.querySelector(".del").onclick = () => {
      if (confirm("确定删除这条饮食记录吗？")) {
        setRecords(getRecords().filter(x => x.id !== r.id));
        renderDates();
      }
    };
    ul.appendChild(li);
  }
  $("record-summary").textContent =
    `${filtered.length} 条 · 热量 ${fmt(tk, 0)} kcal · 碳水 ${fmt(tc)} g · 蛋白质 ${fmt(tp)} g · 脂肪 ${fmt(tf)} g`;
}

/* ==================== 初始化 ==================== */
function init() {
  // 导航
  document.querySelectorAll(".tab").forEach(t => t.onclick = () => switchScreen(t.dataset.screen));

  // 性别分段
  document.querySelectorAll("#gender-seg .seg").forEach(b => {
    b.onclick = () => {
      currentGender = b.dataset.gender;
      document.querySelectorAll("#gender-seg .seg").forEach(x => x.classList.toggle("active", x === b));
    };
  });

  // 事件绑定
  $("bmr-calc").onclick = calcBmr;
  $("food-select").onchange = updateFoodInfo;
  $("add-item").onclick = addItem;
  $("clear-items").onclick = clearItems;
  $("save-record").onclick = saveRecord;
  $("m-save").onclick = saveFood;
  $("m-delete").onclick = deleteFood;
  $("d-532").onclick = calc532;
  $("d-cycle").onclick = calcCycle;

  // 初始渲染
  renderFoodSelect();
  renderFoodLibrary();
  renderItems();
  renderDates();

  // 注册 Service Worker（PWA 离线）
  if ("serviceWorker" in navigator) {
    navigator.serviceWorker.register("./sw.js").catch(() => {});
  }
}

document.addEventListener("DOMContentLoaded", init);
