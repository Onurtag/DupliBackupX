import subprocess, sys, time, threading, json, webbrowser
import atexit
import argparse
from os import path
from datetime import datetime
from termcolor import colored
from consolemenu import *
from consolemenu.format import *
from consolemenu.items import *

## -------- DupliBackupX --------
## https://github.com/Onurtag/DupliBackupX
##
## 📑 The main purpose of DupliBackupX is to be able to quickly create and remove a portable backup set.
## What DupliBackupX does can be done using duplicati.commandline in a few lines, but with a bit worse performance as it is a bit slow at startup.
##
## 📂 The destination folder will include everything that was used in the backup:
## - Files that are backed-up
## - Duplicati server database, duplicati backup database
## - Backups that were restored using the menu
## - Generated json file (if Backup Config is used)
##
## When they are no longer needed, you can just delete the destination folder to quickly get rid of everything.
## ___
## For configuration, you can either use the inline Backup Config or just import a duplicati .json file.
##
## ⭐ You can import a json file using the commandline argument --jsonfile. For example:
##
##     python DupliBackupX --jsonfile="D:\MyBackup.json"
##
##  When using the inline Backup Config, the base file will be DupliBackupX_BASE.json. The Backup Config values will be added onto that.
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

# TODO maybe add application config commandline. Or a custom settings file like an .ini

########################
#######  Config  #######
########################

# ---------- 👟 Application config -------
# Backup timer (seconds). Making this too short might be unwise. 60 seconds will not be enough for larger backups.
backuptimer = 60

# Duplicati 2 and Duplicati_client folders. These could be empty if they are on your PATH variables.
duplicati_location = "C:\\Program Files\\Duplicati 2\\"
# Duplicati_client will run from source if duplicati_client.py is in the folder.
duplicaticlient_location = "C:\\DATA\\Portables\\duplicati_client\\source\\"
# Duplicati server port.
serviceport = "8300"

# Only import json. Enter a json file path to ignore the backup config and just import the json file.
# You can use the commandline argument --jsonfile to set this
# Leave it empty to use the below Backup Config
#
# importjson = "D:\\MyBackup.json"
importjson = ""

# -------------------------------------

# ----------- 📦 Backup Config -----------
# ❗ Backup config is not used if you are using importjson (or the --jsonfile commandline)

# Backup name and destination
backupname = "MyBackup" + "_DupliBackupX"
# By default backupdestination is a folder named backupname under C:\Backups
backupdestination = "C:\\Backups\\" + backupname

# The first source is opened when the "Open Source Folder" menu is selected.
#
# The r prefix allows us to use single backslashes which makes copy-paste quicker.
# Because of that, backup sources can't end in backslash (\).
#
## Examples:
# backupsources = [
#     r"C:\Folder\SubFolder",
#     r"C:\Folder\File.txt",
# ]
backupsources = [
    r"C:\Folder\SubFolder",
    r"C:\Folder\File.txt",
]

# -------------------------------------

########################
########################
########################

version = "1.0.0"
backupconfig = {}
theInterval = None
serverproc = None
backupdbpath = ""
duplicaticlient_ext = ""
duplicaticlient_python = None


def main():
    if importjson != "":
        importjsonvalues()

    createconfig()
    print(colored("\n--------DupliBackupX--------", 'cyan'))
    global serverproc
    serverproc = startserver(backupdestination + "\\DupliBackupX\\")

    if checkbackup() != 0:
        print("Backup does not exist. Importing json...")
        if importjson == "":
            generatejson()
        importbackup()
        # Check again to get the DB path
        checkbackup()
    else:
        print("Backup exists.")
        if importjson != "":
            print("Updating backup...")
            updatebackup()
            checkbackup()
        else:
            if generatejson() != 0:
                print("Updating backup...")
                updatebackup()
                checkbackup()
            else:
                print("No need to update the backup.")

    print("Running first backup...")
    runbackup()
    startscheduler()
    showmenu()
    # Exit the app when the menu exits.
    print("Exiting...")
    stopscheduler()
    try:
        sys.exit()
    except:
        pass


