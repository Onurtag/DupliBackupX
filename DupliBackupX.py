import subprocess, sys, time, threading, json, webbrowser
import atexit
import argparse
from datetime import datetime
from termcolor import colored
from consolemenu import *
from consolemenu.format import *
from consolemenu.items import *

## -------- DupliBackupX --------
## https://github.com/Onurtag/DupliBackupX
##
## 📑 The main purpose of DupliBackupX is to be able to quickly create and remove a portable backup set.
##
## The destination folder will include everything that was used in the backup:
## - Files that are backed-up
## - Duplicati server database, duplicati backup database
## - Backups that were restored using the menu
## - Generated json file (if Backup Config is used)
## When they are no longer needed, you can just delete the destination folder to quickly get rid of everything.
##
## For configuration, you can either use the below Backup Config or just import a duplicati .json file.
## ⭐ You can import a json file using the commandline argument --jsonfile
##      For example > python DupliBackupX --jsonfile="D:\MyBackup.json"
##
##  When using the Backup Config, the base file will be DupliBackupX_BASE.json. The Backup Config values will be added onto that.
##
##
## 👟 Used applications:
## - duplicati 2 (https://github.com/duplicati/duplicati)
## - duplicati-client (https://github.com/Pectojin/duplicati-client)
##
## 📚 Used pip libraries:
## - termcolor (https://pypi.org/project/termcolor/)
## - consolemenu (consolemenu was modified to prevent it from clearing the screen: https://github.com/Onurtag/console-menu)
##

# TODO maybe add application config commandline.

########################
#######  Config  #######
########################

# ---------- 👟 Application config -------
# Backup timer (seconds)
backupTimer = 60
# Duplicati 2 and Duplicati_client folders. These could be empty if they are on your PATH variables
duplicatiLocation = "C:\\Program Files\\Duplicati 2\\"
duplicaticlientLocation = "C:\\DATA\\Portables\\duplicati_client\\"
# Duplicati server port.
servicePort = "8304"

# Only import json. Enter a json file path to ignore the backup config and just import the json file.
# You can use the commandline argument --jsonfile to set this
# Leave it empty to use the below Backup Config
#
# onlyImportJson = "D:\\MyBackup.json"
onlyImportJson = ""

# -------------------------------------

# ----------- 📦 Backup Config -----------
# ❗ Backup config is not used if you are using onlyImportJson (or the --jsonfile commandline)

# Backup name and destination
backupName = "MyBackup" + "_DupliBackupX"
# By default backupDestination is a folder named backupName under C:\Backups
backupDestination = "C:\\Backups\\" + backupName

# The first source is opened when the "Open Source Folder" menu is selected.
#
# The r prefix allows us to use single backslashes which makes copy-paste quicker.
# Because of that, backup sources can't end in backslash (\).
#
## Examples:
# backupSources = [
#     r"C:\Folder\SubFolder",
#     r"C:\Folder\File.txt",
# ]
backupSources = [
    r"C:\Folder\SubFolder",
    r"C:\Folder\File.txt",
]

# -------------------------------------

########################
########################
########################

backupConfig = {}
theInterval = None
serverProc = None
backupDBPath = ""


def main():
    if onlyImportJson != "":
        importJsonValues()

    createPrintConfig()
    print(colored("\n--------DupliBackupX--------", 'cyan'))
    global serverProc
    serverProc = startServer(backupDestination + "\\DupliBackupX\\")

    if checkBackup() != 0:
        print("Backup does not exist. Importing json...")
        if onlyImportJson == "":
            GenerateJson()
        importBackup()
        # Check again to get the DB path
        checkBackup()
    else:
        print("Backup exists.")
        if onlyImportJson != "":
            print("Updating backup...")
            updateBackup()
            checkBackup()
        else:
            if GenerateJson() != 0:
                print("Updating backup...")
                updateBackup()
                checkBackup()
            else:
                print("No need to update the backup.")

    print("Running first backup...")
    runBackup()
    startScheduler()
    showMenu()
    # Exit the app when the menu exits.
    print("Exiting...")
    stopScheduler()
    sys.exit()


