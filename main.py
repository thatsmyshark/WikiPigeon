import time
import threading
import tkinter as tk
import webbrowser
import pygetwindow as gw
import requests
from bs4 import BeautifulSoup # type: ignore

class WikiPigeon:
    def __init__(self, root):
        self.root = root
        self.root.title("WikiPigeon")
        self.root.configure(bg="#2E2E2E")
        self.root.geometry("500x600+100+100")

        self.history = []
        self.last_node_positions = {}
        self.current_page = None

        self.running = False
        self.start_time = None
        self.elapsed_time = 0
        self.page_entry_time = None  # Track when a page is first visited

        self.stopwatch_color = "#cccccc"
        self.node_count = 0
        self.score = 0  # Add a score variable
        self.Backtracks = 0

        stopwatch_frame = tk.Frame(root, bg="#2E2E2E")
        stopwatch_frame.pack()

        self.time_label = tk.Label(stopwatch_frame, text="00:00:00", bg="#2e2e2e", fg=self.stopwatch_color, font=("Inter", 12))
        self.time_label.pack(side=tk.LEFT, padx=5)

        self.node_count_label = tk.Label(stopwatch_frame, text="Nodes: 0", bg="#2E2E2E", fg="light green", font=("Inter", 12))
        self.node_count_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.score_label = tk.Label(stopwatch_frame, text=": 0", bg="#2E2E2E", fg="yellow", font=("Inter", 12))
        self.score_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.Backtracks_label = tk.Label(stopwatch_frame, text="Backtracks: 0", bg="#2E2E2E", fg="#ff6961", font=("Inter", 12))
        self.Backtracks_label.pack(side=tk.LEFT, padx=5, pady=5)

        self.end_button = tk.Button(stopwatch_frame, text="End", fg="white", bg="#2e2e2e", command=self.stop)
        self.end_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.canvas_frame = tk.Frame(root)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, width=300, height=300, scrollregion=(0, 0, 10000, 10000))

        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=self.h_scrollbar.set)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set)
        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        for x in range(0, 30000, 10):
            self.canvas.create_line(x, 0, x, 30000, fill="#CCCCCC")

        for y in range(0, 30000, 10):
            self.canvas.create_line(0, y, 30000, y, fill="#CCCCCC")

        self.history_label = tk.Label(root, text="<timeline>", bg="#2e2e2e", fg="#ffffff", font=("Inter", 10, "bold"))
        self.history_label.pack()

        self.history_list = tk.Listbox(root, width=500, height=10)
        self.history_list.pack(padx=20)
        self.history_list.bind("<Double-Button-1>", self.open_in_browser)

        self.reset_button = tk.Button(root, width=6, text="Reset", fg="white", bg="#2e2e2e", command=self.reset_program)
        self.reset_button.pack(pady=5)

        tracking_thread = threading.Thread(target=self.track_wikipedia, daemon=True)
        tracking_thread.start()

    #tracks current wiki page and runs operations to update program memory
    def track_wikipedia(self):
        initial_x = 100
        fixed_y = 200

        while True:
            active_window = gw.getActiveWindow()
            if active_window:
                title = active_window.title
                if " - Wikipedia" in title:
                    self.start()
                    page_title = title.replace(" - Wikipedia", "").replace(" - Opera", "").strip()

                    if page_title != self.current_page:
                        if self.current_page and self.page_entry_time:
                            time_spent = int(time.time() - self.page_entry_time)
                            current_position = self.last_node_positions.get(self.current_page, (initial_x, fixed_y))
                            self.canvas.create_text(current_position[0], current_position[1] + 15, text=f"{time_spent}s", fill="#222222", font=("Arial", 8))

                        self.page_entry_time = time.time()  # Reset entry time for the new page

                        previous_page = self.current_page
                        self.current_page = page_title

                        if page_title not in self.history:
                            self.history.append(page_title)
                            self.update_history()
                        else:
                            self.add_score(5)  # Add 5 points if the user goes back to a previously visited page
                            self.add_Backtracks(1)

                        if previous_page:
                            parent_position = self.last_node_positions.get(previous_page, (initial_x, fixed_y))
                            new_x = parent_position[0] + 200
                            parent_y = parent_position[1]

                            if page_title in self.last_node_positions:
                                new_x, new_y = self.last_node_positions[page_title]
                            else:
                                branch_y_offset = 100
                                children = [pos for pos in self.last_node_positions.values() if pos[0] == parent_position[0] + 200]
                                new_y = parent_y + (len(children) + 1) * branch_y_offset

                                yes_hyperlink = self.check_for_hyperlink(previous_page, page_title)
                                oval_color = "light green" if yes_hyperlink else "#ff6961"

                                self.canvas.create_oval(new_x - 10, new_y - 45, new_x + 10, new_y - 25, fill=oval_color, tags="oval")
                                self.canvas.create_text(new_x, new_y, text=page_title, fill="black", font=("Arial", 8, "bold"))
                                self.node_count += 1
                                self.add_score(2)
                                self.update_node_count()

                            if yes_hyperlink:
                                self.canvas.create_line(parent_position[0], parent_position[1] - 33, new_x, new_y - 33, fill="black", tags="line")
                                self.canvas.tag_lower("line", "oval")

                            self.last_node_positions[page_title] = (new_x, new_y)
                            max_width = new_x + 300
                            max_height = new_y + 100
                            self.canvas.configure(scrollregion=(0, 0, max_width, max_height))

                        else:
                            new_x = initial_x
                            self.canvas.create_oval(new_x - 10, fixed_y - 45, new_x + 10, fixed_y - 25, fill="light green", tags="oval")
                            self.canvas.create_text(new_x, fixed_y, text=page_title, fill="black", font=("Arial", 8, "bold"))
                            self.last_node_positions[page_title] = (new_x, fixed_y)
                            self.node_count += 1
                            self.add_score(2)
                            self.update_node_count()

            time.sleep(0)

    #checks for links in prev. page to compare to current page
    def check_for_hyperlink(self, previous_page, current_page):
        if not previous_page:
            return False
        else:
            previous_page_url = f"https://en.wikipedia.org/wiki/{previous_page.replace(' ', '_')}"
            current_page_url = f"https://en.wikipedia.org/wiki/{current_page.replace(' ', '_')}"

        try:
            response = requests.get(previous_page_url)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link['href']
                if href.startswith("/wiki/"):
                    absolute_url = f"https://en.wikipedia.org{href}"
                    if absolute_url == current_page_url:
                        return True

        except requests.exceptions.RequestException as e:
            print(f"Couldn't retrieve {previous_page_url}: {e}")
        return False

    #update timeline list func
    def update_history(self):
        self.history_list.delete(0, tk.END)
        for item in self.history:
            self.history_list.insert(tk.END, item)

    #hyperlinking counting func
    def open_in_browser(self, event):
        selected_index = self.history_list.curselection()
        if selected_index:
            title = self.history_list.get(selected_index)
            webbrowser.open(f"https://en.wikipedia.org/wiki/{title.replace(' ', '_')}")

    #node counting function
    def update_node_count(self):
        self.node_count_label.config(text=f"Nodes: {self.node_count}")

    #score counting function
    def add_score(self, points):
        self.score += points
        self.score_label.config(text=f"Score: {self.score}")

    #Backtracks counting function
    def add_Backtracks(self, tbs):
        self.Backtracks += tbs
        self.Backtracks_label.config(text=f"Backtracks: {self.Backtracks}")

    #program reset function
    def reset_program(self):
        self.history = []
        self.last_node_positions = {}
        self.current_page = None
        self.canvas.delete("all")
        self.node_count = 0
        self.score = 0  # Reset score
        self.update_node_count()
        self.score_label.config(text="Score: 0")
        self.update_history()

        for x in range(0, 3000, 10):
            self.canvas.create_line(x, 0, x, 3000, fill="#CCCCCC")

        for y in range(0, 3000, 10):
            self.canvas.create_line(0, y, 3000, y, fill="#CCCCCC")

        self.running = False
        self.elapsed_time = 0
        self.time_label.config(text="00:00:00")

    #stopwatch functions
    def update_time(self):
        if self.running:
            self.elapsed_time = time.time() - self.start_time
            minutes, seconds = divmod(int(self.elapsed_time), 60)
            hours, minutes = divmod(minutes, 60)
            time_string = f"{hours:02}:{minutes:02}:{seconds:02}"
            self.time_label.config(text=time_string)

            if int(self.elapsed_time) % 60 == 0 and self.elapsed_time > 0:  # Add score every 10 seconds
                self.add_score(10)

            self.root.after(1000, self.update_time)
    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.time() - self.elapsed_time
            self.update_time()
    def stop(self):
        if self.running:
            self.running = False

if __name__ == "__main__":
    root = tk.Tk()
    root.iconbitmap(r"C:\\Users\\user\\Documents\\wikitrack\\wikipigeon.ico")
    app = WikiPigeon(root)
    root.mainloop()
