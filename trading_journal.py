import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import pandas as pd
import pickle
from datetime import datetime
from PIL import Image, ImageTk, ImageGrab

class TradingJournal:
    def __init__(self, root):
        self.root = root
        self.root.title("Trading Journal")
        self.root.geometry("1200x800")
        self.trades = self.load_trades()
        self.pairs = self.load_pairs()
        self.validate_trades()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        self.create_menu()
        self.create_calendar()
        self.create_stats_sections()  # Ensure stats sections are created
        self.add_logo()

    def add_logo(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            logo_path = os.path.join(script_dir, 'logo.webp')
            logo = Image.open(logo_path)
            logo = logo.resize((50, 50), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(logo)
            self.logo_label = tk.Label(self.root, image=self.logo_img)
            self.logo_label.place(x=20, y=30)
        except Exception as e:
            print(f"Error loading logo: {e}")

    def create_menu(self):
        menubar = tk.Menu(self.root)
        options_menu = tk.Menu(menubar, tearoff=0)
        options_menu.add_command(label="Manage Pairs", command=self.manage_pairs)
        options_menu.add_command(label="View Yearly Stats", command=self.view_yearly_stats)
        options_menu.add_command(label="View All Trades", command=self.view_all_trades)
        menubar.add_cascade(label="Options", menu=options_menu)
        self.root.config(menu=menubar)

    def create_calendar(self):
        self.calendar_frame = ttk.LabelFrame(self.root, text="Calendar")
        self.calendar_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.month_var = tk.StringVar()
        current_year = datetime.now().year
        current_month = datetime.now().strftime('%B')
        self.year_var = tk.StringVar()
        self.year_var.set(current_year)
        self.month_var.set(current_month)

        self.year_selector_frame = ttk.Frame(self.calendar_frame)
        self.year_selector_frame.grid(row=0, column=0, padx=5, pady=5)
        years = [str(current_year + i) for i in range(3)]
        for year in years:
            button = ttk.Radiobutton(self.year_selector_frame, text=year, variable=self.year_var, value=year,
                                     command=self.update_calendar)
            button.pack(side=tk.LEFT)

        months = [datetime(1900, i, 1).strftime('%B') for i in range(1, 13)]

        month_menu = ttk.OptionMenu(self.calendar_frame, self.month_var, current_month, *months, command=self.update_calendar)
        month_menu.grid(row=0, column=1, padx=5, pady=5)

        self.calendar_grid = ttk.Frame(self.calendar_frame)
        self.calendar_grid.grid(row=1, column=0, columnspan=2, padx=5, pady=5, sticky="nsew")
        self.calendar_frame.rowconfigure(1, weight=1)
        self.calendar_frame.columnconfigure(0, weight=1)
        self.update_calendar()

    def update_calendar(self, *args):
        for widget in self.calendar_grid.winfo_children():
            widget.destroy()

        selected_month = self.month_var.get()
        month_index = datetime.strptime(selected_month, '%B').month
        year = int(self.year_var.get())
        num_days = (pd.Timestamp(year, month_index + 1, 1) - pd.Timestamp(year, month_index, 1)).days if month_index < 12 else 31

        days_of_week = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
        for i, day in enumerate(days_of_week):
            tk.Label(self.calendar_grid, text=day).grid(row=0, column=i)

        first_day_of_month = (datetime(year, month_index, 1).weekday() + 1) % 7  # Adjusting to start the week from Sunday
        for day in range(1, num_days + 1):
            trade_info = self.trades.get((year, month_index, day))

            button_text = str(day)
            if trade_info:
                profit_loss = sum(trade['amount'] for trade in trade_info) if trade_info else 0
                trade_count = len(trade_info) if trade_info else 0
                button_text += f"\n${profit_loss:.2f}\n{trade_count} trades"
                color = "pale green" if profit_loss > 0 else "lightcoral" if profit_loss < 0 else "orange"
            else:
                color = "lightgrey"
                trade_count = 0

            button = tk.Button(self.calendar_grid, text=button_text,
                               command=lambda d=day: self.view_trades(year, month_index, d))
            button.config(bg=color)
            button.grid(row=(day + first_day_of_month) // 7 + 1, column=(day + first_day_of_month) % 7, padx=5, pady=5, ipadx=10, ipady=10, sticky="nsew")

        for i in range(7):
            self.calendar_grid.columnconfigure(i, weight=1)
        for i in range((num_days + first_day_of_month) // 7 + 2):
            self.calendar_grid.rowconfigure(i, weight=1)

        self.update_summary()

    def view_trades(self, year, month, day):
        new_window = tk.Toplevel(self.root)
        new_window.title(f"Trades on {day}-{month}-{year}")

        self.display_trades_in_window(new_window, year, month, day)

    def display_trades_in_window(self, window, year, month, day):
        for widget in window.winfo_children():
            widget.destroy()

        trades = self.trades.get((year, month, day), [])

        for i, trade in enumerate(trades):
            trade_frame = ttk.LabelFrame(window, text=f"Trade {i + 1}")
            trade_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            for key, value in trade.items():
                if key != 'screenshot' and key != 'comment':
                    tk.Label(trade_frame, text=f"{key.capitalize()}: {value}").pack(anchor='w')
                elif key == 'screenshot':
                    screenshot_button = ttk.Button(trade_frame, text="View Screenshot",
                                                   command=lambda p=value: self.view_screenshot(p))
                    screenshot_button.pack(anchor='w')
                elif key == 'comment':
                    comment_button = ttk.Button(trade_frame, text="View Comment",
                                                command=lambda p=value: self.view_comment(p, trade_frame))
                    comment_button.pack(anchor='w')

            delete_button = ttk.Button(trade_frame, text="Delete Trade",
                                       command=lambda i=i: self.delete_trade(year, month, day, i, window))
            delete_button.pack(anchor='e', pady=5)

        add_button = ttk.Button(window, text="Add Trade",
                                command=lambda: self.open_add_trade_window(year, month, day, window))
        add_button.pack(pady=10)

    def open_add_trade_window(self, year, month, day, parent_window):
        parent_window.destroy()
        self.add_trade(year, month, day)

    def view_screenshot(self, filepath):
        try:
            if os.path.exists(filepath):
                os.startfile(filepath)  # Use os.startfile for Windows
            else:
                print(f"File not found: {filepath}")  # Debugging print statement
                messagebox.showerror("File Not Found", "The screenshot file does not exist.")
        except Exception as e:
            print(f"Error opening file: {e}")  # Error handling
            messagebox.showerror("File Open Error", f"An error occurred while opening the file:\n{e}")

    def view_comment(self, comment, parent_frame):
        comment_frame = ttk.LabelFrame(parent_frame, text="Comment")
        comment_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        comment_label = tk.Label(comment_frame, text=comment)
        comment_label.pack(anchor='w')

        edit_button = ttk.Button(comment_frame, text="Edit Comment", command=lambda: self.edit_comment(comment_label))
        edit_button.pack(anchor='e', pady=5)

        delete_button = ttk.Button(comment_frame, text="Delete Comment",
                                   command=lambda: self.delete_comment(comment_frame, comment_label))
        delete_button.pack(anchor='e', pady=5)

    def edit_comment(self, comment_label):
        comment_entry = tk.Entry(comment_label.master)
        comment_entry.insert(0, comment_label.cget("text"))
        comment_entry.pack(anchor='w')

        save_button = ttk.Button(comment_label.master, text="Save Comment",
                                 command=lambda: self.save_comment(comment_label, comment_entry, save_button))
        save_button.pack(anchor='e', pady=5)

    def save_comment(self, comment_label, comment_entry, save_button):
        new_comment = comment_entry.get()
        comment_label.config(text=new_comment)
        comment_entry.pack_forget()
        save_button.pack_forget()

    def delete_comment(self, comment_frame, comment_label):
        comment_frame.pack_forget()

    def delete_trade(self, year, month, day, index, window):
        del self.trades[(year, month, day)][index]
        if not self.trades[(year, month, day)]:
            del self.trades[(year, month, day)]

        self.save_trades()
        self.update_calendar()
        self.update_summary()
        self.update_year_stats()
        self.display_trades_in_window(window, year, month, day)

    def add_trade(self, year, month, day, parent_window=None):
        new_window = tk.Toplevel(self.root)
        new_window.title(f"Add Trade for {day}-{month}-{year}")

        fields = ['Pair', 'Session', 'Timeframe', 'Buy/Sell', 'Amount', 'Screenshot', 'Comment']
        entries = {}

        for i, field in enumerate(fields):
            tk.Label(new_window, text=f"{field}:").grid(row=i, column=0)
            if field == 'Session':
                entries[field] = ttk.Combobox(new_window, values=['Asia', 'London', 'New York'])
            elif field == 'Buy/Sell':
                entries[field] = ttk.Combobox(new_window, values=['Buy', 'Sell'])
            elif field == 'Pair':
                entries[field] = ttk.Combobox(new_window, values=self.pairs)
            else:
                entries[field] = tk.Entry(new_window)
            entries[field].grid(row=i, column=1)

            if field == 'Screenshot':
                browse_button = ttk.Button(new_window, text="Paste Screenshot",
                                           command=lambda e=entries[field]: self.browse_screenshot(e, year, month, day,
                                                                                                  entries['Pair'].get()))
                browse_button.grid(row=i, column=2)

                select_file_button = ttk.Button(new_window, text="Select File",
                                                command=lambda e=entries[field]: self.select_image_file(e))
                select_file_button.grid(row=i, column=3)

        save_button = ttk.Button(new_window, text="Save Trade",
                                 command=lambda: self.save_trade(entries, year, month, day, new_window, parent_window))
        save_button.grid(row=len(fields), column=1, pady=10)

    def browse_screenshot(self, entry, year, month, day, pair):
        try:
            # Create the screenshots directory if it doesn't exist
            script_dir = os.path.dirname(os.path.abspath(__file__))
            screenshots_dir = os.path.join(script_dir, "screenshots")
            if not os.path.exists(screenshots_dir):
                os.makedirs(screenshots_dir)

            # Ensure pair does not contain any invalid characters for filenames
            pair_safe = pair.replace('/', '_')

            # Get the image from the clipboard
            image = ImageGrab.grabclipboard()

            # Ensure the image is of the correct type
            if isinstance(image, list):
                image = next((img for img in image if isinstance(img, Image.Image)), None)

            if image:
                # Format the filename
                existing_files = [f for f in os.listdir(screenshots_dir) if f.startswith(f"{pair_safe}-{year}-{month:02d}-{day:02d}")]
                occurrence = len(existing_files) + 1
                filename = os.path.join(screenshots_dir, f"{pair_safe}-{year}-{month:02d}-{day:02d}-{occurrence}.png")

                # Save the image
                image.save(filename, "PNG")

                # Update the entry with the new filename
                print(f"Saved file: {filename}")
                entry.delete(0, tk.END)
                entry.insert(0, filename)
            else:
                print("No image found in clipboard.")
                messagebox.showerror("Clipboard Error", "No image found in the clipboard.")
        except Exception as e:
            print(f"Error occurred while capturing screenshot: {e}")
            messagebox.showerror("Screenshot Error", f"An error occurred while capturing the screenshot:\n{e}")

    def select_image_file(self, entry):
        filetypes = [
            ('Image files', '*.png;*.jpg;*.jpeg;*.bmp;*.gif'),
            ('All files', '*.*')
        ]
        filepath = filedialog.askopenfilename(title='Select an image file', filetypes=filetypes)
        if filepath:
            entry.delete(0, tk.END)
            entry.insert(0, filepath)

    def save_trade(self, entries, year, month, day, window, parent_window):
        try:
            amount = float(entries['Amount'].get())
            trade_info = {
                'pair': entries['Pair'].get(),
                'session': entries['Session'].get(),
                'timeframe': entries['Timeframe'].get(),
                'buy_sell': entries['Buy/Sell'].get(),
                'amount': amount,
                'screenshot': entries['Screenshot'].get(),
                'comment': entries['Comment'].get()
            }

            if (year, month, day) not in self.trades:
                self.trades[(year, month, day)] = []

            self.trades[(year, month, day)].append(trade_info)

            self.update_calendar()
            self.update_summary()
            self.update_year_stats()
            self.save_trades()
            window.destroy()  # Close the Add Trade window
            if parent_window:
                self.display_trades_in_window(parent_window, year, month, day)
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter a valid number for the amount.")

    def create_stats_sections(self):
        self.stats_frame = ttk.Frame(self.root, padding=(10, 5))
        self.stats_frame.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

        self.monthly_summary_frame = ttk.LabelFrame(self.stats_frame, text="Monthly Summary")
        self.monthly_summary_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.monthly_profit_label = tk.Label(self.monthly_summary_frame, text="Monthly Profit/Loss: $0",
                                             font=("Comic Sans MS", 14, "bold"))
        self.monthly_profit_label.pack(anchor='w', padx=5, pady=2)

        self.win_rate_label = tk.Label(self.monthly_summary_frame, text="Win Rate: 0%", font=("Comic Sans MS", 14, "bold"))
        self.win_rate_label.pack(anchor='w', padx=5, pady=2)

        self.total_trades_label = tk.Label(self.monthly_summary_frame, text="Total Trades: 0", font=("Comic Sans MS", 14, "bold"))
        self.total_trades_label.pack(anchor='w', padx=5, pady=2)

        self.update_summary()

    def update_summary(self):
        try:
            selected_month = self.month_var.get()
            month_index = datetime.strptime(selected_month, '%B').month
            year = int(self.year_var.get())

            # Filter trades for the selected month and year
            monthly_trades = {k: v for k, v in self.trades.items() if k[0] == year and k[1] == month_index}
            total = sum(trade['amount'] for trades in monthly_trades.values() for trade in trades if isinstance(trades, list) and isinstance(trade, dict))
            wins = sum(1 for trades in monthly_trades.values() for trade in trades if isinstance(trades, list) and isinstance(trade, dict) and trade['amount'] > 0)
            total_trades = sum(len(trades) for trades in monthly_trades.values() if isinstance(trades, list))
            win_rate = (wins / total_trades) * 100 if total_trades > 0 else 0

            self.monthly_profit_label.config(text=f"Monthly Profit/Loss: ${total:.2f}")
            self.win_rate_label.config(text=f"Win Rate: {win_rate:.2f}%")
            self.total_trades_label.config(text=f"Total Trades: {total_trades}")

            if total >= 0:
                self.monthly_profit_label.config(bg='lime', fg='black')
            else:
                self.monthly_profit_label.config(bg='red', fg='white')

        except Exception as e:
            print(f"Error updating summary: {e}")

    def view_yearly_stats(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Yearly Stats")

        self.year_stats_label = tk.Label(new_window, text="Yearly Stats will be displayed here", font=("Comic Sans MS", 14))
        self.year_stats_label.pack()

        self.update_year_stats()

    def update_year_stats(self):
        selected_year = int(self.year_var.get())

        yearly_trades = {k: v for k, v in self.trades.items() if k[0] == selected_year}
        pair_stats = self.calculate_pair_stats(yearly_trades)
        total_profit_loss = sum(trade['amount'] for trades in yearly_trades.values() for trade in trades if isinstance(trades, list) and isinstance(trade, dict))

        stats_text = f"Total Profit/Loss: ${total_profit_loss:.2f}\n\n"
        for pair, stats in pair_stats.items():
            stats_text += f"Pair: {pair}\n"
            stats_text += f"Win Rate: {stats['win_rate']:.2f}%\n"
            stats_text += f"Total Trades: {stats['total_trades']}\n\n"

        self.year_stats_label.config(text=stats_text)

    def calculate_pair_stats(self, trades):
        pair_totals = {}
        pair_wins = {}
        for trades_list in trades.values():
            if isinstance(trades_list, list):
                for trade in trades_list:
                    if isinstance(trade, dict):
                        pair = trade['pair']
                        pair_totals[pair] = pair_totals.get(pair, 0) + 1
                        if trade['amount'] > 0:
                            pair_wins[pair] = pair_wins.get(pair, 0) + 1

        pair_stats = {}
        for pair in pair_totals.keys():
            win_rate = (pair_wins.get(pair, 0) / pair_totals[pair]) * 100
            pair_stats[pair] = {
                'win_rate': win_rate,
                'total_trades': pair_totals[pair]
            }

        return pair_stats

    def view_all_trades(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("All Trades")

        self.current_page = 0
        self.trades_per_page = 4

        self.trade_display_frame = ttk.Frame(new_window)
        self.trade_display_frame.pack(fill=tk.BOTH, expand=True)

        self.pagination_frame = ttk.Frame(new_window)
        self.pagination_frame.pack(fill=tk.X, pady=10)

        self.prev_button = ttk.Button(self.pagination_frame, text="Previous", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5)

        self.next_button = ttk.Button(self.pagination_frame, text="Next", command=self.next_page)
        self.next_button.pack(side=tk.RIGHT, padx=5)

        self.display_trades()

    def display_trades(self):
        for widget in self.trade_display_frame.winfo_children():
            widget.destroy()

        all_trades = sorted([(date, trade) for date, trades in self.trades.items() for trade in trades], key=lambda x: x[0])

        start_index = self.current_page * self.trades_per_page
        end_index = start_index + self.trades_per_page

        for date, trade in all_trades[start_index:end_index]:
            trade_frame = ttk.LabelFrame(self.trade_display_frame, text=f"Trade on {date[2]}-{date[1]}-{date[0]}")
            trade_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

            screenshot_path = trade.get('screenshot', 'No screenshot available')
            screenshot_label = tk.Label(trade_frame, text=f"Screenshot: {screenshot_path}")
            screenshot_label.pack(anchor='w')

            for key, value in trade.items():
                if key != 'screenshot':
                    tk.Label(trade_frame, text=f"{key.capitalize()}: {value}").pack(anchor='w')

        self.update_pagination_buttons(len(all_trades))

    def update_pagination_buttons(self, total_trades):
        self.prev_button.config(state=tk.NORMAL if self.current_page > 0 else tk.DISABLED)
        self.next_button.config(state=tk.NORMAL if (self.current_page + 1) * self.trades_per_page < total_trades else tk.DISABLED)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.display_trades()

    def next_page(self):
        self.current_page += 1
        self.display_trades()

    def save_trades(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            trades_path = os.path.join(script_dir, 'trades.pkl')
            with open(trades_path, 'wb') as f:
                pickle.dump(self.trades, f)
            print("Trades saved successfully.")
        except Exception as e:
            print(f"Error saving trades: {e}")

    def load_trades(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            trades_path = os.path.join(script_dir, 'trades.pkl')
            if os.path.exists(trades_path):
                with open(trades_path, 'rb') as f:
                    trades = pickle.load(f)
                    print(f"Loaded Trades: {trades}")
                    return trades
        except Exception as e:
            print(f"Error loading trades: {e}")
        return {}

    def save_pairs(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pairs_path = os.path.join(script_dir, 'pairs.pkl')
            with open(pairs_path, 'wb') as f:
                pickle.dump(self.pairs, f)
            print("Pairs saved successfully.")
        except Exception as e:
            print(f"Error saving pairs: {e}")

    def load_pairs(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            pairs_path = os.path.join(script_dir, 'pairs.pkl')
            if os.path.exists(pairs_path):
                with open(pairs_path, 'rb') as f:
                    pairs = pickle.load(f)
                    return pairs
        except Exception as e:
            print(f"Error loading pairs: {e}")
        return ["EUR/USD", "USD/JPY", "GBP/USD", "USD/CHF", "AUD/USD", "USD/CAD", "NZD/USD", "Gold"]

    def validate_trades(self):
        valid_trades = {}
        for key, value in self.trades.items():
            if isinstance(key, tuple) and all(isinstance(i, int) for i in key) and isinstance(value, list):
                valid_trades[key] = [trade for trade in value if isinstance(trade, dict) and 'pair' in trade and 'amount' in trade]
        self.trades = valid_trades

    def manage_pairs(self):
        new_window = tk.Toplevel(self.root)
        new_window.title("Manage Pairs")

        pairs_listbox = tk.Listbox(new_window, selectmode=tk.SINGLE)
        pairs_listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for pair in self.pairs:
            pairs_listbox.insert(tk.END, pair)

        entry = tk.Entry(new_window)
        entry.pack(padx=10, pady=5)

        def add_pair():
            new_pair = entry.get().strip().upper()
            if new_pair and new_pair not in self.pairs:
                self.pairs.append(new_pair)
                pairs_listbox.insert(tk.END, new_pair)
                self.save_pairs()

        def delete_pair():
            selected = pairs_listbox.curselection()
            if selected:
                pair = pairs_listbox.get(selected)
                self.pairs.remove(pair)
                pairs_listbox.delete(selected)
                self.save_pairs()

        add_button = ttk.Button(new_window, text="Add Pair", command=add_pair)
        add_button.pack(pady=5)

        delete_button = ttk.Button(new_window, text="Delete Pair", command=delete_pair)
        delete_button.pack(pady=5)

    def on_closing(self):
        self.save_trades()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = TradingJournal(root)
    root.mainloop()
