; =====================================================
; AURA Installer Script for Inno Setup
; Creates professional Windows installer (AURA-Setup.exe)
; =====================================================

#define MyAppName "AURA"
#define MyAppVersion "2.0.0"
#define MyAppPublisher "Cyriac Paul Pullan"
#define MyAppURL "https://github.com/cyriac-pullan/aura3"
#define MyAppExeName "AURA.exe"

[Setup]
; App information
AppId={{8A9B3C4D-5E6F-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

; Installation directories
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes

; Output settings
OutputDir=installer_output
OutputBaseFilename=AURA-Setup
SetupIconFile=jarvis_icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}

; Compression
Compression=lzma2/max
SolidCompression=yes

; Windows version requirements
MinVersion=10.0
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

; Privileges
PrivilegesRequired=admin

; Wizard appearance
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "startup"; Description: "Launch AURA at Windows startup"; GroupDescription: "Startup Options:"; Flags: unchecked

[Files]
; Main application files (entire dist\AURA folder) - path relative to this .iss file
Source: "..\dist\AURA\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; Quick start guide
Source: "QUICK_START.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
; Start Menu shortcut
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"

; Desktop shortcut (optional)
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

; Quick Launch shortcut (optional)
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Registry]
; Auto-start entry (optional)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "AURA"; ValueData: """{app}\{#MyAppExeName}"""; Flags: uninsdeletevalue; Tasks: startup

[Run]
; Option to launch AURA after installation
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Clean up processes before uninstall
Filename: "{cmd}"; Parameters: "/c taskkill /f /im {#MyAppExeName}"; Flags: runhidden; RunOnceId: "KillAURA"

[Code]
// Check if AURA is running before installation
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
    ResultCode: Integer;
begin
    // Try to close AURA gracefully
    Exec(ExpandConstant('{cmd}'), '/c taskkill /im ' + '{#MyAppExeName}', '', SW_HIDE, ewWaitUntilTerminated, ResultCode);
    Result := '';
end;

// Custom message for first-run setup
procedure CurStepChanged(CurStep: TSetupStep);
begin
    if CurStep = ssPostInstall then
    begin
        MsgBox('AURA has been installed successfully!' + #13#10 + #13#10 + 
               'On first launch, you will be guided through a quick setup to configure your API key.' + #13#10 + #13#10 +
               'Most commands run locally and are free!', 
               mbInformation, MB_OK);
    end;
end;
