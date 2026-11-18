#!/usr/bin/env pwsh
# Kailasa Temple Documentary — Video Assembly Script
# Input:  output/scenes/scene_1.png ... scene_8.png  (exact extension detected)
# Output: output/kailasa_temple_documentary.mp4
#
# Spec: 9:16 vertical, 4K (2160x3840), 24 fps, ~50 s total,
#       dark golden cinematic grading, cross-fade transitions,
#       slow Ken Burns zoom/pan per scene, no audio, no text/overlay.

$ErrorActionPreference = "Stop"

# ── Configuration ──────────────────────────────────────────────────────────
$width     = 2160
$height    = 3840
$fps       = 24
$scene_dur = 6.5          # seconds per scene
$trans_dur = 0.5          # cross-fade duration (seconds)
$total     = 8            # number of scenes
$out_file  = "output/kailasa_temple_documentary.mp4"
$scene_dir = "output/scenes"

# Dark golden cinematic colour grading:
#   curves  → lift shadows, warm highlights
#   colorbalance → slight red/yellow push, less blue
#   eq      → saturation, contrast tweak
$color_grade = @"
curves=preset=luma:r='0/0 0.25/0.18 0.5/0.52 0.75/0.78 1/1':g='0/0 0.25/0.20 0.5/0.56 0.75/0.81 1/1':b='0/0 0.25/0.15 0.5/0.48 0.75/0.72 1/1',
colorbalance=rs=0.12:gs=0.04:bs=-0.12,
eq=saturation=1.15:brightness=0.02:contrast=1.12
"@

# ── Detect actual scene file extensions ────────────────────────────────────
$scene_files = @()
for ($i = 1; $i -le $total; $i++) {
    $candidates = Get-ChildItem -Path $scene_dir -Filter "scene_$i.*" |
                  Where-Object { $_.Extension -in @('.png','.jpg','.jpeg','.webp') }
    if ($candidates.Count -eq 0) {
        Write-Error "No scene file found for scene_$i in $scene_dir"
    }
    $scene_files += $candidates[0].FullName
}

Write-Host "Found $($scene_files.Count) scene files:"

# ── Phase 1: Create individual segments with slow Ken Burns zoom/pan ───────
$segments = @()
$seg_dir  = Join-Path $scene_dir "segments"
if (-not (Test-Path $seg_dir)) { New-Item -ItemType Directory -Path $seg_dir | Out-Null }

$frames_per_scene = [int]($scene_dur * $fps)

for ($i = 0; $i -lt $total; $i++) {
    $in_file  = $scene_files[$i]
    $seg_file = Join-Path $seg_dir "seg_$([int]($i+1)).mp4"
    $segments += $seg_file

    if (-not (Test-Path $seg_file)) {
        Write-Host "Phase 1 — segment $([int]($i+1))/$total: $seg_file"
        ffmpeg -hide_banner -loglevel error -y `
            -loop 1 -i $in_file `
            -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p -t $scene_dur `
            -vf "scale=$width`:`$height:force_original_aspect_ratio=increase,crop=$width`:`$height,`$
                  zoompan=z='min(zoom+0.0012,1.25)':x='iw/2-(iw/zoom)/2':y='ih/2-(ih/zoom)/2':`$
                  d=$frames_per_scene:s=$width`x$height:fps=$fps" `
            -an $seg_file
    } else {
        Write-Host "  (skipping, already exists) $seg_file"
    }
}

# ── Phase 2: Build xfade filter chain for cross-fade transitions ───────────
# Each xfade consumes two inputs and produces one. Chain them sequentially.
# offset_i = cumulative_duration_before_transition - trans_dur

$filter_parts = @()
$label_prev = "[0:v]"
$cum_dur    = $scene_dur   # duration accumulated before next transition

for ($i = 1; $i -lt $total; $i++) {
    $in_label = "[$i:v]"
    $out_label = "[v$i]"
    $offset = [math]::Round($cum_dur - $trans_dur, 3)

    $xfade = "$label_prev$in_labelxfade=transition=fade:duration=$trans_dur:offset=$offset$out_label"
    $filter_parts += $xfade

    $label_prev = $out_label
    $cum_dur    = [math]::Round($cum_dur + $scene_dur - $trans_dur, 3)
}

# Append colour grading to the final label
$final_label = $label_prev.Trim('[]')   # e.g. v7
$grade_filter = "[$final_label]$color_grade,[vout]"

$filter_complex = ($filter_parts -join ';') + ';' + $grade_filter

Write-Host "`nPhase 2 — assembling final video with xfade transitions + colour grading"
Write-Host "Filter complex length: $($filter_complex.Length) chars"
Write-Host "Estimated total duration: $([math]::Round($cum_dur, 2)) s"

# ── Phase 3: Run ffmpeg assembly ───────────────────────────────────────────
$input_args = @()
for ($i = 0; $i -lt $total; $i++) {
    $input_args += "-i"
    $input_args += $segments[$i]
}

ffmpeg -hide_banner -loglevel error -y `
    $input_args `
    -filter_complex $filter_complex `
    -map "[vout]" `
    -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p -r $fps `
    -an `
    $out_file

if (Test-Path $out_file) {
    Write-Host "`n✓ Video created: $out_file"
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration -of csv=p=0 $out_file
} else {
    Write-Error "Output video was not created: $out_file"
}
