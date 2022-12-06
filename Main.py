#!/usr/bin/env python
# coding: utf-8

# In[58]:


import pydicom
import os
import pymongo
import nibabel as nib
import numpy as np
import matplotlib.pyplot as plt
import json 
from tkinter import *
from tkinter import filedialog
from tkinter import ttk
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)
import pandas as pd
from datetime import datetime
from PIL import ImageTk, Image  

#Connect to MongoDB
client = pymongo.MongoClient("TOBECHANGED") #CHANGE THIS TO MONGODB PYTHON CONNECTING TOKEN


# In[59]:


def dict_dicoms(filepath):
    mainlist = {}
    lst = os.listdir(filepath)
    number = 0
    mainlist["Path"] = filepath
    for i in lst: 
        if (i.endswith(".dcm")):
            mainlist["Layer " + str(number)] = i
            number += 1
    if len(mainlist) != 1: return mainlist
    else: return {}

def list_dicoms(filepath):
    mainlist = []
    lst = os.listdir(filepath)
    number = 0
    for i in lst: 
        if (i.endswith(".dcm")):
            mainlist.append(i)
    return mainlist

def extract_meta(ds):
    exmpl = {}
    for elem in ds:
        el = str(elem)
        el = ' '.join(el.split()[2:])
        exmpl[elem.keyword] = el.split(": ")[1].replace("'", "")
    return exmpl

def get_all_dicoms(rootdir):
    folder_paths = []
    for rootdir, dirs, files in os.walk(rootdir):
        for subdir in dirs:
            foldername = os.path.join(rootdir, subdir)
            folder_paths.append(foldername)
    alldcms = {}
    for el in folder_paths:
        dcm_list = list_dicoms(el)
        dcm_dict = dict_dicoms(el)
        if len(dcm_list) != 0:
            alldcms[el.split("\\")[len(el.split("\\")) - 1]] = dcm_dict #folder name to the dict name
            
    return alldcms

#NIFTI functions

def list_niftis(filepath):
    mainlist = []
    lst = os.listdir(filepath)
    number = 0
    for i in lst: 
        if (i.endswith(".nii")):
            mainlist.append(i)
    return mainlist

#MONGODB functions
def upload_dicoms_push (collection, uid, d_folders): 
    collection.find_one_and_update(
            {"_id" : uid},
            { "$set" :
            {"_id" : uid,
             "DicomFolders" : d_folders }},
            upsert = True)
    print("successfully uploaded", len(d_folders), "-th folder to ", uid)
    
def upload_beh_push (collection, uid, beh_dict):
    collection.find_one_and_update(
            {"_id" : uid},
            { "$set" :
            {"_id" : uid,
             "BehavioralData" : beh_dict}},
            upsert = True)
    
def upload_notes_push (collection, uid, notes_dict):
    collection.find_one_and_update(
            {"_id" : uid},
            { "$set" :
            {"_id" : uid,
             "Notes" : notes_dict}},
            upsert = True)

lengths_pipeline = [
  {
    "$project": {
      "_id": 0,
      "NotesLength": {
        "$size": {
          "$objectToArray": "$Notes"
        }
      },
      "BehavioralLength": {
        "$size": {
          "$objectToArray": "$BehavioralData"
        }
      }
    }
  }
]


#Cosmetic functions
def pic_resized_small(filepath):
    img = Image.open(filepath)
    resized_image= img.resize((10,10))
    new_image= ImageTk.PhotoImage(resized_image)
    return new_image



# In[60]:


def donothing (rubbish = 0): print("zhopa")
db=client["test1"]
collection = db["GUI-Upload-tEsT"]

return_folder = ""
listed = {}
common_metadata = {}
global dicom_dict_upload
dicom_dict_upload = {}
global selected_fname
selected_fname = ""

