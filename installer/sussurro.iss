; Inno Setup script para Sussurro
;
; Pre-requisitos:
;   1. Build do PyInstaller concluido:
;      $env:SUSSURRO_VARIANT="cpu"; pyinstaller --noconfirm sussurro.spec
;      => dist\Sussurro\ (com Sussurro.exe + _internal\)
;   2. Inno Setup 6 instalado (ISCC.exe)
;
; Build do installer:
;   ISCC.exe /DMyAppVersion=0.1.1 /DAppVariant=CPU installer\sussurro.iss
;   ISCC.exe /DMyAppVersion=0.1.1 /DAppVariant=CUDA installer\sussurro.iss
;
; Saida:
;   installer\out\SussurroSetup-CPU.exe ou SussurroSetup-CUDA.exe

#define MyAppName "Sussurro"
#ifndef MyAppVersion
  #define MyAppVersion "0.1.1"
#endif
#ifndef AppVariant
  #define AppVariant "CPU"
#endif
#define MyAppPublisher "Susurro Oficial"
#define MyAppURL "https://github.com/Daniellpego/Sussurro"
#define MyAppExeName "Sussurro.exe"

[Setup]
; Identidade unica do app
AppId={{8F3A9C7E-2E1D-4F5A-A6B8-1C9D5E2F3A4B}
AppName={#MyAppName} ({#AppVariant})
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
OutputBaseFilename=SussurroSetup-{#AppVariant}
SetupIconFile=..\sussurro\assets\sussurro.ico
LicenseFile=..\LICENSE
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
UninstallDisplayIcon={app}\{#MyAppExeName}

; Aparencia compativel com desktop moderno
WizardSizePercent=120

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar atalho na área de trabalho"; GroupDescription: "Atalhos:"
Name: "autostart"; Description: "Iniciar o Sussurro automaticamente no logon"; GroupDescription: "Inicialização:"; Flags: unchecked

[Files]
; PyInstaller bundle inteiro
Source: "..\dist\Sussurro\Sussurro.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\Sussurro\_internal\*"; DestDir: "{app}\_internal"; Flags: ignoreversion recursesubdirs createallsubdirs
; Documentação e Licenças
Source: "..\README.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\README.en.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\LICENSE"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\docs\THIRD_PARTY_LICENSES.md"; DestDir: "{app}"; Flags: ignoreversion

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

; NOTA DE SEGURANÇA E PRIVACIDADE:
; Os dados do usuário persistidos em %APPDATA%\Sussurro (histórico de ditados, dicionário personalizado,
; macros PT-BR e modos configurados) são expressamente PRESERVADOS na desinstalação.
; Nenhum dado pessoal do usuário é apagado sem confirmação manual.
