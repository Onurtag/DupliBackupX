#NoEnv
SendMode Input
#SingleInstance, force
#Persistent
SetFormat, float, 0.3
; ❗ DBX .ico path
IcoFile = %A_ScriptDir%\DBX.ico
Menu, Tray, Icon, %IcoFile%
Menu, Tray, NoStandard
Menu, Tray, Add, Show/Hide DupliBackupX, ShowHideWindow
Menu, Tray, Add
Menu, Tray, Add, Exit, Exited
;Menu, Tray, Standard
Menu, Tray, Default, Show/Hide DupliBackupX
OnExit("Exiting")
version_number := "1.0.3"

/*
DupliBackupX Helper.ahk

A very basic Autohotkey script that does the following work:  

- When you run DupliBackupX Helper.ahk, it starts DupliBackupX with your configuration and sets the icon and the window title of its console window.
- When the DupliBackupX console window is minimized, it hides the window and when you click the tray icon it shows it.
- When you close the ahk script from the Exit option in the tray menu, it closes DupliBackupX as well.

Don't forget to configure the script before running. Configuration lines are marked with ❗❗❗.

If you want to run multiple instances of this helper script, copy it with a different name and edit the config values.
*/

;------ DupliBackupX Helper Configuration ------

;----- Required -----
; ❗❗❗ Json file path (%A_ScriptDir% is the folder that this script resides in): 
jsonfilePath = "%A_ScriptDir%\jsonimports\Import1_DupliBackupX.json"
; ❗❗❗ Duplicati server port number:  
portNumber = 8201
; ❗❗❗ Backup timer in seconds:  
timerSeconds = 60

; ❗ duplicati path (Can be set to "" if its on your PATH):
duplicatiPath = ""
; ❗ duplicati_client path (source or executable) (Can be set to "" if its on your PATH):
duplicaticlientPath = "C:\Users\Onurtag\Desktop\Projects\Git\duplicati-client\\"

; ❗❗ Set window icons and title to DupliBackupX:
setWindowProperties := true

;----- Extra Features (disable if not needed) -----

; ❗ Track log file for warnings/errors
; Only works when you have the "--log-file" settings enabled within your imported json file. 
; ❗ Having --log-file-log-level set to Warning or Error is also pretty much required unless you want to be spammed with notifications.
; ❗❗❗ Enable Tracking of log changes:
trackLogChanges := true
;Check the log file for modifications every x milliseconds:
trackLogTimer := 60 * 1000 ;60 x 1000 milliseconds = 60 seconds
;
; ❗ Ask to edit the json file when opening
; When true, DupliBackupX Helper will ask if you want to edit the json file before starting.
asktoEdit := true
;
;-----------------------------------------------