def showmenu():
    menu = ConsoleMenu("DupliBackupX",
                       "Select an option",
                       clear_screen=False,
                       formatter=MenuFormatBuilder().set_title_align('center').set_subtitle_align('center').set_border_style_type(
                           MenuBorderStyleType.HEAVY_BORDER).show_prologue_top_border(True).show_prologue_bottom_border(True))

    menuitems = [
        FunctionItem("Show Backup Info", showbackupinfo),
        FunctionItem("Open DupliBackupX server in browser", openinbrowser),
        FunctionItem("Open Source Folder", opensourcefolder),
        FunctionItem("Open Destination Folder", opendestinationfolder),
        FunctionItem("List Backups", listbackups),
        FunctionItem("Compare Backups", comparebackups),
        FunctionItem("Restore a Backup", restorebackup),
        FunctionItem("Perform a Backup Now", runbackup),
    ]
    for k in menuitems:
        menu.append_item(k)

    menu.show()
    return


def createconfig():
    #Create displayNames (probably useless)
    displaynames = {}
    for value in backupsources:
        split = value.split("\\")
        #iterate to find the last non-empty split value
        dispName = next(i for i in reversed(split) if i)
        displaynames[value] = dispName

    # Generate dictionary from above values
    # Same data format as the json so we can use .update()
    # DBPath sadly does not work.
    global backupconfig
    backupconfig = {
        "Schedule": None,
        "Backup": {
            "Name": backupname,
            "TargetURL": "file://" + backupdestination,
            "DBPath": backupdestination + "\\DupliBackupX\\" + backupname + ".sqlite",
            "Sources": backupsources,
        },
        "DisplayNames": displaynames
    }
    print(colored("\n--------Configuration--------", 'cyan'))
    if importjson != "":
        print(colored(importjson, 'green'))
        print()
    print(colored(json.dumps(backupconfig, indent=4), 'green'))
    if path.exists(duplicaticlient_location + "duplicati_client.py"):
        global duplicaticlient_ext, duplicaticlient_python
        duplicaticlient_ext = ".py"
        duplicaticlient_python = "python"
    return


def importbackup():
    # lets not bother with importing duplicati_client as a library because we don't need any advanced functionality.
    # Using the executable.
    jsonfile = backupdestination + "\\DupliBackupX\\" + backupname + ".json"
    if importjson != "":
        jsonfile = importjson
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "create", "backup", jsonfile]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    subprocess.run(callargs)
    return


def updatebackup():
    jsonfile = backupdestination + "\\DupliBackupX\\" + backupname + ".json"
    if importjson != "":
        jsonfile = importjson
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "update", "backup", "1", jsonfile]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    subprocess.run(callargs)
    return


# Returns 2 if the backup doesn't exist, 0 if it exists
def checkbackup():
    print("Checking for backup...")
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "get", "backup", "1"]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    checkresult = subprocess.run(callargs, capture_output=True, text=True)
    #print(checkresult.stdout)
    #print(checkresult.stderr)
    split1 = checkresult.stdout.split("database: ")
    global backupdbpath
    if checkresult.returncode == 0:
        backupdbpath = split1[1].split("\n")[0]
    return checkresult.returncode


def showbackupinfo():
    # Returns 2 if backup doesnt exist, 0 if it exists
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "get", "backup", "1"]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    subprocess.run(callargs)


def listbackups():
    callargs = [
        duplicati_location + "duplicati.commandline", "list", backupdestination, "--dbpath=" + backupdbpath, "--encryption-module=", "--compression-module=zip",
        "--no-encryption=true"
    ]
    subprocess.run(callargs)


def startscheduler():
    #Start the backup scheduler
    print("Starting the backup scheduler...")
    global theInterval
    theInterval = SetInterval(backuptimer, runbackup)
    return


def stopscheduler():
    #Stop the backup scheduler
    print("Stopping the backup scheduler...")
    global theInterval
    theInterval.cancel()
    #timer = threading.Timer(60, theInterval.cancel)
    #timer.start()
    return


def opensourcefolder():
    callargs = ["explorer", backupsources[0]]
    subprocess.run(callargs)


def openinbrowser():
    webbrowser.open("http://localhost:" + serviceport)


def opendestinationfolder():
    callargs = ["explorer", backupdestination]
    subprocess.run(callargs)


