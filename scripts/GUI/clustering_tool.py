import os, sys, csv, json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from scripts.GUI.argument_setting import create_argument_settings
from scripts.GUI.cluster_interface import ClusterView

class ClusteringGUI:

    def __init__(self, root):
        self.root = root
        self.root.title("Visual Clustering")
        self.root.geometry("800x600")

        self.input_file = None
        self.output_dir = None
        self.round = 0
        self.continued_clustering = False

        self.show_instructions()

    def show_instructions(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 20)).pack(pady=(20, 20))
        tk.Label(self.root, text="This tool allows you to iteratively cluster images into groups based on their visual descriptions.", font=("Arial", 14)).pack(pady=(0,20))
        tk.Label(self.root, text="After each iteration you can manually inspect the clusters and alter the visual descriptions to improve the clustering result.", font=("Arial", 14)).pack(pady=(0,20))

        tk.Button(self.root, text="Next", command=self.show_instructions_2).pack(pady=(0,20))

    def show_instructions_2(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 20)).pack(pady=(20, 20))
        tk.Label(self.root, text="By starting the tool, you will be guided through the following steps:", font=("Arial", 14)).pack(pady=(0,10))
        instructions = [ 
            "1. Select a CSV file containing the image descriptions and image paths.", 
            "2. Optionally select parameters settings, or continue with the default settings.", 
            "3. Run the clustering algorithm to generate groups of similar images.", 
            "4. Inspect a selection of the images and the top words representing each cluster.", 
            "5. Adjust the top words used to represent the clusters if necessary.", 
            "6. Repeat steps 3-5 until the clusters are satisfactory." ]
        for instruction in instructions:
            tk.Label(self.root, text=instruction, font=("Arial", 12)).pack(padx=50, pady=(0, 3))
        tk.Label(self.root, text="(Additional explanation will be provided during each step.)", font=("Arial", 12)).pack(pady=(17,10))
        tk.Button(self.root, text="Start Tool", command=self.select_cluster_round).pack(pady=(10,20))

    def select_cluster_round(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.continued_clustering = False

        tk.Label(self.root,text="Step 0. Start or Continue Clustering", font=("Arial", 14)).pack(pady=(10, 10))
        tk.Label(self.root, text="[Choose whether you would like to start a new clustering process or continue an existing one]", font=("Arial", 12), wraplength=700,justify="center").pack(pady=(0, 5))
        tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,0))
        tk.Label(self.root, text="A previous clustering process can only be continued if you have used the tool before.", font=("Arial", 10)).pack(pady=(0,20))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(0,20))
        tk.Button(button_frame, text="Start New Clustering", command=self.show_file_selection).pack(side="left", padx=5)
        tk.Button(button_frame, text="Continue Previous Clustering", command=self.clustering_round).pack(side="left", padx=5)

    def clustering_round(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.continued_clustering = True
        tk.Label(self.root, text="Step 0. Clustering Round Selection", font=("Arial", 14)).pack(pady=(10,10))
        tk.Label(self.root, text="[Select the folder containing the previous clustering results]", font=("Arial", 12)).pack(pady=(0,5))
        tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,2))
        tk.Label(self.root, text="Select the overarching folder, do not select one of the round_X subfolders.", font=("Arial", 10)).pack(pady=(0,10))

        tk.Button(self.root, text="Select Clustering Folder", command=self.select_existing_output_dir).pack(pady=5)
        self.folder_label = tk.Label(self.root,text="No folder selected",font=("Arial", 10),wraplength=700)
        self.folder_label.pack(pady=(0, 20))

        tk.Label(self.root, text="[Give the clustering round you would like to continue from]", font=("Arial", 12)).pack(pady=(0,5))
        tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,0))
        tk.Label(self.root, text="Make sure the previous clustering rounds reach this round.", font=("Arial", 10)).pack(pady=(0,2))
        tk.Label(self.root, text="Cluster round:.", font=("Arial", 10)).pack(pady=(0,10))
        self.round_entry = ttk.Entry(self.root)
        self.round_entry.insert(0, "1")
        self.round_entry.pack(pady=(0, 5))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(0,20))
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
        self.show_file_selection()

    def show_file_selection(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Step 1. File Selection", font=("Arial", 14)).pack(pady=(10,10))
        if self.continued_clustering:
            tk.Label(self.root, text="[CSV file selected automatically because you have chosen to continue with previous clustering rounds]", font=("Arial", 12)).pack(pady=(0,20))
        else:
            tk.Label(self.root, text="[1. Select a CSV file containing the image descriptions to cluster]", font=("Arial", 12)).pack(pady=(0,5))
            tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,0))
            tk.Label(self.root, text="The CSV file should contain the image ID's, the image paths and the corresponding descriptions.", font=("Arial", 10)).pack(pady=(0,2))
            tk.Label(self.root, text="These variables should be stored in columns with the respective names ID, Dir, ImageID and Labels.", font=("Arial", 10)).pack(pady=(0,2))
            tk.Label(self.root, text="Make sure the CSV file and the image directory are stored in the current working directory.", font=("Arial", 10)).pack(pady=(0,20))

        self.file_button = tk.Button(self.root, text="Select File", command=self.import_file)
        self.file_button.pack(pady=(0,5))
        self.file_label = tk.Label(self.root, font=("Arial", 10))
        self.file_label.pack(pady=(0,20))
        self.next_button = tk.Button(self.root, text="Next", command=self.argument_setting)

        if self.continued_clustering:
            self.file_button.config(state='disabled')
            self.file_label.config(text=f'Selected file:\n{self.input_file}')
            self.next_button.config(state='normal')
        else:
            self.file_button.config(state='normal')
            self.file_label.config(text='No file selected')
            self.next_button.config(state='disabled')
            tk.Label(self.root, text="[2. Give a name for the results folder]", font=("Arial", 12)).pack(pady=(0,5))
            tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,0))
            tk.Label(self.root, text="This folder does not need to exist already.", font=("Arial", 10)).pack(pady=(0,10))
            self.dir_entry = ttk.Entry(self.root)
            self.dir_entry.insert(0, "clustering_results")
            self.dir_entry.pack(pady=(0, 20))

        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=(0,20))
        self.next_button = tk.Button( button_frame, text="Continue", command=self.argument_setting, state="disabled")
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

        tk.Label(self.root, text="Step 2. Parameter Setting", font=("Arial", 14)).pack(pady=(10, 10))
        tk.Label(self.root, text="[Set the parameters used during clustering]", font=("Arial", 12)).pack(pady=(0,10))
        tk.Label(self.root, text="NOTE:", font=("Arial", 10)).pack(pady=(0,0))
        note_label = tk.Label(self.root, text="If no changes are made, the default values will be used.", font=("Arial", 10))
        note_label.pack(pady=(0, 10))

        if self.continued_clustering:
            note_label.config(text="The parameters used during the previous clustering rounds has been set.")
            parameters_file = os.path.join(self.output_dir, "parameters.json")
            with open(parameters_file, "r", encoding="utf-8") as f:
                arguments = json.load(f)

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


    def done(self):
        tk.Label(self.root, text="Clustering process has ended.", font=("Arial", 20)).pack(pady=(20, 20))
        tk.Label(self.root, text=f"The clustering results are saved in {self.output_dir}.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"This folder contains subfolders round_X containing the resuls of the different clustering rounds.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The cluster_terms.csv file contains information about which images are clustered under which terms.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The updated_input_file.csv file contains the image altered descriptions.", font=("Arial", 14)).pack(pady=(0,10))
        tk.Label(self.root, text=f"The window can now be closed.", font=("Arial", 14)).pack(pady=(0, 10))


root = tk.Tk()

app = ClusteringGUI(root)

root.mainloop()