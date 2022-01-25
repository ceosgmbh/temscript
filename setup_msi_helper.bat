:: @ECHO OFF
@ECHO ON
:: keep variables local
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

:: set default parameters
set __BUILD_CLEAN__=0
set __BUILD_NO_MSI__=0
set TEMSCRIPT_SERVER_SETUP_PACKAGE=
SET TEMSCRIPT_SERVER_SETUP_USE_CYTHON=

:: iterate over passed parameters and change defaults
:nextParam
if "%1"=="clean" (
    set __BUILD_CLEAN__=1
) else (
    if "%1"=="cython" (
        echo Using cython
        SET TEMSCRIPT_SERVER_SETUP_USE_CYTHON=1
    ) else (
        if "%1"=="nomsi" (
            set __BUILD_NO_MSI__=1
        ) else (
            if [%TEMSCRIPT_SERVER_SETUP_PACKAGE%] == [] (
                echo Building %1
                SET TEMSCRIPT_SERVER_SETUP_PACKAGE=%1
            ) else (
                :: set more than once -> invalid parameters
                SET TEMSCRIPT_SERVER_SETUP_PACKAGE=0
            )
        )
    )
)
shift
if not "%~1"=="" goto nextParam

:: check parameters
if [%TEMSCRIPT_SERVER_SETUP_PACKAGE%] == [] (SET TEMSCRIPT_SERVER_SETUP_PACKAGE=0)
IF %TEMSCRIPT_SERVER_SETUP_PACKAGE% == 0 (
    echo Usage:
    echo ------
    echo %0 $target [clean] [cython] [nomsi]
    echo.
    echo $target: must be one of the known targets listed below
    echo clean:   remove build folder before starting
    echo cython:  use cython to compile python files
    echo nomsi:   skip creation of MSI, for debugging
    echo.
    echo Example:
    echo TemScriptServer clean     # builds target "TemScriptServer", clean
    echo.

    :: list known targets
    SET TEMSCRIPT_SERVER_SETUP_PACKAGE=
    python setup_msi.py

    exit /B -2
)

IF %__BUILD_CLEAN__% == 1 (
    echo Removing build directory ...
    rmdir build /s /q || exit /B -1
) else (
    echo Partially cleaning build directory ...
)

:: Without deletion Editor package would contain too much
:: Files to trash folder since recursive delete is unreliable in Windows.
if not exist "build\trash" mkdir "build\trash"
FOR /D %%d IN (build\exe.*) DO @IF EXIST %%d (move "%%d" build\trash) || exit /B -1
FOR /D %%d IN (build\bdist.*) DO @IF EXIST %%d (move "%%d" build\trash) || exit /B -1
FOR /D %%d IN (build\scripts.*) DO @IF EXIST %%d (move "%%d" build\trash) || exit /B -1
rmdir build\trash /s /q


:: Binary and freeze at once does not work.
:: First run uses Cython to create binaries.
:: Second run uses the binaries and collects all required libs.
:: Third run removes some unwanted fils and creates the MSI.

:: build modules to build\lib* folder
SET TEMSCRIPT_SERVER_SETUP_FREEZE=
SET TEMSCRIPT_SERVER_SETUP_MSI_ONLY=
python setup_msi.py build || exit /B -1

:: create frozen version in build\exe* folder
SET TEMSCRIPT_SERVER_SETUP_FREEZE=1
python setup_msi.py build_exe || exit /B -1

:: remove unneded stuff from build\exe* folder
FOR /D %%s in (build\exe.*) do @if exist %%s\lib (
    cd %%s\lib\|| exit /B -1

    if exist numpy (
        cd numpy || exit /B -1
        del core\libopenblas.*.dll
        del linalg\libopenblas.*.dll
        cd ..
    )

    FOR /r %%d IN (VCRUNTIME*.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (VCOMP*.dll) DO @IF EXIST %%d (del /s /q "%%d")
    REM PyQT5 for Python 3.6 32Bit contains a file python3.dll which must not be deleted
    FOR /r %%d IN (python27.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python31.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python32.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python33.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python34.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python35.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python36.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python37.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (python38.dll) DO @IF EXIST %%d (del /s /q "%%d")
    FOR /r %%d IN (tests) DO @IF EXIST %%d (rmdir /s /q "%%d")
    rmdir test /s /q

    cd ..

    :: include Visual Studio OpenMP dll missing in Windows 7
    copy %SystemRoot%\System32\vcomp140.dll . || exit /B -1

    cd ..\..
)

:: copied required stuff to build\bdist and create dist\*.msi
IF %__BUILD_NO_MSI__% == 0 (
    SET TEMSCRIPT_SERVER_SETUP_MSI_ONLY=1
    python setup_msi.py bdist_msi || exit /B -1
)

echo.
echo Finished successfully!
