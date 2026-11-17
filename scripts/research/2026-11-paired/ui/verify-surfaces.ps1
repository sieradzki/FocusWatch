param([Parameter(Mandatory=$true)][string]$ResultsDir)
$ErrorActionPreference='Stop'
Add-Type -AssemblyName System.Drawing
$proofs=@()
foreach($runtime in @('avalonia','electron')) {
  $case=Get-ChildItem -LiteralPath $ResultsDir -Directory | Where-Object Name -Like "*-$runtime" | Sort-Object Name | Select-Object -First 1
  if(-not $case) { throw "No case for $runtime" }
  $beforePath=Join-Path $case.FullName 'surface-before.png'
  $afterPath=Join-Path $case.FullName 'surface-after.png'
  $before=[System.Drawing.Bitmap]::new($beforePath)
  $after=[System.Drawing.Bitmap]::new($afterPath)
  try {
    if($before.Size -ne $after.Size) { throw 'Before/after image sizes differ' }
    $scale=(Get-Content -Raw -LiteralPath (Join-Path $case.FullName 'ready.json') | ConvertFrom-Json).render_scaling
    if(-not $scale) { $scale=1 } # Original pilot did not log scale.
    $beforePurple=0;$afterPurple=0;$transitions=0
    $left=$before.Width;$right=-1;$top=$before.Height;$bottom=-1
    for($y=[int](140*$scale);$y -lt [Math]::Min($before.Height,[int](280*$scale));$y++) {
      for($x=[int](20*$scale);$x -lt [Math]::Min($before.Width-20,[int](880*$scale));$x++) {
        $a=$before.GetPixel($x,$y);$b=$after.GetPixel($x,$y)
        $aPurple=$a.R -eq 139 -and $a.G -eq 63 -and $a.B -eq 186
        $bPurple=$b.R -eq 139 -and $b.G -eq 63 -and $b.B -eq 186
        if($aPurple) { $beforePurple++ };if($bPurple) { $afterPurple++ }
        if($a.R -eq 37 -and $a.G -eq 99 -and $a.B -eq 235 -and $bPurple) {
          $transitions++;$left=[Math]::Min($left,$x);$right=[Math]::Max($right,$x);$top=[Math]::Min($top,$y);$bottom=[Math]::Max($bottom,$y)
        }
      }
    }
    if($transitions -lt 50 -or $afterPurple -le $beforePurple) { throw "No verified axis correction for $runtime" }
    if(($right-$left) -gt 20*$scale -or ($bottom-$top) -gt 30*$scale) { throw 'Unexpected correction extent' }
    $cx=[int][Math]::Floor(($left+$right)/2);$cy=[int][Math]::Floor(($top+$bottom)/2)
    $a=$before.GetPixel($cx,$cy);$b=$after.GetPixel($cx,$cy)
    $beforeRgb='#{0:x2}{1:x2}{2:x2}' -f $a.R,$a.G,$a.B
    $afterRgb='#{0:x2}{1:x2}{2:x2}' -f $b.R,$b.G,$b.B
    if($beforeRgb -ne '#2563eb' -or $afterRgb -ne '#8b3fba') { throw 'Wrong selected block center colors' }
    $proofs += [PSCustomObject]@{runtime=$runtime;case=$case.Name;image_width=$before.Width;image_height=$before.Height;axis_region_logical=@(20,140,880,280);before_purple_pixels=$beforePurple;after_purple_pixels=$afterPurple;blue_to_learning_pixels=$transitions;changed_bounds=@($left,$top,$right,$bottom);center=@($cx,$cy);before_rgb=$beforeRgb;after_rgb=$afterRgb;before_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $beforePath).Hash;after_sha256=(Get-FileHash -Algorithm SHA256 -LiteralPath $afterPath).Hash}
  } finally { $before.Dispose();$after.Dispose() }
}
$proofs | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $ResultsDir 'pixel-proof.json') -Encoding utf8
$proofs | Select-Object runtime,center,before_rgb,after_rgb,blue_to_learning_pixels | ConvertTo-Json -Depth 4
