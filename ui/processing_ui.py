def processing_ui():
    """メイン処理UI - エラーハンドリングを強化"""
    if not st.session_state.get("github_client"):
        st.warning("GitHub接続が必要です")
        return
    
    st.subheader("🔬 クラウド処理実行")
    
    github_client = st.session_state.github_client
    
    # ファイル一覧取得
    with st.spinner("ファイル一覧を取得中..."):
        try:
            model_files = github_client.list_files("models", [".pt", ".pth", ".pkl"])
        except Exception as e:
            st.error(f"ファイル一覧の取得に失敗しました: {e}")
            return
    
    if not model_files:
        st.info("処理対象のモデルファイルがありません")
        return
    
    # ファイル選択
    selected_file_name = st.selectbox(
        "処理するモデルファイル:",
        [f["name"] for f in model_files],
        help="処理したいモデルファイルを選択してください"
    )
    
    # 選択されたファイル情報
    try:
        model_file = next(f for f in model_files if f["name"] == selected_file_name)
    except StopIteration:
        st.error("選択されたファイルが見つかりません")
        return
    
    # ファイル情報表示
    st.write(f"**選択ファイル:** {model_file['name']}")
    st.write(f"**サイズ:** {model_file['size']:,} bytes ({model_file['size']/1024/1024:.1f} MB)")
    st.write(f"**エンコーディング:** {model_file.get('encoding', 'unknown')}")
    
    # ダウンロード可能性チェック
    download_methods = []
    if model_file.get('download_url'):
        download_methods.append("✅ Direct download URL")
    if model_file.get('url'):
        download_methods.append("✅ Contents API")
    if model_file.get('path'):
        download_methods.append("✅ Raw content URL")
    
    if download_methods:
        with st.expander("📡 利用可能なダウンロード方法"):
            for method in download_methods:
                st.write(method)
    else:
        st.warning("⚠️ ダウンロード方法が利用できません")
    
    # 処理実行
    if st.button("🚀 処理開始", type="primary"):
        with st.spinner(f"'{model_file['name']}' をダウンロード中..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            try:
                status_text.text("ファイルをダウンロード中...")
                progress_bar.progress(10)
                
                # ダウンロード実行
                model_bytes = github_client.download_file(model_file)
                
                if model_bytes is None:
                    st.error("❌ ファイルのダウンロードに失敗しました")
                    
                    # デバッグ情報表示
                    with st.expander("🔍 デバッグ情報"):
                        st.json(model_file)
                        st.write("**対処方法:**")
                        st.write("1. ファイルサイズが大きすぎる可能性があります")
                        st.write("2. GitHubトークンの権限を確認してください")
                        st.write("3. ファイルが破損している可能性があります")
                    
                    return
                
                progress_bar.progress(50)
                status_text.text(f"ダウンロード完了 ({len(model_bytes):,} bytes)")
                
                # ここで実際の処理を実行
                # TODO: 実際の処理ロジックを実装
                progress_bar.progress(80)
                status_text.text("処理中...")
                
                # 仮の処理時間
                import time
                time.sleep(1)
                
                progress_bar.progress(100)
                status_text.text("処理完了！")
                
                st.success(f"✅ '{model_file['name']}' の処理が完了しました！")
                st.info(f"処理されたデータサイズ: {len(model_bytes):,} bytes")
                
            except Exception as e:
                st.error(f"❌ エラーが発生しました: {str(e)}")
                logger.error(f"Processing error: {e}", exc_info=True)
                
                # 詳細なエラー情報
                with st.expander("🔍 エラー詳細"):
                    st.text(str(e))
                    st.json(model_file)
                
            finally:
                progress_bar.empty()
                status_text.empty()

# デバッグ用の関数
def debug_github_files():
    """GitHub ファイル情報をデバッグ表示"""
    if not st.session_state.get("github_client"):
        st.error("GitHub クライアントが設定されていません")
        return
    
    st.subheader("🔍 GitHub ファイルデバッグ")
    
    folder = st.selectbox("デバッグするフォルダ:", ["models", "data", "results"])
    
    if st.button("ファイル情報を取得"):
        github_client = st.session_state.github_client
        files = github_client.list_files(folder)
        
        for file_info in files:
            with st.expander(f"📄 {file_info['name']} ({file_info['size']} bytes)"):
                st.json(file_info)
                
                # テストダウンロード
                col1, col2 = st.columns(2)
                
                with col1:
                    if st.button(f"ダウンロードテスト", key=f"test_{file_info['name']}"):
                        with st.spinner("テスト中..."):
                            result = github_client.download_file(file_info)
                            if result:
                                st.success(f"✅ 成功 ({len(result):,} bytes)")
                            else:
                                st.error("❌ 失敗")
                
                with col2:
                    if st.button(f"詳細情報取得", key=f"detail_{file_info['name']}"):
                        detailed = github_client.get_file_info_detailed(file_info['path'])
                        if detailed:
                            st.json(detailed)
                        else:
                            st.error("詳細情報取得失敗")
