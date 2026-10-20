# -*- coding: utf-8 -*-
"""健身数据计算器 —— 主程序（Tkinter 图形界面）。

运行方式：
    python main.py

功能页：
    1. 基础代谢计算
    2. 饮食热量计算（多食物合计 + 确认记录）
    3. 食物管理（录入 / 修改 / 删除）
    4. 饮食结构计算（碳水渐降 / 碳循环）
    5. 饮食记录（按日期查询）
"""

import tkinter as tk
from tkinter import ttk, messagebox

import database
import nutrition

# ---------- 配色方案 ----------
BG = "#F1F5F9"          # 页面背景（浅灰蓝）
CARD = "#FFFFFF"        # 卡片背景
ACCENT = "#0D9488"      # 主色（青绿）
ACCENT_DARK = "#0F766E"
ACCENT_SOFT = "#CCFBF1"
TEXT = "#0F172A"        # 主文字
MUTED = "#64748B"       # 次要文字
BORDER = "#E2E8F0"

# ---------- 字体（参考 Keep 等主流应用的阅读字号） ----------
FONT = ("Microsoft YaHei", 11)
FONT_SMALL = ("Microsoft YaHei", 10)
FONT_TITLE = ("Microsoft YaHei", 18, "bold")
FONT_SECTION = ("Microsoft YaHei", 13, "bold")
FONT_BUTTON = ("Microsoft YaHei", 11, "bold")


def fmt(v, nd=1):
    """把数值格式化成带 nd 位小数的字符串。"""
    return f"{v:.{nd}f}"


def read_float(var, label):
    """读取并校验一个非负数字输入。"""
    raw = var.get().strip()
    try:
        v = float(raw)
    except ValueError:
        raise ValueError(f"「{label}」请输入有效数字")
    if v < 0:
        raise ValueError(f"「{label}」不能为负数")
    return v


def _wheel(widget, event):
    """通用鼠标滚轮滚动。"""
    if event.delta:
        widget.yview_scroll(int(-event.delta / 120), "units")
    else:
        widget.yview_scroll(-1 if event.num == 4 else 1, "units")


def setup_styles(root):
    """统一的现代样式：浅色背景 + 青绿主色 + 扁平按钮 + 卡片。"""
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    style.configure("TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD)

    style.configure("TLabel", background=BG, foreground=TEXT, font=FONT)
    style.configure("Card.TLabel", background=CARD, foreground=TEXT, font=FONT)
    style.configure("Muted.Card.TLabel", background=CARD, foreground=MUTED, font=FONT_SMALL)
    style.configure("Title.TLabel", background=BG, foreground=TEXT, font=FONT_TITLE)
    style.configure("Subtitle.TLabel", background=BG, foreground=MUTED, font=FONT_SMALL)
    style.configure("CardTitle.TLabel", background=CARD, foreground=TEXT, font=FONT_SECTION)
    style.configure("Total.TLabel", background=ACCENT_SOFT, foreground=TEXT,
                    font=FONT_BUTTON, padding=(12, 8))

    style.configure("Accent.TButton", background=ACCENT, foreground="#FFFFFF", borderwidth=0,
                    focusthickness=0, padding=(20, 9), font=FONT_BUTTON)
    style.map("Accent.TButton", background=[("active", ACCENT_DARK), ("pressed", ACCENT_DARK)])

    style.configure("Ghost.TButton", background=CARD, foreground=ACCENT, borderwidth=0,
                    focusthickness=0, padding=(14, 7), font=FONT)
    style.map("Ghost.TButton", background=[("active", ACCENT_SOFT), ("pressed", ACCENT_SOFT)],
              foreground=[("active", ACCENT_DARK)])

    style.configure("TEntry", fieldbackground="#FFFFFF", foreground=TEXT, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, padding=8)
    style.map("TEntry", bordercolor=[("focus", ACCENT)])

    style.configure("TCombobox", fieldbackground="#FFFFFF", background="#FFFFFF",
                    foreground=TEXT, bordercolor=BORDER, arrowcolor=MUTED, padding=7)
    style.map("TCombobox", fieldbackground=[("readonly", "#FFFFFF")], foreground=[("readonly", TEXT)],
              bordercolor=[("focus", ACCENT)])

    style.configure("TRadiobutton", background=CARD, foreground=TEXT, font=FONT)
    style.map("TRadiobutton", background=[("active", CARD)], foreground=[("active", ACCENT)])

    style.configure("Treeview", background=CARD, fieldbackground=CARD, foreground=TEXT,
                    rowheight=32, borderwidth=0, font=FONT)
    style.configure("Treeview.Heading", background="#F8FAFC", foreground=MUTED, borderwidth=0,
                    relief="flat", padding=8, font=FONT_BUTTON)
    style.map("Treeview", background=[("selected", ACCENT_SOFT)], foreground=[("selected", TEXT)])
    style.map("Treeview.Heading", background=[("active", "#E2E8F0")])

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", background=BORDER, foreground=MUTED, padding=(24, 12),
                    borderwidth=0, font=FONT_BUTTON)
    style.map("TNotebook.Tab", background=[("selected", ACCENT)], foreground=[("selected", "#FFFFFF")])