def open_dicom_adder(): 
    dicom_adder = Toplevel(root)
    dicom_adder.title("Add Dicom Folders")
    dicom_adder.geometry("1000x680")
    dicom_adder.iconbitmap('assets\\icon.ico')
    
    ################################################## PREVIEW DATA STRUCTURE
    folders_frame = Frame(dicom_adder, bg = "#eaeaea") #FOLDERS LISTBOX     
    folders_frame.place(relx = 0.05, rely = 0.05, relwidth = 0.24, relheight = 0.45)
    folders_listbox = Listbox (folders_frame, exportselection=False)
    folders_listbox.place(relwidth = 1, relheight = 1)
    
    b_listbox_scrollbar = Scrollbar(folders_frame, orient='horizontal') #Horizontal scrollbar
    b_listbox_scrollbar.pack(side=BOTTOM, fill=X)
    folders_listbox.config(xscrollcommand = b_listbox_scrollbar.set)
    b_listbox_scrollbar.config(command = folders_listbox.xview)
    
    listbox_scrollbar = Scrollbar(folders_frame)
    listbox_scrollbar.pack(side=RIGHT, fill=Y)
    folders_listbox.config(yscrollcommand = listbox_scrollbar.set)
    listbox_scrollbar.config(command = folders_listbox.yview)
    
    ####
    
    dicom_frame = Frame(dicom_adder, bg = "#eaeaea") #DICOM LISTBOX
    dicom_frame.place(relx = 0.3, rely = 0.05, relwidth = 0.24, relheight = 0.5)
    dicom_listbox = Listbox (dicom_frame, exportselection=False)
    dicom_listbox.place(relwidth = 1, relheight = 1) 
    
    b_listbox_scrollbar = Scrollbar(dicom_frame, orient='horizontal') #Horizontal scrollbar
    b_listbox_scrollbar.pack(side=BOTTOM, fill=X)
    dicom_listbox.config(xscrollcommand = b_listbox_scrollbar.set)
    b_listbox_scrollbar.config(command = dicom_listbox.xview)
    
    listbox_scrollbar = Scrollbar(dicom_frame)
    listbox_scrollbar.pack(side=RIGHT, fill=Y)
    dicom_listbox.config(yscrollcommand = listbox_scrollbar.set)
    listbox_scrollbar.config(command = dicom_listbox.yview)
    
    preview_dicom_frame = Frame(dicom_adder, bg = "#eaeaea") #PREVIEW FIRST SCAN 
    preview_dicom_frame.place(relx = 0.05, rely = 0.56, relwidth = 0.24, relheight = 0.29)
    
    def select_folder(event = 0):
        dicom_listbox.delete(0, "end") #Deleting all entries
        name_dicom_text.delete(0 , END) 
        pid_dicom_text.delete(0 , END)
        mod_dicom_text.delete(0 , END)
        fol_dicom_text.delete(0 , END)
        res_dicom_text.delete(0 , END)
        tree_meta.delete(*tree_meta.get_children())
        
        item = folders_listbox.get(folders_listbox.curselection())
        global selected_fname
        selected_fname = item
        
        global dicom_dict_upload        
        selected_folder = dicom_dict_upload["DicomFolders"][item]
        
        for i in reversed(json.dumps(selected_folder["FileList"], indent = 6).replace("{", "").replace("}", "").split("\n")):
            dicom_listbox.insert(0, str(i))
        
        name_dicom_text.insert("insert", str(selected_folder["PatientName"]))
        pid_dicom_text.insert("insert", str(selected_folder["PatientID"]))
        mod_dicom_text.insert("insert", str(selected_folder["Modality"]))
        fol_dicom_text.insert("insert", str(item))
        
        for i in selected_folder["MetaData"].keys(): 
                tree_meta.insert("",'end',text="L1",values=(i,selected_folder["MetaData"][i]))  
        
        
    
    folders_listbox.bind("<<ListboxSelect>>", select_folder)
    
    folders_select = Button (dicom_adder, text = "Select Folder", command = select_folder)
    folders_select.place(relx = 0.05, rely = 0.5, relwidth = 0.12, relheight = 0.03)
    
    def delete_folder(event = 0):
        dicom_listbox.delete(0, "end") #Deleting all entries
        name_dicom_text.delete(0 , END) 
        pid_dicom_text.delete(0 , END)
        mod_dicom_text.delete(0 , END)
        fol_dicom_text.delete(0 , END)
        res_dicom_text.delete(0 , END)
        tree_meta.delete(*tree_meta.get_children())
        
        item = folders_listbox.get(folders_listbox.curselection())
        global dicom_dict_upload        
        dicom_dict_upload["DicomFolders"].pop(item)
        
        folders_listbox.delete(0, "end")
        for i in dicom_dict_upload["DicomFolders"].keys():
            folders_listbox.insert(0, str(i))
    
    folders_delete = Button (dicom_adder, text = "Delete Folder", command = delete_folder) 
    folders_delete.place(relx = 0.17, rely = 0.5, relwidth = 0.12, relheight = 0.03)
    
    #===================================== Console
    
    console_dicom = Text(dicom_adder, bg = "#eaeaea")
    console_dicom.place (relx = 0.3, rely = 0.56, relwidth = 0.24, relheight = 0.29)
    console_dicom.configure(state="disable")
    
    def print_console(text):
        console_dicom.configure(state="normal")
        console_dicom.insert("insert", str(text) + "\n\n")
        console_dicom.configure(state="disable")
    
    ##################################################
    
    ################################################## BROWSE BUTTON
    def browse_button():  #sets return_folder to be the user's folder
        global return_folder
        global listed
        global dicom_dict_upload
        
        filename = filedialog.askdirectory()
        return_folder = filename
        print_console(filename)
        
        dicom_listbox.delete(0, "end")
        folders_listbox.delete(0,"end")
        num = 0
        listed = dict_dicoms(return_folder)
        for i in reversed(json.dumps(listed, indent = 6).replace("{", "").replace("}", "").split("\n")):
            dicom_listbox.insert(num, str(i))
        
        name_dicom_text.delete(0 , END) #Deleting all files
        pid_dicom_text.delete(0 , END)
        mod_dicom_text.delete(0 , END)
        fol_dicom_text.delete(0 , END)
        res_dicom_text.delete(0 , END)
        tree_meta.delete(*tree_meta.get_children())
        
        if (len(listed) != 0):
            first_file_path = listed["Path"] + "\\" + listed["Layer 0"]
            ds = pydicom.dcmread(first_file_path) #Update metadata
            name_dicom_text.insert("insert", str(ds.PatientName))
            pid_dicom_text.insert("insert", str(ds.PatientID))
            mod_dicom_text.insert("insert", str(ds.Modality))
            fol_dicom_text.insert("insert", str(listed["Path"].split("/")[-1]))
                    
            fig = plt.figure(1) #Update preview picture
            canvas = FigureCanvasTkAgg(fig, preview_dicom_frame)
            plot_widget = canvas.get_tk_widget()
            ax = plt.gca()
            ax.axes.xaxis.set_visible(False)
            ax.axes.yaxis.set_visible(False)
            plt.grid(True)
            plt.imshow(ds.pixel_array, cmap=plt.cm.bone)
            plot_widget.place(relwidth = 1, relheight = 1)
            
            global selected_fname
            selected_fname = listed["Path"].split("/")[-1]
            
            global common_metadata
            common_metadata = extract_meta(ds)#adding all metadata to the table
            for i in common_metadata.keys(): 
                tree_meta.insert("",'end',text="L1",values=(i,common_metadata[i])) 
            dicom_dict_upload["DicomFolders"][selected_fname] = {"PatientID" : str(ds.PatientID),
                                                "PatientName" : str(ds.PatientName),
                                                "Modality" : str(ds.Modality),
                                                "ResearchGroup" : "",
                                                "FileList" : listed,
                                                "MetaData" : common_metadata}
            
            dicom_folders = dicom_dict_upload["DicomFolders"]
            for i in dicom_folders.keys():
                folders_listbox.insert(0, str(i))   
            
    
    browse_dicom = Button(dicom_adder, text="Add file", command=browse_button)
    browse_dicom.place(relx = 0.88, rely = 0.05, relwidth = 0.07, relheight = 0.03)
    
    
    ##################################################
    def search_button():
        return_folder = ""
        listed = {}
        common_metadata = {}
        
        global dicom_dict_upload
        dicom_dict_upload = {}
        
        search_result = collection.find_one({"_id" : uid_dicom_text.get()})
        
        dicom_listbox.delete(0, "end") #Deleting all entries
        folders_listbox.delete(0, "end")
        name_dicom_text.delete(0 , END) 
        pid_dicom_text.delete(0 , END)
        mod_dicom_text.delete(0 , END)
        fol_dicom_text.delete(0 , END)
        res_dicom_text.delete(0 , END)
        tree_meta.delete(*tree_meta.get_children())
        
        if search_result == None: 
            print_console("Could not find anything with UID " + 
                                                uid_dicom_text.get() + ", upload to create a new instance")
            dicom_dict_upload = {"_id" : uid_dicom_text.get(),
                                "DicomFolders" : {}}
        else:
            dicom_folders = {}
            dicom_dict_upload = search_result
            print_console(uid_dicom_text.get() + " Found, connected to the database")
            if "DicomFolders" in search_result: dicom_folders = search_result["DicomFolders"]
            for i in dicom_folders.keys():
                folders_listbox.insert(0, str(i))
    
    search_uid = Button(dicom_adder, text="Input UID", command=search_button)
    search_uid.place(relx = 0.55, rely = 0.05, relwidth = 0.07, relheight = 0.03)
    
    uid_dicom_text = Entry(dicom_adder)
    uid_dicom_text.place(relx = 0.62, rely = 0.05, relwidth = 0.26, relheight = 0.03)
    
    ################################################## INPUT METADATA
    
    fol_dicom_label = Label (dicom_adder, text = "Folder Name", anchor="e")
    fol_dicom_label.place(relx = 0.55, rely = 0.10, relwidth = 0.1, relheight = 0.025)
    fol_dicom_text = Entry(dicom_adder)
    fol_dicom_text.place(relx = 0.68, rely = 0.10, relwidth = 0.27, relheight = 0.025)
    
    Frame(dicom_adder, bg = "gray").place(relx = 0.55, rely = 0.1375, relwidth = 0.40, relheight = 0.0001)
    
    name_dicom_label = Label (dicom_adder, text = "PatientName", anchor="e")
    name_dicom_label.place(relx = 0.55, rely = 0.15, relwidth = 0.1, relheight = 0.025)
    name_dicom_text = Entry(dicom_adder)
    name_dicom_text.place(relx = 0.68, rely = 0.15, relwidth = 0.27, relheight = 0.025)
    
    pid_dicom_label = Label (dicom_adder, text = "Patient ID", anchor="e")
    pid_dicom_label.place(relx = 0.55, rely = 0.18, relwidth = 0.1, relheight = 0.025)
    pid_dicom_text = Entry(dicom_adder)
    pid_dicom_text.place(relx = 0.68, rely = 0.18, relwidth = 0.27, relheight = 0.025)
    
    mod_dicom_label = Label (dicom_adder, text = "Modality", anchor="e")
    mod_dicom_label.place(relx = 0.55, rely = 0.21, relwidth = 0.1, relheight = 0.025)
    mod_dicom_text = Entry(dicom_adder)
    mod_dicom_text.place(relx = 0.68, rely = 0.21, relwidth = 0.27, relheight = 0.025)
    
    res_dicom_label = Label (dicom_adder, text = "Research Group", anchor="e")
    res_dicom_label.place(relx = 0.55, rely = 0.24, relwidth = 0.1, relheight = 0.025)
    res_dicom_text = Entry(dicom_adder)
    res_dicom_text.place(relx = 0.68, rely = 0.24, relwidth = 0.27, relheight = 0.025)
    
    #===================================== EXTENDED METADATA DISPLAY
    
    meta_frame = Frame (dicom_adder)
    meta_frame.place(relx = 0.55, rely = 0.32, relwidth = 0.40, relheight = 0.44)
    tree_meta = ttk.Treeview(meta_frame,selectmode='browse')
    
    tree_meta.place(relwidth = 1, relheight = 1)
    tree_meta["columns"] = ("1", "2")
    tree_meta['show'] = 'headings'
    tree_meta.column("1", width=30, anchor='w')
    tree_meta.column("2", width=100, anchor='w')
    tree_meta.heading("1", text="Keys")
    tree_meta.heading("2", text="Values")
    
    #===================================== EXTENDED METADATA INPUT
    
    metaadder_frame = Frame (dicom_adder, bg = "#eaeaea")
    metaadder_frame.place(relx = 0.55, rely = 0.77, relwidth = 0.40, relheight = 0.05) 
    
    key_dicom_text = Text(metaadder_frame)
    key_dicom_text.place(relx = 0, relwidth = 0.4, relheight = 1)
    value_dicom_text = Text(metaadder_frame)
    value_dicom_text.place(relx = 0.4, relwidth = 0.6, relheight = 1)
    
    def add_meta_dicom():
        global dicom_dict_upload
        global selected_fname
        tree_meta.delete(*tree_meta.get_children())
        dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"][key_dicom_text.get("1.0","end-1c")] = value_dicom_text.get("1.0","end-1c")
        for i in dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"].keys(): 
                tree_meta.insert("",'end',text="L1",values=(i,dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"][i]))
        key_dicom_text.delete('1.0', END)
        value_dicom_text.delete('1.0', END)
    
    def select_meta_dicom(event = 0):
        selected = tree_meta.focus()
        temp = tree_meta.item(selected, 'values')
        key_dicom_text.delete('1.0', END)
        key_dicom_text.insert("insert", str(temp[0]))
        value_dicom_text.delete('1.0', END)
        value_dicom_text.insert("insert", str(temp[1]))
    
    def rmv_meta_dicom():
        dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"][key_dicom_text.get("1.0","end-1c")] = "tobedeleted"
        tree_meta.delete(*tree_meta.get_children())
        dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"].pop(key_dicom_text.get("1.0","end-1c"))
        for i in dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"].keys(): 
                tree_meta.insert("",'end',text="L1",values=(i,dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"][i]))
        key_dicom_text.delete('1.0', END)
        value_dicom_text.delete('1.0', END)
                
    tree_meta.bind("<Double-1>", select_meta_dicom)
    
    button_metaadder = Button (dicom_adder, text = "Select", command = select_meta_dicom)
    button_metaadder.place (relx = 0.55, rely = 0.83, relwidth = 0.1, relheight = 0.03)
    button_metaadder = Button (dicom_adder, text = "Add/Edit", command = add_meta_dicom)
    button_metaadder.place (relx = 0.7, rely = 0.83, relwidth = 0.1, relheight = 0.03)
    button_metaadder = Button (dicom_adder, text = "Remove", command = rmv_meta_dicom)
    button_metaadder.place (relx = 0.85, rely = 0.83, relwidth = 0.1, relheight = 0.03)
    
    ##################################################
    
    ##################################################  DATABASE AND UPLOADING MANAGEMENT
    def rename_folder():
        global selected_fname
        dicom_dict_upload["DicomFolders"][fol_dicom_text.get()] = {
            "PatientID" : pid_dicom_text.get(),
            "PatientName" : name_dicom_text.get(),
            "Modality" : mod_dicom_text.get(),
            "ResearchGroup" : res_dicom_text.get(),
            "FileList" : dicom_dict_upload["DicomFolders"][selected_fname]["FileList"],
            "MetaData" : dicom_dict_upload["DicomFolders"][selected_fname]["MetaData"]
        }
        print_console( str(fol_dicom_text.get()) + " - header has been modified")
        folders_listbox.delete(0, "end")
        if selected_fname != fol_dicom_text.get(): dicom_dict_upload["DicomFolders"].pop(selected_fname)
        for i in dicom_dict_upload["DicomFolders"].keys():
            folders_listbox.insert(0, str(i))
        selected_fname = fol_dicom_text.get()
    
    rename_dict = Button(dicom_adder, text="Edit Header", command=rename_folder)
    rename_dict.place(relx = 0.85, rely = 0.27, relwidth = 0.1, relheight = 0.04)
    
    def upload_dicom():
        if dicom_dict_upload != {}: 
            upload_dicoms_push (collection, dicom_dict_upload["_id"], dicom_dict_upload["DicomFolders"])
            print_console("Successfully uploaded " + str(len(dicom_dict_upload["DicomFolders"])) + " folders to" + dicom_dict_upload["_id"])
        else: print_console("Nothing to upload")
    
    upload_button = Button(dicom_adder, text="Upload to Database", command=upload_dicom)
    upload_button.place(relx = 0.75, rely = 0.9, relwidth = 0.2, relheight = 0.05)
    
    ##################################################
    


# In[61]:


def open_behavioral_adder():
    global beh_result  
    beh_result = {"BehavioralData" : {}}
    global dict_to_upload
    dict_to_upload = {}
    global selected_folder
    selected_folder = ""
    
    behavioral_adder = Toplevel(root)
    behavioral_adder.title("Add Behavioral Data")
    behavioral_adder.geometry("1000x680")
    behavioral_adder.iconbitmap('assets\\icon.ico')
        
    ################################################## Search Function
    def search_button():
        if text_search.get() == "": found_label.config(text = "Input non-empty UID")
        if text_search.get() != "":
            beh_list.configure(state=NORMAL)
            templates_listbox.configure(state=NORMAL)

            global beh_result
            global dict_to_upload

            dict_to_upload = {}#resetting everything 
            beh_result = collection.find_one({"_id" : text_search.get()})

            beh_list.delete(0, "end") #clear all
            tree_table.delete(*tree_table.get_children())
            found_label.config(text = "Nothing is found with this UID, uploading the document will create a new instance")

            if beh_result != None:
                print("Found something")
                text_for_label = "Patient " + text_search.get() + " was found. Successfully connected..."
                found_label.config(text = text_for_label)
                if "BehavioralData" in beh_result: dict_to_upload = beh_result["BehavioralData"]
                else: dict_to_upload = {}
                for i in dict_to_upload:beh_list.insert(0, i)
            
            
    
    search_frame = Frame (behavioral_adder)
    search_frame.place (relx = 0.07, rely = 0.05, relwidth = 0.17, relheight = 0.03)
    
    found_label = Label (behavioral_adder, anchor="e")
    found_label.place(rely = 0.02, relx = 0.05)
        
    label_search = Label (behavioral_adder, text = "UID", anchor="e")
    label_search.place(rely = 0.05, relx = 0.07)
    
    text_search = Entry (search_frame)
    text_search.place(rely = 0, relheight = 1, relx = 0, relwidth = 0.7)
    button_search = Button (search_frame, text = "Access", command = search_button)
    button_search.place(rely = 0, relheight = 1, relx = 0.7, relwidth = 0.3)   
    
    ##################################################
    
    ################################################## Database docs display
    
    database_docnames = []
    for document in collection.find({}, { "_id": 1}): database_docnames.append(document["_id"]) #uploading the existing docs to the application
    
    docs_frame = Frame (behavioral_adder)
    docs_frame.place (relx = 0.05, rely = 0.1, relwidth = 0.19, relheight = 0.63)
    docs_listbox = Listbox (docs_frame, exportselection=False)
    docs_listbox.place(relwidth = 1, relheight = 1)
    
    def docs_select(event = 0):
        beh_list.configure(state=NORMAL)
        templates_listbox.configure(state=NORMAL)
        
        item = docs_listbox.get(docs_listbox.curselection())
        global beh_result
        global dict_to_upload
        dict_to_upload = {}#resetting everything 
        beh_result = collection.find_one({"_id" : item})
        
        beh_list.delete(0, "end") #clear all
        tree_table.delete(*tree_table.get_children())
        
        text_search.delete(0, "end")
        text_search.insert(0, item)
        
        text_for_label = "Patient " + item + " was found. Successfully connected..."
        found_label.config(text = text_for_label)
        if "BehavioralData" in beh_result: dict_to_upload = beh_result["BehavioralData"]
        else: dict_to_upload = {}
        for i in dict_to_upload:beh_list.insert(0, i)
    
    docs_listbox.bind("<<ListboxSelect>>", docs_select)
    
    for i in database_docnames: docs_listbox.insert(0, i)
    
    ##################################################
    
    ################################################## Listbox folder management    
    
    lboxes_frame = Frame (behavioral_adder, bg = "#eaeaea")
    lboxes_frame.place(relx = 0.25, rely = 0.05, relwidth = 0.19, relheight = 0.55)
    beh_list = Listbox (lboxes_frame, exportselection=False)
    beh_list.place(relwidth = 1, relheight = 0.95)
    
    def select_folder(event = 0):
        item = beh_list.get(beh_list.curselection())
        global selected_folder
        selected_folder = item
        tree_table.delete(*tree_table.get_children())
        entry_rename.delete(0, END)
        entry_rename.insert(0, selected_folder)
        for i in dict_to_upload[item].keys(): 
                tree_table.insert("",'end',text="L1",values=(i,dict_to_upload[item][i]))
                
    def delete_folder (event = 0):
        item = beh_list.get(beh_list.curselection())
        beh_list.delete(0, "end")
        dict_to_upload.pop(item)
        for i in dict_to_upload: beh_list.insert(0, i)
        
        
    beh_list.bind("<<ListboxSelect>>", select_folder)
    
    lbox_select_button = Button(lboxes_frame, text = "Select", command = select_folder)
    lbox_select_button.place(relx = 0, relwidth = 0.5, rely = 0.95, relheight = 0.05)
    lbox_delete_button = Button(lboxes_frame, text = "Delete", command = delete_folder)
    lbox_delete_button.place(relx = 0.5, relwidth = 0.5, rely = 0.95, relheight = 0.05)
    
    
    ###
    def rename_folder():
        item = beh_list.get(beh_list.curselection())
        temp = dict_to_upload[item]
        dict_to_upload.pop(item)
        beh_list.delete(0, "end")
        dict_to_upload[entry_rename.get()] = temp
        for i in dict_to_upload: beh_list.insert(0, i)
    
    def add_folder():
        item = entry_rename.get()
        if item not in dict_to_upload:
            dict_to_upload[item] = {}
            beh_list.delete(0, "end")
            for i in dict_to_upload: beh_list.insert(0, i)
    
    rename_frame = Frame (behavioral_adder)
    rename_frame.place(relx = 0.25, rely = 0.61, relwidth = 0.19, relheight = 0.03)
    
    entry_rename = Entry (rename_frame)
    entry_rename.place (relwidth = 0.5, relheight = 1)
    
    button_rename = Button (rename_frame, text = "Rename", command = rename_folder)
    button_rename.place(relx = 0.5, relwidth = 0.25, relheight = 1)
    
    button_add = Button (rename_frame, text = "Add", command = add_folder)
    button_add.place(relx = 0.75, relwidth = 0.25, relheight = 1)
    
    
    ################################################## 
    ################################################## Table View
    
    table_frame = Frame(behavioral_adder)
    table_frame.place(relx = 0.45, rely = 0.05, relwidth = 0.50, relheight = 0.65)
    tree_table = ttk.Treeview(table_frame,selectmode='browse')
    
    tree_table.place(relwidth = 1, relheight = 1)
    tree_table["columns"] = ("1", "2")
    tree_table['show'] = 'headings'
    tree_table.column("1", width=30, anchor='w')
    tree_table.column("2", width=100, anchor='w')
    tree_table.heading("1", text="Keys")
    tree_table.heading("2", text="Values")
    
    ##################################################
    ################################################## Adder to Table
    
    adder_frame = Frame (behavioral_adder, bg = "#eaeaea")
    adder_frame.place(relx = 0.45, rely = 0.71, relwidth = 0.50, relheight = 0.04)
    
    key_text = Text(adder_frame)
    key_text.place(relx = 0, relwidth = 0.4, relheight = 1)
    value_text = Text(adder_frame)
    value_text.place(relx = 0.4, relwidth = 0.6, relheight = 1)
    
    def add_beh():
        tree_table.delete(*tree_table.get_children())
        dict_to_upload[selected_folder][key_text.get("1.0","end-1c")] = value_text.get("1.0","end-1c")
        for i in dict_to_upload[selected_folder].keys(): 
                tree_table.insert("",'end',text="L1",values=(i,dict_to_upload[selected_folder][i]))
        key_text.delete('1.0', END)
        value_text.delete('1.0', END)
    
    def select_beh (event = 0):
        selected = tree_table.focus()
        temp = tree_table.item(selected, 'values')
        key_text.delete('1.0', END)
        key_text.insert("insert", str(temp[0]))
        value_text.delete('1.0', END)
        value_text.insert("insert", str(temp[1]))
        
    def rmv_beh():
        dict_to_upload[selected_folder][key_text.get("1.0","end-1c")] = "tobedeleted"
        tree_table.delete(*tree_table.get_children())
        dict_to_upload[selected_folder].pop(key_text.get("1.0","end-1c"))
        for i in dict_to_upload[selected_folder].keys(): 
                tree_table.insert("",'end',text="L1",values=(i,dict_to_upload[selected_folder][i]))
        key_text.delete('1.0', END)
        value_text.delete('1.0', END)
    
    tree_table.bind("<Double-1>", select_beh)
    
    dict_management_frame = Frame (behavioral_adder, bg = "#eaeaea")
    dict_management_frame.place(relx = 0.45, rely = 0.75, relwidth = 0.50, relheight = 0.03)
    
    button_select_beh = Button (dict_management_frame, text = "Select", command = select_beh)
    button_select_beh.place (relwidth = 0.33, relheight = 1)
    
    button_add_beh = Button (dict_management_frame, text = "Add/Edit", command = add_beh)
    button_add_beh.place (relx = 0.33333, relwidth = 0.33, relheight = 1)
    
    button_rmv_beh = Button (dict_management_frame, text = "Remove", command = rmv_beh)
    button_rmv_beh.place (relx = 0.6666, relwidth = 0.33, relheight = 1)   
    
    ##################################################
    
    ################################################## Templates management
    
    with open('templates.json') as json_file: template_data = json.load(json_file)
    templates_frame = Frame (behavioral_adder)
    templates_frame.place(relx = 0.25, rely = 0.65, relwidth = 0.19, relheight = 0.30)
    templates_listbox = Listbox (templates_frame, exportselection=False)
    templates_listbox.place(relwidth = 1, relheight = 0.90)
    
    for i in template_data: templates_listbox.insert("end", i)
    
    def select_template(event = 0):
        global dict_to_upload
        global selected_folder
        item = templates_listbox.get(templates_listbox.curselection())
        tree_table.delete(*tree_table.get_children())
        for i in template_data[item]: tree_table.insert("",'end',text="L1",values=(i,template_data[item][i]))
        
        
        tempname = str(item) +"-"+ datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        dict_to_upload[tempname] = template_data[item]
        selected_folder = tempname
        
        beh_list.delete(0, "end")
        for i in dict_to_upload: beh_list.insert(0, i)
    
    templates_button = Button (templates_frame, text = "Select Template", command = select_template)
    templates_button.place (rely = 0.90, relwidth = 1, relheight = 0.1)
    
    
    ##################################################
    
    ################################################## Database management
    
    database_management_frame = Frame(behavioral_adder, highlightbackground="grey", highlightthickness=2)
    database_management_frame.place(relx = 0.05, rely = 0.75, relwidth = 0.19, relheight = 0.20)
    
    def import_table (filepath = -1): #if -1 given, opens browser
        if filepath == -1:
            filepath = filedialog.askopenfilename(title = "Import Table",
                                              filetypes = (("Excel Table", "*.xlsx*"),))
        xls = pd.ExcelFile(filepath)
        df = xls.parse(xls.sheet_names[0])
        df = df.loc[df['Subject ID'] == import_entry.get()].to_dict(orient = "records")
        
        columnnames = df[0].keys()
        num = 0
        
        for i in df:
            num = 2
            foldername = str(i[list(columnnames)[1]])
            while foldername in dict_to_upload:
                temp = foldername
                foldername = foldername + "-" + str(num)
                if foldername in dict_to_upload: foldername = temp
                num += 1
            dict_to_upload[foldername] = {}
            for key in columnnames:
                dict_to_upload[foldername][key] = i[key]
                
        beh_list.delete(0, "end")
        for i in dict_to_upload: beh_list.insert(0, i)
                
    
    import_button = Button(database_management_frame, text = "Import", command = import_table)
    import_button.place(relwidth = 0.4, relheight = 0.15) 
    
    import_entry = Entry(database_management_frame)
    import_entry.place(relx = 0.4, relwidth = 0.6, relheight = 0.15)
    
    uploading_label = Label(database_management_frame, anchor = CENTER)
    uploading_label.place(rely = 0.35, relheight = 0.3, relwidth = 1) 
    
    def upload_secondary ():
        upload_beh_push(collection, text_search.get(), dict_to_upload)
        uploading_label.config(text = text_search.get() + "Uploaded successfully")
        
    
    upload_button = Button (database_management_frame, text = "Upload to Database", command = upload_secondary)
    upload_button.place(relx = 0.2, rely = 0.85, relwidth = 0.6, relheight = 0.15)
    
    #####################################################
    beh_list.configure(state=DISABLED)
    templates_listbox.configure(state=DISABLED)
    
    
    #####################################################
    def plus_add_folder():
        item = "New-folder-"+ datetime.now().strftime("%d-%m-%Y-%H-%M-%S")
        if item not in dict_to_upload:
            dict_to_upload[item] = {}
            beh_list.delete(0, "end")
            for i in dict_to_upload: beh_list.insert(0, i)
    
    picture_plus_button = PhotoImage(file='C:\\Users\\alist\\OneDrive\\Documents\\Work\\Database codes\\assets\\plus.png')
    plus_button = Button(behavioral_adder, image=picture_plus_button, command= plus_add_folder)
    plus_button.place(relx = 0.9, rely = 0.9, relwidth = 0.2, relheight = 0.2)
    
    


# In[62]:


def open_notes_adder(): 
    global notes_to_upload
    notes_to_upload = {}
    global selected_notes_folder
    selected_notes_folder = ""
    
    notes_adder = Toplevel(root)
    notes_adder.title("Add Notes")
    notes_adder.geometry("1000x680")
    notes_adder.iconbitmap('assets\\icon.ico')
    
    ################################################## Search Function
    
    found_label = Label (notes_adder, anchor="e")
    found_label.place(rely = 0.02, relx = 0.05)
    
    def search_button():
        if text_search.get() == "": found_label.config(text = "Input non-empty UID")
        if text_search.get() != "":
            working_area.configure(state=NORMAL)
            
            global notes_to_upload
            notes_to_upload = {}#resetting everything 
            search_result = collection.find_one({"_id" : text_search.get()})
            
            folders_list.delete(0, "end") #clear all
            working_area.delete('1.0', END)
            
            found_label.config(text = "Nothing is found with this UID, uploading the document will create a new instance")
            
            if search_result != None:
                text_for_label = "Patient " + text_search.get() + " was found. Successfully connected..."
                found_label.config(text = text_for_label)
                if "Notes" in search_result: notes_to_upload = search_result["Notes"]
                else: notes_to_upload = {}
                for i in notes_to_upload: folders_list.insert(0, i)
            
    
    search_frame = Frame (notes_adder)
    search_frame.place (relx = 0.05, rely = 0.05, relwidth = 0.19, relheight = 0.03)
    
    found_label = Label (notes_adder, anchor="e")
    found_label.place(rely = 0.02, relx = 0.05)
    
    label_search = Label (search_frame, text = "UID", anchor="e")
    label_search.place(rely = 0, relheight = 1, relx = 0, relwidth = 0.15)
    text_search = Entry (search_frame)
    text_search.place(rely = 0, relheight = 1, relx = 0.15, relwidth = 0.65)
    button_search = Button (search_frame, text = "Access", command = search_button)
    button_search.place(rely = 0, relheight = 1, relx = 0.80, relwidth = 0.2)   
    
    ##################################################
    
    ################################################## Docs list
    
    database_docnames = []
    for document in collection.find({}, { "_id": 1}): database_docnames.append(document["_id"]) #uploading the existing docs to the application
    
    docs_frame = Frame (notes_adder)
    docs_frame.place (relx = 0.05, rely = 0.1, relwidth = 0.19, relheight = 0.85)
    docs_listbox = Listbox (docs_frame, exportselection=False)
    docs_listbox.place(relwidth = 1, relheight = 1)
    
    def docs_select(event = 0):
        working_area.configure(state=NORMAL)
        
        item = docs_listbox.get(docs_listbox.curselection())
        global notes_to_upload
        notes_to_upload = {}#resetting everything 
        search_result = collection.find_one({"_id" : item})
        
        folders_list.delete(0, "end") #clear all
        working_area.delete('1.0', END)
        
        text_search.delete(0, "end")
        text_search.insert(0, item)
        
        text_for_label = "Patient " + item + " was found. Successfully connected..."
        found_label.config(text = text_for_label)
        if search_result != None:
            if "Notes" in search_result: notes_to_upload = search_result["Notes"]
        else: notes_to_upload = {}
        for i in notes_to_upload:folders_list.insert(0, i)
    
    docs_listbox.bind("<<ListboxSelect>>", docs_select)
    
    for i in database_docnames: docs_listbox.insert(0, i)
    
    ##################################################
    
    ################################################## Import
    
    ##################################################
    
    ################################################## Folders Browser
    
    lboxes_frame = Frame (notes_adder, bg = "#eaeaea")
    lboxes_frame.place(relx = 0.25, rely = 0.05, relwidth = 0.19, relheight = 0.86)
    folders_list = Listbox (lboxes_frame, exportselection=False)
    folders_list.place(relwidth = 1, relheight = 0.95)
    
    def select_folder(event = 0):
        item = folders_list.get(folders_list.curselection())
        working_area.delete('1.0', END)
        entry_rename.delete(0, END)
        entry_rename.insert(0, item)
        working_area.insert("1.0", notes_to_upload[item]) 
                
    def delete_folder (event = 0):
        item = folders_list.get(folders_list.curselection())
        folders_list.delete(0, "end")
        notes_to_upload.pop(item)
        for i in notes_to_upload: folders_list.insert(0, i)
        
        
    folders_list.bind("<<ListboxSelect>>", select_folder)
    
    lbox_select_button = Button(lboxes_frame, text = "Select", command = select_folder)
    lbox_select_button.place(relx = 0, relwidth = 0.5, rely = 0.95, relheight = 0.05)
    lbox_delete_button = Button(lboxes_frame, text = "Delete", command = delete_folder)
    lbox_delete_button.place(relx = 0.5, relwidth = 0.5, rely = 0.95, relheight = 0.05)
    
    ###
    def rename_folder():
        item = folders_list.get(folders_list.curselection())
        temp = notes_to_upload[item]
        notes_to_upload.pop(item)
        folders_list.delete(0, "end")
        notes_to_upload[entry_rename.get()] = temp
        for i in notes_to_upload: folders_list.insert(0, i)
    
    def add_folder():
        item = entry_rename.get()
        if item not in notes_to_upload:
            notes_to_upload[item] = ""
            folders_list.delete(0, "end")
            for i in notes_to_upload: folders_list.insert(0, i)
    
    rename_frame = Frame (notes_adder)
    rename_frame.place(relx = 0.25, rely = 0.92, relwidth = 0.19, relheight = 0.03)
    
    entry_rename = Entry (rename_frame)
    entry_rename.place (relwidth = 0.5, relheight = 1)
    
    button_rename = Button (rename_frame, text = "Rename", command = rename_folder)
    button_rename.place(relx = 0.5, relwidth = 0.25, relheight = 1)
    
    button_add = Button (rename_frame, text = "Add", command = add_folder)
    button_add.place(relx = 0.75, relwidth = 0.25, relheight = 1)
    
    
    
    ##################################################
    
    ################################################## Working Space
    
    working_area = Text(notes_adder)
    working_area.place(relx = 0.45, rely = 0.05, relwidth = 0.50, relheight = 0.65) 
    
    ##################################################
    
    ################################################## File and Database management 
    
    def save_draft():
        item = folders_list.get(folders_list.curselection())
        notes_to_upload[item] = working_area.get("1.0",'end-1c')
        
    
    save_draft_button = Button(notes_adder, command = save_draft, text = "Save Draft")
    save_draft_button.place(relx = 0.87, rely = 0.71, relwidth = 0.08, relheight = 0.03)
    
    def upload_notes ():
        upload_notes_push (collection, text_search.get(), notes_to_upload)
        uploading_label.config(text = text_search.get() + "Uploaded successfully")
        
    uploading_label = Label(notes_adder)
    uploading_label.place(relx = 0.80, rely = 0.78, relwidth = 0.15, relheight = 0.05)
    
    upload_button = Button(notes_adder, command = upload_notes, text = "Upload") 
    upload_button.place(relx = 0.87, rely = 0.74, relwidth = 0.08, relheight = 0.03)
    ##################################################
    working_area.configure(state="disable")
    
    
    my_img = ImageTk.PhotoImage(Image.open("assets\\plus.png")) 
    lbl = Button(notes_adder, image = my_img, relief='solid' , width = 0, borderwidth=0)
    lbl.place(relx = 0.5)


# In[63]:


root = Tk()
root.title('DATABASE BROWSER GUI v0.0')
root.geometry('1000x680')

root.iconbitmap('assets\\icon.ico')

menubar = Menu(root)
filemenu = Menu(menubar, tearoff=0)
filemenu.add_command(label="Add Dicom", command=open_dicom_adder)
filemenu.add_command(label="Add Behavioral", command=open_behavioral_adder)
filemenu.add_command(label="Add Notes", command=open_notes_adder)
filemenu.add_command(label="Save", command=donothing)
filemenu.add_separator()
filemenu.add_command(label="Exit", command=root.quit)
menubar.add_cascade(label="Add", menu=filemenu)

helpmenu = Menu(menubar, tearoff=0)
helpmenu.add_command(label="Help Index", command=donothing)
helpmenu.add_command(label="About...", command=donothing)
menubar.add_cascade(label="Help", menu=helpmenu)

##################################################### SEARCH FIELD

##################################################### MAIN TREEVIEW
table_frame = Frame(root)
table_frame.place(relx = 0.05, rely = 0.1, relwidth = 0.65, relheight = 0.65)

tree_columns = ("patient", "folders", "number")
tree_table = ttk.Treeview(table_frame, columns=tree_columns, selectmode='browse')

tree_table.place(relwidth = 1, relheight = 1)
tree_table['show'] = 'headings'

tree_table.heading("patient", text="Patient")
tree_table.heading("folders", text="Folders")
tree_table.heading("number", text="Number")

def update_tree():
    tree_table.delete(*tree_table.get_children())
    folders_list.delete(0, "end")
    database_doclist = []
    for document in collection.find({}): database_docnames.append(document["_id"]) #uploading the existing docs to the application
    linenumber = 0
    
    
    dict_to_upload[selected_folder][key_text.get("1.0","end-1c")] = value_text.get("1.0","end-1c")
    for i in dict_to_upload[selected_folder].keys(): 
            tree_table.insert("",'end',text="L1",values=(i,dict_to_upload[selected_folder][i]))


#####################################################

##################################################### FOLDERS LISTBOX

lboxes_frame = Frame (root, bg = "#eaeaea")
lboxes_frame.place(relx = 0.71, rely = 0.1, relwidth = 0.24, relheight = 0.65)
folders_list = Listbox (lboxes_frame, exportselection=False)
folders_list.place(relwidth = 1, relheight = 1)

root.config(menu=menubar)
root.mainloop()


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




