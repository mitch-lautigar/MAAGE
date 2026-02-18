import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import gc

import MDW25GuiHeader as gui  # Custom header file with helper functions

# ----------------------------
# Main GUI Initialization
# ----------------------------
DEV_MODE = True  # Mexico - Enable detailed debug/info output
root = tk.Tk()
root.title("MAAGE -- Maritime/Aviation Adjudication for Games/Exercises")
root.geometry("1400x900")
root.configure(bg="black")

# ----------------------------
# Tab Styling Configuration
# ----------------------------
style = ttk.Style()
style.theme_use('default')
style.configure(
    'TNotebook.Tab',
    background='Grey',
    foreground='Black',
    font=('Arial', 14),
    padding=[12, 8]
)

# ----------------------------
# Frame Setup for Left and Right Sections
# ----------------------------
leftFrame = tk.Frame(root, width=300, bg="black")
leftFrame.pack(side="left", fill="y")

rightFrame = tk.Frame(root, bg="black")
rightFrame.pack(side="right", expand=True, fill="both")

# ----------------------------
# Load Banner Image (if found)
# ----------------------------
try:
    bannerImage = Image.open(r"C:/Users/mitch.lautigar/Documents/Wargame Code/Banner1.jpg")
    bannerPhoto = ImageTk.PhotoImage(bannerImage)

    bannerLabel = tk.Label(leftFrame, image=bannerPhoto, bg="black")
    bannerLabel.image = bannerPhoto
    bannerLabel.pack(pady=10)
except Exception as e:
    tk.Label(leftFrame, text="Banner image not found.", bg="black", fg="red").pack(pady=10)
    print("Error loading image:", e)

# ----------------------------
# Load Cheatsheet and Tab Data
# ----------------------------
cheatSheetPathContainer = ["MAAGECheatSheet.txt"]  # Mutable container for cheat sheet filepath
tabData = gui.parseCheatSheet(cheatSheetPathContainer[0])

# ----------------------------
# Create Notebook Tabs container
# ----------------------------
tabControl = ttk.Notebook(rightFrame)
tabControl.pack(expand=True, fill="both")

# ----------------------------
# Build Home Tab with Filepath Entries
# ----------------------------
homeTab = tk.Frame(tabControl, bg="black")
homeTab.pack_propagate(False)
tabControl.add(homeTab, text="Home")

homeRows = []  # List to store filepath entry widgets and related controls on Home tab
showFullPath = tk.BooleanVar(value=True)  # Control variable for showing full file paths or just filenames

# --- Filepath section header ---
togglesFrame = tk.Frame(homeTab, bg="black")
togglesFrame.pack(fill="x", pady=5, padx=10)

togglesLabel = tk.Label(
    togglesFrame,
    text="Filepaths:",
    font=("Arial", 14, "bold", "underline"),
    bg="black",
    fg="white",
    anchor="w"
)
togglesLabel.pack(anchor="w")

