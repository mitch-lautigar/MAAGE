"""
Created on Wed Jul 23 17:40:40 2025
@author: mitch
"""

import os
import re
import string
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pandas as pd
import openpyxl

# === Excel Helpers ===

def getExcelSheetNames(filePath):
    """
    Return all sheet names from an Excel file.
    
    Args:
        filePath (str): Path to the Excel file.
    
    Returns:
        List[str]: List of sheet names, or empty list if file read fails.
    """
    try:
        xls = pd.ExcelFile(filePath)
        return xls.sheet_names
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return []


def getSectionLines(cheatSheetPath, tabName):
    """
    Extract the relevant section lines from cheat sheet text file for a given tab.
    
    Args:
        cheatSheetPath (str): Path to cheat sheet .txt file.
        tabName (str): Name of the tab to extract lines for.
    
    Returns:
        List[str]: Lines for the tab section, excluding the first 2 header lines.
    """
    with open(cheatSheetPath, "r") as f:
        lines = [line.strip() for line in f]

    sectionStart = None
    sectionEnd = None

    # Find the start index for the tab section
    for i, line in enumerate(lines):
        if line.lower().startswith(f"tabname,{tabName.lower()}"):
            sectionStart = i
            break

    if sectionStart is None:
        return []

    # Find the end index for the section (next blank line or EOF)
    for j in range(sectionStart + 1, len(lines)):
        if lines[j] == "":
            sectionEnd = j
            break
    if sectionEnd is None:
        sectionEnd = len(lines)

    # Return lines after the two-line header for this tab section
    return lines[sectionStart + 2 : sectionEnd]


def updateCheatSheetForTab(tabName, cheatSheetPath, tabEntries):
    """
    Update cheat sheet section for a specific tab with new dropdown selections.
    Overwrites the section in the cheat sheet file.
    
    Args:
        tabName (str): Tab to update.
        cheatSheetPath (str): Path to cheat sheet file.
        tabEntries (List[Dict]): List of entries with 'displayName' and 'selectedSheetVar'.
    
    Side Effects:
        Writes updated cheat sheet file in-place.
        Shows success or error messagebox.
    """
    try:
        with open(cheatSheetPath, "r") as f:
            lines = f.readlines()

        startIdx = None
        endIdx = None

        # Locate section start index for tab
        for i, line in enumerate(lines):
            if line.lower().startswith(f"tabname,{tabName.lower()}"):
                startIdx = i
                break

        if startIdx is None:
            messagebox.showerror("Error", f"Tab '{tabName}' not found in cheat sheet.")
            return

        # Locate section end index (next blank line)
        for j in range(startIdx + 1, len(lines)):
            if lines[j].strip() == "":
                endIdx = j
                break
        if endIdx is None:
            endIdx = len(lines)

        # Build new section lines: header + updated tab entries
        newSection = lines[startIdx : startIdx + 2]
        for entry in tabEntries:
            display = entry["displayName"]
            sheet = entry["selectedSheetVar"].get()
            newSection.append(f"{display},{sheet}\n")
        newSection.append("\n")

        # Replace old section with new content
        lines = lines[:startIdx] + newSection + lines[endIdx:]

        # Write updated cheat sheet back to file
        with open(cheatSheetPath, "w") as f:
            f.writelines(lines)

        messagebox.showinfo("Success", f"Cheat sheet updated for tab '{tabName}'.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to update cheat sheet:\n{e}")


