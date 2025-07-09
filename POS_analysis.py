import streamlit as st
import pandas as pd
import plotly.express as px
from collections import Counter

# Streamlitページの基本設定
st.set_page_config(layout="wide", page_title="POSデータ分析ツール for Students")

# タイトルと説明
st.title("🎓 POSデータ分析ツール")
st.markdown("""
このツールはPOSデータをアップロードし、探索的な分析を行うためのアプリケーションです。
データから面白い発見をしたり、売上向上施策のアイデアを考えるきっかけになることを目指しています。
""")

# --- サイドバー: ファイルアップロードと設定 ---
st.sidebar.header("1. データアップロード")
uploaded_file = st.sidebar.file_uploader("CSVファイルをここにドラッグ＆ドロップするか、選択してください。", type=["csv"])

# --- メイン処理 ---
if uploaded_file is not None:
    try:
        # CSVファイルの読み込み (前回生成したデータはUTF-8-SIG)
        df = pd.read_csv(uploaded_file, encoding='utf-8-sig')
        st.sidebar.success("ファイルが正常に読み込まれました！")

        # --- データ前処理 ---
        # YYYY, MM, DD, hh, mm, ss から datetime オブジェクトを作成
        df['日時'] = pd.to_datetime(df['YYYY'].astype(str) + '-' +
                                   df['MM'].astype(str) + '-' +
                                   df['DD'].astype(str) + ' ' +
                                   df['hh'].astype(str).str.zfill(2) + ':' +
                                   df['mm'].astype(str).str.zfill(2) + ':' +
                                   df['ss'].astype(str).str.zfill(2))

        # 曜日フラグから曜日名へ変換 (1:月, ..., 7:日)
        day_map = {1: "月曜日", 2: "火曜日", 3: "水曜日", 4: "木曜日", 5: "金曜日", 6: "土曜日", 7: "日曜日"}
        df['曜日'] = df['曜日フラグ'].map(day_map)

        # 購入者属性フラグを分かりやすい名前に変換
        gender_map = {1: "男性", 2: "女性"}
        age_map = {1: "子供", 2: "若者", 3: "大人", 4: "実年"}
        df['性別'] = df['購入者性別フラグ'].map(gender_map).fillna("不明")
        df['年齢層'] = df['購入者年齢フラグ'].map(age_map).fillna("不明")

        st.sidebar.header("2. 分析メニュー選択")
        analysis_choice = st.sidebar.radio(
            "どの分析を見ますか？",
            ("データ全体の概要", "時間帯ごとの分析", "商品の売れ筋分析", "購買客の属性分析", "人気商品の組み合わせ分析（併売分析）")
        )
        st.sidebar.markdown("---")
        st.sidebar.info("💡 各分析結果の下には、分析のヒントや考えるポイントを記載しています。グループワークの参考にしてください。")


        # --- 分析結果の表示 ---
        st.header(f"📊 分析結果：{analysis_choice}")

        if analysis_choice == "データ全体の概要":
            st.subheader("📈 データ全体の基本情報")
            total_receipts = df['レシート番号'].nunique()
            total_sales_value = df['値段'].sum()
            total_items_sold = df['個数'].sum()
            avg_sales_per_receipt = total_sales_value / total_receipts if total_receipts > 0 else 0
            unique_products_count = df['購入商品名'].nunique()

            col1, col2, col3 = st.columns(3)
            col1.metric("総レシート数（客数）", f"{total_receipts:,}")
            col2.metric("総売上金額", f"¥{total_sales_value:,.0f}")
            col3.metric("総販売個数", f"{total_items_sold:,}")

            col4, col5, _ = st.columns(3)
            col4.metric("平均客単価", f"¥{avg_sales_per_receipt:,.0f}")
            col5.metric("取扱商品アイテム数", f"{unique_products_count:,}")


            st.subheader("📄 データの一部プレビュー（最初の100行）")
            st.dataframe(df.head(100))

            st.markdown("""
            **＜このデータから何がわかる？＞**
            - このお店は1日にどれくらいの人が来て、どれくらい売れているんだろう？
            """)

        elif analysis_choice == "時間帯ごとの分析":
            st.subheader("🕒 時間帯ごとの売れ行きを見てみよう")

            df['時間帯'] = df['hh'] # 時間帯は 'hh' カラムを使用

            # 1. 時間帯別 来店客数（レシート数）
            hourly_customers = df.groupby('時間帯')['レシート番号'].nunique().reset_index()
            hourly_customers.rename(columns={'レシート番号': '来店客数'}, inplace=True)
            fig_customers = px.bar(hourly_customers, x='時間帯', y='来店客数', title='時間帯別 来店客数',
                                   labels={'時間帯': '時間（時）', '来店客数': '購買客数'})
            fig_customers.update_xaxes(type='category') # 時間をカテゴリとして扱う
            st.plotly_chart(fig_customers, use_container_width=True)

            # 2. 時間帯別 売上金額
            hourly_sales = df.groupby('時間帯')['値段'].sum().reset_index()
            fig_sales = px.bar(hourly_sales, x='時間帯', y='値段', title='時間帯別 売上金額',
                               labels={'時間帯': '時間（時）', '値段': '売上金額 (円)'})
            fig_sales.update_xaxes(type='category')
            st.plotly_chart(fig_sales, use_container_width=True)

            # 3. 時間帯別 平均客単価
            hourly_avg_spend = pd.merge(hourly_sales, hourly_customers, on='時間帯')
            hourly_avg_spend['平均客単価'] = hourly_avg_spend['値段'] / hourly_avg_spend['来店客数']
            fig_avg_spend = px.line(hourly_avg_spend, x='時間帯', y='平均客単価', title='時間帯別 平均客単価',
                                    markers=True, labels={'時間帯': '時間（時）', '平均客単価': '一人あたりの平均購入金額 (円)'})
            fig_avg_spend.update_xaxes(type='category')
            st.plotly_chart(fig_avg_spend, use_container_width=True)

            st.markdown("""
            **＜このグラフから何がわかる？ 考えるヒント＞**
            - お店が一番混むのは何時ごろだろう？ その理由は何が考えられるか？ (例: オフィス街ならお昼休みや夕方？)
            - 売上が一番高い時間帯と、購買客数が一番多い時間帯は同じだろうか？ 違う場合はなぜ？
            - 一人のお客さんがたくさんお金を使うのは何時ごろか？ その時間帯には何が売れているだろう？
            - 購買客数が少ない時間帯にお店に来て(商品を購入して)もらうには、どのような工夫ができるだろう？ (例: タイムセール？、限定商品？)
            """)

        elif analysis_choice == "商品の売れ筋分析":
            st.subheader("🛍️ どんな商品が人気だろうか？")

            # 1. 売上金額トップ20商品
            top_sales_products = df.groupby('購入商品名')['値段'].sum().nlargest(20).reset_index()
            fig_top_sales = px.bar(top_sales_products, y='購入商品名', x='値段', orientation='h',
                                   title='売上金額 トップ20商品', labels={'購入商品名': '商品名', '値段': '売上金額 (円)'})
            fig_top_sales.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_sales, use_container_width=True)

            # 2. 販売数量トップ20商品
            top_quantity_products = df.groupby('購入商品名')['個数'].sum().nlargest(20).reset_index()
            fig_top_quantity = px.bar(top_quantity_products, y='購入商品名', x='個数', orientation='h',
                                      title='販売個数 トップ20商品', labels={'購入商品名': '商品名', '個数': '売れた数'})
            fig_top_quantity.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_quantity, use_container_width=True)

            # 3. 商品カテゴリ別 売上構成比
            category_sales = df.groupby('分類名')['値段'].sum().reset_index()
            fig_category_pie = px.pie(category_sales, values='値段', names='分類名',
                                      title='商品カテゴリ別 売上構成比 (どの種類のものがよく売れてる？)',
                                      hole=0.3) # ドーナツチャート風に
            st.plotly_chart(fig_category_pie, use_container_width=True)
            st.dataframe(category_sales.sort_values(by="値段", ascending=False))


            st.markdown("""
            **＜このグラフから何がわかる？ 考えるヒント＞**
            - 一番売れている商品のカテゴリーは何だろうか？ 理由として何が考えられる？ (例: みんなが知ってる人気商品？ お店のオリジナル商品？)
            - たくさん売れているけど、値段が安いから売上金額はそこそこの商品もあるだろうか？
            - 数量はそれほどだが、値段が高いから売上金額が大きい商品もあるかもしれない。
            - お店の売上の大部分を占めているのは、どの種類の商品カテゴリーだろうか？
            - もし新しい商品を置くとしたら、どのカテゴリーの商品がいいだろうか？
            """)

        elif analysis_choice == "購買客の属性分析":
            st.subheader("👥どんなお客さんが来ているだろうか？ (性別・年齢層)")

            col1, col2 = st.columns(2)
            with col1:
                # 性別ごとの分析
                st.markdown("#### 🙋‍♂️🙋‍♀️ 性別ごとの比較")
                gender_grouped = df.groupby('性別').agg(
                    来店客数=('レシート番号', 'nunique'),
                    総売上=('値段', 'sum')
                ).reset_index()
                if not gender_grouped.empty:
                    gender_grouped['平均客単価'] = gender_grouped['総売上'] / gender_grouped['来店客数']
                    st.dataframe(gender_grouped)
                    fig_gender_sales = px.pie(gender_grouped, values='総売上', names='性別', title='性別ごとの総売上シェア')
                    st.plotly_chart(fig_gender_sales, use_container_width=True)
                else:
                    st.write("性別データがありません。")

            with col2:
                # 年齢層ごとの分析
                st.markdown("#### 🎂 年齢層ごとの比較")
                age_grouped = df.groupby('年齢層').agg(
                    来店客数=('レシート番号', 'nunique'),
                    総売上=('値段', 'sum')
                ).reset_index()
                if not age_grouped.empty:
                    age_grouped['平均客単価'] = age_grouped['総売上'] / age_grouped['来店客数']
                    st.dataframe(age_grouped.sort_values(by="総売上", ascending=False))
                    fig_age_sales = px.bar(age_grouped, x='年齢層', y='総売上', title='年齢層ごとの総売上',
                                           category_orders={"年齢層": ["子供", "若者", "大人", "実年", "不明"]})
                    st.plotly_chart(fig_age_sales, use_container_width=True)
                else:
                    st.write("年齢層データがありません。")

            st.markdown("---")
            st.subheader("購買客の属性別 人気商品カテゴリ Top 5 (売上金額ベース)")

            # 性別ごとの人気商品カテゴリ
            st.markdown("#### 性別で人気のカテゴリは違う傾向を有するか？")
            gender_top_categories = df.groupby(['性別', '分類名'])['値段'].sum().reset_index()
            gender_top_categories = gender_top_categories.loc[gender_top_categories.groupby('性別')['値段'].nlargest(5).index.get_level_values(1)]
            if not gender_top_categories.empty:
                fig_gender_cat_sales = px.bar(gender_top_categories, x='分類名', y='値段', color='性別',
                                              title='性別 人気商品カテゴリ Top 5', barmode='group')
                st.plotly_chart(fig_gender_cat_sales, use_container_width=True)
                # 以下に注記を追加
                st.markdown("""
                > **💡グラフの読み方**
                > このグラフは「男性に人気のカテゴリTOP5」と「女性に人気のカテゴリTOP5」を個別に抽出し、並べて表示したものです。特定のカテゴリが片方の性別にしか表示されていない場合、データが存在しないわけではなく、売上ランキングが5位圏外であることを示しています。
                """)
            else:
                st.write("性別ごとの人気カテゴリデータが十分にありません。")

            # 年齢層ごとの人気商品カテゴリ
            st.markdown("#### 年齢層で人気のカテゴリは違うだろうか？")
            age_top_categories = df.groupby(['年齢層', '分類名'])['値段'].sum().reset_index()
            age_top_categories = age_top_categories.loc[age_top_categories.groupby('年齢層')['値段'].nlargest(5).index.get_level_values(1)]
            if not age_top_categories.empty:
                fig_age_cat_sales = px.bar(age_top_categories, x='分類名', y='値段', color='年齢層',
                                           title='年齢層別 人気商品カテゴリ Top 5', barmode='group',
                                           category_orders={"年齢層": ["子供", "若者", "大人", "実年", "不明"]})
                st.plotly_chart(fig_age_cat_sales, use_container_width=True)
            else:
                st.write("年齢層ごとの人気カテゴリデータが十分にありません。")


            st.markdown("""
            **＜このグラフから何がわかる？ 考えるヒント＞**
            - 男性と女性、どちらの購買客が多い？ 売上はどちらが高いだろうか？
            - 一番よく来てくれる年齢層は？ その年齢層はどんな商品をよく買っているだろうか？
            - 性別や年齢層によって、買いたいもの（人気カテゴリ）に違いはあるだろうか？
            - 特定のお客さん（例: 若い女性、働き盛りの男性）にもっとお店に来てもらうには、どんな商品をアピールすると良いだろうか？
            """)

        elif analysis_choice == "人気商品の組み合わせ分析（併売分析）":
            st.subheader("一緒によく買われる商品は何だろう？（簡易版）")
            st.markdown("ある商品を買った購買客が、他に何を買ったかを見てみよう！")

            # 商品リストを作成
            product_list = sorted(df['購入商品名'].unique())
            selected_product = st.selectbox("基準にする商品を選択:", product_list, index=0 if product_list else None)

            if selected_product:
                # 選択された商品が含まれるレシートIDを取得
                receipts_with_product = df[df['購入商品名'] == selected_product]['レシート番号'].unique()

                if len(receipts_with_product) > 0:
                    # それらのレシートに含まれる全ての商品を取得
                    concurrent_purchases_df = df[df['レシート番号'].isin(receipts_with_product)]
                    # 基準となった商品自体は除く
                    concurrent_purchases_df = concurrent_purchases_df[concurrent_purchases_df['購入商品名'] != selected_product]

                    if not concurrent_purchases_df.empty:
                        # 一緒に買われた商品をカウント
                        co_occurrence_counts = concurrent_purchases_df['購入商品名'].value_counts().nlargest(10).reset_index()
                        co_occurrence_counts.columns = ['一緒に買われた商品', '回数']

                        fig_co_occurrence = px.bar(co_occurrence_counts, y='一緒に買われた商品', x='回数', orientation='h',
                                                   title=f'「{selected_product}」と一緒によく買われた商品 Top 10')
                        fig_co_occurrence.update_layout(yaxis={'categoryorder':'total ascending'})
                        st.plotly_chart(fig_co_occurrence, use_container_width=True)
                        st.dataframe(co_occurrence_counts)
                    else:
                        st.write(f"「{selected_product}」は、他の商品とは一緒に買われていないか、単独で購入されています。")
                else:
                    st.write(f"「{selected_product}」の購入データがありません。")

            st.markdown("""
            **＜このグラフから何がわかる？ 考えるヒント＞**
            - 意外な組み合わせで買われているものはあるだろうか？ 新しい発見があるかもしれない！
            - 一緒に買われやすい商品同士を近くに並べてみたら、もっと売れるかもしれない？
            - セットにして少しお得に売ってみるのはどうだろう？
            """)

    except Exception as e:
        st.sidebar.error(f"エラーが発生しました: {e}")
        st.error(f"データを読み込むか処理する途中で問題が発生しました。もう一度試すか、CSVファイルを確認してください。\nエラー詳細: {e}")
        st.info("（ヒント：前回生成したCSVファイルと同じ形式ですか？ 文字コードはUTF-8-SIGがおすすめです。）")

else:
    st.info("👈 まずは左のサイドバーから、分析したいPOSデータのCSVファイルをアップロードしてください！")

st.markdown("---")