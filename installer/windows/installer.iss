; =============================================================================
; Cosmetics Records - Inno Setup Installer Script
; =============================================================================
; This script creates a Windows installer with:
;   - Start Menu shortcuts
;   - Desktop shortcut (optional)
;   - Uninstaller with Add/Remove Programs entry
;   - Automatic upgrade of previous versions
;
; Requirements:
;   - Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
;   - CosmeticsRecords.exe in dist/ directory
;
; Build:
;   iscc installer/windows/installer.iss
; =============================================================================

#define MyAppName "Cosmetics Records"
#define MyAppVersion GetEnv('APP_VERSION')
#if MyAppVersion == ""
#define MyAppVersion "0.9.0"
#endif
#define MyAppPublisher "Cosmetics Records"
#define MyAppURL "https://github.com/fuchsi3010/cosmetics-records"
#define MyAppExeName "CosmeticsRecords.exe"

[Setup]
; Unique App ID - used to identify the app for upgrades
; DO NOT change this between versions!
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
; Allow user to disable Start Menu group creation
AllowNoIcons=yes
; License file (optional - uncomment if you have one)
; LicenseFile=..\..\LICENSE
; Output settings
OutputDir=..\..\dist
OutputBaseFilename=CosmeticsRecords-Windows-Setup
; Compression
Compression=lzma2/ultra64
SolidCompression=yes
; Modern installer look
WizardStyle=modern
; Require admin rights for Program Files installation
PrivilegesRequired=admin
PrivilegesRequiredOverridesAllowed=dialog
; Minimum Windows version (Windows 10)
MinVersion=10.0
; Uninstaller settings
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
; Upgrade behavior - close running app before upgrade
CloseApplications=yes
CloseApplicationsFilter=*.exe
RestartApplications=yes
; Architecture
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "german"; MessagesFile: "compiler:Languages\German.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Main executable
Source: "..\..\dist\CosmeticsRecords.exe"; DestDir: "{app}"; Flags: ignoreversion
; Include VC++ runtime if needed (uncomment if bundling)
; Source: "vcredist_x64.exe"; DestDir: "{tmp}"; Flags: deleteafterinstall

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
; Launch app after installation (optional)
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Code]
// Check if a previous version is installed and handle upgrade
function InitializeSetup(): Boolean;
var
  UninstallKey: String;
  UninstallString: String;
  ResultCode: Integer;
begin
  Result := True;

  // Check for existing installation in registry
  UninstallKey := 'Software\Microsoft\Windows\CurrentVersion\Uninstall\{#SetupSetting("AppId")}_is1';

  if RegQueryStringValue(HKLM, UninstallKey, 'UninstallString', UninstallString) or
     RegQueryStringValue(HKCU, UninstallKey, 'UninstallString', UninstallString) then
  begin
    // Previous version found - ask user if they want to upgrade
    if MsgBox('A previous version of {#MyAppName} is installed. ' +
              'It will be upgraded to version {#MyAppVersion}.' + #13#10 + #13#10 +
              'Do you want to continue?', mbConfirmation, MB_YESNO) = IDNO then
    begin
      Result := False;
      Exit;
    end;

    // Note: Inno Setup automatically handles the upgrade when AppId matches
    // The old version's files will be replaced with the new ones
  end;
end;

// Clean up old user data on uninstall (optional - ask user)
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
var
  UserDataDir: String;
begin
  if CurUninstallStep = usPostUninstall then
  begin
    UserDataDir := ExpandConstant('{userappdata}\CosmeticsRecords');

    if DirExists(UserDataDir) then
    begin
      if MsgBox('Do you want to remove your Cosmetics Records data (client database, settings, backups)?' + #13#10 + #13#10 +
                'Location: ' + UserDataDir + #13#10 + #13#10 +
                'Warning: This cannot be undone!', mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(UserDataDir, True, True, True);
      end;
    end;
  end;
end;