def populateTabFromCheatSheet(tabFrame, excelFilePath, cheatSheetPath, tabName, showStartCols=False):
    """
    Populate a tkinter tab frame with dropdowns based on cheat sheet data,
    including optional Start Row and Columns inputs.
    
    Args:
        tabFrame (tk.Frame): UI frame to populate.
        excelFilePath (str): Path to Excel file to get sheet names.
        cheatSheetPath (str): Path to cheat sheet text file.
        tabName (str): Current tab name.
        showStartCols (bool): If True, display Start Row and Columns inputs.
    
    Side Effects:
        Populates tabFrame with widgets and stores references in tabFrame.entries.
    """
    sheetNames = getExcelSheetNames(excelFilePath)
    sectionLines = getSectionLines(cheatSheetPath, tabName)
    tabFrame.entries = []  # Store entry references for updating cheat sheet
    tabFrame.startColsWidgets = []  # Store widgets for toggling visibility

    for line in sectionLines:
        if not line.strip():
            continue
        parts = [p.strip() for p in line.split(",")]

        displayName = parts[0]
        sheetName = parts[1] if len(parts) > 1 else ""
        startRowVal = parts[2] if len(parts) > 2 else "1"
        columnsVal = parts[3] if len(parts) > 3 else "A:Z"

        rowFrame = ttk.Frame(tabFrame)
        rowFrame.pack(fill="x", pady=2, padx=10)

        # Label for the entry
        ttk.Label(rowFrame, text=displayName, width=25).pack(side="left")

        # Dropdown combobox for sheet selection
        defaultSheet = sheetNames[0] if sheetNames else ""
        selectedValue = sheetName if sheetName in sheetNames else defaultSheet
        selectedSheet = tk.StringVar(value=selectedValue)
        dropdown = ttk.Combobox(rowFrame, textvariable=selectedSheet,
                                values=sheetNames, state="readonly", width=30)
        dropdown.pack(side="left", padx=5)

        # Start Row widgets
        startRowLabel = ttk.Label(rowFrame, text="Starting Row:", width=12)
        startRowVar = tk.StringVar(value=startRowVal)
        startRowEntry = ttk.Entry(rowFrame, textvariable=startRowVar, width=8)

        # Columns widgets
        columnsLabel = ttk.Label(rowFrame, text="Columns:", width=10)
        columnsVar = tk.StringVar(value=columnsVal)
        columnsEntry = ttk.Entry(rowFrame, textvariable=columnsVar, width=10)

        # Show or hide Start Row and Columns widgets based on flag
        if showStartCols:
            startRowLabel.pack(side="left", padx=2)
            startRowEntry.pack(side="left", padx=2)
            columnsLabel.pack(side="left", padx=2)
            columnsEntry.pack(side="left", padx=2)

        # Save references for toggling visibility and saving data
        tabFrame.entries.append({
            "displayName": displayName,
            "selectedSheetVar": selectedSheet,
            "startRowVar": startRowVar,
            "columnsVar": columnsVar
        })

        tabFrame.startColsWidgets.append({
            "startRowLabel": startRowLabel,
            "startRowEntry": startRowEntry,
            "columnsLabel": columnsLabel,
            "columnsEntry": columnsEntry
        })

    # Add update button at bottom of tab
    updateButton = tk.Button(
        tabFrame,
        text="Update Cheat Sheet",
        command=lambda: updateCheatSheetForTab(tabName, cheatSheetPath, tabFrame.entries)
    )
    updateButton.pack(side="bottom", pady=10)


def toggleStartColsVisibility(tabControl, show):
    """
    Show or hide Start Row and Columns inputs on all non-home tabs.
    
    Args:
        tabControl (ttk.Notebook): Main tab control widget.
        show (bool): True to show inputs, False to hide.
    """
    # Skip first tab (assumed home)
    for idx in range(1, len(tabControl.tabs())):
        tabId = tabControl.tabs()[idx]
        tabFrame = tabControl.nametowidget(tabId)
        if hasattr(tabFrame, "startColsWidgets"):
            for widgets in tabFrame.startColsWidgets:
                if show:
                    widgets["startRowLabel"].pack(side="left", padx=2)
                    widgets["startRowEntry"].pack(side="left", padx=2)
                    widgets["columnsLabel"].pack(side="left", padx=2)
                    widgets["columnsEntry"].pack(side="left", padx=2)
                else:
                    widgets["startRowLabel"].pack_forget()
                    widgets["startRowEntry"].pack_forget()
                    widgets["columnsLabel"].pack_forget()
                    widgets["columnsEntry"].pack_forget()


# === Legacy Excel UI Helpers ===

def createTabRows(tabFrame, cheatSheetPath):
    """
    Legacy: Create rows in a tab from cheat sheet data.
    Reads from .xlsx file and associated .txt file.
    
    Args:
        tabFrame (tk.Frame): Container to populate.
        cheatSheetPath (str): Path to cheat sheet (.xlsx) file.
    
    Side Effects:
        Adds Entry and Combobox widgets to tabFrame.
    """
    if not os.path.exists(cheatSheetPath):
        return

    try:
        excelWorkbook = openpyxl.load_workbook(cheatSheetPath, read_only=True)
        allSheetNames = excelWorkbook.sheetnames
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    with open(cheatSheetPath.replace(".xlsx", ".txt"), "r") as f:
        lines = f.readlines()[2:]  # Skip header lines

    for line in lines:
        displayName, sheetName = [x.strip() for x in line.split(",")]
        rowFrame = ttk.Frame(tabFrame)
        rowFrame.pack(fill="x", padx=10, pady=4)

        displayEntry = ttk.Entry(rowFrame, width=40)
        displayEntry.insert(0, displayName)
        displayEntry.pack(side="left", padx=(0, 5))

        selectedSheet = tk.StringVar()
        selectedSheet.set(sheetName if sheetName in allSheetNames else allSheetNames[0])
        dropdown = ttk.Combobox(rowFrame, textvariable=selectedSheet,
                                values=allSheetNames, width=30, state="readonly")
        dropdown.pack(side="left")


