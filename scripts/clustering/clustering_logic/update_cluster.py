import os, json, csv, re
import pandas as pd

def update_clustering_terms(input_file, next_output_dir, round_output_dir, progress_callback):
    """
    Update the terms for a specific cluster.
    """
    clusters = os.path.join(round_output_dir, "clusters.csv")  # ID, ClusterID
    cluster_updates = os.path.join(round_output_dir, "cluster_updates.csv")  # cluster_id, term, delete, new_term
    updated_input_file = os.path.join(next_output_dir, "updated_input_file.csv")
    updated_ids_file = os.path.join(round_output_dir, "updated_ids.json")
    clusters_df = pd.read_csv(clusters)
    cluster_updates_df = pd.read_csv(cluster_updates).fillna("")

    updated_ids = []

    out = open(updated_input_file, 'w', encoding='utf-8')
    out.write('ID' + '\t' + 'Dir' + '\t' + 'ImageID' + '\t' + 'Labels' + '\n')
    with open(input_file, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter='\t')
        for i, row in enumerate(reader):
        # for row in reader:
            if progress_callback:
                progress_callback(i, len(clusters_df), "Updating image descriptions ...")
            id = row['ID']
            dir = row['Dir']
            img = row['ImageID']
            text = row['Labels']
            altered = False
            # replace text
            # find cluster on id in clusters_df
            cluster_id = clusters_df[clusters_df['ID'] == int(id)]['ClusterID'].iloc[0]
            # change text based on cluster_updates
            if cluster_id > -1:
                # at cluster_id -> delete term with True 
                text_updates = cluster_updates_df[cluster_updates_df['cluster_id'] == int(cluster_id)]
                deletions = text_updates[text_updates['delete'] == True]['term'].tolist()
                for term in deletions:
                    new_text = re.sub(re.escape(term), '', text, flags=re.IGNORECASE)
                    if new_text != text:
                        text=new_text
                        altered = True
                # at cluster_id -> replace merged_terms with term
                updates = text_updates[text_updates['delete'] == False][['term', 'new_term']].to_dict('records')
                for update in updates:
                    new_term = update['new_term']
                    if len(new_term) > 0:                
                        new_text = re.sub(update["term"], re.escape(new_term), text, flags=re.IGNORECASE)
                        if new_text != text:
                            text=new_text
                            altered=True
            if altered:
                updated_ids += [id]
            out.write(id + '\t' + dir + '\t' + img + '\t' + text + '\n')
    out.close()
    with open(updated_ids_file, "w", encoding="utf-8") as f:
        json.dump(list(updated_ids), f)
    return updated_input_file, len(updated_ids)