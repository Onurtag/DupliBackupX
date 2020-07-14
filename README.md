# DupliBackupX
### One way to quickly create backups using Duplicati. Everything stays in a single folder.  
https://github.com/Onurtag/DupliBackupX

📑 The main purpose of DupliBackupX is to be able to quickly create and remove a portable backup set.  

The destination folder will include everything that was used in the backup:  
- Files that are backed-up
- Duplicati server database, duplicati backup database
- Backups that were restored using the menu
- Generated json file (if Backup Config is used)  

When they are no longer needed, you can just delete the destination folder to quickly get rid of everything.  

For configuration, you can either use the below Backup Config or just import a duplicati .json file.  

⭐ You can import a json file using the commandline argument --jsonfile. For example:  

    python DupliBackupX --jsonfile="D:\MyBackup.json"  

 When using the Backup Config, the base file will be DupliBackupX_BASE.json. The Backup Config values will be added onto that.  


👟 Used applications:  
- duplicati 2 (https://github.com/duplicati/duplicati)  
- duplicati-client (https://github.com/Pectojin/duplicati-client)  

📚 Used pip libraries:  
- termcolor (https://pypi.org/project/termcolor/)  
- consolemenu (consolemenu was modified to prevent it from clearing the screen: https://github.com/Onurtag/console-menu)  