# === Excel Column Utilities ===

def excelColToIndex(colStr):
    """
    Convert Excel column letter(s) to zero-based index.
    
    Args:
        colStr (str): Excel column string (e.g., 'A', 'Z', 'AA').
    
    Returns:
        int: Zero-based column index.
    """
    colStr = colStr.upper()
    colIndex = 0
    exp = 0
    for char in reversed(colStr):
        colIndex += (ord(char) - ord('A') + 1) * (26 ** exp)
        exp += 1
    return colIndex - 1  # zero-based


def colRangeToIndices(rangeStr):
    """
    Convert Excel column range (e.g. 'A:Z', 'A:AA') to list of zero-based indices.
    
    Args:
        rangeStr (str): Excel column range string.
    
    Returns:
        List[int]: List of column indices.
    
    Raises:
        ValueError: If the range is invalid.
    """
    parts = rangeStr.split(":")
    if len(parts) != 2:
        # No colon, single column only
        startIdx = excelColToIndex(rangeStr)
        return [startIdx]

    startCol, endCol = parts
    startIdx = excelColToIndex(startCol)
    endIdx = excelColToIndex(endCol)

    if endIdx < startIdx:
        raise ValueError(f"Invalid column range: {rangeStr}")

    return list(range(startIdx, endIdx + 1))


# === File and Path Utilities ===

def parseCheatSheet(filePath):
    """
    Parse cheat sheet text file into list of tab definitions.
    
    Args:
        filePath (str): Path to cheat sheet text file.
    
    Returns:
        List[Dict]: List of tabs with keys:
            - 'name' (str): Tab name
            - 'filepath' (str): Filepath
            - 'entries' (List[Dict]): Entries with displayName, sheetName, startRow, columns
    """
    tabs = []
    try:
        with open(filePath, "r") as file:
            lines = [line.strip() for line in file]

        i = 0
        while i < len(lines):
            if lines[i].startswith("TabName"):
                tabName = lines[i].split(",", 1)[1].strip()
                filePathLine = lines[i + 1].split(",", 1)[1].strip()

                tabEntries = []
                i += 2
                while i < len(lines) and lines[i].strip() != "":
                    parts = [p.strip() for p in lines[i].split(",")]
                    if len(parts) >= 2:
                        displayName = parts[0]
                        sheetName = parts[1]
                        startRow = parts[2] if len(parts) > 2 else ""
                        columns = parts[3] if len(parts) > 3 else ""
                        tabEntries.append({
                            "displayName": displayName,
                            "sheetName": sheetName,
                            "startRow": startRow,
                            "columns": columns
                        })
                    i += 1

                tabs.append({
                    "name": tabName,
                    "filepath": filePathLine,
                    "entries": tabEntries
                })
            else:
                i += 1
    except Exception as e:
        print(f"Error reading cheat sheet: {e}")

    return tabs


def checkFileStatus(path):
    """
    Check if a file exists at the given path.
    
    Args:
        path (str): File path.
    
    Returns:
        bool: True if file exists, False otherwise.
    """
    return os.path.isfile(path)


def updateStatusLabel(entryVar, statusLabel):
    """
    Update a status label to indicate if the file path is valid.
    
    Args:
        entryVar (tk.StringVar): Entry variable holding file path.
        statusLabel (tk.Label): Label widget to update.
    """
    path = entryVar.get()
    exists = checkFileStatus(path)
    statusLabel.config(text="✅" if exists else "❌", fg="green" if exists else "red")


def browseFile(entryVar, statusLabel, showFullPath):
    """
    Open a file dialog to select a file and update entry and status label.
    
    Args:
        entryVar (tk.StringVar): Entry variable to update.
        statusLabel (tk.Label): Status indicator label.
        showFullPath (tk.BooleanVar): Whether to show full or base filename.
    """
    filename = filedialog.askopenfilename()
    if filename:
        entryVar.set(filename if showFullPath.get() else os.path.basename(filename))
        updateStatusLabel(entryVar, statusLabel)


def toggleDisplayMode(homeRows, showFullPath):
    """
    Toggle display between full and base filenames in a list of rows.
    
    Args:
        homeRows (List[Dict]): Each dict contains 'full_path', 'entry_var', 'status_label'.
        showFullPath (tk.BooleanVar): True to show full path, False for basename.
    """
    for row in homeRows:
        fullPath = row["full_path"]
        entryVar = row["entry_var"]
        statusLabel = row["status_label"]

        entryVar.set(fullPath if showFullPath.get() else os.path.basename(fullPath))
        updateStatusLabel(entryVar, statusLabel)


