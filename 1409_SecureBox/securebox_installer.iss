; Script generated by the Inno Setup Script Wizard.
; SEE THE DOCUMENTATION FOR DETAILS ON CREATING INNO SETUP SCRIPT FILES!

#define MyAppName "Secure Box"
#define MyAppShortName "SecureBox"
#define MyAppVersion "1.0.5"
#define MyAppPublisher "Thomas Deneux"
#define MyAppExeName "securebox.exe"
#define OutputDir "securebox-guideline"

[Setup]
; NOTE: The value of AppId uniquely identifies this application.
; Do not use the same AppId value in installers for other applications.
; (To generate a new GUID, click Tools | Generate GUID inside the IDE.)
AppId={{E74C2BC4-4378-4EFA-A9EE-8B5B11626D30}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
;AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={pf}\SecureBox
DefaultGroupName={#MyAppName}
OutputDir={#OutputDir}
OutputBaseFilename="{#MyAppName} {#MyAppVersion} Setup"
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "C:\Users\THomas\spyder workspace\SecureBox\python\build\exe.win32-2.7\*"; DestDir: "{app}"; Flags: ignoreversion
Source: "C:\Users\THomas\spyder workspace\SecureBox\python\connect.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Secure Box Board"; Filename: "{app}\secureboxboard.exe"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{commondesktop}\{#MyAppName}"; Filename: "{app}\secureboxboard.exe"; Tasks: desktopicon

[Registry]
; run at startup
Root: HKLM; Subkey: SOFTWARE\Microsoft\Windows\CurrentVersion\Run; ValueType: string; ValueName: "{#MyAppName}"; ValueData: """{app}\secureboxdeamon.exe"""; Flags: uninsdeletevalue deletevalue
; add context menu
Root: HKCR; Subkey: Directory\shell\SecureBox; ValueType: string; ValueData: "Synchronize with cloud"; Flags: uninsdeletekey deletekey
Root: HKCR; Subkey: Directory\shell\SecureBox; ValueType: string; ValueName: Icon; ValueData: """{app}\connect.ico"""
Root: HKCR; Subkey: Directory\shell\SecureBox\command; ValueType: string; ValueData: """{app}\secureboxregister.exe"" ""%1"""

; No more [Run] section as the post-install commands are executed from the [Code] section, only at first install (and not at update)
;[Run]
;Filename: "{app}\secureboxdeamon.exe"; Flags: runasoriginaluser nowait
;Filename: "{app}\secureboxinstall.exe"; Flags: runasoriginaluser nowait

[UninstallRun]
Filename: "{app}\secureboxuninstall.exe"

[Code]
procedure CurStepChanged(CurStep: TSetupStep);
var
  Base: String;
  doUpdate: Boolean;
  ResultCode: Integer;
begin
  if CurStep = ssDone then 
  begin
    Base := ExpandConstant('{app}');
    doUpdate := DirExists(Base);
    ExecAsOriginalUser(Base+'\secureboxdeamon.exe','','',SW_SHOW,ewNoWait,ResultCode);
    if doUpdate then 
    begin
      ExecAsOriginalUser(Base+'\secureboxboard.exe','','',SW_SHOW,ewNoWait,ResultCode);
    end
    else
    begin
      ExecAsOriginalUser(Base+'\secureboxinstall.exe','','',SW_SHOW,ewNoWait,ResultCode);
    end;
    
  end;
end;