def showMenu():
    menu = ConsoleMenu("DupliBackupX",
                       "Select an option",
                       clear_screen=False,
                       formatter=MenuFormatBuilder().set_title_align('center').set_subtitle_align('center').set_border_style_type(
                           MenuBorderStyleType.HEAVY_BORDER).show_prologue_top_border(True).show_prologue_bottom_border(True))

    menuItems = [
        FunctionItem("Show Backup Info", showBackupInfo),
        FunctionItem("Open DupliBackupX server in browser", openInBrowser),
        FunctionItem("Open Source Folder", openSourceFolder),
        FunctionItem("Open Destination Folder", openDestinationFolder),
        FunctionItem("List Backups", listBackups),
        FunctionItem("Compare Backups", compareBackups),
        FunctionItem("Restore a Backup", restoreBackup),
        FunctionItem("Perform a Backup Now", runBackup),
    ]
    for k in menuItems:
        menu.append_item(k)

    menu.show()
    return


def createPrintConfig():
    #Create displayNames (probably useless)
    displayNames = {}
    for value in backupSources:
        split = value.split("\\")
        #iterate to find the last non-empty split value
        dispName = next(i for i in reversed(split) if i)
        displayNames[value] = dispName

    # Generate dictionary from above values
    # Same data format as the json so we can use .update()
    # DBPath sadly does not work.
    global backupConfig
    backupConfig = {
        "Schedule": None,
        "Backup": {
            "Name": backupName,
            "TargetURL": "file://" + backupDestination,
            "DBPath": backupDestination + "\\DupliBackupX\\" + backupName + ".sqlite",
            "Sources": backupSources,
        },
        "DisplayNames": displayNames
    }
    print(colored("\n--------Configuration--------", 'cyan'))
    if onlyImportJson != "":
        print(colored(onlyImportJson, 'green'))
        print()
    print(colored(json.dumps(backupConfig, indent=4), 'green'))
    return


def importBackup():
    # lets not bother with importing duplicati_client as a library because we don't need any advanced functionality.
    # Using the executable.
    jsonfile = backupDestination + "\\DupliBackupX\\" + backupName + ".json"
    if onlyImportJson != "":
        jsonfile = onlyImportJson
    callArgs = [duplicaticlientLocation + "duplicati_client", "create", "backup", jsonfile]
    subprocess.run(callArgs)
    return


def updateBackup():
    jsonfile = backupDestination + "\\DupliBackupX\\" + backupName + ".json"
    if onlyImportJson != "":
        jsonfile = onlyImportJson
    callArgs = [duplicaticlientLocation + "duplicati_client", "update", "backup", "1", jsonfile]
    subprocess.run(callArgs)
    return


# Returns 2 if the backup doesn't exist, 0 if it exists
def checkBackup():
    print("Checking for backup...")
    callArgs = [duplicaticlientLocation + "duplicati_client", "get", "backup", "1"]
    checkresult = subprocess.run(callArgs, capture_output=True, text=True)
    #print(checkresult.stdout)
    #print(checkresult.stderr)
    split1 = checkresult.stdout.split("database: ")
    global backupDBPath
    if checkresult.returncode == 0:
        backupDBPath = split1[1].split("\n")[0]
    return checkresult.returncode


def showBackupInfo():
    # Returns 2 if backup doesnt exist, 0 if it exists
    callArgs = [duplicaticlientLocation + "duplicati_client", "get", "backup", "1"]
    subprocess.run(callArgs)


def listBackups():
    callArgs = [
        duplicatiLocation + "duplicati.commandline", "list", backupDestination, "--dbpath=" + backupDBPath, "--encryption-module=", "--compression-module=zip",
        "--no-encryption=true"
    ]
    subprocess.run(callArgs)


def startScheduler():
    #Start the backup scheduler
    print("Starting the backup scheduler...")
    global theInterval
    theInterval = setInterval(backupTimer, runBackup)
    return


def stopScheduler():
    #Stop the backup scheduler
    print("Stopping the backup scheduler...")
    global theInterval
    theInterval.cancel()
    #timer = threading.Timer(60, theInterval.cancel)
    #timer.start()
    return


