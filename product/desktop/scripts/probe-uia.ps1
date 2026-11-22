param(
    [Parameter(Mandatory = $true)][string]$Handle,
    [Parameter(Mandatory = $true)][int]$ExpectedProcessId,
    [Parameter(Mandatory = $true)][string]$OutputFile
)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
Add-Type @'
using System;
using System.Runtime.InteropServices;
public static class FocusWatchOwnedWindow {
    [DllImport("user32.dll")] public static extern uint GetWindowThreadProcessId(IntPtr hWnd, out uint processId);
    [DllImport("user32.dll")] public static extern bool IsWindowVisible(IntPtr hWnd);
}
'@
$nativeHandle = [IntPtr]::new([long]::Parse($Handle, [Globalization.CultureInfo]::InvariantCulture))
[uint32]$ownerProcessId = 0
[void][FocusWatchOwnedWindow]::GetWindowThreadProcessId($nativeHandle, [ref]$ownerProcessId)
if ($ownerProcessId -ne $ExpectedProcessId) { throw 'Target HWND does not belong to the expected report process.' }
if (-not [FocusWatchOwnedWindow]::IsWindowVisible($nativeHandle)) { throw 'Target report window is not visible.' }
# FromHandle confines inspection to this application's supplied native window.
# No RootElement/desktop discovery or interaction with other applications.
$reportRoot = [System.Windows.Automation.AutomationElement]::FromHandle($nativeHandle)
if ($null -eq $reportRoot) { throw 'Owned report UIA root is unavailable.' }
$elements = $reportRoot.FindAll([System.Windows.Automation.TreeScope]::Descendants, [System.Windows.Automation.Condition]::TrueCondition)
$controls = @($elements | ForEach-Object {
    [PSCustomObject]@{
        name = $_.Current.Name
        type = $_.Current.ControlType.ProgrammaticName
        enabled = $_.Current.IsEnabled
        focusable = $_.Current.IsKeyboardFocusable
    }
})
$document = @($controls | Where-Object { $_.type -eq 'ControlType.Document' })
$filter = @($controls | Where-Object { $_.type -eq 'ControlType.Edit' -and $_.name -eq 'Find an observation' -and $_.enabled -and $_.focusable })
$category = @($controls | Where-Object { $_.type -eq 'ControlType.Edit' -and $_.name -eq 'New category' -and $_.enabled -and $_.focusable })
$save = @($controls | Where-Object { $_.type -eq 'ControlType.Button' -and $_.name -eq 'Save category' -and $_.enabled -and $_.focusable })
$correct = @($controls | Where-Object { $_.type -eq 'ControlType.Button' -and $_.name -like '*synthetic-555*' -and $_.enabled -and $_.focusable })
$result = [PSCustomObject]@{
    status = 'pass'
    method = 'UIAutomationClient FromHandle; target HWND owner PID checked; inspected only own report descendants'
    process_id = $ExpectedProcessId
    visible_owned_window = $true
    document_count = $document.Count
    named_controls = @($filter + $category + $save + $correct)
}
if ($document.Count -lt 1 -or $filter.Count -lt 1 -or $category.Count -lt 1 -or $save.Count -lt 1 -or $correct.Count -lt 1) { $result.status = 'fail' }
$result | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $OutputFile -Encoding UTF8
if ($result.status -ne 'pass') { throw 'The owned report does not expose the required named UIA controls.' }
