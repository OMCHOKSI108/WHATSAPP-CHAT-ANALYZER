import os
import streamlit as st
import preprocessor
import helper
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------- File Converter ----------------

def convert_file_format(input_file, output_file):
    """Convert WhatsApp export format to required format."""
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            lines = file.readlines()

        def convert_time_date_format(line):
            try:
                timestamp, rest = line.split(" - ", 1)
                date, time_am_pm = timestamp.split(", ")

                date_full = datetime.strptime(date, "%d/%m/%y").strftime("%d/%m/%Y")
                time_24hr = datetime.strptime(time_am_pm.strip(), "%I:%M %p").strftime("%H:%M")

                return f"{date_full}, {time_24hr} - {rest}"
            except ValueError:
                return line

        converted_lines = [convert_time_date_format(line) for line in lines]

        with open(output_file, "w", encoding="utf-8") as file:
            file.writelines(converted_lines)

        return output_file

    except Exception as e:
        st.error(f"File conversion error: {e}")
        return None

# ---------------- Streamlit Sidebar ----------------

st.sidebar.title("📊 WhatsApp Chat Analyzer")
uploaded_file = st.sidebar.file_uploader("Upload WhatsApp Chat (.txt)")

if uploaded_file is not None:
    os.makedirs("temp", exist_ok=True)

    input_file_path = os.path.join("temp", uploaded_file.name)

    with open(input_file_path, "wb") as f:
        f.write(uploaded_file.getvalue())

    converted_file_path = os.path.join(
        "temp", f"{os.path.splitext(uploaded_file.name)[0]}_cnv.txt"
    )

    if convert_file_format(input_file_path, converted_file_path):
        data_file = converted_file_path
        st.success("File converted successfully")
    else:
        data_file = input_file_path
        st.warning("Using original file format")

    # ---------------- Read Chat ----------------
    with open(data_file, "r", encoding="utf-8") as f:
        data = f.read()

    df = preprocessor.preprocess(data)

    # ---------------- User List ----------------
    user_list = df["user"].unique().tolist()

    if "group_notification" in user_list:
        user_list.remove("group_notification")

    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show Analysis For", user_list)

    if st.sidebar.button("Show Analysis"):
        # ---------------- Top Stats ----------------
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)

        st.title("📈 Top Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.header("Messages")
            st.title(num_messages)

        with col2:
            st.header("Words")
            st.title(words)

        with col3:
            st.header("Media")
            st.title(num_media_messages)

        with col4:
            st.header("Links")
            st.title(num_links)

        # ---------------- Monthly Timeline ----------------
        st.title("📅 Monthly Timeline")

        timeline = helper.monthly_timeline(selected_user, df)

        if not timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(timeline["time"], timeline["message"])
            plt.xticks(rotation=90)
            st.pyplot(fig)
        else:
            st.info("No monthly timeline data")

        # ---------------- Daily Timeline ----------------
        st.title("📆 Daily Timeline")

        daily_timeline = helper.daily_timeline(selected_user, df)

        if not daily_timeline.empty:
            fig, ax = plt.subplots()
            ax.plot(daily_timeline["only_date"], daily_timeline["message"])
            plt.xticks(rotation=90)
            st.pyplot(fig)
        else:
            st.info("No daily timeline data")

        # ---------------- Activity Map ----------------
        st.title("🗓 Activity Map")

        col1, col2 = st.columns(2)

        with col1:
            st.header("Most Busy Day")

            busy_day = helper.week_activity_map(selected_user, df)

            if not busy_day.empty:
                fig, ax = plt.subplots()
                ax.bar(busy_day.index, busy_day.values)
                plt.xticks(rotation=90)
                st.pyplot(fig)
            else:
                st.info("No data available")

        with col2:
            st.header("Most Busy Month")

            busy_month = helper.month_activity_map(selected_user, df)

            if not busy_month.empty:
                fig, ax = plt.subplots()
                ax.bar(busy_month.index, busy_month.values)
                plt.xticks(rotation=90)
                st.pyplot(fig)
            else:
                st.info("No data available")

        # ---------------- Heatmap ----------------
        st.title("🔥 Weekly Activity Heatmap")

        user_heatmap = helper.activity_heatmap(selected_user, df)

        if user_heatmap.empty:
            st.warning("No heatmap data available")
        else:
            fig, ax = plt.subplots()
            sns.heatmap(user_heatmap, ax=ax)
            st.pyplot(fig)

        # ---------------- Most Busy Users ----------------
        if selected_user == "Overall" and len(user_list) > 2:
            st.title("👥 Most Busy Users")

            x, new_df = helper.most_busy_users(df)

            col1, col2 = st.columns(2)

            with col1:
                fig, ax = plt.subplots()
                ax.bar(x.index, x.values)
                plt.xticks(rotation=90)
                st.pyplot(fig)

            with col2:
                st.dataframe(new_df)

        # ---------------- WordCloud ----------------
        st.title("☁ WordCloud")

        df_wc = helper.create_wordcloud(selected_user, df)

        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        ax.axis("off")
        st.pyplot(fig)

        # ---------------- Most Common Words ----------------
        st.title("🔤 Most Common Words")

        most_common_df = helper.most_common_words(selected_user, df)

        if not most_common_df.empty:
            fig, ax = plt.subplots()
            ax.barh(most_common_df[0], most_common_df[1])
            plt.xticks(rotation=90)
            st.pyplot(fig)

        # ---------------- Emoji Analysis ----------------
        st.title("😂 Emoji Analysis")

        emoji_df = helper.emoji_helper(selected_user, df)

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(emoji_df)

        with col2:
            if not emoji_df.empty:
                fig, ax = plt.subplots()
                ax.pie(
                    emoji_df["count"].head(),
                    labels=emoji_df["emoji"].head(),
                    autopct="%0.2f%%",
                )
                st.pyplot(fig)