# --- Add one row per tab’s filepath (except 'Home') ---
for tab in tabData:
    if tab["name"].lower() == "home":
        continue

    # Container frame for each row on home tab showing resource filepath
    frame = tk.Frame(togglesFrame, bg="black")
    frame.pack(fill="x", pady=2, padx=10)

    label = tk.Label(
        frame,
        text=f"{tab['name']} resources:",
        bg="black",
        fg="white",
        width=20,
        anchor="w"
    )
    label.pack(side="left")

    entryVar = tk.StringVar()
    fullPath = tab["filepath"]
    displayPath = fullPath if showFullPath.get() else os.path.basename(fullPath)
    entryVar.set(displayPath)

    entry = tk.Entry(frame, textvariable=entryVar, width=60)
    entry.pack(side="left", padx=5)

    browseBtn = tk.Button(frame, text="Browse")
    browseBtn.pack(side="left", padx=5)

    statusLabel = tk.Label(frame, text="", bg="black", fg="white", width=2)
    statusLabel.pack(side="left", padx=5)

    gui.updateStatusLabel(entryVar, statusLabel)

    homeRows.append({
        "name": tab['name'],
        "full_path": fullPath,
        "entry_var": entryVar,
        "status_label": statusLabel,
        "browse_btn": browseBtn
    })

    # Per-tab boolean controlling visibility of start row/columns inputs
    showStartColsVar = tk.BooleanVar(value=False)

    # Create a new tab frame for each tabData entry (non-home)
    tabFrame = tk.Frame(tabControl, bg="black", width=1100, height=800)
    tabFrame.pack_propagate(False)
    tabControl.add(tabFrame, text=tab["name"])

    # --- Task 1: Adjudication toggle checkbox on each tab (non-Home) ---
    useForAdjVar = tk.BooleanVar(value=True)
    tabFrame.useForAdjVar = useForAdjVar  # Attach variable to tab frame for later access

    adjFrame = tk.Frame(tabFrame, bg="black")
    adjFrame.pack(fill="x", padx=10, pady=(5, 10), anchor="w")

    tk.Checkbutton(
        adjFrame,
        text="Use data in this tab for adjudication",
        variable=useForAdjVar,
        bg="black",
        fg="white",
        selectcolor="black"
    ).pack(anchor="w")

    # Populate the tab from cheat sheet (your helper function)
    gui.populateTabFromCheatSheet(
        tabFrame,
        tab["filepath"],
        cheatSheetPathContainer[0],
        tab["name"],
        showStartColsVar.get()
    )

# --- Attach browse button commands to each home tab filepath row ---
for row in homeRows:
    row["browse_btn"].config(
        command=lambda ev=row["entry_var"], sl=row["status_label"]: gui.browseFile(ev, sl, showFullPath)
    )

# ----------------------------
# Cheatsheet Path Display (Initially Hidden)
# ----------------------------
cheatsheetFrame = tk.Frame(homeTab, bg="black")
cheatsheetFrame.pack_forget()  # Hidden by default

cheatsheetLabel = tk.Label(
    cheatsheetFrame,
    text="Cheat Sheet File:",
    bg="black",
    fg="white",
    width=20,
    anchor="w"
)
cheatsheetLabel.pack(side="left")

cheatsheetPathVar = tk.StringVar()
displayCheatsheetPath = cheatSheetPathContainer[0] if showFullPath.get() else os.path.basename(cheatSheetPathContainer[0])
cheatsheetPathVar.set(displayCheatsheetPath)

cheatsheetEntry = tk.Entry(cheatsheetFrame, textvariable=cheatsheetPathVar, width=60)
cheatsheetEntry.pack(side="left", padx=5)

cheatsheetStatus = tk.Label(cheatsheetFrame, text="", bg="black", fg="white", width=2)
cheatsheetStatus.pack(side="left", padx=5)

cheatsheetChangeBtn = tk.Button(
    cheatsheetFrame,
    text="Browse",
    command=lambda: gui.changeCheatsheetFile(
        cheatsheetPathVar,
        cheatsheetStatus,
        showFullPath,
        cheatSheetPathContainer,
        tabData
    )
)
cheatsheetChangeBtn.pack(side="left", padx=10)

gui.updateCheatsheetStatus(cheatsheetPathVar, cheatsheetStatus)

# ----------------------------
# Checkbox Toggles Section on Home Tab
# ----------------------------
togglesFrame2 = tk.Frame(homeTab, bg="black")
togglesFrame2.pack(fill="x", pady=5, padx=10)

togglesLabel2 = tk.Label(
    togglesFrame2,
    text="MAAGE Toggles:",
    font=("Arial", 14, "bold", "underline"),
    bg="black",
    fg="white",
    anchor="w"
)
togglesLabel2.pack(anchor="w")

checkboxFrame = tk.Frame(homeTab, bg="black")
checkboxFrame.pack(fill="x", pady=10, padx=10)

