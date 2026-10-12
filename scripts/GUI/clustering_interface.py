import csv, os, ast
import pandas as pd
import tkinter as tk 
from tkinter import messagebox, ttk, simpledialog
import threading
from PIL import Image, ImageTk

from scripts.clustering.orchestrator import orchestrate_clustering 
from scripts.clustering.clustering_logic.update_cluster import update_clustering_terms
from scripts.clustering.clustering_summary.cluster_visualization_images import get_image

class ClusterView:
    """
    Class to view the clusters visually
    """

    def __init__(self, parent, previous, input_file, output_dir, round, arguments):
        self.parent = parent
        self.previous = previous
        self.indeterminate_running= False

        self.input_file = input_file
        self.output_dir = output_dir
        self.previous_output_dir = None

        self.clusters = []
        self.current_cluster = 0
        self.round = round

        self.num_keys = 7
        self.arguments = arguments

        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.create_cluster_view()

    # Main frame functions
    def create_cluster_view(self):
        self.progress_banner_frame = tk.Frame(self.frame)
        self.progress_banner_frame.pack(fill="x", expand=False)
        self.banner_frame = tk.Frame(self.frame)
        self.banner_frame.pack(fill="x", expand=False)
        self.button_frame = tk.Frame(self.frame)
        self.button_frame.pack(fill="x", expand=False)

        self.previous.show_progress_banner(2, self.progress_banner_frame, self.round)
        self.previous.show_instruction_banner(self.banner_frame, "Step 3. Clustering", 
                        "[Press the 'Start Clustering' button to start the clustering]", 
                        [])

        self.button_inner_frame = tk.Frame(self.button_frame)
        self.button_inner_frame.pack(anchor="center", pady=10)
        self.run_button = tk.Button(self.button_inner_frame,text="Start Clustering",command=self.run_clustering_round)
        self.run_button.pack(side="left", padx=5)
        self.review_cluster = tk.Button(self.button_inner_frame,text="Review Clusters",command=self.review_instructions)
        self.review_cluster.pack(side="left", padx=5)
        self.review_cluster.config(state="disabled")

        self.create_clustering_frame()
        self.create_adjustment_explanation_frame()
        self.create_adjustment_frame()
        self.create_finalizing_frame()

        self.clustering_frame.pack(fill="both", expand=True)

        self.finish_button_frame = tk.Frame(self.frame)
        self.finish_button_frame.pack(side="bottom", pady=(10,10))
        self.finish_button = tk.Button(self.finish_button_frame,text="End Clustering Tool",command=self.finish_clustering)
        self.finish_button.pack(pady=(0,0))

    def create_clustering_frame(self):
        self.clustering_frame = tk.Frame(self.frame)
        self.progress_label = tk.Label(self.clustering_frame, text="Progress status:", font=("Arial", 12))
        self.status_label = tk.Label(self.clustering_frame, text="", font=("Arial", 12))
        self.step_status_label = tk.Label(self.clustering_frame, text="", font=("Arial", 11))
        self.progress_bar_status = tk.Label(self.clustering_frame, text="", font=("Arial", 10))
        self.progress_bar = ttk.Progressbar(self.clustering_frame,orient="horizontal",length=400,mode="determinate")

    def create_adjustment_explanation_frame(self):
        self.explanation_container = tk.Frame(self.frame)
        tk.Label(self.explanation_container, text="How to adjust the clusters", font=("Arial", 13, "bold")).pack(pady=(20, 8))
        tk.Label(self.explanation_container, text=(
                "In the coming adjustment step you will see a selection of images representing the cluster"
                "together with the top k most important terms found in their image descriptions."), font=("Arial", 11), wraplength=700, justify="center").pack(pady=(0, 8))
        tk.Label(self.explanation_container, text=(
                "The clustering is based on the descriptions, so by altering the descriptions, different clusters can be made. "
                "There are two options to adjust the image descriptions."), font=("Arial", 11), wraplength=700, justify="center").pack(pady=(0, 10))
        tk.Label(self.explanation_container, text="• Delete a term", font=("Arial", 11, "bold")).pack()
        tk.Label(self.explanation_container, text=(
                "Click on a term to remove it from the descriptions. "
                "This is useful when a term is irrelevant or should not be used to base the clustering decision on."), font=("Arial", 11), wraplength=700, justify="center").pack(pady=(0, 8))
        tk.Label(self.explanation_container, text="• Merge terms", font=("Arial", 11, "bold")).pack()
        tk.Label(self.explanation_container,text=(
                "Right-click a term to change the term for a new one. "
                "You will be asked to provide a new, more informative term of your liking. "
                "The original terms in the descriptions will then be replaced by the new term in the descriptions."),font=("Arial", 11), wraplength=700, justify="center").pack(pady=(0, 8))        
        tk.Label(self.explanation_container,text=(
                "Use these adjustments to make the cluster descriptions more "
                "meaningful and better represent the images in the cluster."),font=("Arial", 11),wraplength=700,justify="center").pack(pady=(0, 8))
        tk.Label(self.explanation_container, text="• Assess cluster", font=("Arial", 11, "bold")).pack()
        tk.Label(self.explanation_container,text=(
                "In addition to changing the terms, the cluster fit can be assessed."
                "Select whether the cluster is coherent and/or meaningful."),font=("Arial", 11), wraplength=700, justify="center").pack(pady=(0, 8))
        tk.Button(self.explanation_container, text="Adjust Clusters", command=self.review_clustering).pack(pady=(20,0))

    def create_adjustment_frame(self):
        self.results_container = tk.Frame(self.frame)
        self.metainfo_label = tk.Frame(self.results_container)
        self.metainfo_label.pack(side="top", fill="x", pady=(10,5))
        self.assessment_frame = tk.Frame(self.results_container)
        self.assessment_frame.pack(side="top", fill="x", pady=(5,5))
        self.scrollable_frame = tk.Frame(self.results_container)
        self.scrollable_frame.pack(side="top", fill="both", expand=True)
        self.results_canvas = tk.Canvas(self.scrollable_frame)
        self.results_canvas.pack(side="left", fill="both", expand=True)
        self.results_scrollbar = tk.Scrollbar(self.results_container,orient="vertical",command=self.results_canvas.yview)
        self.results_scrollbar.pack(side="right", fill="y")
        self.results_canvas.configure(yscrollcommand=self.results_scrollbar.set)
        self.results_frame = tk.Frame(self.results_canvas)
        self.results_canvas_window = self.results_canvas.create_window((0, 0), window=self.results_frame, anchor="nw")
        self.results_frame.bind("<Configure>",lambda e: self.results_canvas.configure(scrollregion=self.results_canvas.bbox("all")))
        self.results_canvas.bind("<Configure>",lambda e: self.results_canvas.itemconfig(self.results_canvas_window,width=e.width))
        self.results_canvas.bind_all("<MouseWheel>",lambda e: self.results_canvas.yview_scroll(int(-1 * (e.delta / 120)),"units"))
        self.navigation_frame = tk.Frame(self.results_container,height=80)
        self.navigation_frame.pack(side="bottom",fill="x",pady=(10,5))

    def create_finalizing_frame(self):
        self.finalize_container = tk.Frame(self.frame)
        tk.Label(self.finalize_container,text=(
            "To be implemented: Merging/Splitting Clusters."),font=("Arial", 11),wraplength=700,justify="center").pack()

    def update_cluster_view(self, number_updated_ids):
        """
        Update the cluster view for a new round of clustering.
        """
        for widget in self.progress_banner_frame.winfo_children():
            widget.destroy()
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        if number_updated_ids == 0: 
            self.clustering_frame.pack_forget()
            self.button_frame.pack_forget()
            self.finish_button.config(state='normal')
            self.finalize_container.pack(fill="both", expand=True)
            self.previous.show_progress_banner(5, self.progress_banner_frame, self.round)
            self.previous.show_instruction_banner(self.banner_frame, "Step 6. Finalize Clusters", 
                "[Press 'End Clustering Tool' to finish the clustering process.]", 
                [])
        else:
            self.step_status_label.pack_forget()
            self.progress_bar_status.pack_forget()
            self.progress_bar.pack_forget()
            self.previous.show_progress_banner(2, self.progress_banner_frame, self.round)
            self.previous.show_instruction_banner(self.banner_frame, "Step 3. Clustering", 
                "[Press 'Start Clustering' to restart the clustering or 'End Clustering Tool' to end the clustering process and save the current results.]", 
                [])
            self.run_button.config(state="normal")
            self.finish_button.config(state='normal')
            self.progress_label.pack_forget()
            self.status_label.config(
                    text=f"Manual adjustment of cluster terms for round {self.round} finished! \n \n The clustering results have been stored and your adjustments have been saved in {self.round_output_dir}. \n \n {str(number_updated_ids)} descriptions have been changed.")

            self.previous_output_dir = self.round_output_dir
            self.round += 1


    # Perform the clustering 
    def run_clustering_round(self):
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        self.previous.show_instruction_banner(self.banner_frame, "Step 3. Clustering", 
                "[Currently no action needed]", 
                [])
        self.progress_label.pack(pady=(30,10))
        self.status_label.config(text=f"Round {self.round} clustering in progress...")
        self.status_label.pack(pady=(20, 20))
        self.step_status_label.config(text=f"")
        self.step_status_label.pack(pady=(0, 10))
        self.progress_bar_status.pack(pady=(0,5))
        self.progress_bar.pack(pady=(0, 10))
        self.run_button.config(state="disabled")
        self.finish_button.config(state="disabled")
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
        try:    
            cluster_terms_filepath = orchestrate_clustering(self.input_file,self.round_output_dir,self.previous_output_dir,self.num_keys,self.arguments,self.round,progress_callback,indeterminate_callback, step_callback)
            self.parent.after(0,self.clustering_finished,cluster_terms_filepath)
        except Exception as e:
            print(f"Clustering error: {e}")
            self.parent.after(0,self.clustering_error,e)

    def clustering_finished(self, cluster_terms_filepath):
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        self.cluster_terms_filepath = cluster_terms_filepath
        self.status_label.config(text="Clustering finished!")
        self.step_status_label.pack_forget()
        self.progress_bar_status.pack_forget()
        self.progress_bar.pack_forget()
        self.previous.show_instruction_banner(self.banner_frame, "Step 3. Clustering", 
                "[Press 'Review Clusters' to manually inspect and alter the clusters]", 
                [])
        self.finish_button.config(state="normal")
        self.review_cluster.config(state="normal")


    # Show the clustering results
    def review_instructions(self):
        for widget in self.progress_banner_frame.winfo_children():
            widget.destroy()
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        self.previous.show_progress_banner(3, self.progress_banner_frame, self.round)
        self.previous.show_instruction_banner(self.banner_frame, "Step 4. Cluster Reviewing", 
            "[Press 'Adjust Clusters' when you have understood the explanation]", 
            [])
        self.button_frame.pack_forget()
        self.finish_button_frame.pack_forget()
        self.clustering_frame.pack_forget()
        self.explanation_container.pack(fill="both", expand=True)
        self.finish_button.config(state="disabled")

    def review_clustering(self):
        self.explanation_container.pack_forget()
        self.results_container.pack(fill="both", expand=True)
        self.load_clustering_result()
        if self.clusters:
            self.show_current_cluster()

    def load_clustering_result(self):
        """
        Read the cluster terms from the CSV file and store them in self.clusters
        """
        self.clusters = []
        # Cluster information      
        with open(self.cluster_terms_filepath, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for i, row in enumerate(reader):
                cluster  = {'cluster_id' : row['CID'],
                'silhouette' : row['Sil'],
                'size' : row['Size'],
                'terms': [{"term": row[f'Term {i}'], "selected": False, "x": None, "y": None, "original_term": row[f'Term {i}']} for i in range(self.num_keys)],
                'assessment': [{"term": 'Coherent', 'selected':False},{"term": 'Meaningful', 'selected':False}]}
                self.clusters.append(cluster)
        self.current_cluster = 0
        self.round_collage_outdir = os.path.join(self.round_output_dir,"collages")
        os.makedirs(self.round_collage_outdir, exist_ok=True)
        # Cluster texts
        cluster_info_file = os.path.join(self.round_output_dir, "cluster_texts.csv")
        self.cluster_img_desc = {}
        with open(cluster_info_file, newline='', encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                cluster_id = row['clusterId']
                if cluster_id not in self.cluster_img_desc:
                    self.cluster_img_desc[cluster_id] = []
                self.cluster_img_desc[cluster_id].append((row['path'], row['text']))

    def show_current_cluster(self):
        cluster = self.clusters[self.current_cluster]
        self.results_canvas.yview_moveto(0)
        self.show_cluster(
            cluster["cluster_id"],
            cluster["silhouette"],
            cluster["size"],
            cluster["terms"], 
            cluster['assessment']
        )

    def show_cluster(self, cluster_id, silhouette, size, terms, assessment):
        """
        Display the cluster information and terms in the results_frame
        """
        for widget in self.metainfo_label.winfo_children():
            widget.destroy()
        for widget in self.results_frame.winfo_children():
            widget.destroy()
        for widget in self.assessment_frame.winfo_children():
            widget.destroy()
        for widget in self.navigation_frame.winfo_children():
            widget.destroy()
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        self.previous.show_instruction_banner(self.banner_frame, "Step 4. Cluster Reviewing", 
            f"Results for clustering round {self.round}", 
            [])
        # tk.Label(self.metainfo_label, text=f"Results for clustering round {self.round}", font=("Arial", 14)).pack(pady=(0,5))
        tk.Label(self.metainfo_label,text=(f"Cluster {self.current_cluster + 1} of {len(self.clusters)}: Cluster ID: {cluster_id}, Silhouette Score: {silhouette}, Cluster Size: {size}"), font=("Arial", 11)).pack(pady=(0, 5))
        
        self.create_assessment_frame(assessment)
        content_frame = tk.Frame(self.results_frame)
        content_frame.pack(pady=(0, 5))
        self.create_image_frame(content_frame, cluster_id)
        self.create_terms_frame(content_frame, terms)

        image_buttons_frame = tk.Frame(self.navigation_frame)
        image_buttons_frame.pack(anchor='center', pady=(0,10))
        self.shuffle_button = tk.Button(image_buttons_frame, text="Show Different Images", command=lambda: self.shuffle_images(cluster_id=cluster_id))
        self.shuffle_button.pack(side="left", padx=5)
        self.change_img_type_button = tk.Button(image_buttons_frame, text="Show Image Descriptions", command=lambda: self.change_image_type(cluster_id=cluster_id))
        self.change_img_type_button.pack(side="left", padx=5)
        tk.Button(image_buttons_frame, text="Show Cluster Plots", command=self.show_visualization).pack(side="left", padx=5)

        # Buttons to navigate between clusters
        navigation_buttons_frame = tk.Frame(self.navigation_frame)
        navigation_buttons_frame.pack(anchor='center')
        if self.current_cluster != 0:
            tk.Button(navigation_buttons_frame, text="First Cluster", command=lambda: self.previous_cluster(first_cluster=True)).pack(side="left", padx=5)
        if self.current_cluster > 0:
            tk.Button(navigation_buttons_frame, text="Previous Cluster", command=self.previous_cluster).pack(side="left", padx=5)
        if self.current_cluster < len(self.clusters) - 1:
            tk.Button(navigation_buttons_frame, text="Next Cluster", command=self.next_cluster).pack(side="left", padx=5)
        if self.current_cluster != len(self.clusters) - 1:
            tk.Button(navigation_buttons_frame, text="Last Cluster", command=lambda: self.next_cluster(last_cluster=True)).pack(side="left", padx=5)
        tk.Button(self.navigation_frame, text="Finish Adjustments", command=self.finish_manual_updates).pack(side="top", pady=10)

    def create_assessment_frame(self, assessment):
        ass_frame = tk.Frame(self.assessment_frame)
        ass_frame.pack(anchor='center')
        tk.Label(ass_frame, text="This cluster is: ", font=('Arial', 12)).pack(side="left", padx=5)

        self.cluster_assessment = []
        for i, ass_dict in enumerate(assessment): 
            term = ass_dict["term"]
            selected = ass_dict["selected"]
            if selected:  
                relief='solid'
                bd = 1
            else:  
                relief='flat'
                bd = 0
            button = tk.Button(ass_frame, text=term, font=("Arial", 10), relief=relief, bd=bd, highlightthickness=0)
            button.pack(side="left", padx=5)
            button.config(command=lambda b=button: self.circle_term(b))
            self.cluster_assessment.append(button)
    
    def create_image_frame(self, content_frame, cluster_id):
        image_frame = tk.Frame(content_frame)
        image_frame.pack(side="left", padx=(10, 15), anchor="n")

        file_path = os.path.join(self.round_collage_outdir, f'collage_{cluster_id}.jpg')
        if os.path.exists(file_path): # Instantate with collage
            self.current_image = file_path
        else:
            self.current_image = get_image(self.cluster_img_desc, self.round_collage_outdir, cluster_id, True)
        image = Image.open(self.current_image)
        image.thumbnail((1000, 800))
        self.cluster_image = ImageTk.PhotoImage(image)
        self.cluster_collage_image = tk.Label(image_frame,image=self.cluster_image)
        self.cluster_collage_image.pack(pady=(0, 10))

    def create_terms_frame(self, content_frame, terms):
        terms_frame = tk.Frame(content_frame)
        terms_frame.pack(side="left", padx=(15, 10), anchor="n")
        tk.Label(terms_frame, text="Top terms:", font=("Arial", 10)).pack(pady=(0, 5))
        self.term_canvas = tk.Canvas(terms_frame,width=200,height=300,highlightthickness=1,highlightbackground="black")
        self.term_canvas.pack(pady=(0, 10))

        self.term_buttons = []
        for i, term_dict in enumerate(terms): 
            term = term_dict["term"]
            overstrike = term_dict["selected"]
            if overstrike:  
                font=("Arial", 10, "overstrike")
            else:  
                font=("Arial", 10)
            button = tk.Button(self.term_canvas, text=term, font=font, relief="flat", bd = 0, highlightthickness=0, padx=8, pady=3)# bd=0, 
            if term_dict["x"] is None:
                x = 100
                y = 21 + i * 42
            else:
                x = term_dict["x"]
                y = term_dict["y"]
            button.original_term = term_dict["original_term"]
            window = self.term_canvas.create_window(x, y, window=button)
            button.canvas_id  = window
            button.config(command=lambda b=button: self.toggle_term(b))
            button.bind("<Button-3>", self.term_right_click)
            self.term_buttons.append(button)

    # Function to show cluster graphs
    def show_visualization(self):
        popup = tk.Toplevel(self.parent)
        popup.title("Cluster Visualization")
        popup.geometry("1600x850")
        popup.transient(self.parent)

        image_frame = tk.Frame(popup)
        image_frame.pack(fill="both", expand=True, padx=10, pady=10)
        visualization_path = os.path.join(self.round_output_dir, "cluster_visualization.png")
        visualization = Image.open(visualization_path)
        visualization_label = tk.Label(image_frame)
        visualization_label.pack(side="left", padx=10, pady=10)

        heatmap_path = os.path.join(self.round_output_dir, "cluster_heatmap.png")
        heatmap = Image.open(heatmap_path)
        heatmap_label = tk.Label(image_frame)
        heatmap_label.pack(side="left", padx=10, pady=10)

        def resize_images(event=None):
            width = max(image_frame.winfo_width() // 2 - 30, 100)
            height = max(image_frame.winfo_height() - 30, 100)
            vis = visualization.copy()
            vis.thumbnail((width, height))
            heat = heatmap.copy()
            heat.thumbnail((width, height))
            visualization_image = ImageTk.PhotoImage(vis)
            heatmap_image = ImageTk.PhotoImage(heat)
            visualization_label.config(image=visualization_image)
            heatmap_label.config(image=heatmap_image)
            visualization_label.image = visualization_image
            heatmap_label.image = heatmap_image
        image_frame.bind("<Configure>", resize_images)

        popup.after(100, resize_images)


    # Function for right clicking terms
    def term_right_click(self, event):
        button = event.widget
        menu = tk.Menu(self.parent, tearoff=0)
        current_font = button.cget("font") 
        term = button.cget("text")
        if "overstrike" in str(current_font): 
            delete_label = "Recover term"
        else: 
            delete_label = "Delete term"
        menu.add_command(label=delete_label, command=lambda b=button: self.toggle_term(b))
        menu.add_command(label="Rename term", command=lambda b=button: self.rename_term(b))
        if "->" in term:
            menu.add_command(label="Reset term", command=lambda b=button: self.reset_term(b))
        menu.tk_popup(event.x_root, event.y_root)


    # Function for the removal or renaming of terms from the cluster view
    def toggle_term(self, button): 
        """ Toggle a strike-through effect on a term.""" 
        term = button.cget("text")
        if "->" in term:
            answer = messagebox.askyesno("Warning", 'Do you want to delete the original term without replacement?')
            if answer: 
                original_term = getattr(button, "original_term")
                button.config(font=("Arial", 10, "overstrike"))
                button.config(text=original_term)
        else:
            current_font = button.cget("font") 
            if "overstrike" in str(current_font): 
                button.config(font=("Arial", 10)) 
            else: button.config(font=("Arial", 10, "overstrike"))

    def circle_term(self, button):
        current_relief = button.cget("relief") 
        if current_relief == 'flat': 
            button.config(relief="solid", bd=1) 
        else: button.config(relief='flat', bd=0)

    def strike(self, text):
        return ''.join(char + '\u0336' for char in text)

    def rename_term(self, button):
        term = button.cget("text")
        if "->" in term:
            term = term.split("->", 1)[1].strip()
        original_term = getattr(button, "original_term")
        new_term = simpledialog.askstring("Rename term", f"Enter a new term for: {term} \n (Original term was: {original_term})", parent=self.parent)
        if not new_term:
            return
        if new_term == original_term:
            new_text = original_term
        else:
            new_text = f"{self.strike(original_term)} -> {new_term}"
        button.config(font=("Arial", 10)) 
        button.config(text=new_text)

    def reset_term(self, button):
        original_term = getattr(button, "original_term")
        button.config(text=original_term)


    # Helper functions for navigating between clusters
    def next_cluster(self, last_cluster=False):
        self.save_current_terms()
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


    # Function to show new image
    def shuffle_images(self, cluster_id):
        if 'collage_' in self.current_image:
            self.current_image = get_image(self.cluster_img_desc, self.round_collage_outdir, cluster_id, True) # get new collage
        else: 
            self.current_image = get_image(self.cluster_img_desc, self.round_collage_outdir, cluster_id, False) # get new descriptions
        image = Image.open(self.current_image)
        image.thumbnail((1000, 800))
        self.cluster_image = ImageTk.PhotoImage(image)
        self.cluster_collage_image.config(image=self.cluster_image)
        self.results_canvas.yview_moveto(0)
    
    def change_image_type(self,cluster_id):
        if 'collage_' in self.current_image:
            self.change_img_type_button.config(text='Show images collage')
            self.current_image = get_image(self.cluster_img_desc, self.round_collage_outdir, cluster_id, False) # current = collage -> get descriptions
        else: 
            self.change_img_type_button.config(text="Show image descriptions")
            self.current_image = get_image(self.cluster_img_desc, self.round_collage_outdir, cluster_id, True) # current = desc -> get collage
        image = Image.open(self.current_image)
        image.thumbnail((1000, 800))
        self.cluster_image = ImageTk.PhotoImage(image)
        self.cluster_collage_image.config(image=self.cluster_image)
        self.results_canvas.yview_moveto(0)


    # Saving cluster terms and their positions for the next round of clustering
    def save_current_terms(self):
        assessments = []
        for button in self.cluster_assessment:
            assessments.append({
                'term': button.cget("text"),
                "selected": True if str(button.cget("relief")) == 'solid' else False
            })
        self.clusters[self.current_cluster]["assessment"] = assessments
        terms = []
        for button in self.term_buttons:
            x, y = self.term_canvas.coords(button.canvas_id)
            terms.append({
                "term": button.cget("text"),
                "selected": "overstrike" in str(button.cget("font")),
                "x": x,
                "y": y,
                "original_term": getattr(button, "original_term")
            })
        self.clusters[self.current_cluster]["terms"] = terms


    # Function to handle finishing the manual updates process 
    def finish_manual_updates(self):
        """
        Write the updated cluster terms to a CSV file and update the clusters data structure.
        """
        for widget in self.progress_banner_frame.winfo_children():
            widget.destroy()
        for widget in self.banner_frame.winfo_children():
            widget.destroy()
        self.previous.show_progress_banner(4, self.progress_banner_frame, self.round)
        self.banner_frame.pack(fill="both", expand=False)
        self.previous.show_instruction_banner(self.banner_frame, "Step 4. Cluster Reviewing", 
                "[Currently no action needed]", 
                [])
        self.save_current_terms()
        self.results_container.pack_forget()
        self.button_frame.pack(fill="both", expand=False)
        self.clustering_frame.pack(fill="both", expand=True)
        self.finish_button_frame.pack(side="bottom", pady=(10,10))
        self.status_label.config(text=f"Updating image decriptions in progress...")
        self.status_label.pack(pady=(0,20))
        self.step_status_label.pack_forget()
        self.progress_bar_status.pack(pady=(0,5))
        self.progress_bar.pack(pady=(0, 20))
        self.run_button.config(state="disabled")
        self.finish_button.config(state="disabled")
        self.review_cluster.config(state="disabled")
        self.next_output_dir = os.path.join(self.output_dir, f"round_{self.round + 1}") # ID	Dir	ImageID	Labels

        cluster_assessments = os.path.join(self.round_output_dir, "cluster_assessments.csv")
        os.makedirs(self.next_output_dir, exist_ok=True)
        with open(cluster_assessments, 'w', encoding='utf-8', newline='') as out:
            out.write('cluster_id,coherence,meaningfulness\n')
            for cluster in self.clusters:
                    ass_row = f"{cluster['cluster_id']}"
                    for ass_dict in cluster["assessment"]:
                        ass_row += (","+ str(ass_dict["selected"]))
                    out.write(f"{ass_row}\n")
            out.close() 

        if self.round == 1:
            self.input_file = os.path.join(self.next_output_dir, "updated_input_file.csv")
            self.update_cluster_view(10)
        elif self.round==2:
            self.input_file = os.path.join(self.next_output_dir, "updated_input_file.csv")
            self.update_cluster_view(0)
        else:   
            cluster_updates = os.path.join(self.round_output_dir, "cluster_updates.csv")
            os.makedirs(self.next_output_dir, exist_ok=True)
            with open(cluster_updates, 'w', encoding='utf-8', newline='') as out:
                out.write('cluster_id,term,delete,new_term\n')
                for cluster in self.clusters:
                    for term_dict in cluster["terms"]:
                        term = term_dict["original_term"]
                        delete = str(term_dict["selected"])
                        text = term_dict["term"]
                        if "->" in text:
                            new_term = text.split("->", 1)[1].strip()
                        else:
                            new_term = ""
                        out.write(f"{cluster['cluster_id']},{term},{delete},{new_term}\n")
            out.close() 
            threading.Thread(target=self.update_texts_background, args=(), daemon=True).start()

    def update_texts_background(self):
        def progress_callback(current, total, message):
            self.parent.after(0,self.update_progress,current,total,message)
        try:    
            updated_input_file, number_updated_ids = update_clustering_terms(self.input_file,self.next_output_dir,self.round_output_dir, progress_callback)
            self.parent.after(0, self.update_texts_finished, updated_input_file, number_updated_ids)
        except Exception as e:
            print(f"Error: {e}")
            self.parent.after(0,self.clustering_error,e)

    def update_texts_finished(self, updated_input_file, number_updated_ids):
        self.input_file = updated_input_file
        self.update_cluster_view(number_updated_ids)


    # Update progress steps
    def update_progress(self, current, total, message):
        if not self.progress_bar_status.winfo_ismapped():
            self.progress_bar_status.pack(pady=(0, 5))
        self.progress_bar_status.config(text=f"{message}: {current}/{total}")
        if not self.progress_bar.winfo_ismapped():
            self.progress_bar.pack(pady=(0, 20))
        if self.indeterminate_running:
            self.progress_bar.stop()
            self.indeterminate_running = False
        self.progress_bar.config(mode="determinate")
        self.progress_bar["maximum"] = total
        self.progress_bar["value"] = current
        if current >= total:
            self.progress_bar_status.pack_forget()
            self.progress_bar.pack_forget()

    def update_indeterminate(self, message):
        if not self.progress_bar_status.winfo_ismapped():
            self.progress_bar_status.pack(pady=(0, 5))
        self.progress_bar_status.config(text=message)
        if not self.progress_bar.winfo_ismapped():
            self.progress_bar.pack(pady=(0, 20))
        if not self.indeterminate_running:
            self.progress_bar.config(mode="indeterminate",maximum=100)
            self.progress_bar["maximum"] = 100
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
        self.previous.end_tool()


    # Error messages
    def clustering_error(self, error):
        print(f"Error: {repr(error)}")
        self.status_label.config(text="Clustering could not be completed.")
        self.step_status_label.pack_forget()
        if self.indeterminate_running:
            self.progress_bar.stop()
            self.indeterminate_running = False
        self.progress_bar.pack_forget()
        self.progress_bar_status.pack_forget()
        self.action_label.config(text="[Error]")
        messagebox.showerror("Error", error)