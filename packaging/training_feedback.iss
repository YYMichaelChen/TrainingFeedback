; TrainingFeedback Windows installer.
; The PyInstaller directory is the application payload. The installer owns only
; the program directory; the application's locator and selected data root are
; deliberately outside it.

#ifndef AppVersion
  #define AppVersion "0.0.0-dev"
#endif
#ifndef SourceDir
  #define SourceDir "..\dist\TrainingFeedback"
#endif
#ifndef OutputDir
  #define OutputDir "..\dist\installer"
#endif

#define MyAppName "TrainingFeedback"
#define MyAppPublisher "TrainingFeedback"
#define MyAppExeName "TrainingFeedback.exe"
[Setup]
AppId={{A5D9D2A7-9C93-4F13-9F1A-7C1C2E1D8D60}
AppName={#MyAppName}
AppVersion={#AppVersion}
AppVerName={#MyAppName} {#AppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
OutputDir={#OutputDir}
OutputBaseFilename=TrainingFeedback-{#AppVersion}-Setup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile=..\icon\TrainingFeedback.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
CloseApplications=yes
RestartApplications=no
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
SetupLogging=yes
VersionInfoVersion={#AppVersion}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional shortcuts:"; Flags: unchecked

[Files]
; Install the complete onedir payload, including _internal and bundled Qt
; resources. A single EXE is not a valid payload for this PyInstaller build.
Source: "{#SourceDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[InstallDelete]
; Remove stale files from an older payload in the program directory before
; copying the new build. Keep the installer-owned uninstaller itself intact.
; User data is not stored under {app}.
Type: filesandordirs; Name: "{app}\_internal"
Type: files; Name: "{app}\{#MyAppExeName}"
; Migrate shortcuts created by the earlier install-local.ps1 workflow so users
; cannot accidentally launch an old versioned directory after installing Setup.
Type: files; Name: "{userprograms}\TrainingFeedback.lnk"

[Icons]
Name: "{group}\TrainingFeedback"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"
Name: "{autodesktop}\TrainingFeedback"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Tasks: desktopicon
Name: "{autodesktop}\TrainingFeedback"; Filename: "{app}\{#MyAppExeName}"; WorkingDir: "{app}"; Check: ShouldMigrateLegacyDesktopShortcut

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch TrainingFeedback"; Flags: nowait postinstall skipifsilent

[Code]
var
  MigrateLegacyDesktopShortcut: Boolean;

function InitializeSetup(): Boolean;
begin
  MigrateLegacyDesktopShortcut :=
    FileExists(ExpandConstant('{autodesktop}\TrainingFeedback.lnk'));
  Result := True;
end;

function ShouldMigrateLegacyDesktopShortcut(): Boolean;
begin
  Result := MigrateLegacyDesktopShortcut;
end;