def updateCheatsheetStatus(cheatsheetPathVar, cheatsheetStatus):
    """
    Update status label for cheat sheet file existence.
    
    Args:
        cheatsheetPathVar (tk.StringVar): Cheat sheet file path variable.
        cheatsheetStatus (tk.Label): Label widget to update.
    """
    path = cheatsheetPathVar.get()
    exists = os.path.isfile(path)
    cheatsheetStatus.config(text="✅" if exists else "❌", fg="green" if exists else "red")


def changeCheatsheetFile(cheatsheetPathVar, cheatsheetStatus, showFullPath, cheatSheetPathContainer, tabDataContainer):
    """
    Open file dialog to select new cheat sheet file and reload tab data.
    
    Args:
        cheatsheetPathVar (tk.StringVar): Path display variable.
        cheatsheetStatus (tk.Label): Status label.
        showFullPath (tk.BooleanVar): Whether to show full path.
        cheatSheetPathContainer (List[str]): Mutable container holding cheat sheet path.
        tabDataContainer (List): Mutable container for parsed tab data.
    
    Side Effects:
        Updates cheat sheet path and tab data containers.
        Shows info message to restart app for changes.
    """
    filename = filedialog.askopenfilename(title="Select Cheat Sheet File")
    if filename:
        cheatSheetPathContainer[0] = filename
        cheatsheetPathVar.set(filename if showFullPath.get() else os.path.basename(filename))
        updateCheatsheetStatus(cheatsheetPathVar, cheatsheetStatus)

        tabDataContainer.clear()
        tabDataContainer.extend(parseCheatSheet(cheatSheetPathContainer[0]))

        messagebox.showinfo("Cheat Sheet Changed",
                            f"Cheat Sheet file changed to:\n{filename}\n\nRestart app to reload tabs.")


def toggleCheatsheetRow(cheatsheetFrame, showCheatsheetPath, cheatsheetPathVar, showFullPath, cheatSheetPath, togglesLabel2):
    """
    Show or hide the cheat sheet path display row.
    
    Args:
        cheatsheetFrame (tk.Frame): Frame containing cheat sheet path display.
        showCheatsheetPath (tk.BooleanVar): Whether to show or hide the row.
        cheatsheetPathVar (tk.StringVar): Cheat sheet path variable.
        showFullPath (tk.BooleanVar): Whether to show full path or basename.
        cheatSheetPath (str): Current cheat sheet full path.
        togglesLabel2 (tk.Widget): Anchor widget for packing order.
    """
    if showCheatsheetPath.get():
        cheatsheetFrame.pack(fill="x", pady=5, padx=10, before=togglesLabel2)
    else:
        cheatsheetFrame.pack_forget()

    cheatsheetPathVar.set(cheatSheetPath if showFullPath.get() else os.path.basename(cheatSheetPath))


def saveInputsToCheatsheet(tabsData, cheatSheetPath):
    """
    Save current tab data, including startRow and columns, back to cheat sheet file.
    
    Args:
        tabsData (List[Dict]): Tabs data with 'name', 'filepath', 'entries' (with keys displayName, sheetName, startRow, columns).
        cheatSheetPath (str): File path to cheat sheet.
    
    Side Effects:
        Writes the updated cheat sheet file.
        Shows error messagebox on failure.
    """
    try:
        with open(cheatSheetPath, "w") as file:
            for tab in tabsData:
                file.write(f"TabName,{tab['name']}\n")
                file.write(f"Filepath,{tab['filepath']}\n")
                
                for entry in tab.get("entries", []):
                    display = entry.get("displayName", "")
                    sheet = entry.get("sheetName", "")
                    startRow = entry.get("startRow", "")
                    columns = entry.get("columns", "")
                    if startRow or columns:
                        file.write(f"{display},{sheet},{startRow},{columns}\n")
                    else:
                        file.write(f"{display},{sheet}\n")
                
                file.write("\n")
        print(f"Inputs saved to {cheatSheetPath}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save inputs: {e}")


