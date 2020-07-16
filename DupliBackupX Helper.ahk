#NoEnv ; Recommended for performance and compatibility with future AutoHotkey releases.
;#Warn  ; Enable warnings to assist with detecting common errors.
SendMode Input ; Recommended for new scripts due to its superior speed and reliability.
#SingleInstance, Force
#Persistent
SetFormat, float, 0.3

; ❗❗❗ DBX icon file path
IcoFile = %A_ScriptDir%\DBX.ico
Menu, Tray, Icon, %IcoFile%
Menu, Tray, NoStandard
Menu, Tray, Add, Show/Hide DupliBackupX, ShowHideWindow
Menu, Tray, Add
Menu, Tray, Standard
Menu, Tray, Default, Show/Hide DupliBackupX
OnExit, Exited

/*
    What this script does:
    - when the duplibackupx window is minimized, it hides the window and when you click the tray icon it shows it.
    - when you close the ahk script from its tray window, it closes the hidden window.
    Configuration lines are marked with ❗❗❗
*/

; ❗❗❗ Json file path
jsonfilepath = %A_ScriptDir%\jsonimports\Import1_DupliBackupX.json

;Run DupliBackupX and get the pid
; ❗❗❗ Set your commandline here
Run, powershell python "%A_ScriptDir%\DupliBackupX.py" --jsonfile="%jsonfilepath%" --port=8203 --timer=60,,, procPID
WinWait, ahk_pid %procPID%,, 20
Sleep, 200
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
; ! Change the shell window's title/taskbar/alt+tab menu icons to DBU icon
hIcon := DllCall( "LoadImage", UInt,0, Str,IcoFile, UInt,1, UInt,24, UInt,24, UInt,0x10 )
SendMessage, 0x80, 0, hIcon ,, ahk_id %winID% ; One affects Title bar and
SendMessage, 0x80, 1, hIcon ,, ahk_id %winID% ; the other the ALT+TAB menu
; ! Change the window title to DupliBackupX
WinSetTitle, ahk_pid %procPID%,, DupliBackupX

needtoCloseWindow := 1
currentlyHidden := 0
SetTimer, CheckIfMinimized, 150
Return

CheckIfMinimized:
    CheckMinimized()
Return

CheckMinimized() {
    global
    WinGet, winNotMin, MinMax, ahk_pid %procPID%
    ;If window process is minimized, hide it. (-1 minimized, 0 visible)
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
        ;wait until the window is active probably useless
        ;WinWaitActive, ahk_pid %procPID%
        SetTimer, CheckIfMinimized, 150
    } else {
        SetTimer, CheckIfMinimized, Off
        WinHide, ahk_pid %procPID%
        currentlyHidden = 1
    }
Return

Exited:
    if (needtoCloseWindow) {
        MsgBox, tata
        WinClose, ahk_pid %procPID%
    }
ExitApp
