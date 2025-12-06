"""
=============================================================================
FRONTEND MODULE - CRYPTO ANALYTICS SYSTEM
=============================================================================
Contains: Tkinter UI Classes, Charts, Event Handling
"""
import threading
import time
import logging
import os
import datetime
from datetime import datetime as dt_class
from typing import List
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

from core import (
    BinanceTokensFetcher,
    CryptoAnalyzer,
    TokenData,
    HistoricalData,
    TokenDocument,
    HistoricalDocument
)

logger = logging.getLogger(__name__)

# ============================================================================
# MODULE 6: USER INTERFACE (TKINTER)
# ============================================================================
class CryptoAnalyticsApp:
    """
    Main Application Class for the Crypto Analytics System.
    Handles the GUI, Event Loop, and Data Visualization.
    """
    def __init__(self, root, limit=50):
        self.root = root
        self.limit = limit

        self.root.title(f"BINANCE ANALYTICS SYSTEM - Top {self.limit} Tracker")
        self.root.geometry("1280x768")
        self.root.configure(bg='#121212')

        self.is_fetching = False
        self.fetcher = BinanceTokensFetcher(limit=self.limit)
        self.analyzer = CryptoAnalyzer()

        self.initial_prices = {}
        self.cached_data = []

        self.chart_window = None
        self.chart_canvas = None
        self.selected_token_for_chart = None
        self.ax = None
        self.chart_fig = None
        self.detail_text = None
        self.style = None
        self.colors = {}

        self.status_var = None
        self.btn_fetch = None
        self.tree = None
        self.txt_analysis = None

        self.setup_styles()
        self.create_header_section()
        self.create_status_section()
        self.create_table_section()
        self.create_analysis_section()

        self.initial_db_check()

    def setup_styles(self):
        """Configures the visual styles (colors, fonts) for the application."""
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            pass

        self.colors = {
            'bg': '#121212',
            'card': '#1e1e1e',
            'text': '#ffffff',
            'green': '#00ff88',
            'red': '#ff5555',
            'accent': '#3700b3'
        }

        self.style.configure(
            "Treeview",
            background=self.colors['card'],
            foreground=self.colors['text'],
            fieldbackground=self.colors['card'],
            rowheight=30,
            font=('Segoe UI', 10)
        )

        self.style.configure(
            "Treeview.Heading",
            background="#333333",
            foreground="white",
            font=('Segoe UI', 10, 'bold')
        )

        self.style.map("Treeview", background=[('selected', '#444444')])

    def create_header_section(self):
        """Creates the top header section."""
        header_frame = tk.Frame(self.root, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=15, padx=20)

        tk.Label(
            header_frame,
            text=f"🚀 BINANCE REAL-TIME ANALYTICS (Top {self.limit})",
            bg=self.colors['bg'],
            fg='white',
            font=('Segoe UI', 20, 'bold')
        ).pack(side='left')

    def create_status_section(self):
        """Creates the control buttons and status bar."""
        control_frame = tk.Frame(self.root, bg=self.colors['bg'])
        control_frame.pack(fill='x', padx=20, pady=5)

        self.status_var = tk.StringVar(value="System Ready. Waiting for command.")
        lbl_status = tk.Label(
            control_frame, textvariable=self.status_var,
            bg='#2c2c2c', fg=self.colors['green'],
            font=('Consolas', 11), padx=10, pady=5, anchor='w'
        )
        lbl_status.pack(side='left', fill='x', expand=True, padx=(0, 10))

        self.btn_fetch = tk.Button(
            control_frame, text="▶ START STREAM", command=self.toggle_fetching,
            bg=self.colors['green'], fg='black',
            font=('Arial', 10, 'bold'), width=15
        )
        self.btn_fetch.pack(side='left', padx=5)

        tk.Button(
            control_frame, text="📊 ANALYZE", command=self.run_analysis,
            bg=self.colors['accent'], fg='white',
            font=('Arial', 10, 'bold'), width=15
        ).pack(side='left', padx=5)

        tk.Button(
            control_frame, text="🕷️ RUN SCRAPY", command=self.run_scrapy,
            bg='#ff9800', fg='black',
            font=('Arial', 10, 'bold'), width=15
        ).pack(side='left', padx=5)

        tk.Button(
            control_frame, text="📈 CHART", command=self.open_chart_window,
            bg='#03a9f4', fg='black',
            font=('Arial', 10, 'bold'), width=15
        ).pack(side='left', padx=5)

    def create_table_section(self):
        """Creates the main data table (Treeview)."""
        table_frame = tk.Frame(self.root, bg=self.colors['bg'])
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)

        cols = ('rank', 'symbol', 'price', '24h', 'session', 'volume')
        self.tree = ttk.Treeview(table_frame, columns=cols, show='headings', height=15)

        headers = {
            'rank': '#',
            'symbol': 'Symbol',
            'price': 'Price ($)',
            '24h': '24h Change %',
            'session': 'Session %',
            'volume': 'Volume (24h)'
        }

        for col, title in headers.items():
            self.tree.heading(col, text=title)
            self.tree.column(col, anchor='center', width=120)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        self.tree.tag_configure('up', foreground=self.colors['green'])
        self.tree.tag_configure('down', foreground=self.colors['red'])
        self.tree.tag_configure('neutral', foreground='white')

        self.tree.bind("<Double-1>", self.on_tree_double_click)
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)

    def create_analysis_section(self):
        """Creates the analysis report text area."""
        report_frame = tk.LabelFrame(
            self.root, text="Analysis Report",
            bg=self.colors['bg'], fg='white', padx=10, pady=10
        )
        report_frame.pack(fill='x', padx=20, pady=10)

        self.txt_analysis = scrolledtext.ScrolledText(
            report_frame, height=8,
            bg='#1e1e1e', fg='white',
            font=('Consolas', 10), insertbackground='white'
        )
        self.txt_analysis.pack(fill='x')

    def initial_db_check(self):
        """Checks if there is existing data in MongoDB."""
        try:
            if TokenDocument.objects().limit(1):
                self.status_var.set("Database Connection: OK. Previous data found.")
        except Exception: 
            self.status_var.set("Database Connection: Ready (Empty or not connected).")

    # --- LOGIC METHODS ---

    def toggle_fetching(self):
        """Starts or stops the background fetching thread."""
        if not self.is_fetching:
            self.is_fetching = True
            self.btn_fetch.config(text="⏸ STOP STREAM", bg=self.colors['red'], fg='white')
            self.status_var.set("Initializing Binance Stream...")
            threading.Thread(target=self.fetch_loop, daemon=True).start()
        else:
            self.is_fetching = False
            self.btn_fetch.config(text="▶ START STREAM", bg=self.colors['green'], fg='black')
            self.status_var.set("Stream Stopped by User.")

    def fetch_loop(self):
        """Background loop to fetch data from API."""
        while self.is_fetching:
            try:
                tokens = self.fetcher.fetch_data()

                if tokens:
                    self.cached_data = tokens
                    self.root.after(0, self.update_token_table_safe, tokens)
                    self.save_to_mongodb(tokens)
                    timestamp_str = dt_class.now().strftime('%H:%M:%S')
                    msg = (
                        f"LIVE: {timestamp_str} | "
                        f"Tracking {len(tokens)} Assets | API: Binance"
                    )
                    self.root.after(0, lambda: self.status_var.set(msg))
                else:
                    self.root.after(
                        0, lambda: self.status_var.set("Network Lag... Retrying...")
                    )

                time.sleep(0.2)

            except Exception: 
                logger.error("Fetch loop encountered an error; continuing.")
                time.sleep(1)

    def update_token_table_safe(self, tokens: List[TokenData]):
        """Updates the Treeview with new data (Thread-Safe)."""
        self.tree.delete(*self.tree.get_children())

        for t in tokens:
            if t.symbol not in self.initial_prices:
                self.initial_prices[t.symbol] = t.current_price

            start_price = self.initial_prices[t.symbol]
            session_txt = "0.00%"
            tag = 'neutral'

            if start_price > 0:
                try:
                    diff = ((t.current_price - start_price) / start_price) * 100
                    session_txt = f"{diff:+.2f}%"
                    if diff > 0.001:
                        tag = 'up'
                    elif diff < -0.001:
                        tag = 'down'
                except ZeroDivisionError:
                    session_txt = "0.00%"
                    tag = 'neutral'

            if t.current_price < 1:
                price_fmt = f"${t.current_price:.4f}"
            else:
                price_fmt = f"${t.current_price:,.2f}"

            values = (
                t.market_cap_rank,
                t.symbol,
                price_fmt,
                f"{t.price_change_percentage_24h:+.2f}%",
                session_txt,
                f"${t.total_volume:,.0f}"
            )
            self.tree.insert('', 'end', values=values, tags=(tag,))

    def is_valid_token_id(self, token_id):
        """Validates if token ID is suitable for DB."""
        if not isinstance(token_id, str):
            return False
        token_id = token_id.strip()
        if not token_id:
            return False
        if not token_id.isalnum():
            return False
        if not 5 <= len(token_id) <= 64:
            return False
        return True

    def save_to_mongodb(self, tokens: List[TokenData]):
        """Saves fetched tokens to MongoDB."""
        try:
            for t in tokens:
                try:
                    if not self.is_valid_token_id(t.id):
                        logger.error("Skipping save: invalid token id.")
                        continue

                    existing = None
                    try:
                        existing = TokenDocument.objects(token_id=t.id).first()
                    except Exception: 
                        logger.error("DB query failed for existence check; skipping.")
                        continue

                    if existing:
                        existing.update_from_dto(t)
                    else:
                        TokenDocument.from_pydantic(t).save()

                except Exception: 
                    logger.error("Error while processing individual token for DB save.")
        except Exception: 
            pass

    def run_analysis(self):
        """Runs the analysis logic and displays the report."""
        try:
            data = self.cached_data
            if not data:
                try:
                    db_docs = TokenDocument.objects().limit(self.limit)
                    data = [TokenData(
                        id=d.token_id, symbol=d.symbol, name=d.name,
                        current_price=d.current_price,
                        price_change_percentage_24h=d.price_change_percentage_24h
                    ) for d in db_docs]
                except Exception: 
                    logger.error("Failed to load data from DB for analysis.")

            if not data:
                self.txt_analysis.insert(
                    tk.END,
                    ">>> Error: No data available for analysis. Please start stream first.\n"
                )
                return

            res = self.analyzer.analyze_trend(data)

            self.txt_analysis.delete(1.0, tk.END)
            self.txt_analysis.insert(tk.END, "=== MARKET ANALYSIS REPORT ===\n")
            self.txt_analysis.insert(tk.END, f"Timestamp: {res.get('timestamp', 'N/A')}\n")
            self.txt_analysis.insert(
                tk.END, f"Total Assets Scanned: {res.get('total_tokens', 0)}\n\n"
            )

            self.txt_analysis.insert(tk.END, "🏆 TOP GAINERS (24h):\n")
            for t in res.get('top_gainers', []):
                line = f"  • {t['symbol']:<5} : {t['change']:>+6.2f}%  (${t['price']})\n"
                self.txt_analysis.insert(tk.END, line)

            self.txt_analysis.insert(tk.END, "\n📉 TOP LOSERS (24h):\n")
            for t in res.get('top_losers', []):
                line = f"  • {t['symbol']:<5} : {t['change']:>+6.2f}%  (${t['price']})\n"
                self.txt_analysis.insert(tk.END, line)

        except Exception: 
            self.txt_analysis.insert(tk.END, "Analysis Failed: internal error occurred.\n")
            logger.error("Analysis failed to run.")

    def run_scrapy(self):
        """Generates and runs a Scrapy spider dynamically."""
        try:
            spider_code = '''
import scrapy
import json
from datetime import datetime

class BinanceSpider(scrapy.Spider):
    name = "binance_spider"
    start_urls = ["https://api.binance.com/api/v3/ticker/24hr"]

    def parse(self, response):
        data = json.loads(response.text)
        usdt_pairs = [d for d in data if d['symbol'].endswith('USDT')]
        usdt_pairs.sort(key=lambda x: float(x.get('quoteVolume', 0)), reverse=True)
        for item in usdt_pairs[:20]:
            yield {
                'symbol': item['symbol'],
                'last_price': item['lastPrice'],
                'volume_24h': item['quoteVolume'],
                'price_change_pct': item['priceChangePercent'],
                'scraped_at': datetime.now().isoformat()
            }
'''
            with open('binance_spider.py', 'w', encoding='utf-8') as f:
                f.write(spider_code)

            self.txt_analysis.insert(tk.END, "\n>>> Running Scrapy Spider...\n")
            self.root.update()

            os.system('scrapy runspider binance_spider.py -o binance_data.json')

            messagebox.showinfo(
                "Success", "Scrapy Spider Finished!\nData saved to 'binance_data.json'"
            )
            self.txt_analysis.insert(tk.END, ">>> Scrapy Task Completed Successfully.\n")

        except Exception: 
            messagebox.showerror("Scrapy Error", "Scrapy failed. Check logs.")
            logger.error("Scrapy execution failed.")

    def on_tree_select(self, _event):
        """Store selected token symbol for chart preview."""
        try:
            sel = self.tree.selection()
            if not sel:
                return
            item = self.tree.item(sel[0])
            symbol = item['values'][1]
            self.selected_token_for_chart = symbol
        except Exception: 
            pass

    def on_tree_double_click(self, event):
        """Open chart window on double click."""
        self.on_tree_select(event)
        self.open_chart_window()

    def open_chart_window(self):
        """Creates or focuses the chart window."""
        try:
            if self.chart_window and tk.Toplevel.winfo_exists(self.chart_window):
                self.chart_window.lift()
                self.update_chart_window()
                return

            self.chart_window = tk.Toplevel(self.root)
            self.chart_window.title("Coin Detail & Chart")
            self.chart_window.geometry("900x600")
            self.chart_window.configure(bg=self.colors['bg'])

            left_frame = tk.Frame(self.chart_window, bg=self.colors['bg'])
            left_frame.pack(side='left', fill='both', expand=True, padx=10, pady=10)

            fig = plt.Figure(figsize=(6, 4), dpi=100)
            self.ax = fig.add_subplot(111)
            self.ax.set_title("Price (last days)")
            self.ax.set_xlabel("Date")
            self.ax.set_ylabel("Price (USDT)")

            canvas = FigureCanvasTkAgg(fig, master=left_frame)
            canvas.get_tk_widget().pack(fill='both', expand=True)
            self.chart_canvas = canvas
            self.chart_fig = fig

            right_frame = tk.Frame(
                self.chart_window, width=300, bg=self.colors['card']
            )
            right_frame.pack(side='right', fill='y', padx=10, pady=10)

            lbl_title = tk.Label(
                right_frame, text="Coin Detail", bg=self.colors['card'],
                fg='white', font=('Segoe UI', 14, 'bold')
            )
            lbl_title.pack(pady=(10, 5))

            self.detail_text = scrolledtext.ScrolledText(
                right_frame, width=30, height=20,
                bg=self.colors['card'], fg='white', font=('Consolas', 10),
                insertbackground='white'
            )
            self.detail_text.pack(padx=5, pady=5, fill='y')

            tk.Button(
                right_frame, text="🔄 Refresh", command=self.update_chart_window,
                bg=self.colors['accent'], fg='white', font=('Arial', 10, 'bold')
            ).pack(pady=10)

            self.update_chart_window()

        except Exception as e: 
            logger.error("Failed to open chart window: %s", e)
            messagebox.showerror("Error", "Unable to open chart window.")

    def update_chart_window(self):
        """Populate detail panel and draw chart for selected token."""
        try:
            symbol = self.selected_token_for_chart
            if not symbol:
                children = self.tree.get_children()
                if not children:
                    self.detail_text.delete(1.0, tk.END)
                    self.detail_text.insert(tk.END, "No data. Start stream first.")
                    return
                item = self.tree.item(children[0])
                symbol = item['values'][1]
                self.selected_token_for_chart = symbol

            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, f"Loading {symbol}...\n")

            token_obj = None
            for t in self.cached_data:
                if t.symbol == symbol:
                    token_obj = t
                    break

            details = []
            if token_obj:
                details.append(f"Symbol: {token_obj.symbol}")
                details.append(f"Full ID: {token_obj.id}")
                details.append(f"Name: {token_obj.name}")
                details.append(f"Price: ${token_obj.current_price:,.6g}")
                change = token_obj.price_change_percentage_24h
                details.append(f"24h Change: {change:+.2f}%")
                details.append(f"Volume (24h): ${token_obj.total_volume:,.0f}")
                cat_val = token_obj.category.value if token_obj.category else 'N/A'
                details.append(f"Category: {cat_val}")
            else:
                details.append(f"Symbol: {symbol}")
                details.append("Live data not found in cache. Refresh.")

            details.append(f"\nData fetched at: {dt_class.now().isoformat()}")

            self.detail_text.delete(1.0, tk.END)
            self.detail_text.insert(tk.END, "\n".join(details))

            hist = []
            try:
                param = symbol if symbol.upper().endswith('USDT') else f"{symbol}USDT"
                hist = self.fetcher.fetch_historical(param, days=30)
            except Exception: 
                hist = []

            if not hist:
                try:
                    docs = HistoricalDocument.objects(
                        token_id__icontains=symbol
                    ).order_by('-timestamp').limit(30)
                    hist = [
                        HistoricalData(
                            timestamp=d.timestamp, token_id=d.token_id,
                            price=d.price, volume=d.volume, market_cap=d.market_cap
                        ) for d in docs
                    ]
                    hist = list(reversed(hist))
                except Exception: 
                    hist = []

            if not hist and token_obj:
                now = dt_class.now()
                hist = []
                for i in range(30):
                    _ts = now - (30 - i) * datetime.timedelta(days=1)
                    hist.append(HistoricalData(
                        timestamp=now, token_id=symbol,
                        price=token_obj.current_price, volume=0.0, market_cap=0.0
                    ))

            self.ax.clear()
            if hist:
                xs = [h.timestamp for h in hist]
                ys = [h.price for h in hist]
                self.ax.plot(xs, ys)
                self.ax.set_title(f"{symbol} - Last {len(hist)} days")
                self.ax.set_xlabel("Date")
                self.ax.set_ylabel("Price (USDT)")
                self.ax.grid(True)
            else:
                self.ax.text(
                    0.5, 0.5, "No historical data available",
                    transform=self.ax.transAxes, ha='center', va='center'
                )

            if self.chart_canvas:
                self.chart_canvas.draw()

        except Exception as e: 
            logger.error("Error updating chart window: %s", e)
            self.detail_text.insert(tk.END, "\n\nError loading chart data.\n")