if (asktoEdit) {
    MsgBox, 4132, DupliBackupX Helper, Would you like to edit the imported json file before starting?
    IfMsgBox, Yes 
    {
        ;run the json file with the default editor
        Run, %jsonfilePath%
        MsgBox, 4161, DupliBackupX Helper, Press OK when you finish editing the json file. `nPress Cancel to quit.
        IfMsgBox, OK 
        {
            ;continue running
        } else {
            ExitApp
        }
    } else {
        ;continue running
    }
}


runArgs = powershell python "%A_ScriptDir%\DupliBackupX.py" --jsonfile=%jsonfilePath% --port=%portNumber% --timer=%timerSeconds%
if (duplicatiPath != """""") {
    runArgs = %runArgs% --duplicati=%duplicatiPath%
}
if (duplicaticlientPath != """""") {
    runArgs = %runArgs% --duplicaticlient=%duplicaticlientPath%
}
;MsgBox, %runArgs%

;Run DupliBackupX and get the pid
Run, %runArgs%,,, procPID
WinWait, ahk_pid %procPID%,, 20
winID := WinExist("ahk_pid" procPID)

/*
-----
From: https://autohotkey.com/board/topic/20990-help-with-dllcall-loadimage/        

h_Icon:=DllCall("LoadImage"
    , uInt, 0                   ; hinst - Handle of modual, if 0 load stand alone resource
    , Str, "Icon.ico"           ; lpszName - Path to image
    , uInt, 2                   ; uType - 0=bitmap, 1=icon, 2=cursor
    , Int, 0                    ; cxDesired - Width of image, if 0 use actual size 
    , Int, 0                    ; cyDesired - Height of image, if 0 use actual size
    , uInt, 0x10)               ; fuLoad - 0x10=LR_LOADFROMFILE

-----
*/
if (setWindowProperties) {
    ; ! Change the shell window's title/taskbar/alt+tab menu icons to DBU icon
    Sleep, 200
    hIcon := DllCall( "LoadImage", UInt,0, Str,IcoFile, UInt,1, UInt,24, UInt,24, UInt,0x10 )
    SendMessage, 0x80, 0, hIcon ,, ahk_id %winID% ; One affects Title bar and
    SendMessage, 0x80, 1, hIcon ,, ahk_id %winID% ; the other the ALT+TAB menu
    ; ! Change the window title to DupliBackupX
    WinSetTitle, ahk_pid %procPID%,, DupliBackupX
}
if (trackLogChanges) {
    ;Get the log file location from the imported json
    jsonfilePath_AHK := StrReplace(jsonfilePath, """", "")
    FileRead, jsonfileData, %jsonfilePath_AHK%
    logFile := RegExReplace(jsonfileData, "sm).*?""Name"":\ ""--log-file"",\s*?""Value"":\ ""(.*?)"",.*" , Replacement := "$1", OutputVarCount := "", Limit := -1, StartingPosition := 1)
    if (logFile == "") {
        trackLogChanges = 0
    } else {
        logFile := StrReplace(logFile, "\\", "\")
        FileGetTime, logfileModifiedTime, %logFile%, M
        FileGetSize, logfileSize, %logFile%
        ;set size to 0 if the log file doesn't exist yet (size == "")
        if (logfileSize == "") {
            logfileSize == 0
        }
        SetTimer, CheckIfLogModified, %trackLogTimer%
    }
}

needtoCloseWindow := 1
currentlyHidden := 0
SetTimer, CheckIfMinimized, 150
Return

CheckIfMinimized:
    CheckMinimized()
Return

CheckMinimized() {
    global
    if (setWindowProperties) {
        ;Check if the window title is still correct
        WinGetTitle, winTitle, ahk_pid %procPID%
        if (winTitle != "DupliBackupX") {
            WinSetTitle, ahk_pid %procPID%,, DupliBackupX
        }
    }
    ;If window process is minimized, hide it. (-1 minimized, 0 visible)
    WinGet, winNotMin, MinMax, ahk_pid %procPID%
    if (winNotMin == -1) {
        SetTimer, CheckIfMinimized, Off
        WinHide, ahk_pid %procPID%
        currentlyHidden = 1
        ;exit if the window process doesn't exist
    } else if (winNotMin == "") {
        needtoCloseWindow = 0
        ExitApp
    }
}

ShowHideWindow:
    if (currentlyHidden) {
        WinShow, ahk_pid %procPID%
        currentlyHidden = 0
        ;Restore minimized window 
        WinRestore, ahk_pid %procPID%
        ;wait until the window is active (probably useless)
        ;WinWaitActive, ahk_pid %procPID%
        SetTimer, CheckIfMinimized, 150
    } else {
        SetTimer, CheckIfMinimized, Off
        WinHide, ahk_pid %procPID%
        currentlyHidden = 1
    }
Return

CheckIfLogModified:
    FileGetTime, logfileModifiedTime_new, %logFile%, M
    FileGetSize, logfileSize_new, %logFile%
    if (logfileSize_new == "") {
        logfileSize_new == 0
    }
    if (logfileModifiedTime_new != logfileModifiedTime) {
        logfileModifiedTime := logfileModifiedTime_new
        logfileSize := logfileSize_new
        ;only notify of the change if the file size is bigger (log file always appends)
        if (logfileSize_new > logfileSize) {
            TrayTip, DupliBackupX Helper, DupliBackupX log file was modified.`nAn error or a warning might have occurred!, 5, 0x10
        }
    }
Return

Exited: 
    ExitApp
Return

Exiting(ExitReason, ExitCode) {
    Global
    if (needtoCloseWindow) {
        ;Bug workaround: Show the window before closing or DupliBackupX exit functions do not work (Duplicati server stays open)
        WinShow, ahk_pid %procPID%
        WinClose, ahk_pid %procPID%
        WinWaitClose, ahk_pid %procPID%
    } else {
        ;Close the DupliBackupX window even if its still visible
        WinClose, ahk_pid %procPID%
        WinWaitClose, ahk_pid %procPID%
    }
    ExitApp
}