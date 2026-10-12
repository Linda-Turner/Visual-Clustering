import os, sys, csv, json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from scripts.GUI.argument_setting import create_argument_settings
from scripts.GUI.clustering_interface import ClusterView

class ClusteringGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Visual Clustering")
        self.root.geometry("800x600")

        self.input_file = None
        self.output_dir = None
        self.round = 1
        self.continued_clustering = False

        self.show_instructions()


    def show_progress_banner(self, current_step, frame, clustering_round=1):
        canvas_height = 40
        self.step_tracker_frame = tk.Frame(frame, height=canvas_height, background="#CCCCCC",bd=0,highlightthickness=0)
        self.step_tracker_frame.pack(fill="x", expand=False)
        self.step_tracker_canvas = tk.Canvas(self.step_tracker_frame,  height=canvas_height, background="#CCCCCC",bd=0,highlightthickness=0)#background="#F5F5F5",
        self.step_tracker_canvas.pack(fill="x", expand=False)
        def draw_step_tracker(event=None):
            self.step_tracker_canvas.delete("all")
            dist = 10
            shape_length = (self.step_tracker_canvas.winfo_width()/6) - (dist)
            for i in range(6):
                if i == current_step:
                    outline_width = 2
                    fill = "#F0F0F0"
                    font = ("Arial", 11, "bold")
                else:
                    outline_width = 1
                    # fill = "#F5F5F5"
                    fill = "#CCCCCC"
                    font = ("Arial", 11)
                shape_point_length = shape_length / 6
                x_left = ((shape_length + dist) * i) + (dist * 0.5)
                x_middle_right = x_left + shape_length - shape_point_length
                x_right = x_middle_right + shape_point_length
                x_middle_left = x_left + shape_point_length
                # polygon_points = [x_left,38,x_middle_right,38,x_right,23,x_middle_right,21,x_left,8,x_middle_left,21]
                polygon_points = [x_left,7,x_middle_right,7,x_right,22,x_middle_right,37,x_left,37,x_middle_left,22]
                self.step_tracker_canvas.create_polygon(polygon_points, outline="#000000", fill=fill, width=outline_width)
                if i == 0: text='File Selection'
                elif i == 1: text='Parameter Setting'
                elif i == 2: text='Clustering'
                elif i == 3: text='Text Adjusting'
                elif i == 4: text='Cluster Updates'
                elif i == 5: text='Finalize Clusters'
                if 5 > i > 1:
                    circle_points = [x_middle_right - (15), 32, x_middle_right + (5), 12]
                    self.step_tracker_canvas.create_oval(circle_points, outline="#000000", fill=fill, width=outline_width)
                    self.step_tracker_canvas.create_text(x_middle_right - (5), 22, text= str(clustering_round), font=font)
                    self.step_tracker_canvas.create_text(x_middle_left + ((x_middle_right - x_middle_left) / 2) - 10, 22, text= text, font=font)
                else:
                    self.step_tracker_canvas.create_text(x_middle_left + ((x_middle_right - x_middle_left) / 2), 22, text= text, font=font)
        self.step_tracker_canvas.bind("<Configure>", draw_step_tracker)

    def show_instruction_banner(self, frame, step_text, action_text, note_text):
        height = 51 + 15 * len(note_text)
        banner_frame = tk.Frame(frame, bg="#CCCCCC", height=height)
        banner_frame.pack(fill="x", expand=False)
        step_label = tk.Label(banner_frame, text=step_text, font=("Arial", 14), bg="#CCCCCC")
        step_label.pack(pady=(5,7))
        action_label = tk.Label(banner_frame, text=action_text, font=("Arial", 12), bg="#CCCCCC")
        action_label.pack(pady=(0,7))
        for note in note_text:
            note_label = tk.Label(banner_frame, text=note, font=("Arial", 10), bg="#CCCCCC")
            note_label.pack(pady=(0,4))

    def show_instructions(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 20)).pack(pady=(20, 30))
        tk.Label(self.root, text="This tool allows you to iteratively cluster images into groups based on their visual descriptions.", font=("Arial", 14)).pack(pady=(0,30))

        tk.Button(self.root, text="Next", command=self.show_instructions_2, font=('Arial', 12)).pack(pady=(0,20))

    def show_instructions_2(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 20)).pack(pady=(20, 30))
        tk.Label(self.root, text="By starting the tool, you will be guided through the following steps:", font=("Arial", 14)).pack(pady=(0,20))
        instructions = [ 
            "1. Select a CSV file containing the image descriptions and image paths.", 
            "2. Optionally alter parameter settings, or continue with the default settings.", 
            "3. Run the clustering algorithm to generate groups of similar images.", 
            "4. Inspect a the clusters' images and corresponding descriptions.", 
            "5. Adjust the clusters' top terms if necessary.", 
            "6. Repeat steps 3-5 until the clusters are satisfactory." ]
        for instruction in instructions:
            tk.Label(self.root, text=instruction, font=("Arial", 12)).pack(padx=50, pady=(0, 5))
        tk.Label(self.root, text="NOTE: Additional explanation will be provided during each step.", font=("Arial", 12)).pack(pady=(15,30))
        tk.Button(self.root, text="Start Tool", command=self.select_cluster_round, font=('Arial', 12)).pack(pady=(10,20))

    def select_cluster_round(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.continued_clustering = False

        self.show_progress_banner(0, self.root)
        self.show_instruction_banner(self.root, "Step 0. Start or Continue Clustering", 
                                "[Choose whether you would like to start a new clustering process or continue an existing one]", 
                                ["NOTE: A previous clustering process can only be continued if you have used the tool before."])

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(20,20))
        tk.Button(button_frame, text="Start New Clustering", command=self.show_file_selection).pack(side="left", padx=5)
        tk.Button(button_frame, text="Continue Previous Clustering", command=self.clustering_round).pack(side="left", padx=5)

    def clustering_round(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.show_progress_banner(0, self.root)
        self.show_instruction_banner(self.root, "Step 1. File Selection", 
                                "[Select the folder containing the previous clustering results]", 
                                ["NOTE: Select the previous output directory, not one of the round_X subfolders."])
        self.continued_clustering = True

        tk.Button(self.root, text="Select Clustering Folder", command=self.select_existing_output_dir).pack(pady=(20,7))
        self.folder_label = tk.Label(self.root,text="No folder selected",font=("Arial", 10),wraplength=700)
        self.folder_label.pack(pady=(0, 20))

        banner_frame = tk.Frame(self.root, bg="#CCCCCC", height=12+5+10+10)
        banner_frame.pack(fill="x", expand=False)
        tk.Label(banner_frame, text="[Give the clustering round you would like to continue from]", font=("Arial", 12), background="#CCCCCC").pack(pady=(5,7))
        tk.Label(banner_frame, text="NOTE: Make sure the previous clustering rounds reach this round.", font=("Arial", 10), background="#CCCCCC").pack(pady=(0,5))
        tk.Label(self.root, text="Cluster round:", font=("Arial", 10)).pack(pady=(20,7))
        self.round_entry = ttk.Entry(self.root)
        self.round_entry.insert(0, "2")
        self.round_entry.pack(pady=(0, 7))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(20,20))
        self.continue_button = tk.Button( button_frame, text="Continue", command=self.check_clustering_round, state="disabled")
        self.continue_button.pack(side="left", padx=5)
        tk.Button(button_frame, text="Back", command=self.select_cluster_round, state="normal").pack(side="left", padx=5)


    def select_existing_output_dir(self):
        folder = filedialog.askdirectory(title="Select clustering output folder")
        if folder:
            self.output_dir = folder
            self.folder_label.config(text=f"Selected folder:\n{folder}")
            self.continue_button.config(state="normal")

    def check_clustering_round(self):
        try:
            round_number = int(self.round_entry.get())
        except ValueError:
            messagebox.showerror("Invalid clustering round", "Please enter a valid clustering round number (e.g. 1, 3 or 10).")
            return
        if round_number < 1:
            messagebox.showerror("Invalid clustering round", "The clustering round must be 0 or higher.")
            return
        round_dir = os.path.join(self.output_dir,f"round_{round_number}")
        if not os.path.exists(round_dir):
            messagebox.showerror("Clustering round not found", f"Round {round_number} could not be found in the selected folder.\n\n" f"Expected folder:\n{round_dir}")
            return
        input_file = os.path.join(round_dir,f"updated_input_file.csv")
        if not os.path.exists(input_file):
            messagebox.showerror("Clustering round not accessible", f"Round {round_number} does not have an updated input file.\n\n" f"Expected folder:\n{input_file}")
            return
        self.input_file = input_file
        self.round = round_number
        self.argument_setting()

    def show_file_selection(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.show_progress_banner(0, self.root)
        self.show_instruction_banner(self.root, "Step 1. File Selection", 
                                "[Select a CSV file containing the image descriptions to cluster]", 
                                ["NOTE: The CSV file should contain the image ID's, the image paths and the corresponding descriptions.", "NOTE: These variables should be stored in columns with the respective names ID, Dir, ImageID and Labels.", "NOTE: Make sure the CSV file and the image directory are stored in the current working directory."])
        
        self.file_button = tk.Button(self.root, text="Select File", command=self.import_file)
        self.file_button.pack(pady=(20,7))
        self.file_label = tk.Label(self.root,text="No file selected",font=("Arial", 10),wraplength=700)
        self.file_label.pack(pady=(0, 20))

        banner_frame = tk.Frame(self.root, bg="#CCCCCC", height=12+5+10+10)
        banner_frame.pack(fill="x", expand=False)
        tk.Label(banner_frame, text="[Give a name for the output directory]", font=("Arial", 12), background="#CCCCCC").pack(pady=(5,7))
        tk.Label(banner_frame, text="NOTE: This folder does not need to exist already.", font=("Arial", 10), background="#CCCCCC").pack(pady=(0,5))
        tk.Label(self.root, text="Cluster round:", font=("Arial", 10)).pack(pady=(20,7))
        self.dir_entry = ttk.Entry(self.root)
        self.dir_entry.insert(0, "clustering_results_ngram")
        self.dir_entry.pack(pady=(0, 20))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(0,20))
        self.next_button = tk.Button(button_frame, text="Continue", command=self.argument_setting, state="disabled")
        self.next_button.pack(side="left", padx=5)
        tk.Button(button_frame, text="Back", command=self.select_cluster_round, state="normal").pack(side="left", padx=5)

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Select a file",filetypes=[("CSV files", "*.csv"),("All files", "*.*")])

        if file_path:
            self.input_file = file_path
            self.file_label.config(text=f"Selected file:\n{file_path}")
            self.next_button.config(state="normal")

        
    def argument_setting(self):
        if not self.continued_clustering:
            self.output_dir = self.dir_entry.get()
            os.makedirs(self.output_dir, exist_ok=True)
            arguments = None

        for widget in self.root.winfo_children():
            widget.destroy()

        self.show_progress_banner(1, self.root)
        if self.continued_clustering:
            note_list = ["NOTE: The parameters used during the previous clustering rounds has been set."]
            parameters_file = os.path.join(self.output_dir, "parameters.json")
            with open(parameters_file, "r", encoding="utf-8") as f:
                arguments = json.load(f)
        else: 
            note_list = ["NOTE: If no changes are made, the default values will be used."]
        self.show_instruction_banner(self.root, "Step 2. Parameter Setting", 
                                "[Set the parameters used during clustering]", 
                                note_list)
        
        self.arguments = create_argument_settings(self.root, arguments)

        self.next_button = tk.Button(self.root, text="Next", command=self.cluster)
        self.next_button.pack(pady=(0,20))


    def cluster(self):
        arguments = {
            key: widget.get()
            for key, widget in self.arguments.items()}
        valid, error_message = self.validate_arguments(arguments)
        if not valid:
            messagebox.showerror("Invalid input", error_message)
            return
        self.arguments = arguments
        parameters_file = os.path.join(self.output_dir, "parameters.json")
        with open(parameters_file, "w", encoding="utf-8") as f:
            json.dump(self.arguments, f, indent=4)
        for widget in self.root.winfo_children():
            widget.destroy()

        self.cluster_view = ClusterView(parent=self.root, previous=self, input_file=self.input_file, output_dir=self.output_dir, round=self.round, arguments=self.arguments)


    def validate_arguments(self, arguments):
        try:
            embedding_batch = int(arguments["embedding_batch"])
            if embedding_batch <= 0:
                return False, "Embedding batch size must be greater than 0."
        except ValueError:
            return False, "Embedding batch size must be an integer."
        if arguments["embedding_model"] == "tfidf":
            try:
                topk = int(arguments["topk"])
                if topk <= 0:
                    return False, "Number of top terms must be greater than 0."
            except ValueError:
                return False, "Number of top terms must be an integer."
        try:
            components = int(arguments["components"])
            if components <= 0:
                return False, "Number of dimensions must be greater than 0."
        except ValueError:
            return False, "Number of dimensions must be an integer."
        if arguments["reduction_model"] == "umap":
            try:
                neighbors = int(arguments["neighbors"])
                if neighbors <= 0:
                    return False, "Number of neighbors must be greater than 0."
            except ValueError:
                return False, "Number of neighbors must be an integer."
        if arguments["cluster_method"] == "hdbscan":
            try:
                min_cluster_size = int(arguments["min_cluster_size"])
                if min_cluster_size <= 0:
                    return False, "Minimum cluster size must be greater than 0."
            except ValueError:
                return False, "Minimum cluster size must be an integer."
        elif arguments["cluster_method"] == "kmeans":
            try:
                num_clusters = int(arguments["num_clusters"])
                if num_clusters <= 0:
                    return False, "Number of clusters must be greater than 0."
            except ValueError:
                return False, "Number of clusters must be an integer."
        return True, None


    def end_tool(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Clustering tool has been terminated.", font=("Arial", 20)).pack(pady=(20, 20))
        tk.Label(self.root, text=f"All clustering results are saved in {self.output_dir}.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The output directory contains subfolders 'round_X' containing the resuls of the different clustering rounds.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The clusters and correspongin top terms can be found in cluster_terms.csv.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The alterered image descriptions can be found in updated_input_file.csv.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The window can now be closed.", font=("Arial", 14)).pack(pady=(0, 10))


root = tk.Tk()

app = ClusteringGUI(root)

root.mainloop()