import streamlit as st
import matplotlib.pyplot as plt
import matplotlib
import matplotlib.font_manager as fm
from datetime import date, datetime, time
import json
import os
import math
import random

# フォント設定
matplotlib.rcParams['font.family'] = 'Meiryo'

# ファイル・ディレクトリ定義
SCHEDULE_FILE = "schedule.json"
DIARY_FILE = "diary.json"
MOOD_FILE = "mood.json"
MEDIA_DIR = "media"

# ページ設定
st.set_page_config(page_title="予定管理アプリ", layout="centered")
st.title("📅 予定管理アプリ")

# ファイル読み込み
def load_json(filename):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

schedule = load_json(SCHEDULE_FILE)
diary = load_json(DIARY_FILE)
mood_data = load_json(MOOD_FILE)

if not os.path.exists(MEDIA_DIR):
    os.makedirs(MEDIA_DIR)

# 日付選択
selected_date = st.date_input("📆 日付を選んでください", value=date.today())
date_str = selected_date.isoformat()

# 古い形式の修正
for items in schedule.values():
    for item in items:
        if "time_range" in item and ("start" not in item or "end" not in item):
            try:
                item["start"], item["end"] = item["time_range"].split("-")
            except:
                continue
with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
    json.dump(schedule, f, ensure_ascii=False, indent=2)

# サイドバー（セクション表示のみ・リンクなし）
sections = {
    "fortune": "🔮 運勢くじ",
    "add_schedule": "📝 予定の入力",
    "mood": "😊 気分スタンプ",
    "list_graph": "📋 予定一覧とグラフ",
    "delete_schedule": "🗑️ 予定削除",
    "diary": "📖 日記の記入",
    "media": "📸 メディア添付",
    "delete_media": "🗑️ メディア削除"
}

st.sidebar.title("📚 セクション一覧")
for label in sections.values():
    st.sidebar.write(label)


# セクション描画関数定義
def anchor(title, anchor_id):
    st.markdown(f'<h2 id="{anchor_id}">{title}</h2>', unsafe_allow_html=True)

def show_fortune():
    anchor("🔮 今日の運勢くじ", "fortune")
    if st.button("くじを引く"):
        fortune = random.choice(["🎉 大吉", "😊 中吉", "😐 小吉", "😥 凶", "💀 大凶"])
        st.success(f"あなたの今日の運勢は… {fortune}！")

def add_schedule():
    anchor(f"📝 {selected_date} の予定入力", "add_schedule")
    with st.form("add_schedule"):
        activity = st.text_input("アクティビティ（例：勉強）")
        col1, col2 = st.columns(2)
        with col1:
            start_hour = st.selectbox("開始時間（時）", list(range(0, 24)))
            start_min = st.selectbox("開始時間（分）", list(range(0, 60, 10)))
        with col2:
            end_hour = st.selectbox("終了時間（時）", list(range(0, 24)))
            end_min = st.selectbox("終了時間（分）", list(range(0, 60, 10)))
        submitted = st.form_submit_button("追加")

        if submitted:
            start_time = time(start_hour, start_min)
            end_time = time(end_hour, end_min)
            if end_time <= start_time:
                st.error("終了時間は開始時間より後にしてください。")
            else:
                duration = (datetime.combine(date.today(), end_time) - datetime.combine(date.today(), start_time)).total_seconds() / 3600
                if date_str not in schedule:
                    schedule[date_str] = []
                conflict = any(item.get("start") == start_time.strftime("%H:%M") and item.get("end") == end_time.strftime("%H:%M") for item in schedule[date_str])
                if conflict:
                    st.warning("⚠️ 同じ時間帯の予定がすでに登録されています。")
                else:
                    schedule[date_str].append({
                        "activity": activity.strip(),
                        "start": start_time.strftime("%H:%M"),
                        "end": end_time.strftime("%H:%M"),
                        "duration": duration
                    })
                    with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                        json.dump(schedule, f, ensure_ascii=False, indent=2)
                    st.success(f"✅ 追加されました: {activity.strip()}")

def mood_stamp():
    anchor("😊 今日の気分スタンプ", "mood")
    mood_options = {
        "😄 とても良い": "😄",
        "😊 良い": "😊",
        "😐 普通": "😐",
        "😟 悪い": "😟",
        "😭 とても悪い": "😭"
    }
    current_mood = mood_data.get(date_str, "")
    selected_mood_label = st.selectbox(
        "今日の気分を選んでください", 
        list(mood_options.keys()),
        index=list(mood_options.values()).index(current_mood) if current_mood in mood_options.values() else 2
    )
    selected_mood = mood_options[selected_mood_label]
    if st.button("気分を保存"):
        mood_data[date_str] = selected_mood
        with open(MOOD_FILE, "w", encoding="utf-8") as f:
            json.dump(mood_data, f, ensure_ascii=False, indent=2)
        st.success(f"気分スタンプ「{selected_mood}」を保存しました！")

