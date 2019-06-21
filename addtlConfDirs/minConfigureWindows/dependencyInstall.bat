rem This file sets up for an EPICS windows-x64 build
REM https://epics.anl.gov/tech-talk/2015/msg01582.php

set EPICS_HOST_ARCH=windows-x64-static

rem make sure to have binaries for 'make', 're2c', 'perl', 'base', and 'wget' in the system PATH
rem set PATH=C:\epics\dependancies;%PATH%

rem Execute the Visual Studio batch file for 64-bit builds
rem make sure that this points to your local install of visual studio 
"C:\Program Files (x86)\Microsoft Visual Studio\2017\Community\VC\Auxiliary\Build\vcvarsall.bat" x86_amd64

REM ======================================================
REM --------------- EPICS --------------------------------
REM ======================================================
REM set EPICS_HOST_ARCH=windows-x64
REM set EPICS_HOST_ARCH=win32-x86
REM set PATH=%PATH%;C:\epics\base-3.15.5\bin\%EPICS_HOST_ARCH%
REM set PATH=%PATH%;G:\epics\extensions\bin\%EPICS_HOST_ARCH%

REM ======================================================
REM ----------------- GNU make flags ---------------------
REM ======================================================
set MAKEFLAGS=-w