def comparebackups():
    comparever1 = input("Enter first version number to compare: ")
    comparever2 = input("Enter second version number to compare: ")
    callargs = [
        duplicati_location + "duplicati.commandline", "compare", backupdestination, "--dbpath=" + backupdbpath, "--encryption-module=",
        "--compression-module=zip", "--no-encryption=true", comparever1, comparever2
    ]
    subprocess.run(callargs)
    #input("\nEnter anything to return to the menu...")


def restorebackup():
    restoreversion = input("Enter the version number to restore: ")
    callargs = [
        duplicati_location + "duplicati.commandline", "restore", backupdestination, "--dbpath=" + backupdbpath, "--encryption-module=",
        "--compression-module=zip", "--no-encryption=true",
        "--restore-path=" + backupdestination + "\\Restored_" + datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + restoreversion, "--version=" + restoreversion
    ]
    subprocess.run(callargs)
    #input("\nEnter anything to return to the menu...")


def runbackup():
    #print("Running backup...")
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "run", "1"]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    runresult = subprocess.run(callargs, capture_output=True, text=True)
    return


# Returns 1 if the file was updated.
def generatejson():
    filename = "DupliBackupX_BASE.json"
    with open(filename, "r") as basefile:
        basedata = json.load(basefile)

    currentdata = None
    try:
        filename = backupdestination + "\\DupliBackupX\\" + backupname + ".json"
        with open(filename, "r") as basefile:
            currentdata = json.load(basefile)
    except:
        pass

    # Update the subkeys
    # This way we can keep the default values like Backup.ID and Backup.Settings instead of overwriting ["Backup"] and deleting them
    basedata["Backup"].update(backupconfig["Backup"])
    basedata["DisplayNames"].update(backupconfig["DisplayNames"])
    basedata["Schedule"] = backupconfig["Schedule"]

    if currentdata == basedata:
        return 0

    newfile = backupdestination + "\\DupliBackupX\\" + backupname + ".json"
    with open(newfile, "w") as nfile:
        json.dump(basedata, nfile, indent=2)

    return 1


# Returns 1 if the file was updated.
def importjsonvalues():
    filename = importjson
    with open(filename, "r") as basefile:
        basedata = json.load(basefile)

    global backupname, backupdestination, backupsources
    backupname = basedata["Backup"]["Name"]
    backupdestination = basedata["Backup"]["TargetURL"].split("file://")[1]
    backupsources = basedata["Backup"]["Sources"]

    return


def startserver(serverdatafolder):
    #Duplicati.Server --webservice-port=8304 --server-datafolder=D:\DUMMY\DupliBackupX
    print("Starting Duplicati Server...")
    callargs = [duplicati_location + "Duplicati.Server", "--webservice-port=" + serviceport, "--server-datafolder=" + serverdatafolder]
    proc = subprocess.Popen(callargs, creationflags=subprocess.IDLE_PRIORITY_CLASS)
    #Login using duplicati-client (once is enough, unless you are using it for another server as well)
    callargs = [duplicaticlient_location + "duplicati_client" + duplicaticlient_ext, "login", "http://localhost:" + serviceport]
    if duplicaticlient_python != None:
        callargs.insert(0, duplicaticlient_python)
    subprocess.run(callargs)
    return proc


def stopserver():
    #Duplicati.Server.exe --webservice-port=8300 --server-datafolder=D:\DUMMY\DupliBackupX
    print("Stopping Duplicati Server...")
    global serverproc
    serverproc.terminate()
    return


# Basic threaded interval function that is used for scheduling
class SetInterval:
    def __init__(self, interval, action):
        self.interval = interval
        self.action = action
        self.stopEvent = threading.Event()
        thread = threading.Thread(target=self.__SetInterval)
        thread.start()

    def __SetInterval(self):
        nextTime = time.time() + self.interval
        while not self.stopEvent.wait(nextTime - time.time()):
            nextTime += self.interval
            self.action()

    def cancel(self):
        self.stopEvent.set()


def exit_handler():
    stopserver()
    return


if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="DupliBackupX")
    parser.add_argument("--jsonfile", help="Optional: import a json file instead of using the backup config")
    parser.add_argument('--version', action='version', version='%(prog)s ' + version)
    args = parser.parse_args()
    if args.jsonfile != None:
        importjson = args.jsonfile
    atexit.register(exit_handler)
    main()