def show_schedule_and_graph():
    anchor("📋 予定一覧とグラフ", "list_graph")
    items = sorted(schedule.get(date_str, []), key=lambda x: x.get("start", "00:00"))
    if items:
        for i, item in enumerate(items, start=1):
            st.write(f"{i}. {item['activity']} - {item['start']}〜{item['end']} ({item['duration']:.2f}時間)")

        st.subheader("🕓 24時間予定グラフ")
        fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(6, 6))
        for item in items:
            start_h, start_m = map(int, item["start"].split(":"))
            end_h, end_m = map(int, item["end"].split(":"))
            start_angle = (start_h + start_m / 60) / 24 * 2 * math.pi
            end_angle = (end_h + end_m / 60) / 24 * 2 * math.pi
            width = end_angle - start_angle
            ax.bar(x=start_angle, height=1, width=width, alpha=0.6, label=item["activity"])
        ticks = [i * 2 * math.pi / 24 for i in range(24)]
        labels = [f"{i}:00" for i in range(24)]
        ax.set_xticks(ticks)
        ax.set_xticklabels(labels)
        ax.set_yticklabels([])
        ax.set_theta_zero_location("N")
        ax.set_theta_direction(-1)
        ax.set_title(f"{selected_date} の予定（24時間）")
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1))
        st.pyplot(fig)
    else:
        st.info("この日の予定はまだありません。")

def delete_schedule():
    anchor("🗑️ 予定削除", "delete_schedule")
    items = sorted(schedule.get(date_str, []), key=lambda x: x.get("start", "00:00"))
    if items:
        option_labels = [f"{i+1}. {item['activity']} ({item['start']}〜{item['end']})" for i, item in enumerate(items)]
        delete_index = st.selectbox("削除する予定を選択", options=range(len(items)), format_func=lambda i: option_labels[i])
        if st.button("選択した予定を削除"):
            removed = schedule[date_str].pop(delete_index)
            with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
                json.dump(schedule, f, ensure_ascii=False, indent=2)
            st.success(f"削除しました: {removed['activity']}")
    else:
        st.info("この日の予定はまだありません。")

def write_diary():
    anchor("📖 日記の記入", "diary")
    diary_text = st.text_area("今日の振り返りを記入してください", value=diary.get(date_str, ""))
    if st.button("日記を保存"):
        diary[date_str] = diary_text
        with open(DIARY_FILE, "w", encoding="utf-8") as f:
            json.dump(diary, f, ensure_ascii=False, indent=2)
        st.success("日記を保存しました！")

def add_media():
    anchor("📸 メディア添付", "media")
    uploaded_files = st.file_uploader("画像または動画をアップロード", type=["png", "jpg", "jpeg", "mp4", "mov"], accept_multiple_files=True)
    media_files = diary.get(f"{date_str}_media", [])
    for uploaded_file in uploaded_files or []:
        file_path = os.path.join(MEDIA_DIR, f"{date_str}_{uploaded_file.name}")
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        media_files.append(file_path)
        st.success(f"{uploaded_file.name} を保存しました。")
    if media_files:
        diary[f"{date_str}_media"] = media_files
        with open(DIARY_FILE, "w", encoding="utf-8") as f:
            json.dump(diary, f, ensure_ascii=False, indent=2)
        st.subheader("📂 添付メディア")
        for file_path in media_files:
            if file_path.lower().endswith((".png", ".jpg", ".jpeg")):
                st.image(file_path, use_column_width=True)
            elif file_path.lower().endswith((".mp4", ".mov")):
                st.video(file_path)

def delete_media():
    anchor("🗑️ メディア削除", "delete_media")
    media_files = diary.get(f"{date_str}_media", [])
    if media_files:
        delete_file = st.selectbox("削除したいメディアを選択してください", options=media_files)
        if st.button("選択したメディアを削除"):
            try:
                os.remove(delete_file)
                media_files.remove(delete_file)
                diary[f"{date_str}_media"] = media_files
                with open(DIARY_FILE, "w", encoding="utf-8") as f:
                    json.dump(diary, f, ensure_ascii=False, indent=2)
                st.success("メディアを削除しました。")
            except Exception as e:
                st.error(f"削除中にエラーが発生しました: {e}")
    else:
        st.info("この日のメディアはまだありません。")

# 全セクション表示
show_fortune()
add_schedule()
mood_stamp()
show_schedule_and_graph()
delete_schedule()
write_diary()
add_media()
delete_media()