def loadCheatSheetSegment(cheatSheetPath, startRow, colRange):
    """
    Load a segment of data from cheat sheet file starting at a specific row
    and restricted to specified columns. Appends new columns if needed.
    
    Args:
        cheatSheetPath (str): Path to cheat sheet text file.
        startRow (int): Zero-based row to start reading.
        colRange (str): Excel column range string (e.g., 'A:D').
    
    Returns:
        List[List[str]]: List of lists representing the selected columns per line.
    """
    def _colRangeToIndices(rangeStr):
        letters = list(string.ascii_uppercase)
        start, end = rangeStr.split(":")
        startIdx = letters.index(start.upper())
        endIdx = letters.index(end.upper())
        return list(range(startIdx, endIdx + 1))

    colIndices = _colRangeToIndices(colRange)

    with open(cheatSheetPath, "r") as f:
        lines = [line.strip() for line in f if line.strip()]

    data = []
    modified = False
    for i, line in enumerate(lines[startRow:], start=startRow):
        parts = [p.strip() for p in line.split(",")]

        # Append new columns if needed
        if len(parts) <= max(colIndices):
            needed = max(colIndices) + 1 - len(parts)
            parts += [f"NewCol{j+1}" for j in range(needed)]
            lines[i] = ",".join(parts)
            modified = True

        selected = [parts[idx] for idx in colIndices]
        data.append(selected)

    if modified:
        with open(cheatSheetPath, "w") as f:
            f.write("\n".join(lines) + "\n")

    return data
#Mexico
def buildWorkspaceSnapshot(tabControl):
    workspace = {}

    for idx in range(len(tabControl.tabs())):
        tabId = tabControl.tabs()[idx]
        tabFrame = tabControl.nametowidget(tabId)
        tabName = tabControl.tab(tabId, "text")

        tabData = {}

        if hasattr(tabFrame, "useForAdjVar"):
            tabData["use_for_adjudication"] = tabFrame.useForAdjVar.get()

        if hasattr(tabFrame, "entries"):
            tabData["entries"] = []
            for entry in tabFrame.entries:
                tabData["entries"].append({
                    "displayName": entry["displayName"],
                    "sheet": entry["selectedSheetVar"].get(),
                    "startRow": entry["startRowVar"].get(),
                    "columns": entry["columnsVar"].get()
                })

        workspace[tabName] = tabData

    return workspace
#End Mexico
def incrementAllMoveNumbers(cheatSheetPath):
    """
    Increment all occurrences of 'Move N' to 'Move N+1' in the cheat sheet text file.

    Args:
        cheatSheetPath (str): Path to the cheat sheet file.

    Side Effects:
        Updates the cheat sheet file in place.
    """
    # Read original content
    with open(cheatSheetPath, "r") as f:
        content = f.read()

    # Regex to find 'Move ' followed by a number
    def increment_match(match):
        num = int(match.group(1))
        return f"Move {num + 1}"

    # Replace all occurrences of Move N with Move N+1
    new_content = re.sub(r"Move (\d+)", increment_match, content)

    # Write updated content safely
    dir_name = os.path.dirname(cheatSheetPath)
    with tempfile.NamedTemporaryFile("w", dir=dir_name, delete=False) as tmp_file:
        tmp_file.write(new_content)
        temp_name = tmp_file.name

    os.replace(temp_name, cheatSheetPath)


def buildFilenamesDictFromTabs(tabControl):
    """
    Build a nested dictionary mapping tab names to sheet names and
    corresponding start row and column indices from UI tab control.
    
    Args:
        tabControl (ttk.Notebook): Tab control widget containing tabs.
    
    Returns:
        Dict[str, Dict[str, Tuple[int, List[int]]]]:
            Outer dict keyed by tab name.
            Inner dict keyed by sheet name with tuple of (startRow, colIndices).
    """
    filenames = {}

    # Skip first tab (assumed home)
    for idx in range(1, len(tabControl.tabs())):
        tabId = tabControl.tabs()[idx]
        tabFrame = tabControl.nametowidget(tabId)
        tabName = tabControl.tab(tabId, "text")
        #mexico
        if hasattr(tabFrame, "useForAdjVar") and not tabFrame.useForAdjVar.get():
            continue
        #end mexico
        filenames[tabName] = {}

        # tabFrame.entries is list of dicts with sheetVar, startRowVar, columnsVar
        if hasattr(tabFrame, "entries"):
            for entry in tabFrame.entries:
                sheetName = entry["selectedSheetVar"].get()
                startRowStr = entry["startRowVar"].get()
                columnsStr = entry["columnsVar"].get()

                # Parse start row (default to 0)
                startRow = int(startRowStr) - 1 if startRowStr.strip().isdigit() else 0

                # Parse columns string to indices
                try:
                    colIndices = colRangeToIndices(columnsStr) if columnsStr else list(range(26))
                except Exception:
                    colIndices = list(range(26))

                filenames[tabName][sheetName] = (startRow, colIndices)

    return filenames