# Checkbox to toggle display of full filepaths or just filenames
checkbox = tk.Checkbutton(
    checkboxFrame,
    text="Show full filepaths",
    variable=showFullPath,
    bg="black",
    fg="white",
    selectcolor="black",
    command=lambda: (
        gui.toggleDisplayMode(homeRows, showFullPath),
        gui.toggleCheatsheetRow(
            cheatsheetFrame,
            showCheatsheetPath,
            cheatsheetPathVar,
            showFullPath,
            cheatSheetPathContainer[0],
            togglesFrame2
        )
    )
)
checkbox.pack(anchor="w")

# Checkbox to toggle display of cheat sheet path
showCheatsheetPath = tk.BooleanVar(value=False)
cheatsheetCheckbox = tk.Checkbutton(
    checkboxFrame,
    text="Show Cheat Sheet Path",
    variable=showCheatsheetPath,
    bg="black",
    fg="white",
    selectcolor="black",
    command=lambda: gui.toggleCheatsheetRow(
        cheatsheetFrame,
        showCheatsheetPath,
        cheatsheetPathVar,
        showFullPath,
        cheatSheetPathContainer[0],
        togglesFrame2
    )
)
cheatsheetCheckbox.pack(anchor="w")

# --- Task 2: Checkbox to enable incrementing "Move #" on run ---
incrementMoveVar = tk.BooleanVar(value=True)
tk.Checkbutton(
    checkboxFrame,
    text="Increment Move # on Run",
    variable=incrementMoveVar,
    bg="black",
    fg="white",
    selectcolor="black"
).pack(anchor="w")

# ----------------------------
# Starting Row and Columns Toggle on Home Tab
# ----------------------------
def onToggleStartCols():
    if showStartColsVar.get():
        if not messagebox.askokcancel(
            "Warning",
            "Changing Starting Row and Column Range inputs affects how data is read.\n"
            "Are you sure you want to enable these inputs?"
        ):
            showStartColsVar.set(False)
            return
    gui.toggleStartColsVisibility(tabControl, showStartColsVar.get())

startColsCheckbox = tk.Checkbutton(
    checkboxFrame,
    text="Show Starting Row and Columns",
    variable=showStartColsVar,
    bg="black",
    fg="white",
    selectcolor="black",
    command=onToggleStartCols
)
startColsCheckbox.pack(anchor="w")

# ----------------------------
# Run Button Setup with logic for DEV_MODE, adjudication flags, and incrementing move numbers
# ----------------------------
def runCode():
    global filenames
    filenames = gui.buildFilenamesDictFromTabs(tabControl)
    
    if incrementMoveVar.get():
        filenames["_postprocess"] = "increment_move"
    
    # If DEV_MODE enabled, print workspace snapshot for debugging
    if DEV_MODE:
        workspace = gui.buildWorkspaceSnapshot(tabControl)
        from pprint import pprint
        pprint(workspace)
    
    # Collect adjudication flags from all non-home tabs' checkboxes
    adjudicationFlags = []
    for idx in range(1, len(tabControl.tabs())):  # skip Home tab at index 0
        tabId = tabControl.tabs()[idx]
        tabFrame = tabControl.nametowidget(tabId)
        adjudicationFlags.append(1 if tabFrame.useForAdjVar.get() else 0)

    print("Adjudication flags:", adjudicationFlags)

    root.quit()
    root.destroy()

    # Call incrementAllMoveNumbers to update the cheat sheet file if needed
    if filenames.get("_postprocess") == "increment_move":
        outputText = gui.incrementAllMoveNumbers("MAAGECheatSheet.txt")

runBtnFrame = tk.Frame(homeTab, bg="black")
runBtnFrame.pack(side="bottom", fill="x", pady=10, padx=10)

runBtn = tk.Button(
    runBtnFrame,
    text="Run",
    font=("Arial", 14, "bold"),
    bg="green",
    fg="white",
    command=runCode
)
runBtn.pack(fill="x")

# ----------------------------
# Initial Display Setup for toggling cheatsheet visibility
# ----------------------------
gui.toggleCheatsheetRow(
    cheatsheetFrame,
    showCheatsheetPath,
    cheatsheetPathVar,
    showFullPath,
    cheatSheetPathContainer[0],
    togglesFrame2
)

# ----------------------------
# Start GUI Event Loop
# ----------------------------
root.mainloop()