class ScrollableFrame(ttk.Frame):
    """可滚动的容器：Canvas + 垂直滚动条 + 鼠标滚轮。

    所有标签页都继承它，这样窗口较小时也能滚动看到底部的内容。
    """

    def __init__(self, parent):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.vsb = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.content = ttk.Frame(self.canvas, style="TFrame", padding=24)

        self._win = self.canvas.create_window((0, 0), window=self.content, anchor="nw")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.vsb.pack(side="right", fill="y")

        self.content.bind("<Configure>", self._on_content_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        # 鼠标滚轮：仅当指针在本区域内时才滚动（add="+" 允许多个标签页各自挂载）
        self._hovered = False
        self.canvas.bind("<Enter>", lambda e: self._set_hover(True))
        self.canvas.bind("<Leave>", lambda e: self._set_hover(False))
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _set_hover(self, value):
        self._hovered = value

    def _on_content_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self._win, width=event.width)

    def _on_mousewheel(self, event):
        if not self._hovered:
            return
        if isinstance(event.widget, ttk.Treeview):
            return  # 表格由自身处理滚轮
        _wheel(self.canvas, event)


def card(parent, padding=20):
    """一张白色卡片（白底 + 内边距）。"""
    return ttk.Frame(parent, style="Card.TFrame", padding=padding)


def add_header(parent, text, subtext=""):
    """页面顶部标题与副标题。"""
    ttk.Label(parent, text=text, style="Title.TLabel").pack(anchor="w")
    if subtext:
        ttk.Label(parent, text=subtext, style="Subtitle.TLabel").pack(anchor="w", pady=(4, 0))


def card_field(parent, row, label, var, unit=""):
    """在卡片内放置「标签 + 输入框 + 单位」。"""
    ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="e", pady=8, padx=(0, 12))
    entry = ttk.Entry(parent, textvariable=var, width=16)
    entry.grid(row=row, column=1, sticky="w", pady=8)
    if unit:
        ttk.Label(parent, text=unit, style="Card.TLabel").grid(row=row, column=2, sticky="w", padx=(8, 0))
    return entry


def make_tree(parent, columns, headings, widths, height=8):
    """创建带垂直滚动条的表格，返回 (容器 frame, tree)。"""
    frame = ttk.Frame(parent, style="Card.TFrame")
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)
    for col, h, w in zip(columns, headings, widths):
        tree.heading(col, text=h)
        tree.column(col, anchor="center", width=w)
    tree.pack(side="left", fill="both", expand=True)
    vsb.pack(side="right", fill="y")
    tree.bind("<MouseWheel>", lambda e: _wheel(tree, e))
    return frame, tree


class ResultPanel(tk.Text):
    """只读的结果面板。"""

    def __init__(self, parent, height=8):
        super().__init__(parent, height=height, wrap="word",
                         bg="#F8FAFC", fg=TEXT, relief="flat", borderwidth=0,
                         padx=16, pady=14, font=FONT,
                         highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT)
        self.configure(state="disabled")

    def set_text(self, text):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.insert("1.0", text)
        self.configure(state="disabled")


