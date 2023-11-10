import streamlit as st
import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN
import Levenshtein
import warnings
warnings.filterwarnings("ignore")
import sys
from collections import defaultdict

def page_2():

    st.title("Clustering option")

    updated_dataframe = st.session_state.df

    if 'df' in st.session_state:
        updated_dataframe = st.session_state.df
        # Using the previous DataFrame on this page
        st.write("Dataframe")
        st.write(updated_dataframe)
    if 'header_name' not in st.session_state:
        st.session_state.header_name = 'none' # from user
    if 'distance_matrix' not in st.session_state:
        st.session_state.distance_matrix = None # from function
    if 'clusters' not in st.session_state:
        st.session_state.clusters = None
    if 'old_names' not in st.session_state:
        st.session_state.old_names = None
    if 'item_to_move' not in st.session_state:
        st.session_state.item_to_move = 'none'
    if 'from_cluster_id' not in st.session_state:
        st.session_state.from_cluster_id = 'none'
    if 'editing_clusters' not in st.session_state:
        st.session_state.editing_clusters = None
    if 'cluster1_id' not in st.session_state:
        st.session_state.cluster1_id = None
    if 'cluster2_id' not in st.session_state:
        st.session_state.cluster2_id = None
    if 'new_item' not in st.session_state:
        st.session_state.new_item = None
    if 'edit_cluster' not in st.session_state:
        st.session_state.edit_cluster = None
    if 'name_to_edit' not in st.session_state:
        st.session_state.name_to_edit = None
    
    def levenshtein_distance(s1, s2):
        return Levenshtein.distance(s1, s2)
    
    def clustering(data):
        # Add a widget to set the 'header_name' variable
        # st.subheader('Set Header Name:')
        header_name = st.text_input("Enter the Header Name:", key="header_name_input")
        # Add a button to trigger the distance matrix computation
        submit_button = st.button("Compute Clustering")
        if submit_button:
            st.session_state.header_name = header_name  # Update session state
            if header_name != 'none':
                texts = data[st.session_state.header_name].str.lower()
                distance_matrix = np.zeros((len(texts), len(texts)))
                for i in range(len(texts)):
                    for j in range(i, len(texts)):
                        distance_matrix[i, j] = levenshtein_distance(texts[i], texts[j])
                        distance_matrix[j, i] = distance_matrix[i, j]
                st.session_state.distance_matrix = distance_matrix  # Update session state
                # Perform DBSCAN clustering
                dbscan = DBSCAN(eps=0.05, min_samples=1, metric="cosine")
                labels = dbscan.fit_predict(distance_matrix)
                # Analyze the clustering results
                clusters = {}
                old_names = {}
                for i, label in enumerate(labels):
                    if label not in clusters:
                        clusters[label] = []
                    clusters[label].append(texts[i])
                    if label not in old_names:
                        old_names[label] = []
                    old_names[label].append(texts[i])
                
                st.session_state.clusters = clusters  # Update session state
                st.session_state.old_names = old_names  # Update session state
            
            # Display the clustering results
            st.subheader('Clustering Results:')
            if st.session_state.clusters is not None:
                st.write(st.session_state.clusters)
        
        return clusters, old_names, header_name
    
    def editing_cluster(data):
        # calling the clustering function
        editing_clusters, old_names, header_name = clustering(data)
        while True:
            st.write("Current Clusters:")
            for cluster_label, cluster_items in editing_clusters.items():
                st.write(f"Cluster {cluster_label}: {cluster_items}")
            choice = st.selectbox("Options for editing clusters:",("Move an item to another cluster","Merge clusters", "Split a cluster","Create a new cluster","Edit the information within the cluster", "Skip"))
            if choice == "Move an item to another cluster":
                item_to_move = st.text_input("Enter the item you want to move:", key="item_to_move_input")
                from_cluster_id = st.text_input("Enter the current cluster ID:", key="from_cluster_id_input")
                to_cluster_id = st.text_input("Enter the target cluster ID:", key="to_cluster_id_input")
                # Add a button to trigger the distance matrix computation
                submit_button = st.button("Move item")
                if submit_button:
                    st.session_state.item_to_move = item_to_move  # Update session state
                    st.session_state.from_cluster_id = from_cluster_id
                    if item_to_move in editing_clusters[from_cluster_id]:
                        editing_clusters[from_cluster_id].remove(item_to_move)
                        editing_clusters[to_cluster_id].append(item_to_move)
                    st.session_state.editing_clusters = editing_clusters
            elif choice == "Merge clusters":
                cluster1_id = st.text_input("Enter the first cluster ID to merge: ")
                cluster2_id = st.text_input("Enter the second cluster ID to merge: ")
                submit_button = st.button("Merge item")
                if submit_button:
                    st.session_state.cluster1_id = cluster1_id  # Update session state
                    st.session_state.cluster2_id = cluster2_id
                    editing_clusters[cluster1_id] += editing_clusters[cluster2_id]
                    del editing_clusters[cluster2_id]
                st.session_state.editing_clusters = editing_clusters
            elif choice == "Split a cluster":
                cluster_id = st.text_input("Enter the cluster ID to split: ")
                item_to_split = st.text_input("Enter the item you want to split: ")
                submit_button = st.button("Split a cluster")
                if submit_button:
                    st.session_state.cluster_id = cluster_id  # Update session state
                    st.session_state.item_to_split = item_to_split
                    if item_to_split in editing_clusters[cluster_id]:
                        editing_clusters[cluster_id].remove(item_to_split)
                        new_cluster_id = max(editing_clusters.keys()) + 1 # could be an error
                        editing_clusters[new_cluster_id] = [item_to_split]
                st.session_state.editing_clusters = editing_clusters
        
            elif choice == "Create a new cluster":
                new_cluster_id = max(editing_clusters.keys()) + 1
                new_item = st.text_input("Enter the new item to create a cluster:", key="new_item_input")
                submit_button = st.button("Create cluster")
                if submit_button:
                    st.session_state.new_item = new_item
                    editing_clusters[new_cluster_id] = [new_item]
                st.session_state.editing_clusters = editing_clusters

            elif choice == "Edit the information within the cluster":
                edit_cluster = st.text_input("Enter the cluster ID to edit: ")
                name_to_edit = st.text_input("Enter the name you want to replace: ")
                submit_button = st.button("Edit cluster")
                if submit_button:
                    st.session_state.edit_cluster = edit_cluster
                    st.session_state.name_to_edit = name_to_edit
                    for item in editing_clusters[edit_cluster]:
                        if item != name_to_edit:
                            editing_clusters[edit_cluster][editing_clusters[edit_cluster].index(item)] = name_to_edit
                st.session_state.editing_clusters = editing_clusters
            elif choice == "Skip":
                break

        data[header_name] = data[header_name].str.lower()
        for clusters_key, clusters_items in old_names.items():
            for item in clusters_items:
                data = data.replace(item, editing_clusters[clusters_key][0])

        editing_clusters = editing_cluster(updated_dataframe)
        return editing_clusters

