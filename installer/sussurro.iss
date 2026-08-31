; Inno Setup script para Sussurro
;
; Pre-requisitos:
;   1. Build do PyInstaller concluido:
;      .\.venv\Scripts\pyinstaller.exe --noconfirm sussurro.spec
;      => dist\Sussurro\ (com Sussurro.exe + _internal\)
;   2. Inno Setup 6 instalado (https://jrsoftware.org/isdl.php)
;
; Build do installer:
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer\sussurro.iss
;
; Saida:
;   installer\out\SussurroSetup.exe

#define MyAppName "Sussurro"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Sussurro"
#define MyAppURL "https://github.com/Daniellpego/Sussurro"
#define MyAppExeName "Sussurro.exe"

[Setup]
; Identidade unica do app
AppId={{8F3A9C7E-2E1D-4F5A-A6B8-1C9D5E2F3A4B}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
AllowNoIcons=yes
OutputDir=out
OutputBaseFilename=SussurroSetup
SetupIconFile=..\sussurro\assets\sussurro.ico
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

; Aparencia escura(-ish) compativel com app
WizardSizePercent=120

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na area de trabalho"; GroupDescription: "Atalhos:"
Name: "autostart"; Description: "Iniciar o Sussurro automaticamente no logon"; GroupDescription: "Inicializacao:"; Flags: unchecked

[Files]
; PyInstaller bundle inteiro
Source: "..\dist\Sussurro\Sussurro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Sussurro\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; README opcional
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion; AfterInstall: ""

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{group}\Desinstalar {#MyAppName}"; Filename: "{uninstallexe}"

[Registry]
; Autostart no logon (HKCU)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "Sussurro"; ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Abrir Sussurro agora"; \
    Flags: nowait postinstall skipifsilent

; Dados do usuário em %APPDATA%\Sussurro são preservados na desinstalação.
; Isso evita apagar histórico, dicionário e configurações sem confirmação.