class BmrTab(ScrollableFrame):
    """功能 1：基础代谢计算。"""

    def __init__(self, parent):
        super().__init__(parent)
        body = self.content
        self.gender = tk.StringVar(value="男")
        self.age = tk.StringVar()
        self.height = tk.StringVar()
        self.weight = tk.StringVar()

        add_header(body, "基础代谢计算", "输入身体数据，计算静息状态下维持生命所需的每日热量（Mifflin-St Jeor 公式）")

        form = card(body)
        form.pack(fill="x", pady=(20, 14))
        ttk.Label(form, text="性别", style="Card.TLabel").grid(row=0, column=0, sticky="e", pady=8, padx=(0, 12))
        g = ttk.Frame(form, style="Card.TFrame")
        g.grid(row=0, column=1, sticky="w", pady=8)
        ttk.Radiobutton(g, text="男", variable=self.gender, value="男").pack(side="left")
        ttk.Radiobutton(g, text="女", variable=self.gender, value="女").pack(side="left", padx=(18, 0))
        card_field(form, 1, "年龄（岁）", self.age)
        card_field(form, 2, "身高（cm）", self.height)
        card_field(form, 3, "体重（kg）", self.weight)
        ttk.Button(form, text="计算基础代谢", style="Accent.TButton", command=self.calc).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(16, 2))

        self.result = ResultPanel(body, height=7)
        self.result.pack(fill="both", expand=True)

    def calc(self):
        try:
            age = read_float(self.age, "年龄")
            height = read_float(self.height, "身高")
            weight = read_float(self.weight, "体重")
        except ValueError as e:
            messagebox.showerror("输入有误", str(e))
            return

        bmr = nutrition.bmr(self.gender.get(), weight, height, age)
        self.result.set_text(
            f"性别：{self.gender.get()}\n基础代谢（BMR）：约 {fmt(bmr, 0)} kcal / 天\n\n"
            "说明：BMR 为静息状态下维持生命所需的每日热量。\n"
            "每日总消耗（TDEE）≈ BMR × 活动系数（久坐 1.2 / 轻度 1.375 / 中度 1.55 / 高强度 1.725）。"
        )


