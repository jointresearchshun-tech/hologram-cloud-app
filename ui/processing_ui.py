def processing_ui():
    """メイン処理UI"""
    if not st.session_state.get("github_client"):
        st.warning("GitHub接続が必要です")
        return
    
    st.subheader("🔬 クラウド処理実行")
    
    github_client = st.session_state.github_client
    
    # 入力ファイル選択
    with st.spinner("ファイル一覧を取得中..."):
        model_files = github_client.list_files("models", [".pt", ".pth", ".pkl"])
    
    if not model_files:
        st.info("処理対象のモデルファイルがありません")
        return
    
    # ファイル選択UI
    selected_file_name = st.selectbox(
        "処理するモデルファイル:",
        [f["name"] for f in model_files]
    )
    
    model_file = next(f for f in model_files if f["name"] == selected_file_name)
    
    # ファイル情報表示
    st.write(f"**選択ファイル:** {model_file['name']}")
    st.write(f"**サイズ:** {model_file['size']:,} bytes ({model_file['size']/1024/1024:.1f} MB)")
    if model_file.get('encoding'):
        st.write(f"**エンコーディング:** {model_file['encoding']}")
    
    # 処理実行ボタン
    if st.button("🚀 処理開始", type="primary"):
        with st.spinner(f"'{model_file['name']}' をダウンロード中..."):
            # 進捗表示
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                # ダウンロード実行
                status_text.text("ファイルをダウンロード中...")
                progress_bar.progress(20)
                
                model_bytes = github_client.download_file(model_file)
                
                if model_bytes is None:
                    st.error("❌ ファイルのダウンロードに失敗しました")
                    st.info("以下を確認してください:")
                    st.info("• ファイルが存在するか")
                    st.info("• GitHubトークンに適切な権限があるか") 
                    st.info("• ネットワーク接続に問題がないか")
                    return
                
                progress_bar.progress(50)
                status_text.text(f"ダウンロード完了 ({len(model_bytes):,} bytes)")
                
                # ここで実際の処理を実行
                # process_model(model_bytes) など
                
                progress_bar.progress(100)
                status_text.text("処理完了！")
                st.success(f"✅ '{model_file['name']}' の処理が完了しました！")
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                logger.error(f"Processing error: {e}")
            finally:
                # プログレスバーをクリア
                progress_bar.empty()
                status_text.empty()

# デバッグ用のヘルパー関数
def debug_file_info():
    """ファイル情報をデバッグ表示"""
    if not st.session_state.get("github_client"):
        return
    
    st.subheader("🔍 ファイル情報デバッグ")
    
    github_client = st.session_state.github_client
    files = github_client.list_files("models")
    
    for file_info in files:
        with st.expander(f"📄 {file_info['name']}"):
            st.json(file_info)
            
            # ダウンロードテスト
            if st.button(f"ダウンロードテスト", key=f"test_{file_info['name']}"):
                with st.spinner("テスト中..."):
                    result = github_client.download_file(file_info)
                    if result:
                        st.success(f"✅ ダウンロード成功 ({len(result):,} bytes)")
                    else:
                        st.error("❌ ダウンロード失敗")