def openSourceFolder():
    callArgs = ["explorer", backupSources[0]]
    subprocess.run(callArgs)


def openInBrowser():
    webbrowser.open("http://localhost:" + servicePort)


def openDestinationFolder():
    callArgs = ["explorer", backupDestination]
    subprocess.run(callArgs)


def compareBackups():
    compareVer1 = input("Enter first version number to compare: ")
    compareVer2 = input("Enter second version number to compare: ")
    callArgs = [
        duplicatiLocation + "duplicati.commandline", "compare", backupDestination, "--dbpath=" + backupDBPath, "--encryption-module=",
        "--compression-module=zip", "--no-encryption=true", compareVer1, compareVer2
    ]
    subprocess.run(callArgs)
    #input("\nEnter anything to return to the menu...")


def restoreBackup():
    restoreVersion = input("Enter the version number to restore: ")
    callArgs = [
        duplicatiLocation + "duplicati.commandline", "restore", backupDestination, "--dbpath=" + backupDBPath, "--encryption-module=",
        "--compression-module=zip", "--no-encryption=true",
        "--restore-path=" + backupDestination + "\\Restored_" + datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + restoreVersion, "--version=" + restoreVersion
    ]
    subprocess.run(callArgs)
    #input("\nEnter anything to return to the menu...")


def runBackup():
    #print("Running backup...")
    callArgs = [duplicaticlientLocation + "duplicati_client", "run", "1"]
    runresult = subprocess.run(callArgs, capture_output=True, text=True)
    return


# Returns 1 if the file was updated.
def GenerateJson():
    filename = "DupliBackupX_BASE.json"
    with open(filename, "r") as basefile:
        basedata = json.load(basefile)

    currentdata = None
    try:
        filename = backupDestination + "\\DupliBackupX\\" + backupName + ".json"
        with open(filename, "r") as basefile:
            currentdata = json.load(basefile)
    except:
        pass

    # Update the subkeys
    # This way we can keep the default values like Backup.ID and Backup.Settings instead of overwriting ["Backup"] and deleting them
    basedata["Backup"].update(backupConfig["Backup"])
    basedata["DisplayNames"].update(backupConfig["DisplayNames"])
    basedata["Schedule"] = backupConfig["Schedule"]

    if currentdata == basedata:
        return 0

    newfile = backupDestination + "\\DupliBackupX\\" + backupName + ".json"
    with open(newfile, "w") as nfile:
        json.dump(basedata, nfile, indent=2)

    return 1


# Returns 1 if the file was updated.
def importJsonValues():
    filename = onlyImportJson
    with open(filename, "r") as basefile:
        basedata = json.load(basefile)

    global backupName, backupDestination, backupSources
    backupName = basedata["Backup"]["Name"]
    backupDestination = basedata["Backup"]["TargetURL"].split("file://")[1]
    backupSources = basedata["Backup"]["Sources"]

    return


def startServer(serverdatafolder):
    #Duplicati.Server --webservice-port=8304 --server-datafolder=D:\DUMMY\DupliBackupX
    print("Starting Duplicati Server...")
    callArgs = [duplicatiLocation + "Duplicati.Server", "--webservice-port=" + servicePort, "--server-datafolder=" + serverdatafolder]
    proc = subprocess.Popen(callArgs)
    #Login using duplicati-client (once is enough, unless you are using it for another server as well)
    callArgs = [duplicaticlientLocation + "duplicati_client", "login", "http://localhost:" + servicePort]
    subprocess.run(callArgs)
    return proc


def stopServer():
    #Duplicati.Server.exe --webservice-port=8300 --server-datafolder=D:\DUMMY\DupliBackupX
    print("Stopping Duplicati Server...")
    global serverProc
    serverProc.terminate()
    return


# Basic threaded interval function that is used for scheduling
class setInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__setInterval)
        thread.start()

    def __setInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


def exit_handler():
    stopServer()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--jsonfile", help="Optional: import a json file instead of using the backup config")
    args = parser.parse_args()
    if args.jsonfile != None:
        onlyImportJson = args.jsonfile
    atexit.register(exit_handler)
    main()