class FoodCalorieTab(ScrollableFrame):
    """功能 2：饮食热量计算（多食物合计 + 确认记录）。"""

    def __init__(self, parent):
        super().__init__(parent)
        body = self.content
        self.food_name = tk.StringVar()
        self.weight = tk.StringVar()
        self.meal_period = tk.StringVar(value="早餐")
        self._foods = {}
        self.items = []  # 本次清单，每项为 dict

        add_header(body, "饮食热量计算", "选择食物加入清单，自动汇总总热量与三大营养素，确认后写入记录")

        # —— 添加食物 ——
        add_card = card(body)
        add_card.pack(fill="x", pady=(20, 12))
        ttk.Label(add_card, text="添加食物", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=5, sticky="w", pady=(0, 8))
        ttk.Label(add_card, text="食物", style="Card.TLabel").grid(row=1, column=0, sticky="e", pady=6, padx=(0, 12))
        self.combo = ttk.Combobox(add_card, textvariable=self.food_name, state="readonly", width=18)
        self.combo.grid(row=1, column=1, sticky="w", pady=6)
        self.combo.bind("<<ComboboxSelected>>", self._on_select)
        ttk.Label(add_card, text="重量(g)", style="Card.TLabel").grid(row=1, column=2, sticky="e", pady=6, padx=(20, 12))
        ttk.Entry(add_card, textvariable=self.weight, width=10).grid(row=1, column=3, sticky="w", pady=6)
        ttk.Button(add_card, text="＋ 加入清单", style="Accent.TButton", command=self.add_item).grid(
            row=1, column=4, padx=(18, 0), pady=6)
        self.food_info = ttk.Label(add_card, text="", style="Muted.Card.TLabel")
        self.food_info.grid(row=2, column=0, columnspan=5, sticky="w", pady=(4, 0))

        # —— 本次清单 ——
        list_card = card(body)
        list_card.pack(fill="both", expand=True, pady=(0, 12))
        ttk.Label(list_card, text="本次清单", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        cols = ("name", "weight", "kcal", "carbs", "protein", "fat")
        tree_frame, self.tree = make_tree(
            list_card, cols, ("食物", "重量(g)", "热量(kcal)", "碳水(g)", "蛋白质(g)", "脂肪(g)"),
            (150, 80, 100, 90, 100, 90), height=7)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        self.total_label = ttk.Label(list_card, text="", style="Total.TLabel")
        self.total_label.grid(row=2, column=0, sticky="ew", pady=(10, 4))
        btns = ttk.Frame(list_card, style="Card.TFrame")
        btns.grid(row=3, column=0, sticky="w")
        ttk.Button(btns, text="移除所选", style="Ghost.TButton", command=self.remove_item).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="清空清单", style="Ghost.TButton", command=self.clear_items).pack(side="left")
        list_card.rowconfigure(1, weight=1)
        list_card.columnconfigure(0, weight=1)

        # —— 确认记录 ——
        save_card = card(body)
        save_card.pack(fill="x")
        ttk.Label(save_card, text="确认记录", style="CardTitle.TLabel").grid(
            row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        ttk.Label(save_card, text="餐次", style="Card.TLabel").grid(row=1, column=0, sticky="e", pady=6, padx=(0, 12))
        self.meal_combo = ttk.Combobox(save_card, textvariable=self.meal_period, state="readonly", width=10,
                                       values=("早餐", "午餐", "晚餐", "加餐"))
        self.meal_combo.grid(row=1, column=1, sticky="w", pady=6)
        ttk.Button(save_card, text="确认记录", style="Accent.TButton", command=self.save_record).grid(
            row=1, column=2, padx=(18, 0), pady=6)
        ttk.Label(save_card, text="点击后把本次清单写入数据库，自动记录日期时间，可在「饮食记录」页查询。",
                  style="Muted.Card.TLabel").grid(row=2, column=0, columnspan=3, sticky="w", pady=(4, 0))

        self.refresh()
        self._refresh_list()

    def refresh(self):
        """从数据库重新加载食物列表。"""
        self._foods = {name: (c, p, f) for name, c, p, f in database.all_foods()}
        names = list(self._foods.keys())
        self.combo["values"] = names
        if names and self.food_name.get() not in self._foods:
            self.food_name.set(names[0])
            self._show_info(names[0])

    def _on_select(self, _event=None):
        self._show_info(self.food_name.get())

    def _show_info(self, name):
        if name in self._foods:
            c, p, f = self._foods[name]
            self.food_info.configure(text=f"每 100g：碳水 {fmt(c)}g · 蛋白质 {fmt(p)}g · 脂肪 {fmt(f)}g")

    def add_item(self):
        name = self.food_name.get()
        if name not in self._foods:
            messagebox.showerror("提示", "请先选择一种食物")
            return
        try:
            weight = read_float(self.weight, "重量")
        except ValueError as e:
            messagebox.showerror("输入有误", str(e))
            return

        carbs, protein, fat = self._foods[name]
        kcal, c, p, f = nutrition.food_nutrition(weight, carbs, protein, fat)
        self.items.append({"name": name, "weight": weight, "kcal": kcal, "carbs": c, "protein": p, "fat": f})
        self.weight.set("")
        self._refresh_list()

    def _refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        tkcal = tc = tp = tf = 0.0
        for it in self.items:
            self.tree.insert("", "end", values=(
                it["name"], fmt(it["weight"], 0), fmt(it["kcal"], 0),
                fmt(it["carbs"]), fmt(it["protein"]), fmt(it["fat"])))
            tkcal += it["kcal"]
            tc += it["carbs"]
            tp += it["protein"]
            tf += it["fat"]
        self.total_label.configure(
            text=f"合计：热量 {fmt(tkcal, 0)} kcal · 碳水 {fmt(tc)} g · 蛋白质 {fmt(tp)} g · 脂肪 {fmt(tf)} g")

    def remove_item(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先在清单中选择要移除的食物")
            return
        idx = self.tree.index(sel[0])
        del self.items[idx]
        self._refresh_list()

    def clear_items(self):
        self.items.clear()
        self._refresh_list()

    def save_record(self):
        if not self.items:
            messagebox.showerror("提示", "清单为空，请先加入食物")
            return
        tkcal = sum(it["kcal"] for it in self.items)
        tc = sum(it["carbs"] for it in self.items)
        tp = sum(it["protein"] for it in self.items)
        tf = sum(it["fat"] for it in self.items)
        when = database.add_record(self.meal_period.get(), tkcal, tc, tp, tf, self.items)
        messagebox.showinfo("已记录", f"已记录「{self.meal_period.get()}」\n{when}\n\n"
                                    f"本餐：热量 {fmt(tkcal, 0)} kcal · 碳水 {fmt(tc)} g · 蛋白质 {fmt(tp)} g · 脂肪 {fmt(tf)} g")
        self.items.clear()
        self._refresh_list()


class FoodManageTab(ScrollableFrame):
    """功能 3：手动录入 / 修改 / 删除食物。"""

    def __init__(self, parent):
        super().__init__(parent)
        body = self.content
        self.name = tk.StringVar()
        self.carbs = tk.StringVar()
        self.protein = tk.StringVar()
        self.fat = tk.StringVar()

        add_header(body, "食物管理", "录入、修改或删除食物库数据，营养含量按「每 100 克」填写")

        form = card(body)
        form.pack(fill="x", pady=(20, 12))
        ttk.Label(form, text="编辑食物", style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        card_field(form, 1, "食物名称", self.name)
        card_field(form, 2, "碳水（g/100g）", self.carbs)
        card_field(form, 3, "蛋白质（g/100g）", self.protein)
        card_field(form, 4, "脂肪（g/100g）", self.fat)
        btns = ttk.Frame(form, style="Card.TFrame")
        btns.grid(row=5, column=0, columnspan=2, sticky="w", pady=(14, 2))
        ttk.Button(btns, text="保存", style="Accent.TButton", command=self.save).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="删除所选", style="Ghost.TButton", command=self.delete).pack(side="left", padx=(0, 8))
        ttk.Button(btns, text="清空输入", style="Ghost.TButton", command=self.clear).pack(side="left")

        list_card = card(body)
        list_card.pack(fill="both", expand=True)
        ttk.Label(list_card, text="当前食物库（点击一行可载入编辑）", style="CardTitle.TLabel").grid(
            row=0, column=0, sticky="w", pady=(0, 8))
        tree_frame, self.tree = make_tree(
            list_card, ("name", "carbs", "protein", "fat"),
            ("名称", "碳水", "蛋白质", "脂肪"), (150, 100, 100, 100), height=10)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        list_card.rowconfigure(1, weight=1)
        list_card.columnconfigure(0, weight=1)

        self.refresh()

    def refresh(self):
        self.tree.delete(*self.tree.get_children())
        for name, c, p, f in database.all_foods():
            self.tree.insert("", "end", values=(name, fmt(c), fmt(p), fmt(f)))

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        values = self.tree.item(sel[0], "values")
        if not values:
            return
        self.name.set(values[0])
        self.carbs.set(values[1])
        self.protein.set(values[2])
        self.fat.set(values[3])

    def clear(self):
        self.name.set("")
        self.carbs.set("")
        self.protein.set("")
        self.fat.set("")

    def delete(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("提示", "请先在列表中选择或输入要删除的食物名称")
            return
        if not messagebox.askyesno("确认删除", f"确定要删除食物「{name}」吗？"):
            return
        database.delete_food(name)
        self.clear()
        self.refresh()
        messagebox.showinfo("成功", f"已删除食物「{name}」")

    def save(self):
        name = self.name.get().strip()
        if not name:
            messagebox.showerror("输入有误", "请输入食物名称")
            return
        try:
            carbs = read_float(self.carbs, "碳水")
            protein = read_float(self.protein, "蛋白质")
            fat = read_float(self.fat, "脂肪")
        except ValueError as e:
            messagebox.showerror("输入有误", str(e))
            return

        is_new = database.add_food(name, carbs, protein, fat)
        self.refresh()
        messagebox.showinfo("成功", f"已{'新增' if is_new else '更新'}食物「{name}」")
        self.clear()


class DietStructureTab(ScrollableFrame):
    """功能 4：饮食结构计算（碳水渐降 / 碳循环）。"""

    def __init__(self, parent):
        super().__init__(parent)
        body = self.content
        self.total_kcal = tk.StringVar()
        self.body_weight = tk.StringVar()
        self.carbs_per_kg = tk.StringVar(value="3.0")
        self.protein_per_kg = tk.StringVar(value="2.0")
        self.fat_per_kg = tk.StringVar(value="0.8")

        add_header(body, "饮食结构计算", "碳水渐降与碳循环两种方案，帮你规划每日三大营养素")

        c1 = card(body)
        c1.pack(fill="x", pady=(20, 12))
        ttk.Label(c1, text="① 碳水渐降（热量占比 碳水:蛋白:脂肪 = 0.5:0.3:0.2）",
                  style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        card_field(c1, 1, "每日总热量（kcal）", self.total_kcal)
        ttk.Button(c1, text="计算碳水渐降", style="Accent.TButton", command=self.calc_532).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.result_532 = ResultPanel(c1, height=4)
        self.result_532.grid(row=3, column=0, columnspan=3, sticky="ew", pady=(10, 0))

        c2 = card(body)
        c2.pack(fill="both", expand=True)
        ttk.Label(c2, text="② 碳循环（倍数为每日平均摄入，每周 2 高碳日 + 3 中碳日 + 2 低碳日）",
                  style="CardTitle.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 8))
        card_field(c2, 1, "体重（kg）", self.body_weight)
        card_field(c2, 2, "碳水（g/kg体重）", self.carbs_per_kg)
        card_field(c2, 3, "蛋白质（g/kg体重）", self.protein_per_kg)
        card_field(c2, 4, "脂肪（g/kg体重）", self.fat_per_kg)
        ttk.Button(c2, text="计算碳循环", style="Accent.TButton", command=self.calc_cycle).grid(
            row=5, column=0, columnspan=2, sticky="w", pady=(10, 2))
        self.result_cycle = ResultPanel(c2, height=14)
        self.result_cycle.grid(row=6, column=0, columnspan=3, sticky="nsew", pady=(10, 0))
        c2.rowconfigure(6, weight=1)
        c2.columnconfigure(2, weight=1)

    def calc_532(self):
        try:
            total = read_float(self.total_kcal, "每日总热量")
        except ValueError as e:
            messagebox.showerror("输入有误", str(e))
            return
        c, p, f = nutrition.split_532(total)
        self.result_532.set_text(
            f"每日总热量：{fmt(total, 0)} kcal\n"
            f"碳水（50%）：{fmt(c)} g\n蛋白质（30%）：{fmt(p)} g\n脂肪（20%）：{fmt(f)} g"
        )

    def calc_cycle(self):
        try:
            weight = read_float(self.body_weight, "体重")
            carbs_per_kg = read_float(self.carbs_per_kg, "碳水(g/kg体重)")
            protein_per_kg = read_float(self.protein_per_kg, "蛋白质(g/kg体重)")
            fat_per_kg = read_float(self.fat_per_kg, "脂肪(g/kg体重)")
        except ValueError as e:
            messagebox.showerror("输入有误", str(e))
            return

        daily, weekly = nutrition.carb_cycling(weight, carbs_per_kg, protein_per_kg, fat_per_kg)

        count_map = {"高碳日": 2, "中碳日": 3, "低碳日": 2}
        lines = []
        for day_name in ("高碳日", "中碳日", "低碳日"):
            d = daily[day_name]
            carb_pct = 4 * d["carbs"] / d["total_kcal"] * 100
            prot_pct = 4 * d["protein"] / d["total_kcal"] * 100
            fat_pct = 9 * d["fat"] / d["total_kcal"] * 100
            lines.append(f"【{day_name}】(每周 {count_map[day_name]} 天)")
            lines.append(f"   总热量：{fmt(d['total_kcal'], 0)} kcal")
            lines.append(f"   碳水：{fmt(d['carbs'])} g   ({fmt(d['carbs'] / weight, 2)} g/kg，占 {fmt(carb_pct, 0)}%)")
            lines.append(f"   蛋白质：{fmt(d['protein'])} g   ({fmt(d['protein'] / weight, 2)} g/kg，占 {fmt(prot_pct, 0)}%)")
            lines.append(f"   脂肪：{fmt(d['fat'])} g   ({fmt(d['fat'] / weight, 2)} g/kg，占 {fmt(fat_pct, 0)}%)")
            lines.append("")

        lines.append("【每周合计】(2 高碳日 + 3 中碳日 + 2 低碳日)")
        lines.append(f"   总热量：{fmt(weekly['total_kcal'], 0)} kcal")
        lines.append(f"   碳水：{fmt(weekly['carbs'])} g")
        lines.append(f"   蛋白质：{fmt(weekly['protein'])} g")
        lines.append(f"   脂肪：{fmt(weekly['fat'])} g")

        self.result_cycle.set_text("\n".join(lines))


class RecordTab(ScrollableFrame):
    """功能 5：饮食记录（按日期查询）。"""

    def __init__(self, parent):
        super().__init__(parent)
        body = self.content
        self._dates = []
        self._current_date = None
        self._rows = []

        add_header(body, "饮食记录", "选择日期查看当天所有饮食记录与总摄入量")

        main = ttk.Frame(body)
        main.pack(fill="both", expand=True, pady=(20, 0))

        # 左侧：记录日期列表
        left = card(main)
        left.pack(side="left", fill="y", padx=(0, 12))
        ttk.Label(left, text="记录日期", style="CardTitle.TLabel").pack(anchor="w", pady=(0, 8))
        self.date_list = tk.Listbox(
            left, width=16, font=FONT, bg=CARD, fg=TEXT, relief="flat",
            highlightthickness=1, highlightbackground=BORDER, highlightcolor=ACCENT,
            activestyle="none", selectbackground=ACCENT_SOFT, selectforeground=TEXT,
            exportselection=False)
        self.date_list.pack(fill="both", expand=True)
        self.date_list.bind("<<ListboxSelect>>", self._on_date_select)
        self.date_list.bind("<MouseWheel>", lambda e: _wheel(self.date_list, e))

        # 右侧：当天记录明细
        right = card(main)
        right.pack(side="left", fill="both", expand=True)
        ttk.Label(right, text="饮食记录", style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(0, 8))
        tree_frame, self.tree = make_tree(
            right, ("time", "period", "kcal", "carbs", "protein", "fat"),
            ("时间", "餐次", "热量(kcal)", "碳水(g)", "蛋白质(g)", "脂肪(g)"),
            (130, 80, 100, 90, 100, 90), height=9)
        tree_frame.grid(row=1, column=0, sticky="nsew")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        self.summary = ttk.Label(right, text="", style="Total.TLabel")
        self.summary.grid(row=2, column=0, sticky="ew", pady=(10, 4))
        self.detail = ResultPanel(right, height=5)
        self.detail.grid(row=3, column=0, sticky="ew", pady=(0, 4))
        ttk.Button(right, text="删除所选记录", style="Ghost.TButton", command=self.delete).grid(
            row=4, column=0, sticky="w", pady=(4, 0))

        self.refresh()

    def refresh(self):
        """重新加载日期列表，并保持当前选中的日期（若仍存在）。"""
        prev = self._current_date
        self._dates = database.get_record_dates()
        self.date_list.delete(0, "end")
        self.date_list.insert("end", "全部")
        for d in self._dates:
            self.date_list.insert("end", d)
        if prev in self._dates:
            idx = self._dates.index(prev) + 1
        elif self._dates:
            idx = 1  # 默认选中最近一天
        else:
            idx = 0  # 无记录时选中「全部」
        self.date_list.selection_clear(0, "end")
        self.date_list.selection_set(idx)
        self.date_list.see(idx)
        self._on_date_select()

    def _on_date_select(self, _event=None):
        sel = self.date_list.curselection()
        if not sel:
            return
        idx = sel[0]
        if idx == 0:
            self._current_date = None
            self._load(database.get_records(None), "全部记录")
        else:
            d = self._dates[idx - 1]
            self._current_date = d
            self._load(database.get_records(d), f"{d} 本日总摄入")

    def _load(self, rows, title):
        self._rows = rows
        self.tree.delete(*self.tree.get_children())
        tkcal = tc = tp = tf = 0.0
        for r in rows:
            rid, dt, period, kcal, carbs, protein, fat, _items = r
            self.tree.insert("", "end", iid=str(rid), values=(dt, period, fmt(kcal, 0), fmt(carbs), fmt(protein), fmt(fat)))
            tkcal += kcal
            tc += carbs
            tp += protein
            tf += fat
        self.summary.configure(
            text=f"{title}：{len(rows)} 条 · 热量 {fmt(tkcal, 0)} kcal · 碳水 {fmt(tc)} g · 蛋白质 {fmt(tp)} g · 脂肪 {fmt(tf)} g"
        )
        self.detail.set_text("点击上方记录查看食物明细")

    def _on_select(self, _event=None):
        sel = self.tree.selection()
        if not sel:
            return
        rid = int(sel[0])
        for r in self._rows:
            if r[0] == rid:
                _, dt, period, kcal, carbs, protein, fat, items = r
                lines = [f"{dt} · {period}", ""]
                for it in items:
                    lines.append(
                        f"• {it['name']}  {fmt(it['weight'], 0)}g  →  {fmt(it['kcal'], 0)} kcal / "
                        f"碳水 {fmt(it['carbs'])}g / 蛋白质 {fmt(it['protein'])}g / 脂肪 {fmt(it['fat'])}g"
                    )
                lines.append("")
                lines.append(f"小计：{fmt(kcal, 0)} kcal · 碳水 {fmt(carbs)} g · 蛋白质 {fmt(protein)} g · 脂肪 {fmt(fat)} g")
                self.detail.set_text("\n".join(lines))
                break

    def delete(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("提示", "请先选择一条记录")
            return
        rid = int(sel[0])
        if not messagebox.askyesno("确认删除", "确定删除这条饮食记录吗？"):
            return
        database.delete_record(rid)
        self.refresh()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("健身数据计算器")
        self.configure(bg=BG)

        setup_styles(self)
        self._build_header()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        self.food_calorie_tab = FoodCalorieTab(nb)
        self.food_manage_tab = FoodManageTab(nb)
        self.record_tab = RecordTab(nb)
        nb.add(BmrTab(nb), text="基础代谢")
        nb.add(self.food_calorie_tab, text="饮食热量")
        nb.add(self.food_manage_tab, text="食物管理")
        nb.add(DietStructureTab(nb), text="饮食结构")
        nb.add(self.record_tab, text="饮食记录")

        nb.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        self._center(920, 800)

    def _build_header(self):
        bar = tk.Frame(self, bg=ACCENT)
        bar.pack(fill="x")
        inner = tk.Frame(bar, bg=ACCENT)
        inner.pack(fill="x", padx=28, pady=18)
        tk.Label(inner, text="健身数据计算器", bg=ACCENT, fg="#FFFFFF",
                 font=("Microsoft YaHei", 17, "bold")).pack(side="left")
        tk.Label(inner, text="基础代谢 · 饮食热量 · 食物库 · 饮食结构 · 饮食记录",
                 bg=ACCENT, fg="#CCFBF1", font=("Microsoft YaHei", 10)).pack(side="left", padx=(16, 0))

    def _center(self, w, h):
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = max((sw - w) // 2, 0)
        y = max((sh - h) // 2, 0)
        self.geometry(f"{w}x{h}+{x}+{y}")

    def _on_tab_changed(self, _event=None):
        # 食物库增删改后，切页时同步刷新各相关列表
        self.food_calorie_tab.refresh()
        self.food_manage_tab.refresh()
        self.record_tab.refresh()


def main():
    database.init_db()
    app = App()
    app.mainloop()


if __name__ == "__main__":
    main()
