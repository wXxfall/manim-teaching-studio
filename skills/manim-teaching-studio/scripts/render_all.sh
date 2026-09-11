#!/usr/bin/env bash
# 批量渲染全部场景(低清/高清两档),日志 + rc 记录 + ffprobe 实测时长,失败不中断。
#
# Run:
#   render_all.sh <project_path> --quality low|high [--only scene01,scene02]
#
# low 档:export MANIM_LOW_RES=1(480x854@15,画面审查用,快)
# high 档:1080p60 成片
# 场景清单从 <project_path>/spec_lock.md 的 "## scenes" 节解析(dir= 与 class=)。

set -u
# ffmpeg 查找:PATH 优先;否则 FFMPEG_DIR 环境变量(指向含 ffmpeg 的目录)
if ! command -v ffmpeg >/dev/null 2>&1 && [ -n "${FFMPEG_DIR:-}" ]; then
  if [ -x "$FFMPEG_DIR/ffmpeg" ] || [ -x "$FFMPEG_DIR/ffmpeg.exe" ]; then
    export PATH="$FFMPEG_DIR:$PATH"
  fi
fi

PROJECT=""
QUALITY=""
ONLY=""

while [ $# -gt 0 ]; do
  case "$1" in
    --quality) QUALITY="$2"; shift 2 ;;
    --only)    ONLY="$2"; shift 2 ;;
    *)         PROJECT="$1"; shift ;;
  esac
done

if [ -z "$PROJECT" ] || [ "$QUALITY" != "low" ] && [ "$QUALITY" != "high" ]; then
  echo "用法: render_all.sh <project_path> --quality low|high [--only scene01,scene02]"
  exit 1
fi

# 转绝对路径:场景渲染在子目录中运行,相对路径的 LOG/DUR_FILE 会失效
case "$PROJECT" in
  /*) ;;
  *) PROJECT="$(pwd)/$PROJECT" ;;
esac

SPEC="$PROJECT/spec_lock.md"
if [ ! -f "$SPEC" ]; then
  echo "[错误] 未找到 $SPEC"
  exit 1
fi

LOG_DIR="$PROJECT/render_log"
DUR_FILE="$LOG_DIR/durations.tsv"
mkdir -p "$LOG_DIR"
LOG="$LOG_DIR/render_${QUALITY}.log"
: > "$LOG"
echo "scene	dir	class	rc	duration_s" > "$DUR_FILE"

run() {
  local dir="$1" cls="$2" idx="$3"
  local file="$PROJECT/scenes/$dir/main.py"
  if [ ! -f "$file" ]; then
    echo "[跳过] $idx $dir: 无 $file" | tee -a "$LOG"
    return
  fi
  local t0 t1 rc
  t0=$(date +%s)
  echo "[渲染] $idx $dir $cls $(date '+%H:%M:%S')" | tee -a "$LOG"
  if [ "$QUALITY" = "low" ]; then
    export MANIM_LOW_RES=1
    (cd "$PROJECT/scenes/$dir" && manim -ql main.py "$cls" >> "$LOG" 2>&1)
  else
    unset MANIM_LOW_RES
    (cd "$PROJECT/scenes/$dir" && manim -qh main.py "$cls" >> "$LOG" 2>&1)
  fi
  rc=$?
  t1=$(date +%s)
  echo "[完成] $idx $dir rc=$rc 耗时 $((t1 - t0))s" | tee -a "$LOG"
  # ffprobe 实测时长
  local mp4
  if [ "$QUALITY" = "low" ]; then
    mp4=$(ls "$PROJECT/scenes/$dir/media/videos/main/480p15/$cls.mp4" 2>/dev/null | head -1)
  else
    mp4=$(ls "$PROJECT/scenes/$dir/media/videos/main/1080p60/$cls.mp4" 2>/dev/null | head -1)
  fi
  local dur=""
  if [ -n "$mp4" ]; then
    # 用 ffmpeg -i 的 stderr 解析 Duration(不依赖 ffprobe)
    dur=$(ffmpeg -i "$mp4" 2>&1 | sed -n 's/.*Duration: \([0-9]*\):\([0-9]*\):\([0-9.]*\).*/\1 \2 \3/p' | head -1 | awk '{printf "%.2f", $1*3600+$2*60+$3}')
  fi
  echo "$idx	$dir	$cls	$rc	$dur" >> "$DUR_FILE"
}

idx=1
total=0
fails=0
in_scenes=0
while IFS= read -r line; do
  case "$line" in
    "## scenes") in_scenes=1; continue ;;
    "## "*)      in_scenes=0; continue ;;
  esac
  if [ "$in_scenes" != "1" ]; then
    continue
  fi
  case "$line" in
    "- scene"*)
      idx_num=$(echo "$line" | sed 's/^- scene0*//; s/:.*//')
      dir=$(echo "$line" | sed 's/.*dir=\([^,]*\).*/\1/')
      cls=$(echo "$line" | sed 's/.*class=\([^,]*\).*/\1/')
      key="scene$(printf '%02d' "$idx_num")"
      if [ -n "$ONLY" ]; then
        case ",$ONLY," in
          *",$key,"*) ;;
          *) continue ;;
        esac
      fi
      run "$dir" "$cls" "$key"
      total=$((total + 1))
      last_rc=$(tail -1 "$DUR_FILE" | cut -f4)
      [ "$last_rc" != "0" ] && fails=$((fails + 1))
      ;;
  esac
done < "$SPEC"

echo ""
echo "===== 汇总:$total 场景,失败 $fails ====="
grep -v "^scene	" "$DUR_FILE" || true
