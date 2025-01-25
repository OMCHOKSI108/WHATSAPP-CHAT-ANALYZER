import os
import streamlit as st
import preprocessor, helper
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

def convert_file_format(input_file, output_file):
    """Convert file format to the required structure."""
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
        st.error(f"Error converting file: {e}")
        return None

st.sidebar.title("WhatsApp Chat Analyzer")

uploaded_file = st.sidebar.file_uploader("Choose a file")
if uploaded_file is not None:
    # Save the uploaded file temporarily
    input_file_path = os.path.join("temp", uploaded_file.name)
    os.makedirs("temp", exist_ok=True)
    with open(input_file_path, "wb") as temp_file:
        temp_file.write(uploaded_file.getvalue())

    # Check and convert the file format if necessary
    converted_file_path = os.path.join("temp", f"{os.path.splitext(uploaded_file.name)[0]}_cnv.txt")
    input_file = input_file_path
    if convert_file_format(input_file, converted_file_path):
        data_file = converted_file_path
        st.success(f"File converted successfully. Using: {os.path.basename(data_file)}")
    else:
        data_file = input_file
        st.warning("Using the original file format as conversion failed.")

    # Read and preprocess the chat data
    with open(data_file, "r", encoding="utf-8") as file:
        data = file.read()

    df = preprocessor.preprocess(data)

    # Fetch unique users
    user_list = df['user'].unique().tolist()
    if 'group_notification' in user_list:
        user_list.remove('group_notification')
    user_list.sort()
    user_list.insert(0, "Overall")

    selected_user = st.sidebar.selectbox("Show analysis wrt", user_list)

    if st.sidebar.button("Show Analysis"):
        # Stats Area
        num_messages, words, num_media_messages, num_links = helper.fetch_stats(selected_user, df)
        st.title("Top Statistics")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.header("Total Messages")
            st.title(num_messages)
        with col2:
            st.header("Total Words")
            st.title(words)
        with col3:
            st.header("Media Shared")
            st.title(num_media_messages)
        with col4:
            st.header("Links Shared")
            st.title(num_links)

        # Monthly timeline
        st.title("Monthly Timeline")
        timeline = helper.monthly_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(timeline['time'], timeline['message'], color='green')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # Daily timeline
        st.title("Daily Timeline")
        daily_timeline = helper.daily_timeline(selected_user, df)
        fig, ax = plt.subplots()
        ax.plot(daily_timeline['only_date'], daily_timeline['message'], color='black')
        plt.xticks(rotation='vertical')
        st.pyplot(fig)

        # Activity map
        st.title('Activity Map')
        col1, col2 = st.columns(2)

        with col1:
            st.header("Most Busy Day")
            busy_day = helper.week_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_day.index, busy_day.values, color='purple')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        with col2:
            st.header("Most Busy Month")
            busy_month = helper.month_activity_map(selected_user, df)
            fig, ax = plt.subplots()
            ax.bar(busy_month.index, busy_month.values, color='orange')
            plt.xticks(rotation='vertical')
            st.pyplot(fig)

        # Heatmap
        st.title("Weekly Activity Map")
        user_heatmap = helper.activity_heatmap(selected_user, df)
        fig, ax = plt.subplots()
        sns.heatmap(user_heatmap, ax=ax)
        st.pyplot(fig)

        # Busiest users
        if selected_user == 'Overall':
            st.title('Most Busy Users')
            x, new_df = helper.most_busy_users(df)
            fig, ax = plt.subplots()

            col1, col2 = st.columns(2)

            with col1:
                ax.bar(x.index, x.values, color='red')
                plt.xticks(rotation='vertical')
                st.pyplot(fig)
            with col2:
                st.dataframe(new_df)

        # WordCloud
        st.title("WordCloud")
        df_wc = helper.create_wordcloud(selected_user, df)
        fig, ax = plt.subplots()
        ax.imshow(df_wc)
        st.pyplot(fig)

        # Most common words
        most_common_df = helper.most_common_words(selected_user, df)
        fig, ax = plt.subplots()
        ax.barh(most_common_df[0], most_common_df[1], color='skyblue')
        plt.xticks(rotation='vertical')
        st.title('Most Common Words')
        st.pyplot(fig)

        # Emoji analysis
        emoji_df = helper.emoji_helper(selected_user, df)
        st.title("Emoji Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.dataframe(emoji_df)
        with col2:
            fig, ax = plt.subplots()
            ax.pie(emoji_df['count'].head(), labels=emoji_df['emoji'].head(), autopct="%0.2f")
            st.pyplot(fig)
