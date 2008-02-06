; Script generated by the HM NIS Edit Script Wizard.

; HM NIS Edit Wizard helper defines
!define PRODUCT_NAME                         "AppSnap"
!define PRODUCT_VERSION                      "#VERSION#"
!define PRODUCT_PUBLISHER                    "Ganesh Viswanathan"
!define PRODUCT_WEB_SITE                     "http://appsnap.genotrance.com"
!define PRODUCT_UNINST_KEY                   "Software\Microsoft\Windows\CurrentVersion\Uninstall\${PRODUCT_NAME}"
!define PRODUCT_UNINST_ROOT_KEY              "HKLM"

; Output file name of the resulting installer
!define INSTALLER_FILE_NAME                  "appsnapsetup-${PRODUCT_VERSION}.exe"

; Install directory
!define INSTALL_DIRECTORY                    "$PROGRAMFILES\AppSnap"

; Location of the installation files
!define INSTALLATION_FILES_LOCATION          "dist"

; Location of the library files
!define APPSNAPLIB_FILES_LOCATION            "#SRC_PATH#appsnaplib"

; Location of the locale files
!define LOCALE_FILES_LOCATION                "#SRC_PATH#locale"

; Messages
!define ABORT_INSTALL_MESSAGE                 "${PRODUCT_NAME} ${PRODUCT_VERSION} install failed! Aborting installation."
!define ABORT_UNINSTALL_MESSAGE               "${PRODUCT_NAME} ${PRODUCT_VERSION} uninstall failed! Aborting uninstallation."

; MUI 1.67 compatible ------
!include "MUI.nsh"

; MUI Settings
!define MUI_ABORTWARNING
!define MUI_ICON "${NSISDIR}\Contrib\Graphics\Icons\modern-install.ico"
!define MUI_UNICON "${NSISDIR}\Contrib\Graphics\Icons\modern-uninstall.ico"

; Welcome page
!insertmacro MUI_PAGE_WELCOME
; Directory page
!insertmacro MUI_PAGE_DIRECTORY
; Instfiles page
!insertmacro MUI_PAGE_INSTFILES
; Finish page
!insertmacro MUI_PAGE_FINISH

; Uninstaller pages
!insertmacro MUI_UNPAGE_INSTFILES

; Language files
!insertmacro MUI_LANGUAGE "English"

; MUI end ------

Name "${PRODUCT_NAME} ${PRODUCT_VERSION}"
OutFile "${INSTALLER_FILE_NAME}"
InstallDir "${INSTALL_DIRECTORY}"
ShowInstDetails nevershow
ShowUnInstDetails nevershow

Section "Installer" SEC01
  ; Close and uninstall older version of AppSnap
  ReadRegStr $R0 ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString"
  StrCmp $R0 "" uninstalldone
  fct::fct /WC 'wxWindowClassNR' /WTP '${PRODUCT_NAME}' /TIMEOUT 2000 /QUESTION '${PRODUCT_NAME} is not responding. Terminate?'
  StrCpy $R1 $R0 -10
  ExecWait '$R0 /S _?=$R1'
  Delete $R0
  ; Move 1.3.0 cache and installed.ini
  SetShellVarContext all
  SetOutPath "$APPDATA\${PRODUCT_NAME}"
  Rename "$R1\cache" "$APPDATA\${PRODUCT_NAME}\cache"
  Rename "$R1\installed.ini" "$APPDATA\${PRODUCT_NAME}\installed.ini"
  RMDir $R1
  uninstalldone:

  ; Copy install files
  SetOutPath "$INSTDIR"
  File "${INSTALLATION_FILES_LOCATION}\*.*"

  ; Copy appsnaplib
  SetOutPath "$INSTDIR\appsnaplib"
  File /r /x .svn "${APPSNAPLIB_FILES_LOCATION}\*.py"

  ; Copy locale
  SetOutPath "$INSTDIR\locale"
  File /r /x .svn "${LOCALE_FILES_LOCATION}\*.*"
SectionEnd

Section -Post
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayName" "$(^Name)"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "UninstallString" "$INSTDIR\uninst.exe"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "DisplayVersion" "${PRODUCT_VERSION}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "URLInfoAbout" "${PRODUCT_WEB_SITE}"
  WriteRegStr ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}" "Publisher" "${PRODUCT_PUBLISHER}"

  ; Create shortcut for GUI
  SetOutPath "$INSTDIR"
  CreateShortCut "$SMPROGRAMS\AppSnapGui.lnk" "$INSTDIR\appsnapgui.exe"

  ; Start AppSnap
  ExecShell "open" "$INSTDIR\appsnapgui.exe"
SectionEnd

Function un.onUninstSuccess
  HideWindow
  MessageBox MB_ICONINFORMATION|MB_OK "$(^Name) was successfully removed from your computer." /SD IDOK
FunctionEnd

Function un.onInit
  MessageBox MB_ICONQUESTION|MB_YESNO|MB_DEFBUTTON2 "Are you sure you want to completely remove $(^Name) and all of its components?" /SD IDYES IDYES +2
  Abort
FunctionEnd

Section Uninstall
  ; Close any running instances of AppSnapGui
  fct::fct /WC 'wxWindowClassNR' /WTP '${PRODUCT_NAME}' /TIMEOUT 2000 /QUESTION '${PRODUCT_NAME} is not responding. Terminate?'
  
  ; Delete shortcut
  Delete "$SMPROGRAMS\AppSnapGui.lnk"

  ; Delete all installed files and directories
  RMDir /r "$INSTDIR\appsnaplib"
  RMDir /r "$INSTDIR\locale"
  Delete "$INSTDIR\*.pyd"
  Delete "$INSTDIR\*.exe"
  Delete "$INSTDIR\*.ico"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.log"
  Delete "$INSTDIR\*.lib"
  Delete "$INSTDIR\db.ini"
  Delete "$INSTDIR\config.ini"
  Delete "$INSTDIR\version.dat"
  RMDir "$INSTDIR"

  DeleteRegKey ${PRODUCT_UNINST_ROOT_KEY} "${PRODUCT_UNINST_KEY}"
  SetAutoClose true
SectionEnd
