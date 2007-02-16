@echo off

:: Version
set VERSION=1.3

::Set personal Path to the Apps:
set PythonEXE=D:\Mess\Python25\python.exe
set SevenZipEXE=D:\Mess\Progra~1\SevenZip\7z.exe
set UpxEXE=D:\Windows\upx.exe
set NSIS=D:\Mess\Progra~1\NSIS\makensis.exe

::Check existance of files
if not exist appsnap.py         call FileNotFound appsnap.py
if not exist %PythonEXE%        call FileNotFound %PythonEXE%
if not exist %SevenZipEXE%      call FileNotFound %SevenZipEXE%
if not exist %UpxEXE%           call FileNotFound %UpxEXE%

::Write the Py2EXE-Setup File
call :MakeSetupFile >"appsnap_EXESetup.py"

::Compile the Python-Script
%PythonEXE% -OO "appsnap_EXESetup.py" py2exe
if not "%errorlevel%"=="0" (
        echo Py2EXE Error!
        pause
        goto eof
)

:: Delete the Py2EXE-Setup File
del "appsnap_EXESetup.py"
del *.pyc

:: Copy the Py2EXE Results to the SubDirectory and Clean Py2EXE-Results
rd build /s /q
xcopy dist\*.* "appsnap_EXE\" /d /y /s
rd dist /s /q

:: Compress the files
call :CompressFiles
call :Package
echo.
echo.
echo Done: "appsnap_EXE\"
echo.
pause
goto eof

:: Compression
:CompressFiles
        %SevenZipEXE% -aoa x "appsnap_EXE\shared.lib" -o"appsnap_EXE\shared\"
        del "appsnap_EXE\shared.lib"

        cd appsnap_EXE\shared\
        %SevenZipEXE% a -tzip -mx9 "..\shared.lib" -r
        cd..
        rd "shared" /s /q

		cd appsnap_EXE
        %UpxEXE% --best *.*
		cd..
goto eof

:: Package
:Package
		del appsnapsetup-%VERSION%.exe
		del appsnap-%VERSION%.zip

		%NSIS% appsnapsetup.nsi
		%SevenZipEXE% a appsnap-%VERSION%.zip *.py db.ini config.ini appsnap.ico docs\*.txt
goto eof

:: Generate the setup file
:MakeSetupFile
        echo.
        echo from distutils.core import setup
        echo import py2exe
        echo.
        echo setup (
        echo    console = [{
        echo       "script"         : "appsnap.py",
        echo       "icon_resources" : [(1, "appsnap.ico")]
        echo    }],
        echo    windows = [{
        echo       "script"         : "appsnapgui.py",
        echo       "icon_resources" : [(1, "appsnap.ico")]
        echo    }],
        echo    options = {
        echo       "py2exe": {
        echo          "packages" : ["encodings"],
        echo          "optimize" : 2,
        echo          "compressed" : 0,
        echo       }
        echo    },
		echo    data_files = [(
		echo       "" , ["appsnap.ico","db.ini","config.ini",]
		echo    )],
        echo    zipfile = "shared.lib")
        echo.
goto eof

:: Errors
:FileNotFound
        echo.
        echo Error, File not found:
        echo [%1]
        echo.
        echo Check Path in %~nx0???
        echo.
        pause
        exit
goto eof

:eof