import os, sys, csv
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
        self.output_dir = "results"
        os.makedirs(self.output_dir, exist_ok=True)
        self.round = 0

        self.show_instructions()

    def show_instructions(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 16)).pack(pady=(20, 20))
        tk.Label(self.root, text="This tool allows the user to cluster images into groups based on their descriptions.", font=("Arial", 11)).pack(pady=(0,3))
        tk.Label(self.root, text="Once the clusters have been generated, the user can review them to make adjustments.", font=("Arial", 11)).pack(pady=(0,3))
        tk.Label(self.root, text="The adjustments are made by removing or altering the top k words representing each cluster.", font=("Arial", 11)).pack(pady=(0,3))
        tk.Label(self.root, text="This process allows the user to refine the clusters to their liking.", font=("Arial", 11)).pack(pady=(0,15))
        tk.Label(self.root, text="NOTE: The top k words stem from the image descriptions.", font=("Arial", 10)).pack(pady=(0,20))

        tk.Button(self.root, text="Next", command=self.show_instructions_2).pack(pady=(0,20))

    def show_instructions_2(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        tk.Label(self.root, text="Welcome to the Visual Clustering Tool!", font=("Arial", 16)).pack(pady=(20, 20))
        tk.Label(self.root, text="By starting the tool, the user will be guided through the following steps:", font=("Arial", 11)).pack(pady=(0,10))
        instructions = [ 
            "1. Select a CSV file containing the image descriptions and image paths.", 
            "2. Optionally set the clustering parameters, or continue with the default settings.", 
            "3. Run the clustering algorithm to generate groups of similar images.", 
            "4. Inspect a selection of the images and the top words representing each cluster.", 
            "5. Adjust the top words used to represent the clusters if necessary.", 
            "6. Repeat steps 3-5 until the clusters are satisfactory." ]
        for instruction in instructions:
            tk.Label(self.root, text=instruction, font=("Arial", 11)).pack(padx=50, pady=(0, 3))
        tk.Button(self.root, text="Start", command=self.show_file_selection).pack(pady=(17,20))

    def show_file_selection(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="File Selection.", font=("Arial", 14)).pack(pady=(20,20))
        tk.Label(self.root, text="Select a CSV file containing the image descriptions to cluster.", font=("Arial", 11)).pack(pady=(0,15))
        tk.Label(self.root, text="NOTE: The CSV file should contain the image descriptions and corresponding image paths.", font=("Arial", 10)).pack(pady=(0,3))
        tk.Label(self.root, text="NOTE: Make sure the images and corresponding description CSV files are saved in the same directory.", font=("Arial", 10)).pack(pady=(0,20))

        tk.Button(self.root, text="Select File", command=self.import_file).pack(pady=(0,10))

        self.file_label = tk.Label(self.root,text="No file selected")
        self.file_label.pack(pady=(0,20))

        self.next_button = tk.Button(self.root, text="Next", command=self.argument_setting, state="disabled")
        self.next_button.pack(pady=(0,20))

    def import_file(self):
        file_path = filedialog.askopenfilename(title="Select a file",filetypes=[("CSV files", "*.csv"),("All files", "*.*")])

        if file_path:
            self.input_file = file_path
            self.file_label.config(text=f"Selected file:\n{file_path}")
            self.next_button.config(state="normal")

    def argument_setting(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        tk.Label(self.root, text="Set clustering variables.", font=("Arial", 14)).pack(pady=(20, 15))
        tk.Label(self.root, text="If no changes are made, the default values will be used.", font=("Arial", 11)).pack(pady=(0, 15))

        self.arguments = create_argument_settings(self.root)

        self.next_button = tk.Button(self.root, text="Next", command=self.cluster)
        self.next_button.pack(pady=(0,20))

    def cluster(self):
        arguments = {
            key: widget.get()
            for key, widget in self.arguments.items()}
            # Validate before changing the screen
        valid, error_message = self.validate_arguments(arguments)
        if not valid:
            messagebox.showerror("Invalid input", error_message)
            return
        self.arguments = arguments

        for widget in self.root.winfo_children():
            widget.destroy()

        self.cluster_view = ClusterView(self.root, self, self.input_file, self.output_dir, self.round, self.arguments)

    from tkinter import messagebox


    def validate_arguments(self, arguments):
        # Embedding batch size
        try:
            embedding_batch = int(arguments["embedding_batch"])
            if embedding_batch <= 0:
                return False, "Embedding batch size must be greater than 0."
        except ValueError:
            return False, "Embedding batch size must be an integer."
        # TF-IDF
        if arguments["embedding_model"] == "tfidf":
            try:
                topk = int(arguments["topk"])
                if topk <= 0:
                    return False, "Number of top terms must be greater than 0."
            except ValueError:
                return False, "Number of top terms must be an integer."
        # Reduction
        try:
            components = int(arguments["components"])
            if components <= 0:
                return False, "Number of dimensions must be greater than 0."
        except ValueError:
            return False, "Number of dimensions must be an integer."
        # UMAP
        if arguments["reduction_model"] == "umap":
            try:
                neighbors = int(arguments["neighbors"])
                if neighbors <= 0:
                    return False, "Number of neighbors must be greater than 0."
            except ValueError:
                return False, "Number of neighbors must be an integer."
        # HDBSCAN
        if arguments["cluster_method"] == "hdbscan":
            try:
                min_cluster_size = int(arguments["min_cluster_size"])
                if min_cluster_size <= 0:
                    return False, "Minimum cluster size must be greater than 0."
            except ValueError:
                return False, "Minimum cluster size must be an integer."
        # KMeans
        elif arguments["cluster_method"] == "kmeans":
            try:
                num_clusters = int(arguments["num_clusters"])
                if num_clusters <= 0:
                    return False, "Number of clusters must be greater than 0."
            except ValueError:
                return False, "Number of clusters must be an integer."
        return True, None

    def done(self):
        tk.Label(self.root, text="Clustering process is completed.", font=("Arial", 14)).pack(pady=(20, 15))
        tk.Label(self.root, text=f"All results are stored in the {self.output_dir} directory.", font=("Arial", 11)).pack(pady=(0, 15))
        tk.Label(self.root, text=f"The window can now be closed.", font=("Arial", 11)).pack(pady=(0, 15))
        pass




root = tk.Tk()

app = ClusteringGUI(root)

root.mainloop()