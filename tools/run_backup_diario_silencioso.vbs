' Executa backup diário sem janela (pythonw + --silencioso).
' Uso: duplo clique ou Agendador de Tarefas apontando para este .vbs
Option Explicit

Dim fso, root, py, script, cmd
Set fso = CreateObject("Scripting.FileSystemObject")
root = fso.GetParentFolderName(fso.GetParentFolderName(WScript.ScriptFullName))
py = root & "\.venv\Scripts\pythonw.exe"
script = root & "\tools\backup_diario.py"

If Not fso.FileExists(py) Then
    py = "pythonw.exe"
End If

cmd = """" & py & """ """ & script & """ --silencioso"
CreateObject("WScript.Shell").Run cmd, 0, False
