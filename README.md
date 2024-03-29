*Repo is now archived.  
Please use other tools that have better performance (i.e restic.)*  

---  

# DupliBackupX
### One way to quickly create backups using Duplicati. Everything stays in a single folder.    
https://github.com/Onurtag/DupliBackupX

 📑 The main purpose of DupliBackupX is to be able to quickly create and remove a portable backup set.  
 What DupliBackupX does can be done using duplicati.commandline in a few lines, but with a bit worse performance as it is a bit slow at startup.  
  
 📂 The destination folder will include everything that was used in the backup:  
 - Files that are backed-up  
 - Duplicati server database, duplicati backup database  
 - Backups that were restored using the menu  
 - Generated json file (if Backup Config is used)  
  
 When they are no longer needed, you can just delete the destination folder to quickly get rid of everything.  
 ___  

### **How to use DupliBackupX**

 1. Install Python.  
 2. Install DupliBackupX requirements by entering the following command into your terminal:  
    ```
    pip install termcolor, console-menu, colorama
    ```

 For application and backup configuration, you can modify the inline configs or set them using commandline.  
 When using the inline Backup Config (i.e. when you are not using the --jsonfile commandline), the base file will be DupliBackupX_BASE.json. The Backup Config values will be added onto that.  

 ⭐ Commandline arguments:  
    
  - **--help**: display help
  - **--jsonfile**: import a json file instead of using the inline backup config
  - **--port**: use a different server port instead of the default
  - **--timer**: use a custom timer in seconds instead of the default
  - **--duplicati**: use commandline to set duplicati folder path instead of using the inline application config
  - **--duplicaticlient**: use commandline to set duplicati_client folder path instead of using the inline application config
  - **--version**: display application version

When the value is a folder path, you might have to end it with double backslashes. Like: option2=\"path\\to\\folder\\\\\"

Example full commandline:
```bash
python DupliBackupX --jsonfile="D:\MyBackup.json" --timer=120 --port=8408 --duplicati="C:\Program Files\Duplicati 2\\" --duplicaticlient="C:\Applications\duplicati_client\\"
```
___

### **Extra: DupliBackupX Helper.ahk**

A very basic Autohotkey script that does the following work:  
- When you run DupliBackupX Helper.ahk, it starts DupliBackupX with your configuration and sets the icon and the window title of its console window.
- When the DupliBackupX console window is minimized, it hides the window and when you click the tray icon it shows it.
- When you close the ahk script from the Exit option in the tray menu, it closes DupliBackupX as well.

Don't forget to configure the script before running. Configuration lines are marked with ❗❗❗.

___

### **Changelog:**
https://github.com/Onurtag/DupliBackupX/blob/master/CHANGELOG.md

___

 👟 Used applications:  
 - duplicati 2 (https://github.com/duplicati/duplicati)  
 - duplicati-client (https://github.com/Pectojin/duplicati-client)  
  
 📚 Used python libraries:  
 - termcolor (https://pypi.org/project/termcolor/)  
 - console-menu (https://pypi.org/project/console-menu/)  
 - colorama (https://pypi.org/project/colorama/)  
   
 🤖 Icon font:  
 - Octicity (http://www.umop.com/)