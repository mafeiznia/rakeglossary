; ---------------------------------------------------------------------------
; Inno Setup script for RakeGlossary
; ---------------------------------------------------------------------------
; Build:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\setup.iss
;
; Output:
;   dist\installer\RakeGlossary-Setup-x.y.z.exe
; ---------------------------------------------------------------------------

#define MyAppName "RakeGlossary"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Mahmoud Aharpour Feiznia"
#define MyAppURL "https://github.com/mafeiznia/rakeglossary"
#define MyAppExeName "RakeGlossary.exe"

; Path to the PyInstaller output (one level up from installer/)
#define BuildDir "..\dist\RakeGlossary"

[Setup]
AppId={{8F3D5B4C-2A19-4E7D-9F5C-1B6A8D2E9F01}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist\installer
OutputBaseFilename=RakeGlossary-Setup-{#MyAppVersion}
SetupIconFile=..\desktop\assets\icon.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayIcon={app}\{#MyAppExeName}
DisableWelcomePage=no
AllowNoIcons=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Copy everything PyInstaller produced (exe + _internal/)
Source: "{#BuildDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#BuildDir}\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; IconFilename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Clean up user data only if the user explicitly chooses to (see below)
; We do NOT delete %APPDATA%\RakeGlossary by default to preserve user data.
Type: filesandordirs; Name: "{app}\_internal"

[Code]
// ---------------------------------------------------------------------------
// Uninstall: optionally remove user data (%APPDATA%\RakeGlossary)
// ---------------------------------------------------------------------------
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  DataDir: string;
  Response: Integer;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    DataDir := ExpandConstant('{userappdata}\RakeGlossary');
    if DirExists(DataDir) then
    begin
      Response := MsgBox(
        'Do you want to delete your RakeGlossary projects and settings?' + #13#10 +
        'Location: ' + DataDir + #13#10 + #13#10 +
        'Choose "No" to keep them for a future reinstall.',
        mbConfirmation, MB_YESNO or MB_DEFBUTTON2
      );
      if Response = IDYES then
      begin
        DelTree(DataDir, True, True, True);
      end;
    end;
  end;
end;