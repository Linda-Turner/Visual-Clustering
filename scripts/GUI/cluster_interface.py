import csv, os
import tkinter as tk
from tkinter import ttk
from tkinter import simpledialog
import threading

from scripts.clustering.main import cluster 
from scripts.clustering.clustering_summary.clustering_terms import update_clustering_terms

class ClusterView:
    """
    Class to view the clusters visually
    """

    def __init__(self, parent, previous, input_file, output_dir, round, arguments):
        self.parent = parent
        self.previous = previous
        self.input_file = input_file
        self.output_dir = output_dir
        self.previous_output_dir = None
        # self.previous_output_dir = os.path.join('results','round_0')
        self.round = round
        self.clusters = []
        self.current_cluster = 0
        self.arguments = arguments
        self.indeterminate_running= False

        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)

        self.create_cluster_view()

    # Main frame functions
    def create_cluster_view(self):
        tk.Label(self.frame, text="Visual Clustering", font=("Arial", 16)).pack(pady=(20, 20))

        self.clustering_frame = tk.Frame(self.frame)
        self.clustering_frame.pack(fill="both", expand=True)

        self.action_label_frame = tk.Frame(self.clustering_frame)
        self.action_label_frame.pack(pady=10)
        self.action_label = tk.Label(self.action_label_frame, text=f"Press the 'Start Clustering' button to start the clustering", font=("Arial", 14))
        self.action_label.pack(pady=(0, 20))

        self.clustering_progress_frame = tk.Frame(self.clustering_frame)
        self.clustering_progress_frame.pack(fill="both", expand=True)

        tk.Label(self.clustering_progress_frame, text="Progress status:", font=("Arial", 14)).pack(pady=(0, 10))
        self.status_label = tk.Label(self.clustering_progress_frame, text=f"", font=("Arial", 12))
        self.step_status_label = tk.Label(self.clustering_progress_frame, text=f"", font=("Arial", 10))
        self.progress_bar_status = tk.Label(self.clustering_progress_frame, text="", font=("Arial", 10))
        self.progress_bar = ttk.Progressbar(self.clustering_progress_frame,orient="horizontal",length=400,mode="indeterminate")

        self.button_frame = tk.Frame(self.clustering_frame)
        self.button_frame.pack(pady=10)
        self.run_button = tk.Button(self.button_frame,text="Start Clustering",command=self.run_clustering_round)
        self.run_button.pack(side="left", padx=5)
        self.review_cluster = tk.Button(self.button_frame,text="Review Clusters",command=self.review_clustering)
        self.review_cluster.pack(side="left", padx=5)
        self.review_cluster.config(state="disabled")
        self.finish_button = tk.Button(self.clustering_frame,text="Finish Clusterings",command=self.finish_clustering)
        self.finish_button.pack(pady=(0,10))

        self.results_frame = tk.Frame(self.frame)

    def update_cluster_view(self, number_updated_ids):
        """
        Update the cluster view for a new round of clustering.
        """
        # self.status_label.pack_forget()
        self.step_status_label.pack_forget()
        self.progress_bar_status.pack_forget()
        if self.indeterminate_running:
            self.progress_bar.stop()
            self.indeterminate_running = False
        self.progress_bar.pack_forget()

        self.action_label.config(text=f"Press 'Start Clustering' to restart the clustering or 'Finish Clusterings' to end the clustering process.")
        self.action_label.pack(pady=(0, 20))
        self.run_button.config(state="normal")
        self.finish_button.config(state='normal')

        self.status_label.config(
                 text=f"Manual adjustment of clustering results for round {self.round} finished! \n The clustering results have been stored and your adjustments have been saved. \n {str(number_updated_ids)} sentences have been changed.")

        self.previous_output_dir = self.round_output_dir
        self.round += 1
        print(self.round, self.previous_output_dir, self.input_file)


    # Perform the clustering 
    def run_clustering_round(self):
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        self.action_label.config(text=f"Currently no action needed.")
        self.status_label.config(text=f"Round {self.round} clustering in progress...")
        self.status_label.pack(pady=(0, 10))
        self.step_status_label.config(text=f"")
        self.step_status_label.pack(pady=(0, 10))
        self.progress_bar_status.pack(pady=(0,5))
        self.progress_bar.pack(pady=(0, 20))
        self.run_button.config(state="disabled")
        self.finish_button.config(state="disabled")
        # Main clustering function
        self.round_output_dir = os.path.join(self.output_dir, f"round_{self.round}")
        if not os.path.exists(self.round_output_dir):
            os.makedirs(self.round_output_dir)
        threading.Thread(target=self.clustering_background, daemon=True).start()

    def clustering_background(self):
        def progress_callback(current, total, message):
            self.parent.after(0, self.update_progress, current, total, message)
        def indeterminate_callback(message):
            self.parent.after(0,self.update_indeterminate, message)
        def step_callback(step):
            self.parent.after(0,self.update_step,step)
        cluster_terms_filepath, key_terms_filepath = cluster(self.input_file,self.round_output_dir,self.previous_output_dir,self.arguments,self.round,progress_callback,indeterminate_callback, step_callback)
        self.parent.after(0,self.clustering_finished,cluster_terms_filepath,key_terms_filepath)

    def clustering_finished(self, cluster_terms_filepath, key_terms_filepath):
        self.cluster_terms_filepath = cluster_terms_filepath
        self.status_label.config(text="Clustering finished!")
        self.step_status_label.pack_forget()
        self.progress_bar_status.pack_forget()
        if self.indeterminate_running:
            self.progress_bar.stop()
            self.indeterminate_running = False
        self.progress_bar.pack_forget()
        self.action_label.config(text="Press 'Review Clusters' to manually inspect and alter the clusters.")
        self.action_label_frame.pack(pady=(20, 0),before=self.clustering_progress_frame)
        # self.run_button.config(state="normal")
        # self.finish_button.config(state="normal")
        self.review_cluster.config(state="normal")


    # Show the clustering results
    def review_clustering(self):
        # Show clustering results
        self.clustering_frame.pack_forget()
        self.results_frame.pack(fill="both", expand=True)
        self.load_clustering_result('REPLACE')
        if self.clusters:
            self.show_current_cluster()

    def load_clustering_result(self, key_terms_filepath):
        """
        Read the cluster terms from the CSV file and store them in self.clusters
        """
        self.clusters = []
        with open(self.cluster_terms_filepath, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cluster  = {'cluster_id' : row['CID'],
                'silhouette' : row['Sil'],
                'size' : row['Size'],
                'terms': [{"term": row[f'Term {i}'],"selected": False,"x": None,"y": None,"merged_terms": None} for i in range(5)], 
                'merge_history' : []}
                self.clusters.append(cluster)
        self.current_cluster = 0

    def show_current_cluster(self):
        cluster = self.clusters[self.current_cluster]

        self.show_cluster(
            cluster["cluster_id"],
            cluster["silhouette"],
            cluster["size"],
            cluster["terms"]
        )

    def show_cluster(self, cluster_id, silhouette, size, terms):
        """
        Display the cluster information and terms in the results_frame
        """
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        tk.Label(self.results_frame, text="Alter cluster terms", font=("Arial", 14)).pack(pady=(20,20))
        tk.Label(self.results_frame, text=f"Results for clustering round {self.round} : Cluster {self.current_cluster + 1} of {len(self.clusters)}", font=("Arial", 11)).pack(pady=(0,3))
        tk.Label(self.results_frame,text=(f"Silhouette Score: {silhouette}  Cluster Size: {size}"), font=("Arial", 10)).pack(pady=(0, 20))

        # TODO: Display images

        tk.Label(self.results_frame, text="Top terms:", font=("Arial", 11)).pack(pady=(0, 5))

        self.term_canvas = tk.Canvas(self.results_frame,width=600,height=50,highlightthickness=1,highlightbackground="black")
        self.term_canvas.pack(pady=(0, 20))
        self.undo_button = tk.Button(self.results_frame, text="Undo last merge", command=self.undo_merge)
        self.undo_button.pack(pady=5)

        self.term_buttons = []
        for i, term_dict in enumerate(terms): 
            term = term_dict["term"]
            overstrike = term_dict["selected"]
            if overstrike:  
                font=("Arial", 10, "overstrike")
            else:  
                font=("Arial", 10)
            button = tk.Button(self.term_canvas, text=term, font=font, relief="flat", bd=0, highlightthickness=0, padx=10, pady=5)
            # Set the button position within the term_canvas
            if term_dict["x"] is None:
                x = 60 + i * 120
                y = 25
            else:
                x = term_dict["x"]
                y = term_dict["y"]
            button.merged_terms = term_dict.get("merged_terms")
            window = self.term_canvas.create_window(x, y, window=button)
            button.canvas_id  = window
            button.bind("<ButtonPress-1>", self.start_drag)
            button.bind("<B1-Motion>", self.drag)
            button.bind("<ButtonRelease-1>", self.end_drag)
            self.term_buttons.append(button)

        # Buttons to navigate between clusters
        navigation_frame = tk.Frame(self.results_frame)
        navigation_frame.pack(pady=(20, 20))
        if self.current_cluster != 0:
            tk.Button(navigation_frame, text="First Cluster", command=lambda: self.previous_cluster(first_cluster=True)).pack(side="left", padx=10)
        if self.current_cluster > 0:
            tk.Button(navigation_frame, text="Previous Cluster", command=self.previous_cluster).pack(side="left", padx=10)
        if self.current_cluster < len(self.clusters) - 1:
            tk.Button( navigation_frame, text="Next Cluster", command=self.next_cluster).pack(side="left", padx=10)
        if self.current_cluster != len(self.clusters) - 1:
            tk.Button(navigation_frame, text="Last Cluster", command=lambda: self.next_cluster(last_cluster=True)).pack(side="left", padx=10)
        tk.Button(self.results_frame, text="Finish Adjustments", command=self.finish_manual_updates).pack(pady=10)


    # Functions for moving terms around the canvas and merging them
    def start_drag(self, event):
        self.dragged_button = event.widget
        # Where the button was grabbed
        self.last_dragged_x = event.x_root
        self.last_dragged_y = event.y_root
        # Original position of the grabbed button in the term canvas
        self.dragged_original_x, self.dragged_original_y = self.term_canvas.coords(self.dragged_button.canvas_id)
        self.is_dragging = False

    def drag(self, event):
        # Movement of the button in the canvas
        dx = event.x_root - self.last_dragged_x
        dy = event.y_root - self.last_dragged_y
        if abs(dx) > 3 or abs(dy) > 3:
            self.is_dragging = True
        if not self.is_dragging:
            return
        x, y = self.term_canvas.coords(self.dragged_button.canvas_id)
        self.term_canvas.coords(self.dragged_button.canvas_id, x + dx, y + dy)
        self.last_dragged_x = event.x_root
        self.last_dragged_y = event.y_root

    def end_drag(self, event):
        if not self.is_dragging:
            self.toggle_term(self.dragged_button)
            return
        for button in self.term_buttons:
            if button == self.dragged_button:
                continue
            if self.buttons_overlap(self.dragged_button, button):
                self.merge_terms(self.dragged_button, button)
                return
        # If no merge occurred, return the button to its original position
        self.term_canvas.coords(self.dragged_button.canvas_id,self.dragged_original_x,self.dragged_original_y)

        
    # Functions used for the merging of terms
    def buttons_overlap(self, dragged_button, button):
        x1, y1 = self.term_canvas.coords(dragged_button.canvas_id)
        w1, h1 = dragged_button.winfo_width(), dragged_button.winfo_height()
        x2, y2 = self.term_canvas.coords(button.canvas_id)
        w2, h2 = button.winfo_width(), button.winfo_height()
        return (abs(x1 - x2) < (w1 + w2) / 2 and abs(y1 - y2) < (h1 + h2) / 2)

    def merge_terms(self, dragged_button, button):
        merge_history = self.clusters[self.current_cluster]['merge_history']
        term1 = dragged_button.cget("text")
        term2 = button.cget("text")
        merged_x, merged_y = self.term_canvas.coords(button.canvas_id)

        name = simpledialog.askstring("Merge terms", f"Enter a name for:\n{term1} + {term2}", parent=self.parent)
        if not name:
            self.term_canvas.coords(dragged_button.canvas_id, self.dragged_original_x, self.dragged_original_y)
            return
        previously_merged_term1 = getattr(dragged_button, "merged_terms", None)
        if previously_merged_term1 is None:
            previously_merged_term1 = [term1]
        previously_merged_term2 = getattr(button, "merged_terms", None)
        if previously_merged_term2 is None:
            previously_merged_term2 = [term2]
        merge_info = {
            "term1": previously_merged_term1,
            "term2": previously_merged_term2,
            "pos1": (self.dragged_original_x, self.dragged_original_y),
            "pos2": (merged_x, merged_y),
            "name": name
        }
        merge_history.append(merge_info)
        self.clusters[self.current_cluster]['merge_hisotry'] = merge_history
        self.term_canvas.delete(dragged_button.canvas_id)
        self.term_canvas.delete(button.canvas_id)
        self.term_buttons.remove(dragged_button)
        self.term_buttons.remove(button)
        merged_button = tk.Button(self.term_canvas, text=name, font=("Arial", 10), relief="flat", bd=0, highlightthickness=0, padx=10, pady=5)
        window = self.term_canvas.create_window(merged_x, merged_y, window=merged_button)
        merged_button.canvas_id = window
        merged_button.merged_terms = previously_merged_term1 + previously_merged_term2
        merged_button.bind("<ButtonPress-1>", self.start_drag)
        merged_button.bind("<B1-Motion>", self.drag)
        merged_button.bind("<ButtonRelease-1>", self.end_drag)
        self.term_buttons.append(merged_button)

    def undo_merge(self):
        merge_history = self.clusters[self.current_cluster]['merge_hisotry']
        if not merge_history:
            return
        merge = merge_history.pop()
        merged_button = None
        for button in self.term_buttons:
            if button.cget("text") == merge["name"]:
                merged_button = button
                break
        if merged_button is None:
            return
        self.term_canvas.delete(merged_button.canvas_id)
        self.term_buttons.remove(merged_button)
        button1 = tk.Button(self.term_canvas, text=merge["term1"], font=("Arial", 10), relief="flat", bd=0, highlightthickness=0, padx=10, pady=5)
        window1 = self.term_canvas.create_window(merge["pos1"][0], merge["pos1"][1], window=button1)
        button1.canvas_id = window1
        button2 = tk.Button(self.term_canvas, text=merge["term2"], font=("Arial", 10), relief="flat", bd=0, highlightthickness=0, padx=10, pady=5)
        window2 = self.term_canvas.create_window(merge["pos2"][0], merge["pos2"][1], window=button2)
        button2.canvas_id = window2
        for button in (button1, button2):
            button.bind("<ButtonPress-1>", self.start_drag)
            button.bind("<B1-Motion>", self.drag)
            button.bind("<ButtonRelease-1>", self.end_drag)
            self.term_buttons.append(button)


    # Function for the removal of terms from the cluster view
    def toggle_term(self, button): 
        """ Toggle a strike-through effect on a term.""" 
        current_font = button.cget("font") 
        if "overstrike" in str(current_font): 
            button.config(font=("Arial", 10)) 
        else: button.config(font=("Arial", 10, "overstrike"))


    # Saving cluster terms and their positions for the next round of clustering
    def save_current_terms(self):
        terms = []
        for button in self.term_buttons:
            x, y = self.term_canvas.coords(button.canvas_id)
            terms.append({
                "term": button.cget("text"),
                "selected": "overstrike" in str(button.cget("font")),
                "x": x,
                "y": y,
                "merged_terms": getattr(button, "merged_terms", None)
            })
        self.clusters[self.current_cluster]["terms"] = terms


    # Helper functions for navigating between clusters
    def next_cluster(self, last_cluster=False):
        self.save_current_terms()
        # print(self.clusters[self.current_cluster]["terms"])
        if last_cluster:
            self.current_cluster = len(self.clusters) - 1
        elif self.current_cluster < len(self.clusters) - 1:
            self.current_cluster += 1
        self.show_current_cluster()

    def previous_cluster(self, first_cluster=False):
        self.save_current_terms()
        if first_cluster:
            self.current_cluster = 0
        elif self.current_cluster > 0:
            self.current_cluster -= 1
        self.show_current_cluster()


    # Function to handle finishing the manual updates process 
    def finish_manual_updates(self):
        """
        Write the updated cluster terms to a CSV file and update the clusters data structure.
        """
        self.save_current_terms()
        self.results_frame.pack_forget()
        self.clustering_frame.pack(fill="both", expand=True)
        self.action_label.config(text=f"Currently no action needed.")
        self.status_label.config(text=f"Updating image decriptions in progress...")
        self.status_label.pack(pady=(0,10))
        self.step_status_label.pack_forget()
        self.progress_bar_status.pack(pady=(0,5))
        self.progress_bar.pack(pady=(0, 20))
        self.run_button.config(state="disabled")
        self.finish_button.config(state="disabled")
        self.review_cluster.config(state="disabled")
        self.next_output_dir = os.path.join(self.output_dir, f"round_{self.round + 1}") # ID	Dir	ImageID	Labels
        if self.round > 0:
            cluster_updates = os.path.join(self.round_output_dir, "cluster_updates.csv")
            os.makedirs(self.next_output_dir, exist_ok=True)
            with open(cluster_updates, 'w', encoding='utf-8', newline='') as out:
                out.write('cluster_id,term,delete,merged_terms\n')
                for cluster in self.clusters:
                    for term_dict in cluster["terms"]:
                        term = term_dict["term"]
                        delete = str(term_dict["selected"])
                        merged_terms = term_dict["merged_terms"]
                        if merged_terms:
                            terms = "|".join(merged_terms)
                        else:
                            terms = ""
                        out.write(f"{cluster['cluster_id']},{term},{delete},{terms}\n")
            out.close()
        threading.Thread(target=self.update_texts_background, args=(), daemon=True).start()

    def update_texts_background(self):
        def progress_callback(current, total, message):
            self.parent.after(0,self.update_progress,current,total,message)
        updated_input_file, number_updated_ids = update_clustering_terms(self.input_file,self.next_output_dir,self.round_output_dir, progress_callback)
        self.parent.after(0, self.update_texts_finished, updated_input_file, number_updated_ids)

    def update_texts_finished(self, updated_input_file, number_updated_ids):
        self.input_file = updated_input_file
        self.update_cluster_view(number_updated_ids)


    # Updates
    def update_progress(self, current, total, message):
        self.progress_bar_status.config(text=f"{message}: {current}/{total}")
        if self.indeterminate_running:
            self.progress_bar.stop()
            self.indeterminate_running = False
        self.progress_bar.config(mode="determinate")
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current

    def update_indeterminate(self, message):
        self.progress_bar_status.config(text=message)
        if not self.indeterminate_running:
            self.progress_bar.config(mode="indeterminate")
            self.progress_bar.start(10)
            self.indeterminate_running = True

    def update_step(self, step):
        self.step_status_label.config(text=step)


    # Finish all clustering
    def finish_clustering(self):
        """
        Finish the clustering process and return to the previous screen.
        """
        self.frame.destroy()
        self.previous.done()
