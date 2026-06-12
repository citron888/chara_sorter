import shutil, os, json, sys, subprocess, time, threading
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"

# ══════════════════════════════════════════════
#  i18n
# ══════════════════════════════════════════════
_SUPPORTED_LANGS = ("ja","en","zh-cn","zh-tw","ko","es","fr","de","ru")

def _detect_lang() -> str:
    # 1) configに保存された言語設定を優先
    import sys, json, pathlib
    _base = pathlib.Path(sys.executable).parent if getattr(sys, "frozen", False) \
            else pathlib.Path(__file__).parent
    _cfg_path = _base / "sort_ui_config.json"
    try:
        _cfg = json.loads(_cfg_path.read_text(encoding="utf-8"))
        if _cfg.get("lang") in _SUPPORTED_LANGS:
            return _cfg["lang"]
    except Exception:
        pass
    # 2) PCのロケールから自動判別
    import locale
    lc = (locale.getlocale()[0] or "").lower()
    if lc.startswith("ja"):           return "ja"
    if lc.startswith("zh_cn") or lc.startswith("zh_sg"): return "zh-cn"
    if lc.startswith("zh"):           return "zh-tw"
    if lc.startswith("ko"):           return "ko"
    if lc.startswith("es"):           return "es"
    if lc.startswith("fr"):           return "fr"
    if lc.startswith("de"):           return "de"
    if lc.startswith("ru"):           return "ru"
    return "en"

LANG = _detect_lang()

def _S(ja,en,zh_cn,zh_tw,ko,es,fr,de,ru):
    return {"ja":ja,"en":en,"zh-cn":zh_cn,"zh-tw":zh_tw,"ko":ko,"es":es,"fr":fr,"de":de,"ru":ru}

STRINGS: dict[str, dict[str, str]] = {lang: {} for lang in _SUPPORTED_LANGS}

def _fill():
    _D = [
        # key, ja, en, zh-cn, zh-tw, ko, es, fr, de, ru
        ("title",           "CharaSorter","CharaSorter","CharaSorter","CharaSorter","CharaSorter","CharaSorter","CharaSorter","CharaSorter","CharaSorter"),
        ("dest",            "振り分け先:","Destination:","目标文件夹:","目標資料夾:","대상 폴더:","Destino:","Destination:","Ziel:","Назначение:"),
        ("source",          "仕分け元:","Source:","来源文件夹:","來源資料夾:","소스 폴더:","Origen:","Source:","Quelle:","Источник:"),
        ("folder_on",       "📁 フォルダに分ける","📁 Sort to folders","📁 按文件夹分类","📁 依資料夾分類","📁 폴더로 분류","📁 Ordenar en carpetas","📁 Trier en dossiers","📁 In Ordner sortieren","📁 По папкам"),
        ("folder_off",      "📄 ルートに置く","📄 Place at root","📄 放置于根目录","📄 放置於根目錄","📄 루트에 배치","📄 Colocar en raíz","📄 Placer à la racine","📄 Im Stammverz. ablegen","📄 В корень"),
        ("work_name",       "🤖 作品名:","🤖 Work name:","🤖 作品名:","🤖 作品名:","🤖 작품명:","🤖 Obra:","🤖 Œuvre:","🤖 Werk:","🤖 Произведение:"),
        ("work_hint",       "(空=全キャラ)","(blank=all)","(空=全角色)","(空=全角色)","(공백=전체)","(vacío=todos)","(vide=tous)","(leer=alle)","(пусто=все)"),
        ("auto_ai",         "🤖 自動AI","🤖 Auto AI","🤖 自动AI","🤖 自動AI","🤖 자동 AI","🤖 IA auto","🤖 IA auto","🤖 Auto-KI","🤖 Авто ИИ"),
        ("multi_folder",    "複数人フォルダ:","Multi:","多角色文件夹:","多角色資料夾:","다중 캐릭터:","Multi:","Multi:","Multi:","Мульти:"),
        ("multi_hint",      "(空=ルート直下)","(blank=root)","(空=根目录)","(空=根目錄)","(공백=루트)","(vacío=raíz)","(vide=racine)","(leer=Stamm)","(пусто=корень)"),
        ("vid_prefix",      "動画prefix:","Vid prefix:","视频前缀:","影片前綴:","영상 접두사:","Prefijo vídeo:","Préfixe vidéo:","Video-Präfix:","Префикс видео:"),
        ("prefix_hint",     "(空=なし)","(blank=none)","(空=无)","(空=無)","(공백=없음)","(vacío=ninguno)","(vide=aucun)","(leer=keiner)","(пусто=нет)"),
        ("char_label",      "キャラ{n}:","Char {n}:","角色{n}:","角色{n}:","캐릭터{n}:","Personaje {n}:","Perso {n}:","Char. {n}:","Персонаж {n}:"),
        ("btn_move",        "移動 (Ctrl+Enter)","Move (Ctrl+Enter)","移动 (Ctrl+Enter)","移動 (Ctrl+Enter)","이동 (Ctrl+Enter)","Mover (Ctrl+Enter)","Déplacer (Ctrl+Enter)","Verschieben (Ctrl+Enter)","Переместить (Ctrl+Enter)"),
        ("btn_prev",        "◀ 前へ (Ctrl+←)","◀ Prev (Ctrl+←)","◀ 上一个 (Ctrl+←)","◀ 上一個 (Ctrl+←)","◀ 이전 (Ctrl+←)","◀ Anterior (Ctrl+←)","◀ Précédent (Ctrl+←)","◀ Zurück (Ctrl+←)","◀ Назад (Ctrl+←)"),
        ("btn_skip",        "スキップ (Ctrl+→)","Skip (Ctrl+→)","跳过 (Ctrl+→)","跳過 (Ctrl+→)","건너뛰기 (Ctrl+→)","Omitir (Ctrl+→)","Passer (Ctrl+→)","Überspringen (Ctrl+→)","Пропустить (Ctrl+→)"),
        ("btn_delete",      "🗑 削除 (Ctrl+D)","🗑 Delete (Ctrl+D)","🗑 删除 (Ctrl+D)","🗑 刪除 (Ctrl+D)","🗑 삭제 (Ctrl+D)","🗑 Eliminar (Ctrl+D)","🗑 Supprimer (Ctrl+D)","🗑 Löschen (Ctrl+D)","🗑 Удалить (Ctrl+D)"),
        ("btn_undo",        "戻す (Ctrl+Z)","Undo (Ctrl+Z)","撤销 (Ctrl+Z)","復原 (Ctrl+Z)","실행취소 (Ctrl+Z)","Deshacer (Ctrl+Z)","Annuler (Ctrl+Z)","Rückgängig (Ctrl+Z)","Отменить (Ctrl+Z)"),
        ("btn_ai",          "🤖 AI分析 (Ctrl+Q)","🤖 AI (Ctrl+Q)","🤖 AI分析 (Ctrl+Q)","🤖 AI分析 (Ctrl+Q)","🤖 AI분석 (Ctrl+Q)","🤖 IA (Ctrl+Q)","🤖 IA (Ctrl+Q)","🤖 KI (Ctrl+Q)","🤖 ИИ (Ctrl+Q)"),
        ("btn_ai_loading",  "⏳ 分析中...","⏳ Analyzing...","⏳ 分析中...","⏳ 分析中...","⏳ 분석중...","⏳ Analizando...","⏳ Analyse...","⏳ Analysiere...","⏳ Анализ..."),
        ("btn_play",        "▶ 外部再生 (Ctrl+P)","▶ Open (Ctrl+P)","▶ 打开 (Ctrl+P)","▶ 開啟 (Ctrl+P)","▶ 열기 (Ctrl+P)","▶ Abrir (Ctrl+P)","▶ Ouvrir (Ctrl+P)","▶ Öffnen (Ctrl+P)","▶ Открыть (Ctrl+P)"),
        ("btn_fix",         "🔧 番号修正","🔧 Fix nums","🔧 修正编号","🔧 修正編號","🔧 번호 수정","🔧 Corregir nums","🔧 Corriger nums","🔧 Nums korrigieren","🔧 Исправить нум."),
        ("hotkeys",         "Ctrl+Enter:移動  Ctrl+←/→:前/次  Ctrl+D:削除  Ctrl+Q:AI  Ctrl+Z:戻す",
                            "Ctrl+Enter:Move  Ctrl+←/→:Prev/Next  Ctrl+D:Delete  Ctrl+Q:AI  Ctrl+Z:Undo",
                            "Ctrl+Enter:移动  Ctrl+←/→:上/下  Ctrl+D:删除  Ctrl+Q:AI  Ctrl+Z:撤销",
                            "Ctrl+Enter:移動  Ctrl+←/→:上/下  Ctrl+D:刪除  Ctrl+Q:AI  Ctrl+Z:復原",
                            "Ctrl+Enter:이동  Ctrl+←/→:이전/다음  Ctrl+D:삭제  Ctrl+Q:AI  Ctrl+Z:실행취소",
                            "Ctrl+Enter:Mover  Ctrl+←/→:Ant/Sig  Ctrl+D:Eliminar  Ctrl+Q:IA  Ctrl+Z:Deshacer",
                            "Ctrl+Enter:Déplacer  Ctrl+←/→:Préc/Suiv  Ctrl+D:Supprimer  Ctrl+Q:IA  Ctrl+Z:Annuler",
                            "Ctrl+Enter:Verschieben  Ctrl+←/→:Zurück/Weiter  Ctrl+D:Löschen  Ctrl+Q:KI  Ctrl+Z:Rückgängig",
                            "Ctrl+Enter:Переместить  Ctrl+←/→:Назад/Далее  Ctrl+D:Удалить  Ctrl+Q:ИИ  Ctrl+Z:Отменить"),
        ("select_dest",     "振り分け先フォルダを選択","Select destination folder","选择目标文件夹","選擇目標資料夾","대상 폴더 선택","Seleccionar carpeta destino","Sélectionner dossier dest.","Zielordner auswählen","Выбрать папку назначения"),
        ("select_source",   "仕分け元フォルダを選択","Select source folder","选择来源文件夹","選擇來源資料夾","소스 폴더 선택","Seleccionar carpeta origen","Sélectionner dossier source","Quellordner auswählen","Выбрать папку источника"),
        ("please_select",   "フォルダを選択してください","Please select folders","请选择文件夹","請選擇資料夾","폴더를 선택하세요","Por favor seleccione carpetas","Veuillez sélectionner des dossiers","Bitte Ordner auswählen","Пожалуйста, выберите папки"),
        ("all_done",        "完了！","Done!","完成！","完成！","완료!","¡Listo!","Terminé !","Fertig!","Готово!"),
        ("all_done_counter","全て処理済み","All files processed","全部处理完毕","全部處理完畢","모든 파일 처리 완료","Todos los archivos procesados","Tous les fichiers traités","Alle Dateien verarbeitet","Все файлы обработаны"),
        ("counter",         "{cur} / {total}  残り {rem} 件","{cur} / {total}  Remaining: {rem}","{cur} / {total}  剩余 {rem} 件","{cur} / {total}  剩餘 {rem} 件","{cur} / {total}  남은 {rem} 개","{cur} / {total}  Restantes: {rem}","{cur} / {total}  Restants: {rem}","{cur} / {total}  Verbleibend: {rem}","{cur} / {total}  Осталось: {rem}"),
        ("media_gif",       "▶ GIF","▶ GIF","▶ GIF","▶ GIF","▶ GIF","▶ GIF","▶ GIF","▶ GIF","▶ GIF"),
        ("media_video",     "▶ 動画再生中","▶ Playing video","▶ 播放视频","▶ 播放影片","▶ 영상 재생 중","▶ Reproduciendo vídeo","▶ Lecture vidéo","▶ Video wird abgespielt","▶ Воспроизведение видео"),
        ("gif_error",       "GIF読み込みエラー","GIF load error","GIF加载错误","GIF載入錯誤","GIF 로드 오류","Error al cargar GIF","Erreur chargement GIF","GIF-Ladefehler","Ошибка загрузки GIF"),
        ("video_no_cv2",    "▶ 動画\n(cv2 未インストール)","▶ Video\n(cv2 not installed)","▶ 视频\n(未安装cv2)","▶ 影片\n(未安裝cv2)","▶ 영상\n(cv2 미설치)","▶ Vídeo\n(cv2 no instalado)","▶ Vidéo\n(cv2 non installé)","▶ Video\n(cv2 nicht installiert)","▶ Видео\n(cv2 не установлен)"),
        ("load_error",      "読み込みエラー\n{ex}","Load error\n{ex}","加载错误\n{ex}","載入錯誤\n{ex}","로드 오류\n{ex}","Error de carga\n{ex}","Erreur de chargement\n{ex}","Ladefehler\n{ex}","Ошибка загрузки\n{ex}"),
        ("ai_error",        "AI エラー: {msg}","AI error: {msg}","AI错误: {msg}","AI錯誤: {msg}","AI 오류: {msg}","Error IA: {msg}","Erreur IA: {msg}","KI-Fehler: {msg}","Ошибка ИИ: {msg}"),
        ("ai_unknown",      "AI: キャラ不明（閾値未満）","AI: No character detected","AI: 未检测到角色","AI: 未偵測到角色","AI: 캐릭터 미검출","IA: No se detectó personaje","IA: Aucun personnage détecté","KI: Kein Charakter erkannt","ИИ: Персонаж не обнаружен"),
        ("ai_no_frame",     "有効なフレームが取得できませんでした","No valid frames found","无有效帧","無有效畫格","유효한 프레임 없음","No se encontraron fotogramas","Aucune image valide trouvée","Keine gültigen Frames gefunden","Нет подходящих кадров"),
        ("fix_none",        "修正が必要なファイルはありませんでした。","No files need renaming.","无需修正的文件。","無需修正的檔案。","수정이 필요한 파일이 없습니다.","No hay archivos que corregir.","Aucun fichier à corriger.","Keine Dateien zu korrigieren.","Нет файлов для исправления."),
        ("fix_confirm_title","番号修正の確認","Confirm fix numbering","确认修正编号","確認修正編號","번호 수정 확인","Confirmar corrección","Confirmer la correction","Korrektur bestätigen","Подтвердить исправление"),
        ("fix_confirm_msg", "{n} 件を修正します。内容を確認してください。","Will rename {n} files. Please review.","将重命名 {n} 个文件。请确认内容。","將重新命名 {n} 個檔案。請確認內容。","{n}개 파일을 수정합니다. 내용을 확인하세요.","Se renombrarán {n} archivos. Por favor revise.","{n} fichiers seront renommés. Veuillez vérifier.","{n} Dateien werden umbenannt. Bitte überprüfen.","Будет переименовано {n} файлов. Проверьте содержимое."),
        ("fix_ok",          "✅ 実行","✅ Execute","✅ 执行","✅ 執行","✅ 실행","✅ Ejecutar","✅ Exécuter","✅ Ausführen","✅ Выполнить"),
        ("fix_cancel",      "❌ キャンセル","❌ Cancel","❌ 取消","❌ 取消","❌ 취소","❌ Cancelar","❌ Annuler","❌ Abbrechen","❌ Отмена"),
        ("fix_done",        "✅ {n} 件修正完了  (ログ: rename_log.txt)","✅ {n} files renamed  (log: rename_log.txt)","✅ {n} 个文件已重命名  (日志: rename_log.txt)","✅ {n} 個檔案已重新命名  (記錄: rename_log.txt)","✅ {n}개 파일 수정 완료  (로그: rename_log.txt)","✅ {n} archivos renombrados  (log: rename_log.txt)","✅ {n} fichiers renommés  (log: rename_log.txt)","✅ {n} Dateien umbenannt  (Log: rename_log.txt)","✅ {n} файлов переименовано  (лог: rename_log.txt)"),
        ("tag_win_title",   "タグ一覧  作品名: '{w}'","Tag list  Work: '{w}'","标签列表  作品名: '{w}'","標籤列表  作品名: '{w}'","태그 목록  작품명: '{w}'","Lista de etiquetas  Obra: '{w}'","Liste des tags  Œuvre: '{w}'","Tag-Liste  Werk: '{w}'","Список тегов  Произведение: '{w}'"),
        ("tag_win_title_all","タグ一覧（全キャラ）","Tag list (all characters)","标签列表（全角色）","標籤列表（全角色）","태그 목록 (전체 캐릭터)","Lista de etiquetas (todos)","Liste des tags (tous)","Tag-Liste (alle Charaktere)","Список тегов (все персонажи)"),
        ("tag_loading",     "⏳ 読み込み中...","⏳ Loading...","⏳ 加载中...","⏳ 載入中...","⏳ 로딩중...","⏳ Cargando...","⏳ Chargement...","⏳ Lade...","⏳ Загрузка..."),
        ("tag_done",        "✅ {n} タグ  |  作品名: '{w}'","✅ {n} tags  |  Work: '{w}'","✅ {n} 个标签  |  作品名: '{w}'","✅ {n} 個標籤  |  作品名: '{w}'","✅ {n}개 태그  |  작품명: '{w}'","✅ {n} etiquetas  |  Obra: '{w}'","✅ {n} tags  |  Œuvre: '{w}'","✅ {n} Tags  |  Werk: '{w}'","✅ {n} тегов  |  Произведение: '{w}'"),
        ("tag_done_all",    "✅ {n} タグ（全キャラ）","✅ {n} tags (all characters)","✅ {n} 个标签（全角色）","✅ {n} 個標籤（全角色）","✅ {n}개 태그 (전체 캐릭터)","✅ {n} etiquetas (todos)","✅ {n} tags (tous)","✅ {n} Tags (alle Charaktere)","✅ {n} тегов (все персонажи)"),
        ("tag_error",       "エラー: {ex}","Error: {ex}","错误: {ex}","錯誤: {ex}","오류: {ex}","Error: {ex}","Erreur: {ex}","Fehler: {ex}","Ошибка: {ex}"),
        ("tag_hint",        "クリックでキャラ欄に挿入","Click to insert into char field","点击插入角色栏","點擊插入角色欄","클릭하여 캐릭터 입력란에 삽입","Clic para insertar en campo","Cliquer pour insérer dans le champ","Klicken zum Einfügen","Нажмите для вставки в поле"),
        ("tag_count",       "{n} 件","{n} items","{n} 件","{n} 件","{n}개","{n} elementos","{n} éléments","{n} Einträge","{n} элементов"),
        ("settings_title",      "設定","Settings","设置","設定","설정","Configuración","Paramètres","Einstellungen","Настройки"),
        ("settings_lang",       "言語:","Language:","语言:","語言:","언어:","Idioma:","Langue:","Sprache:","Язык:"),
        ("settings_char_rows",  "キャラ欄の数:","Char entry rows:","角色栏数量:","角色欄數量:","캐릭터 입력란 수:","Filas de personaje:","Lignes de personnage:","Charakter-Zeilen:","Строки персонажей:"),
        ("settings_ac_limit",   "補完候補数:","Autocomplete limit:","自动补全数量:","自動補全數量:","자동완성 제한:","Límite autocompletar:","Limite autocomplétion:","Autovervollständigung:","Лимит автодополнения:"),
        ("settings_ai_thresh",  "AI閾値 (0.1〜0.9):","AI threshold (0.1–0.9):","AI阈值 (0.1~0.9):","AI閾值 (0.1~0.9):","AI 임계값 (0.1~0.9):","Umbral IA (0.1–0.9):","Seuil IA (0.1–0.9):","KI-Schwellenwert (0.1–0.9):","Порог ИИ (0.1–0.9):"),
        ("settings_vid_frames", "動画サンプルフレーム数:","Video sample frames:","视频采样帧数:","影片取樣幀數:","영상 샘플 프레임 수:","Fotogramas de muestra:","Images échantillons:","Video-Beispielframes:","Кадры выборки видео:"),
        ("settings_skip_remove","スキップ済みをリストから除く","Remove skipped from list","从列表中移除已跳过","從列表移除已跳過","건너뛴 파일 목록에서 제거","Eliminar omitidos de lista","Retirer les ignorés de la liste","Übersprungene aus Liste entfernen","Удалять пропущенные из списка"),
        ("settings_char_order", "キャラ順序を学習する","Learn character order","学习角色顺序","學習角色順序","캐릭터 순서 학습","Aprender orden de personajes","Apprendre l'ordre des personnages","Charakter-Reihenfolge lernen","Изучать порядок персонажей"),
        ("settings_restart",    "※ 再起動で適用されます","* Restart to apply","※ 重启后生效","※ 重新啟動後生效","※ 재시작 후 적용됩니다","* Reiniciar para aplicar","* Redémarrer pour appliquer","* Neustart zum Anwenden","* Перезапустите для применения"),
        ("settings_ok",         "OK","OK","OK","OK","OK","OK","OK","OK","OK"),
        ("settings_cancel",     "キャンセル","Cancel","取消","取消","취소","Cancelar","Annuler","Abbrechen","Отмена"),
        ("settings_dupe_check",  "完全一致を自動削除","Auto-delete duplicates","自动删除重复","自動刪除重複","중복 자동 삭제","Eliminar duplicados","Supprimer les doublons","Duplikate löschen","Авто-удалять дубли"),
        ("settings_similar_ins", "類似画像を隣に挿入","Insert similar images adjacent","相似图片插入旁边","相似圖片插入旁邊","유사 이미지 인접 삽입","Insertar similares adyacente","Insérer similaires adjacent","Ähnliche nebeneinander einfügen","Вставлять похожие рядом"),
        ("settings_similar_thr", "類似度閾値 (小=厳格):","Similarity threshold (low=strict):","相似度阈值 (小=严格):","相似度閾值 (小=嚴格):","유사도 임계값 (낮음=엄격):","Umbral similitud (bajo=estricto):","Seuil similarité (bas=strict):","Ähnlichkeitsschwelle (klein=streng):","Порог похожести (мало=строго):"),
        ("dupe_deleted",         "🗑 重複 ({matched}) → 削除","🗑 Dupe of {matched} → deleted","🗑 重复 ({matched}) → 删除","🗑 重複 ({matched}) → 刪除","🗑 중복 ({matched}) → 삭제","🗑 Duplic. de {matched} → eliminado","🗑 Doublon de {matched} → supprimé","🗑 Duplikat von {matched} → gelöscht","🗑 Дубл. {matched} → удалён"),
        ("similar_inserted",     "📎 類似画像を {n} 番の後に挿入","📎 Similar: inserted after {n}","📎 相似图片插入 {n} 后","📎 相似圖片插入 {n} 後","📎 유사: {n} 뒤에 삽입","📎 Similar: insertado tras {n}","📎 Similaire: inséré après {n}","📎 Ähnlich: nach {n} eingefügt","📎 Похожее: вставлено после {n}"),
        ("btn_keep_on",         "📌 キャラ名保持 ON","📌 Keep names ON","📌 保留角色名 ON","📌 保留角色名 ON","📌 이름 유지 ON","📌 Mantener ON","📌 Garder noms ON","📌 Namen behalten ON","📌 Сохранять ON"),
        ("btn_keep_off",        "📌 キャラ名保持 OFF","📌 Keep names OFF","📌 保留角色名 OFF","📌 保留角色名 OFF","📌 이름 유지 OFF","📌 Mantener OFF","📌 Garder noms OFF","📌 Namen behalten OFF","📌 Сохранять OFF"),
        ("btn_sim_sort",        "📎 類似整列","📎 Sim.sort","📎 相似整列","📎 相似整列","📎 유사정렬","📎 Ord.sim.","📎 Tri sim.","📎 Ähnl.sort","📎 Похож.сорт"),
        ("sim_sort_title",      "類似画像の整列確認","Confirm similarity sort","确认相似整列","確認相似整列","유사 정렬 확인","Confirmar ord. similar","Confirmer tri similar","Ähnlichkeitssortierung","Подтверждение сортировки"),
        ("sim_sort_msg",        "{n} 件のリネームが発生します。実行しますか?","Rename {n} files. Proceed?","将重命名 {n} 个文件，继续吗?","將重命名 {n} 個檔案，繼續嗎?","{n}개 파일을 재명명합니다. 계속하시겠습니까?","¿Renombrar {n} archivos?","Renommer {n} fichiers ?","{n} Dateien umbenennen?","Переименовать {n} файлов?"),
        ("sim_sort_no_char",    "キャラ名を入力してください","Enter character name","请输入角色名","請輸入角色名","캐릭터 이름을 입력하세요","Ingrese nombre de personaje","Saisissez le nom du personnage","Charaktername eingeben","Введите имя персонажа"),
        ("sim_sort_none",       "整列対象のファイルが見つかりません","No files found to sort","未找到需要整列的文件","未找到需要整列的檔案","정렬할 파일이 없습니다","No se encontraron archivos","Aucun fichier trouvé","Keine Dateien gefunden","Файлы для сортировки не найдены"),
        ("sim_sort_done",       "📎 類似整列完了: {n} 件","📎 Sim.sort done: {n}","📎 相似整列完成: {n}","📎 相似整列完成: {n}","📎 유사정렬 완료: {n}","📎 Ord.sim. hecha: {n}","📎 Tri sim. fait: {n}","📎 Ähnl.sort fertig: {n}","📎 Похож.сорт готово: {n}"),
        ("sim_sort_select",     "対象フォルダを選択してください","Select target folders","选择目标文件夹","選擇目標資料夾","대상 폴더 선택","Seleccionar carpetas","Sélectionner les dossiers","Zielordner auswählen","Выберите папки"),
        ("sim_sort_toggle_all", "☑ 全選択 / 全解除","☑ Select all / None","☑ 全选 / 全不选","☑ 全選 / 全不選","☑ 전체 선택/해제","☑ Todo / Nada","☑ Tout / Rien","☑ Alle / Keine","☑ Все / Ничего"),
        ("sim_sort_danbooru",   "🌸 Danbooruの親子関係も使う (遅)","🌸 Use Danbooru parent/child (slow)","🌸 使用Danbooru亲子关系(慢)","🌸 使用Danbooru親子關係(慢)","🌸 Danbooru 부모/자식 사용 (느림)","🌸 Usar Danbooru padre/hijo (lento)","🌸 Utiliser Danbooru parent/enfant (lent)","🌸 Danbooru Eltern/Kind nutzen (langsam)","🌸 Использ. Danbooru родитель/дочь (медл.)"),
        ("settings_danbooru",     "Danbooru自動検索","Danbooru auto lookup","Danbooru自动搜索","Danbooru自動搜尋","Danbooru 자동 검색","Búsqueda Danbooru","Recherche Danbooru","Danbooru-Suche","Поиск Danbooru"),
        ("settings_db_login",     "Danbooruログイン名:","Danbooru login:","Danbooru登录名:","Danbooru登入名:","Danbooru 로그인:","Login Danbooru:","Login Danbooru:","Danbooru-Login:","Логин Danbooru:"),
        ("settings_db_apikey",    "Danbooru APIキー:","Danbooru API key:","Danbooru API密钥:","Danbooru API金鑰:","Danbooru API키:","Clave API Danbooru:","Clé API Danbooru:","Danbooru API-Schlüssel:","API-ключ Danbooru:"),
        ("danbooru_hit",          "🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}","🌸 {chars}  /  artist: {artist}"),
        ("danbooru_miss",         "","","","","","","","",""),
        ("danbooru_err",          "","","","","","","","",""),
    ]
    keys = ("ja","en","zh-cn","zh-tw","ko","es","fr","de","ru")
    for row in _D:
        k = row[0]
        for i, lang in enumerate(keys):
            STRINGS[lang][k] = row[i+1]

_fill()

def t(key: str, **kw) -> str:
    s = STRINGS.get(LANG, STRINGS["en"]).get(key) or STRINGS["en"].get(key, key)
    return s.format(**kw) if kw else s

import tkinter as tk
from tkinter import ttk, filedialog
from pathlib import Path
from PIL import Image, ImageTk, ImageSequence

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

try:
    from send2trash import send2trash
    HAS_TRASH = True
except ImportError:
    HAS_TRASH = False

IMG_EXTS   = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".webm", ".mkv", ".avi", ".mov", ".wmv", ".flv"}
GIF_EXTS   = {".gif"}
ALL_EXTS   = IMG_EXTS | VIDEO_EXTS | GIF_EXTS

# ── 重複・類似検出ユーティリティ ──────────────────
import hashlib as _hashlib

def _file_md5(path: Path) -> str | None:
    """ファイル全体のMD5ハッシュ。読み取れない場合は None を返す。"""
    h = _hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def _dhash_img(img, size: int = 8) -> int:
    """PIL.Image(グレースケール)からdHashを計算"""
    img = img.resize((size + 1, size), Image.LANCZOS)
    px = list(img.getdata())
    h = 0
    for row in range(size):
        for col in range(size):
            if px[row * (size + 1) + col] > px[row * (size + 1) + col + 1]:
                h |= 1 << (row * size + col)
    return h

def _dhash(path: Path, size: int = 8) -> list[int] | None:
    """差分ハッシュ(dHash): 全体・上半分・左半分・左上1/4 の4領域を返す
    差分画像（部分追加・色変更等）にも対応するためマルチリージョン方式を採用"""
    try:
        img = Image.open(path).convert("L")
        w, h = img.size
        regions = [
            img,                                    # 全体
            img.crop((0,    0,    w,    h // 2)),   # 上半分
            img.crop((0,    0,    w//2, h)),         # 左半分
            img.crop((0,    0,    w//2, h // 2)),   # 左上1/4
        ]
        return [_dhash_img(r, size) for r in regions]
    except Exception:
        return None

def _hamming(a: list[int], b: list[int]) -> int:
    """4領域ハッシュのうち最小ハミング距離を返す"""
    return min(bin(x ^ y).count("1") for x, y in zip(a, b))

if getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent
CONFIG_PATH = BASE_DIR / "sort_ui_config.json"

# ── Danbooru API ──────────────────────────────────
import re as _re_danbooru
_danbooru_last_req: float = 0.0

def _danbooru_fetch(md5: str, login: str = "", api_key: str = "") -> dict | None:
    """MD5でDanbooru検索。ヒットしたらpost dictを返す。なければNone。"""
    global _danbooru_last_req
    import time, urllib.request, json as _json
    elapsed = time.time() - _danbooru_last_req
    if elapsed < 0.6:
        time.sleep(0.6 - elapsed)
    url = (f"https://danbooru.donmai.us/posts.json"
           f"?tags=md5:{md5}"
           f"&only=id,md5,tag_string_character,tag_string_artist,parent_id,rating"
           f"&limit=1")
    req = urllib.request.Request(url, headers={"User-Agent": "CharaSorter/1.0"})
    if login and api_key:
        import base64 as _b64
        creds = _b64.b64encode(f"{login}:{api_key}".encode()).decode()
        req.add_header("Authorization", f"Basic {creds}")
    try:
        _danbooru_last_req = time.time()
        with urllib.request.urlopen(req, timeout=4) as resp:
            posts = _json.loads(resp.read())
            return posts[0] if posts else None
    except Exception:
        return None

def _danbooru_parse_chars(tag_string: str) -> list[str]:
    """キャラタグ文字列から名前リストを生成。_(series)サフィックスを除去。"""
    result = []
    for tag in tag_string.strip().split():
        name = _re_danbooru.sub(r'_\([^)]+\)$', '', tag)
        if name:
            result.append(name)
    return result

def load_config():
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}

def save_config(data: dict):
    CONFIG_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

def valid_dir(p: Path) -> bool:
    return bool(str(p)) and str(p) not in (".", "") and p.is_dir()

def get_folders(image_dir: Path, source_dir: Path, exclude: set[str] | None = None):
    try:
        ex = exclude or set()
        return sorted([d.name for d in image_dir.iterdir()
                       if d.is_dir()
                       and d.name not in ex])
    except Exception:
        return []


# ══════════════════════════════════════════════
#  WD-Tagger（作品名フィルタ対応）
# ══════════════════════════════════════════════
class Tagger:
    MODEL_REPO = "SmilingWolf/wd-swinv2-tagger-v3"
    THRESHOLD  = 0.25

    def __init__(self):
        self._session   = None
        self._char_tags = None   # {idx: raw_tag_name}  category==4 全件
        self._lock      = threading.Lock()

    def _load_tags_only(self):
        """CSV のみロード（モデル不要）"""
        import pandas as pd
        from huggingface_hub import hf_hub_download
        tags_path = hf_hub_download(self.MODEL_REPO, "selected_tags.csv")
        df = pd.read_csv(tags_path)
        char_mask = (df["category"] == 4)
        self._char_tags = {int(i): row["name"] for i, row in df[char_mask].iterrows()}

    def get_work_list(self) -> list[str]:
        """タグCSVに存在する作品名一覧を返す（例: series_a, touhou, …）"""
        import re
        with self._lock:
            if self._char_tags is None:
                self._load_tags_only()
        works = set()
        pat = re.compile(r"_\(([^)]+)\)$")
        for name in self._char_tags.values():
            m = pat.search(name)
            if m:
                works.add(m.group(1).replace(" ", "_"))
        return sorted(works)

    def _filtered_tags(self, work_name: str) -> dict[int, str]:
        """作品名でフィルタしたキャラタグを {idx: 表示名} で返す共通ヘルパー。
        work_name が空なら全タグ、指定時は _(work_name) サフィックス付きのみ。"""
        wn = work_name.strip().lower().replace(" ", "_")
        if wn:
            suffix = f"_({wn})"
            return {
                idx: name.replace(suffix, "").replace(" ", "_")
                for idx, name in self._char_tags.items()
                if suffix in name
            }
        return {idx: name.replace(" ", "_") for idx, name in self._char_tags.items()}

    def get_tag_list(self, work_name: str = "") -> list[str]:
        """作品名フィルタ後のキャラタグ名一覧（モデルロード不要）"""
        with self._lock:
            if self._char_tags is None:
                self._load_tags_only()
        return sorted(set(self._filtered_tags(work_name).values()))

    def _load(self):
        import pandas as pd
        import onnxruntime as ort
        from huggingface_hub import hf_hub_download

        model_path = hf_hub_download(self.MODEL_REPO, "model.onnx")
        tags_path  = hf_hub_download(self.MODEL_REPO, "selected_tags.csv")

        providers = ["DmlExecutionProvider", "CPUExecutionProvider"]
        self._session = ort.InferenceSession(model_path, providers=providers)

        # タグが未ロードなら CSV も読む
        if self._char_tags is None:
            df = pd.read_csv(tags_path)
            char_mask = (df["category"] == 4)
            self._char_tags = {int(i): row["name"] for i, row in df[char_mask].iterrows()}
        else:
            # 既にロード済み（get_tag_list 経由）→ session のみ作成
            pass

    def _build_tag_map(self, work_name: str) -> dict:
        """推論結果のスコア配列インデックスをキャラ名に変換するマップを返す"""
        return self._filtered_tags(work_name)

    def _infer(self, pil_img: Image.Image) -> "np.ndarray":
        import numpy as np
        img = pil_img.convert("RGB").resize((448, 448), Image.LANCZOS)
        arr = np.array(img, dtype=np.float32)[:, :, ::-1]
        arr = np.expand_dims(arr, 0)
        input_name = self._session.get_inputs()[0].name
        return self._session.run(None, {input_name: arr})[0][0]

    def predict(self, image_path: Path, work_name: str = "", threshold: float = 0.25) -> list[str]:
        """単一画像ファイルから推論"""
        import numpy as np
        with self._lock:
            if self._session is None:
                self._load()
        tag_map = self._build_tag_map(work_name)
        if not tag_map:
            return []
        outputs = self._infer(Image.open(image_path))
        results = [(name, float(outputs[idx]))
                   for idx, name in tag_map.items()
                   if idx < len(outputs) and outputs[idx] >= threshold]
        results.sort(key=lambda x: -x[1])
        return [name for name, _ in results]

    def predict_frames(self, frames: list, work_name: str = "", threshold: float = 0.25) -> list[str]:
        """複数PIL Imageフレームから推論（スコアをmax集約）"""
        import numpy as np
        with self._lock:
            if self._session is None:
                self._load()
        tag_map = self._build_tag_map(work_name)
        if not tag_map or not frames:
            return []
        scores: dict[str, float] = {}
        for pil_img in frames:
            outputs = self._infer(pil_img)
            for idx, name in tag_map.items():
                if idx < len(outputs):
                    scores[name] = max(scores.get(name, 0.0), float(outputs[idx]))
        results = [(name, score) for name, score in scores.items()
                   if score >= threshold]
        results.sort(key=lambda x: -x[1])
        return [name for name, _ in results]


# ── グローバル Tagger インスタンス（lazy load）──
_tagger = None
def get_tagger() -> Tagger:
    global _tagger
    if _tagger is None:
        _tagger = Tagger()
    return _tagger


# ══════════════════════════════════════════════
#  動画プレビュー用ヘルパー
# ══════════════════════════════════════════════
def load_gif_frames(path: Path, max_w=900, max_h=440):
    img = Image.open(path)
    frames, delays = [], []
    try:
        while True:
            frame = img.copy().convert("RGBA")
            frame.thumbnail((max_w, max_h), Image.LANCZOS)
            frames.append(ImageTk.PhotoImage(frame))
            delays.append(img.info.get("duration", 80))
            img.seek(img.tell() + 1)
    except EOFError:
        pass
    return frames, delays


# ══════════════════════════════════════════════
#  CharEntry
# ══════════════════════════════════════════════
_FORBIDDEN_CHARS = frozenset('\\/:*?"<>|')

class CharEntry:
    def __init__(self, parent, folders_fn, label="", ac_limit=8):
        self.folders_fn   = folders_fn
        self.ac_limit     = ac_limit
        self.siblings:list= []   # 他のCharEntryインスタンス（重複除外用）
        self.single_match = None
        self._dropdown    = None
        self._dd_btns     = []
        self._dd_cursor   = -1
        self._dd_matches  = []

        self.frame = tk.Frame(parent, bg="#1e1e1e")
        if label:
            tk.Label(self.frame, text=label, bg="#1e1e1e", fg="#ccc",
                     font=("Arial", 11), width=7).pack(side="left")

        self.var = tk.StringVar()
        self.var.trace_add("write", self._on_type)
        self.entry = ttk.Entry(self.frame, textvariable=self.var, font=("Arial", 13), width=26)
        self.entry.pack(side="left", padx=4)
        self.entry.bind("<KeyRelease>", self._normalize)
        self.entry.bind("<FocusOut>",   lambda e: (self.root.after(150, self._hide_dropdown), self._normalize_blur()))
        self.entry.bind("<Escape>",     lambda e: (self._hide_dropdown(), "break"))
        self.entry.bind("<Tab>",        lambda e: (self._cursor_move(+1), "break"))
        self.entry.bind("<Down>",       lambda e: (self._cursor_move(+1), "break"))
        self.entry.bind("<Up>",         lambda e: (self._cursor_move(-1), "break"))
        self.entry.bind("<Return>",     self._on_entry_return)

    @property
    def root(self):
        return self.frame.winfo_toplevel()

    def get(self):
        return self.single_match if self.single_match else self.var.get().strip()

    def set(self, value):
        self._set_silent(value)
        self.single_match = value if value else None

    def clear(self):
        self._set_silent("")
        self._hide_dropdown()
        self.single_match = None

    def focus(self):
        self.entry.focus()

    def _cursor_move(self, delta):
        if not self._dd_btns:
            return
        if 0 <= self._dd_cursor < len(self._dd_btns):
            self._set_btn_highlight(self._dd_cursor, False)
        self._dd_cursor = (self._dd_cursor + delta) % len(self._dd_btns)
        self._set_btn_highlight(self._dd_cursor, True)

    def _set_btn_highlight(self, idx, on):
        btn = self._dd_btns[idx]
        is_single = len(self._dd_btns) == 1
        btn.config(bg="#1a5a2a" if on else ("#5a1a1a" if is_single else "#3a3a3a"),
                   fg="#7fff9a" if on else ("#ff6b6b" if is_single else "white"))

    def _on_entry_return(self, event):
        if self._dropdown is None:
            return
        if 0 <= self._dd_cursor < len(self._dd_matches):
            self._select(self._dd_matches[self._dd_cursor])
        elif self.single_match:
            self._select(self.single_match)
        else:
            return
        return "break"

    def _normalize(self, _=None):
        val = self.var.get()
        n = val.replace("　", "_").replace(" ", "_")
        n = "".join(c for c in n if c not in _FORBIDDEN_CHARS)
        n = n.lower()
        if n != val:
            self._set_silent(n)
            self.entry.icursor(len(n))
            self._on_type()

    def _normalize_blur(self):
        """フォーカスを外したとき末尾の_を除去"""
        val = self.var.get()
        n = val.rstrip("_")
        if n != val:
            self._set_silent(n)
            self._on_type()

    def _set_silent(self, value):
        for mode, cb in self.var.trace_info():
            self.var.trace_remove(mode, cb)
        self.var.set(value)
        self.var.trace_add("write", self._on_type)

    def _hide_dropdown(self):
        if self._dropdown:
            try:
                self._dropdown.destroy()
            except Exception:
                pass
            self._dropdown = None
        self._dd_btns   = []
        self._dd_cursor = -1
        self._dd_matches = []

    def _show_dropdown(self, matches):
        self._hide_dropdown()
        ex = self.entry.winfo_rootx()
        ey = self.entry.winfo_rooty() + self.entry.winfo_height() + 2
        ew = self.entry.winfo_width()
        top = tk.Toplevel(self.root)
        top.wm_overrideredirect(True)
        top.wm_attributes("-topmost", True)
        top.geometry(f"{max(ew, 220)}x{len(matches)*28+4}+{ex}+{ey}")
        top.configure(bg="#2d2d2d")
        self._dd_matches = matches
        is_single = len(matches) == 1
        for m in matches:
            btn = tk.Button(top, text=m,
                            bg="#5a1a1a" if is_single else "#3a3a3a",
                            fg="#ff6b6b" if is_single else "white",
                            font=("Arial", 10, "bold" if is_single else "normal"),
                            anchor="w", relief="flat", bd=0,
                            command=lambda name=m: self._select(name))
            btn.pack(fill="x", padx=2, pady=1)
            self._dd_btns.append(btn)
        self._dropdown = top

    def _on_type(self, *_):
        query = self.var.get().strip().lower()
        self.single_match = None
        if not query:
            self._hide_dropdown()
            return
        try:
            folders = self.folders_fn()
        except Exception:
            self._hide_dropdown()
            return
        used = {s.get() for s in self.siblings if s.get()}
        matches = [f for f in folders if query in f.lower() and f not in used][:self.ac_limit]
        if not matches:
            self._hide_dropdown()
            return
        if len(matches) == 1:
            self.single_match = matches[0]
        self._show_dropdown(matches)

    def _select(self, name):
        self._hide_dropdown()
        self.single_match = name
        self._set_silent(name)
        self.entry.focus()


# ══════════════════════════════════════════════
#  Mixin: AI推論・Danbooru検索
# ══════════════════════════════════════════════
class _AIMixin:
    """AIタガー・Danbooru検索の責務。
    SortApp に Mix-in される。self.root / self.images / self.cfg などは SortApp が提供する。"""

    # ── AI 分析 ──
    # ── Danbooru 検索 ──
    def _run_danbooru(self, path: Path):
        """バックグラウンドでDanbooru MD5検索を実行する"""
        md5 = _file_md5(path)
        if not md5:
            return
        # 現在表示中の画像と一致するか確認（スクロール済みなら無視）
        post = _danbooru_fetch(md5, self._danbooru_login, self._danbooru_apikey)
        self.root.after(0, self._danbooru_done, path, post)

    def _danbooru_done(self, path: Path, post: dict | None):
        """Danbooru検索結果をUIに反映する"""
        # 表示中の画像が変わっていたら無視
        if not self.images or self.images[self.index] != path:
            return
        if post is None:
            return  # ヒットなし・エラー → 何もしない

        chars  = _danbooru_parse_chars(post.get("tag_string_character", ""))
        artist = post.get("tag_string_artist", "").strip().replace(" ", ", ")

        # ステータスに表示（常に）
        char_str = "  ".join(chars[:3]) if chars else "?"
        self.counter_var.set(t("danbooru_hit", chars=char_str, artist=artist or "?"))

        # エントリが全部空の場合のみ自動入力（AIが先に入れていたら触らない）
        all_empty = all(not e.get() for e in self.char_entries)
        if all_empty and chars:
            sorted_names = self._sort_by_learned_order(chars)
            for i, name in enumerate(sorted_names[:len(self.char_entries)]):
                matched = self._match_to_folder(name)
                self.char_entries[i].set(matched)
            self.char_entries[0].focus()

    def analyze_ai(self):
        if not self.images:
            return
        path = self.images[self.index]
        ext  = path.suffix.lower()
        work_name = self._work_name_var.get()
        self.ai_btn.config(text=t("btn_ai_loading"), state="disabled", bg="#333")
        if ext in VIDEO_EXTS | GIF_EXTS:
            threading.Thread(target=self._run_tagger_video,
                             args=(path, work_name), daemon=True).start()
        else:
            threading.Thread(target=self._run_tagger,
                             args=(path, work_name), daemon=True).start()

    def _extract_video_frames(self, path: Path, n: int = 3) -> list:
        """動画から n フレームを均等サンプリング（暗すぎるフレームを除外）"""
        import numpy as np
        frames = []
        if path.suffix.lower() in GIF_EXTS:
            # GIF: PIL で読む
            gif = Image.open(path)
            total = 0
            try:
                while True:
                    total += 1
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass
            ratios = [i / (n + 1) for i in range(1, n + 1)]
            positions = [int(total * r) for r in ratios]
            for pos in positions:
                try:
                    gif.seek(min(pos, total - 1))
                    frame = gif.copy().convert("RGB")
                    if np.mean(np.array(frame)) >= 20:
                        frames.append(frame)
                except Exception:
                    pass
        elif HAS_CV2:
            cap = cv2.VideoCapture(str(path))
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT)) or 1
            ratios = [i / (n + 1) for i in range(1, n + 1)]
            positions = [int(total * r) for r in ratios]
            for pos in positions:
                cap.set(cv2.CAP_PROP_POS_FRAMES, min(pos, total - 1))
                ret, frame = cap.read()
                if ret:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil = Image.fromarray(frame_rgb)
                    if np.mean(frame_rgb) >= 20:   # 暗すぎるフレームをスキップ
                        frames.append(pil)
            cap.release()
        return frames

    def _run_tagger_video(self, path: Path, work_name: str = ""):
        import numpy as np
        try:
            frames = self._extract_video_frames(path, n=self._vid_frames)
            if not frames:
                self.root.after(0, self._ai_done, [], t("ai_no_frame"))
                return
            names = get_tagger().predict_frames(frames, work_name, threshold=self._ai_threshold)
        except Exception as ex:
            self.root.after(0, self._ai_done, [], str(ex))
            return
        self.root.after(0, self._ai_done, names, None)

    def _run_tagger(self, path: Path, work_name: str = ""):
        try:
            names = get_tagger().predict(path, work_name, threshold=self._ai_threshold)
        except Exception as ex:
            self.root.after(0, self._ai_done, [], str(ex))
            return
        self.root.after(0, self._ai_done, names, None)

    def _match_to_folder(self, name: str) -> str:
        """AI結果名をフォルダ一覧に照合して最適なフォルダ名を返す"""
        import difflib
        if not self.folders:
            return name
        # 1. 完全一致
        if name in self.folders:
            return name
        # 2. アンダースコア正規化（除去して比較）
        normalized = name.replace("_", "").lower()
        for f in self.folders:
            if f.replace("_", "").lower() == normalized:
                return f
        # 3. difflib 類似度マッチ（0.7以上）
        matches = difflib.get_close_matches(name, self.folders, n=1, cutoff=0.7)
        if matches:
            return matches[0]
        return name

    def _ai_done(self, names: list, error: str | None):
        self.ai_btn.config(text=t("btn_ai"), state="normal", bg="#4a2a6a")
        if error:
            self.counter_var.set(t("ai_error", msg=error[:60]))
            return
        if not names:
            self.counter_var.set(t("ai_unknown"))
            return
        self._clear_inputs()
        sorted_names = self._sort_by_learned_order(names)
        for i, name in enumerate(sorted_names[:len(self.char_entries)]):
            matched = self._match_to_folder(name)
            self.char_entries[i].set(matched)
        self.char_entries[0].focus()


# ══════════════════════════════════════════════
#  Mixin: 類似整列・番号修正
# ══════════════════════════════════════════════
class _SortMixin:
    """類似整列・番号修正などファイル整理操作の責務。
    SortApp に Mix-in される。self.root / self.image_dir 等は SortApp が提供する。"""

    # ── 共通ユーティリティ ──────────────────────────────

    def _rename_confirm_dialog(self, title: str, msg: str,
                               renames: list[tuple[Path, Path]]) -> bool:
        """スクロール付き確認ダイアログを表示し、OKならTrueを返す。DRY用共通メソッド。"""
        confirmed = [False]
        win = tk.Toplevel(self.root)
        win.title(f"{title}  ({len(renames)})")
        win.configure(bg="#1e1e1e")
        win.geometry("640x520")
        win.grab_set()

        tk.Label(win, text=msg, bg="#1e1e1e", fg="#aaa",
                 font=("Arial", 10)).pack(pady=(8, 2))

        frame = tk.Frame(win, bg="#1e1e1e")
        frame.pack(fill="both", expand=True, padx=10, pady=4)
        sb = ttk.Scrollbar(frame)
        sb.pack(side="right", fill="y")
        txt = tk.Text(frame, bg="#0d1117", fg="#e6edf3", font=("Consolas", 10),
                      yscrollcommand=sb.set, relief="flat", state="normal", wrap="none")
        txt.pack(fill="both", expand=True)
        sb.config(command=txt.yview)
        sbx = ttk.Scrollbar(win, orient="horizontal", command=txt.xview)
        sbx.pack(fill="x", padx=10)
        txt.config(xscrollcommand=sbx.set)
        txt.tag_config("old", foreground="#ff7b72")
        txt.tag_config("new", foreground="#7ee787")
        txt.tag_config("sep", foreground="#484f58")

        prev_dir = None
        for old, new in renames:
            if old.parent != prev_dir:
                if prev_dir is not None:
                    txt.insert("end", "\n")
                txt.insert("end", f"  📁 {old.parent.name}/\n", "sep")
                prev_dir = old.parent
            txt.insert("end", f"  - {old.name}\n", "old")
            txt.insert("end", f"  + {new.name}\n", "new")
        txt.config(state="disabled")
        txt.bind("<MouseWheel>", lambda e: txt.yview_scroll(int(-1*(e.delta/120)), "units"))

        btn_frame = tk.Frame(win, bg="#1e1e1e")
        btn_frame.pack(pady=8)

        def on_ok():
            confirmed[0] = True
            win.destroy()

        tk.Button(btn_frame, text=t("fix_ok"), command=on_ok,
                  bg="#2ea44f", fg="white", font=("Arial", 12), width=10).pack(side="left", padx=8)
        tk.Button(btn_frame, text=t("fix_cancel"), command=win.destroy,
                  bg="#6e6e6e", fg="white", font=("Arial", 12), width=10).pack(side="left", padx=8)
        win.wait_window()
        return confirmed[0]

    @staticmethod
    def _atomic_rename_batch(renames: list[tuple[Path, Path]]) -> None:
        """衝突を避けるため2パスでリネーム（tmp退避 → 正式名）。DRY用共通メソッド。"""
        tmp_map: list[tuple[Path, Path]] = []
        for old, new in renames:
            tmp = old.parent / f"__tmp_{old.name}"
            old.rename(tmp)
            tmp_map.append((tmp, new))
        for tmp, new in tmp_map:
            tmp.rename(new)

    # ── 類似画像の整列（既存ファイルを類似順に並び替え）──
    def sort_by_similarity(self):
        """フォルダ選択ダイアログ → プログレス → 確認 → リネーム"""
        from tkinter import messagebox
        import re as _re
        from collections import defaultdict

        if not valid_dir(self.image_dir):
            return

        # ── ① フォルダ選択ダイアログ ──
        all_dirs = [self.image_dir] + sorted(
            [d for d in self.image_dir.iterdir() if d.is_dir()]
        )

        sel_win = tk.Toplevel(self.root)
        sel_win.title(t("btn_sim_sort"))
        sel_win.configure(bg="#1e1e1e")
        sel_win.geometry("420x480")
        sel_win.grab_set()
        sel_win.resizable(False, True)

        tk.Label(sel_win, text=t("sim_sort_select"), bg="#1e1e1e", fg="#aaa",
                 font=("Arial", 10)).pack(pady=(10, 4))

        # チェックボックスリスト（スクロール付き）
        list_frame = tk.Frame(sel_win, bg="#1e1e1e")
        list_frame.pack(fill="both", expand=True, padx=12, pady=4)
        sb = ttk.Scrollbar(list_frame)
        sb.pack(side="right", fill="y")
        canvas = tk.Canvas(list_frame, bg="#0d1117", highlightthickness=0,
                           yscrollcommand=sb.set)
        canvas.pack(fill="both", expand=True)
        sb.config(command=canvas.yview)
        inner = tk.Frame(canvas, bg="#0d1117")
        canvas_win = canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_resize(e):
            canvas.config(scrollregion=canvas.bbox("all"))
            canvas.itemconfig(canvas_win, width=canvas.winfo_width())
        inner.bind("<Configure>", _on_inner_resize)
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_win, width=e.width))

        def _on_mousewheel(e):
            canvas.yview_scroll(int(-1 * (e.delta / 120)), "units")
        canvas.bind("<MouseWheel>", _on_mousewheel)
        inner.bind("<MouseWheel>", _on_mousewheel)

        check_vars = []
        for d in all_dirs:
            label = f"(ルート)  {d.name}" if d == self.image_dir else f"📁 {d.name}"
            v = tk.BooleanVar(value=False)
            check_vars.append(v)
            cb = tk.Checkbutton(inner, text=label, variable=v,
                                bg="#0d1117", fg="#e6edf3", selectcolor="#1e1e1e",
                                activebackground="#0d1117", activeforeground="#fff",
                                font=("Arial", 10), anchor="w")
            cb.pack(fill="x", padx=6, pady=1)
            cb.bind("<MouseWheel>", _on_mousewheel)

        # 全選択/解除ボタン
        def _toggle_all():
            all_checked = all(v.get() for v in check_vars)
            for v in check_vars:
                v.set(not all_checked)

        ctrl_frame = tk.Frame(sel_win, bg="#1e1e1e")
        ctrl_frame.pack(pady=(4, 2))
        tk.Button(ctrl_frame, text=t("sim_sort_toggle_all"), command=_toggle_all,
                  bg="#2a2a4a", fg="#aaaaff", font=("Arial", 10)).pack(side="left", padx=6)

        # Danbooru使用チェック（設定でDanbooru有効な場合のみ表示）
        use_danbooru_var = tk.BooleanVar(value=False)
        if self._danbooru_on:
            tk.Checkbutton(sel_win, text=t("sim_sort_danbooru"),
                           variable=use_danbooru_var,
                           bg="#1e1e1e", fg="#ffaacc", selectcolor="#333",
                           activebackground="#1e1e1e", activeforeground="#ffaacc",
                           font=("Arial", 9)).pack(pady=(4, 0))

        selected_dirs: list[list[Path]] = [[]]
        use_db: list[bool] = [False]
        btn_frame = tk.Frame(sel_win, bg="#1e1e1e")
        btn_frame.pack(pady=8)

        def _on_start():
            selected_dirs[0] = [d for d, v in zip(all_dirs, check_vars) if v.get()]
            use_db[0] = use_danbooru_var.get()
            sel_win.destroy()

        tk.Button(btn_frame, text=t("fix_ok"), command=_on_start,
                  bg="#2ea44f", fg="white", font=("Arial", 12), width=10).pack(side="left", padx=8)
        tk.Button(btn_frame, text=t("fix_cancel"), command=sel_win.destroy,
                  bg="#6e6e6e", fg="white", font=("Arial", 12), width=10).pack(side="left", padx=8)

        sel_win.wait_window()
        if not selected_dirs[0]:
            return

        # ── ② 選択フォルダのファイル列挙 ──
        num_pat = _re.compile(r"^(.+)_(\d+)$")
        # (dir, base) → [(n, path), ...]
        dir_base_files: dict[tuple[Path,str], list[tuple[int,Path]]] = defaultdict(list)
        for d in selected_dirs[0]:
            for f in d.iterdir():
                if not f.is_file() or f.suffix.lower() not in IMG_EXTS:
                    continue
                m = num_pat.match(f.stem)
                if m:
                    dir_base_files[(d, m.group(1))].append((int(m.group(2)), f))

        total_files = sum(len(v) for v in dir_base_files.values())
        if total_files == 0:
            messagebox.showinfo(t("btn_sim_sort"), t("sim_sort_none"))
            return

        # ── プログレスウィンドウ ──
        prog_win = tk.Toplevel(self.root)
        prog_win.title(t("btn_sim_sort"))
        prog_win.configure(bg="#1e1e1e")
        prog_win.geometry("400x100")
        prog_win.grab_set()
        prog_win.resizable(False, False)
        prog_lbl = tk.Label(prog_win, text="...", bg="#1e1e1e", fg="#aaa", font=("Arial", 10))
        prog_lbl.pack(pady=(12, 4))
        prog_bar = ttk.Progressbar(prog_win, length=360, mode="determinate",
                                   maximum=total_files, value=0)
        prog_bar.pack(padx=20)

        # ── バックグラウンドで計算 ──
        result: list[list[tuple[Path,Path]]] = [[]]
        done_flag = [False]
        done_count = [0]

        def _worker():
            import re as _re2
            from collections import defaultdict as dd2
            all_renames = []
            for (d, base), files in dir_base_files.items():
                if len(files) < 2:
                    done_count[0] += len(files)
                    continue
                files.sort()
                hashes = []
                db_parent: dict[int, int | None] = {}  # index → danbooru parent_id or post_id
                for idx, (n, f) in enumerate(files):
                    hashes.append((n, f, _dhash(f)))
                    done_count[0] += 1
                    if use_db[0]:
                        md5 = _file_md5(f)
                        post = _danbooru_fetch(md5, self._danbooru_login, self._danbooru_apikey) if md5 else None
                        if post:
                            # parent_id があればそれ、なければ自身のid（ルート扱い）
                            db_parent[idx] = post.get("parent_id") or post.get("id")
                        else:
                            db_parent[idx] = None

                parent_uf = list(range(len(hashes)))
                def find(x):
                    while parent_uf[x] != x:
                        parent_uf[x] = parent_uf[parent_uf[x]]
                        x = parent_uf[x]
                    return x
                def union(x, y):
                    parent_uf[find(x)] = find(y)

                # Danbooru parent_id でグループ化
                if use_db[0]:
                    pid_to_indices: dict[int, list[int]] = dd2(list)
                    for idx, pid in db_parent.items():
                        if pid is not None:
                            pid_to_indices[pid].append(idx)
                    for indices in pid_to_indices.values():
                        for k in range(1, len(indices)):
                            union(indices[0], indices[k])

                # dHash でさらにグループ化（Danbooruでヒットしなかったものも拾う）
                for i in range(len(hashes)):
                    if hashes[i][2] is None: continue
                    for j in range(i+1, len(hashes)):
                        if hashes[j][2] is None: continue
                        if _hamming(hashes[i][2], hashes[j][2]) <= self._similar_thresh:
                            union(i, j)

                groups = dd2(list)
                for i, (n, f, _h) in enumerate(hashes):
                    groups[find(i)].append((n, f))
                sorted_groups = sorted(groups.values(), key=lambda g: min(x[0] for x in g))
                for g in sorted_groups:
                    g.sort(key=lambda x: x[0])

                flat = [f for g in sorted_groups for _, f in g]
                for new_n, f in enumerate(flat, start=1):
                    new_name = f"{base}_{new_n:03d}{f.suffix.lower()}"
                    new_path = f.parent / new_name
                    if f.name != new_name:
                        all_renames.append((f, new_path))

            result[0] = all_renames
            done_flag[0] = True

        def _poll():
            prog_bar["value"] = done_count[0]
            if done_count[0] > 0:
                prog_lbl.config(text=f"{done_count[0]} / {total_files}")
            if not done_flag[0]:
                self.root.after(80, _poll)
            else:
                prog_win.destroy()
                _show_confirm(result[0])

        threading.Thread(target=_worker, daemon=True).start()
        self.root.after(80, _poll)

        # ── 確認ダイアログ（計算完了後） ──
        def _show_confirm(all_renames):
            if not all_renames:
                messagebox.showinfo(t("btn_sim_sort"), t("sim_sort_none"))
                return
            if not self._rename_confirm_dialog(
                    t("sim_sort_title"),
                    t("sim_sort_msg", n=len(all_renames)),
                    all_renames):
                return
            self._stop_anim()
            self._atomic_rename_batch(all_renames)
            self.counter_var.set(t("sim_sort_done", n=len(all_renames)))
            self._load_images()

    # ── 一括番号修正 ──
    def fix_numbering(self):
        if not valid_dir(self.image_dir):
            return
        import re as _re

        # image_dir 直下 + 1段サブフォルダを対象
        dirs_to_scan = [self.image_dir] + [
            d for d in self.image_dir.iterdir() if d.is_dir()
        ]

        renames: list[tuple[Path, Path]] = []  # (old, new)
        vid_prefix  = self._prefix_var.get() if self._prefix_on_var.get() else ""
        multi_dir_name = self._multi_dir_var.get().strip()

        for d in dirs_to_scan:
            # (base, is_video) → [(current_n, path), ...]
            groups: dict[tuple[str, bool], list[tuple[int, Path]]] = {}
            pat = _re.compile(r"^(.+)_(\d+)$")
            folder_base    = d.name if d != self.image_dir else None
            is_multi_dir   = bool(folder_base and multi_dir_name and folder_base == multi_dir_name)

            for f in sorted(d.iterdir(), key=lambda x: x.name):
                if not f.is_file():
                    continue
                ext = f.suffix.lower()
                if ext not in ALL_EXTS:
                    continue
                is_vid = ext in VIDEO_EXTS | GIF_EXTS

                m_pat = pat.match(f.stem)
                if is_multi_dir:
                    # multi_dir 内: ファイル自身のbaseを維持して再採番のみ
                    if m_pat:
                        base_part = m_pat.group(1)
                        n         = int(m_pat.group(2))
                    else:
                        continue  # パターンなしは判断不能のためスキップ
                else:
                    # 通常フォルダ: 動画ならprefixつき、画像はそのまま
                    correct_base = ((vid_prefix + folder_base) if is_vid else folder_base) if folder_base else None
                    if m_pat:
                        base_part, num_str = m_pat.group(1), m_pat.group(2)
                        if correct_base and base_part != correct_base:
                            base_part = correct_base
                            n = 10000 + len(groups.get((correct_base, is_vid), []))
                        else:
                            n = int(num_str)
                    elif correct_base:
                        base_part = correct_base
                        n = 10000 + len(groups.get((correct_base, is_vid), []))
                    else:
                        continue

                key = (base_part, is_vid)
                groups.setdefault(key, []).append((n, f))

            for (base_part, is_vid), items in groups.items():
                # 拡張子でまとめ、その中で番号順→ファイル名順
                items.sort(key=lambda x: (x[1].suffix.lower(), x[0], x[1].name))
                for new_n, (_, path) in enumerate(items, start=1):
                    new_name = f"{base_part}_{new_n:03d}{path.suffix.lower()}"
                    new_path = path.parent / new_name
                    if path != new_path:
                        renames.append((path, new_path))

        if not renames:
            from tkinter import messagebox
            messagebox.showinfo(t("btn_fix"), t("fix_none"))
            return

        if not self._rename_confirm_dialog(
                t("fix_confirm_title"),
                t("fix_confirm_msg", n=len(renames)),
                renames):
            return

        self._stop_anim()
        self._atomic_rename_batch(renames)

        # ── リネームログ保存 ──
        import datetime
        log_path = self.image_dir / "rename_log.txt"
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [f"# {ts}  ({len(renames)} 件)\n"]
        for old, new in renames:
            lines.append(f"{old.parent.name}/{old.name}\t→\t{new.parent.name}/{new.name}\n")
        lines.append("\n")
        with open(log_path, "a", encoding="utf-8") as fp:
            fp.writelines(lines)

        self.counter_var.set(t("fix_done", n=len(renames)))
        self._load_images()


# ══════════════════════════════════════════════
#  Mixin: 設定ダイアログ・タグ一覧・設定保存
# ══════════════════════════════════════════════
class _SettingsMixin:
    """設定管理・作品リスト・タグ一覧の責務。
    SortApp に Mix-in される。self.root / self.cfg 等は SortApp が提供する。"""

    # ── 作品リスト非同期ロード ──
    def _load_work_list(self):
        try:
            works = get_tagger().get_work_list()
            def _set(w=works):
                self._work_all_list = w
                self._work_combo.config(values=w)
            self.root.after(0, _set)
        except Exception:
            pass

    def _on_work_key(self, event):
        # ナビ系キーは無視
        if event.keysym in ("Return", "Escape", "Tab", "Up", "Down",
                            "Shift_L", "Shift_R", "Control_L", "Control_R",
                            "Alt_L", "Alt_R"):
            return
        q = self._work_name_var.get().strip().lower()
        filtered = [w for w in self._work_all_list if q in w] if q else self._work_all_list
        self._work_combo.config(values=filtered)

    # ── 設定保存 ──
    def _save_work_name(self):
        self.cfg["work_name"] = self._work_name_var.get()
        save_config(self.cfg)

    def _save_auto_ai(self):
        self.cfg["auto_ai"] = self._auto_ai_var.get()
        save_config(self.cfg)

    def _save_multi_dir(self):
        self.cfg["multi_dir"] = self._multi_dir_var.get().strip()
        save_config(self.cfg)
        # フォルダリストを更新
        if valid_dir(self.image_dir):
            self.folders = get_folders(self.image_dir, self.source_dir, self._exclude_folders())

    def _exclude_folders(self) -> set[str]:
        ex = set()
        m = self._multi_dir_var.get().strip()
        if m:
            ex.add(m)
        return ex

    # ── 設定ウィンドウ ──
    def show_settings(self):
        win = tk.Toplevel(self.root)
        win.title(t("settings_title"))
        win.configure(bg="#1e1e1e")
        win.resizable(False, False)
        win.attributes("-topmost", True)
        win.grab_set()

        BG, FG, FG2 = "#1e1e1e", "#ccc", "#888"
        FONT  = ("Arial", 11)
        FONT2 = ("Arial", 9)
        SPIN  = dict(font=FONT, width=6, bg="#2a2a2a", fg=FG,
                     buttonbackground="#333", relief="flat")

        # gridで左列=ラベル・右列=コントロール（ラベルが自然幅で揃う）
        grid = tk.Frame(win, bg=BG)
        grid.pack(fill="x", padx=24, pady=(16, 4))
        grid.columnconfigure(0, weight=1)

        def lbl(row, key):
            tk.Label(grid, text=t(key), bg=BG, fg=FG, font=FONT,
                     anchor="w").grid(row=row, column=0, sticky="w", pady=3)

        # 言語
        lbl(0, "settings_lang")
        lang_options = {
            "日本語":   "ja",
            "English":  "en",
            "简体中文":  "zh-cn",
            "繁體中文":  "zh-tw",
            "한국어":   "ko",
            "Español":  "es",
            "Français": "fr",
            "Deutsch":  "de",
            "Русский":  "ru",
        }
        current_label = next((k for k, v in lang_options.items() if v == LANG), "English")
        lang_combo = ttk.Combobox(grid, values=list(lang_options.keys()),
                                  font=FONT, width=12, state="readonly")
        lang_combo.set(current_label)
        lang_combo.grid(row=0, column=1, sticky="w", padx=(12, 0), pady=3)

        # キャラ欄の数
        lbl(1, "settings_char_rows")
        char_rows_var = tk.IntVar(value=self._char_rows)
        tk.Spinbox(grid, from_=2, to=12, textvariable=char_rows_var,
                   **SPIN).grid(row=1, column=1, sticky="w", padx=(12, 0), pady=3)

        # 補完候補数
        lbl(2, "settings_ac_limit")
        ac_limit_var = tk.IntVar(value=self._ac_limit)
        tk.Spinbox(grid, from_=3, to=20, textvariable=ac_limit_var,
                   **SPIN).grid(row=2, column=1, sticky="w", padx=(12, 0), pady=3)

        # AI閾値
        lbl(3, "settings_ai_thresh")
        thresh_var = tk.DoubleVar(value=self._ai_threshold)
        tk.Spinbox(grid, from_=0.1, to=0.9, increment=0.05,
                   textvariable=thresh_var, format="%.2f",
                   **SPIN).grid(row=3, column=1, sticky="w", padx=(12, 0), pady=3)

        # 動画サンプルフレーム数
        lbl(4, "settings_vid_frames")
        vid_frames_var = tk.IntVar(value=self._vid_frames)
        tk.Spinbox(grid, from_=1, to=10, textvariable=vid_frames_var,
                   **SPIN).grid(row=4, column=1, sticky="w", padx=(12, 0), pady=3)

        # スキップ済みをリストから除く
        lbl(5, "settings_skip_remove")
        skip_remove_var = tk.BooleanVar(value=self._skip_remove)
        tk.Checkbutton(grid, variable=skip_remove_var, bg=BG,
                       selectcolor="#333", activebackground=BG,
                       relief="flat").grid(row=5, column=1, sticky="w", padx=(12, 0), pady=3)

        # キャラ順序を学習する
        lbl(6, "settings_char_order")
        learn_order_var = tk.BooleanVar(value=self._learn_order)
        tk.Checkbutton(grid, variable=learn_order_var, bg=BG,
                       selectcolor="#333", activebackground=BG,
                       relief="flat").grid(row=6, column=1, sticky="w", padx=(12, 0), pady=3)

        # 完全一致を自動削除
        lbl(7, "settings_dupe_check")
        dupe_check_var = tk.BooleanVar(value=self._dupe_check)
        tk.Checkbutton(grid, variable=dupe_check_var, bg=BG,
                       selectcolor="#333", activebackground=BG,
                       relief="flat").grid(row=7, column=1, sticky="w", padx=(12, 0), pady=3)

        # 類似画像を隣に挿入
        lbl(8, "settings_similar_ins")
        similar_ins_var = tk.BooleanVar(value=self._similar_insert)
        tk.Checkbutton(grid, variable=similar_ins_var, bg=BG,
                       selectcolor="#333", activebackground=BG,
                       relief="flat").grid(row=8, column=1, sticky="w", padx=(12, 0), pady=3)

        # 類似度閾値
        lbl(9, "settings_similar_thr")
        similar_thr_var = tk.IntVar(value=self._similar_thresh)
        tk.Spinbox(grid, from_=1, to=20, textvariable=similar_thr_var,
                   **SPIN).grid(row=9, column=1, sticky="w", padx=(12, 0), pady=3)

        # Danbooru
        tk.Frame(grid, bg="#444", height=1).grid(
            row=10, column=0, columnspan=2, sticky="ew", pady=(10, 4))
        lbl(11, "settings_danbooru")
        danbooru_var = tk.BooleanVar(value=self._danbooru_on)
        tk.Checkbutton(grid, variable=danbooru_var, bg=BG,
                       selectcolor="#333", activebackground=BG,
                       relief="flat").grid(row=11, column=1, sticky="w", padx=(12, 0), pady=3)

        lbl(12, "settings_db_login")
        db_login_var = tk.StringVar(value=self._danbooru_login)
        tk.Entry(grid, textvariable=db_login_var, bg="#333", fg="#eee",
                 insertbackground="#eee", font=FONT2, width=20,
                 relief="flat").grid(row=12, column=1, sticky="w", padx=(12, 0), pady=3)

        lbl(13, "settings_db_apikey")
        db_apikey_var = tk.StringVar(value=self._danbooru_apikey)
        tk.Entry(grid, textvariable=db_apikey_var, bg="#333", fg="#eee",
                 insertbackground="#eee", font=FONT2, width=20, show="*",
                 relief="flat").grid(row=13, column=1, sticky="w", padx=(12, 0), pady=3)

        # ボタン
        btn_row = tk.Frame(win, bg=BG)
        btn_row.pack(pady=(12, 14))

        def on_ok():
            new_lang      = lang_options.get(lang_combo.get(), LANG)
            new_char_rows = int(char_rows_var.get())
            needs_rebuild = (new_lang != LANG or new_char_rows != self._char_rows)

            self.cfg["lang"]            = new_lang
            self.cfg["char_rows"]       = new_char_rows
            self.cfg["ac_limit"]        = int(ac_limit_var.get())
            self.cfg["ai_threshold"]    = round(float(thresh_var.get()), 2)
            self.cfg["vid_frames"]      = int(vid_frames_var.get())
            self.cfg["skip_remove"]     = bool(skip_remove_var.get())
            self.cfg["learn_order"]     = bool(learn_order_var.get())
            self.cfg["dupe_check"]      = bool(dupe_check_var.get())
            self.cfg["similar_insert"]  = bool(similar_ins_var.get())
            self.cfg["similar_thresh"]  = int(similar_thr_var.get())
            self.cfg["danbooru_on"]     = bool(danbooru_var.get())
            self.cfg["danbooru_login"]  = db_login_var.get().strip()
            self.cfg["danbooru_apikey"] = db_apikey_var.get().strip()
            # 即時反映
            self._danbooru_on     = self.cfg["danbooru_on"]
            self._danbooru_login  = self.cfg["danbooru_login"]
            self._danbooru_apikey = self.cfg["danbooru_apikey"]
            self._skip_remove     = self.cfg["skip_remove"]
            self._ai_threshold    = self.cfg["ai_threshold"]
            self._learn_order     = self.cfg["learn_order"]
            self._dupe_check      = self.cfg["dupe_check"]
            self._similar_insert  = self.cfg["similar_insert"]
            self._similar_thresh  = self.cfg["similar_thresh"]
            self._ac_limit        = self.cfg["ac_limit"]
            self._vid_frames      = self.cfg["vid_frames"]
            save_config(self.cfg)
            win.destroy()
            if needs_rebuild:
                self._rebuild_ui()

        tk.Button(btn_row, text=t("settings_ok"), command=on_ok,
                  bg="#2ea44f", fg="white", font=FONT, padx=14).pack(side="left", padx=6)
        tk.Button(btn_row, text=t("settings_cancel"), command=win.destroy,
                  bg="#555", fg="white", font=FONT, padx=14).pack(side="left", padx=6)

        win.bind("<Return>", lambda e: on_ok())
        win.bind("<Escape>", lambda e: win.destroy())

    # ── タグ一覧ウィンドウ ──
    def show_tag_list(self):
        work_name = self._work_name_var.get()
        win = tk.Toplevel(self.root)
        win.title(t("tag_win_title", w=work_name) if work_name
                  else t("tag_win_title_all"))
        win.configure(bg="#1e1e1e")
        win.geometry("420x560")
        win.attributes("-topmost", True)

        # 読み込み中ラベル
        status_var = tk.StringVar(value=t("tag_loading"))
        status_lbl = tk.Label(win, textvariable=status_var,
                              bg="#1e1e1e", fg="#aaa", font=("Arial", 10))
        status_lbl.pack(pady=(6, 0))

        # 検索
        search_frame = tk.Frame(win, bg="#1e1e1e")
        search_frame.pack(fill="x", padx=10, pady=4)
        tk.Label(search_frame, text="🔍", bg="#1e1e1e", fg="#aaa",
                 font=("Arial", 12)).pack(side="left")
        search_var = tk.StringVar()
        search_e = ttk.Entry(search_frame, textvariable=search_var,
                             font=("Arial", 11), width=26)
        search_e.pack(side="left", padx=4)
        count_var = tk.StringVar()
        tk.Label(search_frame, textvariable=count_var, bg="#1e1e1e",
                 fg="#888", font=("Arial", 9)).pack(side="left", padx=4)

        # リストボックス
        list_frame = tk.Frame(win, bg="#1e1e1e")
        list_frame.pack(fill="both", expand=True, padx=10, pady=(0, 4))
        scrollbar = ttk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        listbox = tk.Listbox(list_frame, bg="#2a2a2a", fg="#eeeeee",
                             font=("Arial", 11), selectbackground="#4a2a6a",
                             yscrollcommand=scrollbar.set,
                             activestyle="none", relief="flat")
        listbox.pack(fill="both", expand=True)
        scrollbar.config(command=listbox.yview)

        tk.Label(win, text=t("tag_hint"), bg="#1e1e1e",
                 fg="#666", font=("Arial", 9)).pack(pady=(0, 6))

        all_tags: list[str] = []

        def populate(tags):
            all_tags.clear()
            all_tags.extend(tags)
            _update_list()

        def _update_list(*_):
            q = search_var.get().strip().lower()
            filtered = [tag for tag in all_tags if q in tag] if q else all_tags
            listbox.delete(0, "end")
            for tag in filtered:
                listbox.insert("end", tag)
            count_var.set(t("tag_count", n=len(filtered)))

        def on_select(event):
            sel = listbox.curselection()
            if not sel:
                return
            tag = listbox.get(sel[0])
            for e in self.char_entries:
                if not e.get():
                    e.set(tag)
                    break

        listbox.bind("<<ListboxSelect>>", on_select)
        search_var.trace_add("write", _update_list)

        def load_tags():
            try:
                tags = get_tagger().get_tag_list(work_name)
                _msg = t("tag_done", n=len(tags), w=work_name) if work_name else t("tag_done_all", n=len(tags))
                win.after(0, lambda msg=_msg, tgs=tags: (
                    status_var.set(msg),
                    populate(tgs)
                ))
            except Exception as ex:
                win.after(0, lambda e=ex: status_var.set(t("tag_error", ex=e)))

        threading.Thread(target=load_tags, daemon=True).start()
        search_e.focus()

    def _save_prefix(self):
        self.cfg["vid_prefix_on"]  = self._prefix_on_var.get()
        self.cfg["vid_prefix_val"] = self._prefix_var.get()
        save_config(self.cfg)

    def _save_position(self):
        if self.images and 0 <= self.index < len(self.images):
            self.cfg["last_file"]       = str(self.images[self.index])
            self.cfg["last_source_dir"] = str(self.source_dir)
            save_config(self.cfg)


# ══════════════════════════════════════════════
#  Mixin: 操作・ナビゲーション・メディア表示
# ══════════════════════════════════════════════
class _OpsMixin:
    """ディレクトリ管理・画像ナビゲーション・メディア再生・ファイル操作の責務。
    SortApp に Mix-in される。self.root / self.images / self.cfg 等は SortApp が提供する。"""
    def toggle_folder(self):
        self.use_folder = not self.use_folder
        self.folder_btn.config(
            bg="#2a6a2a" if self.use_folder else "#444",
            fg="white"   if self.use_folder else "#aaaaaa",
            text=t("folder_on") if self.use_folder else t("folder_off"))

    def _swap_entries(self, a: int, b: int):
        if not (0 <= a < len(self.char_entries) and 0 <= b < len(self.char_entries)):
            return
        val_a = self.char_entries[a].get()
        val_b = self.char_entries[b].get()
        self.char_entries[a].set(val_b)
        self.char_entries[b].set(val_a)

    def _clear_inputs(self):
        for e in self.char_entries:
            e.clear()

    # ── フォルダ履歴 ──
    def _push_history(self, key, path_str):
        hist = self.cfg.get(key, [])
        if path_str in hist:
            hist.remove(path_str)
        hist.insert(0, path_str)
        self.cfg[key] = hist[:10]
        return self.cfg[key]

    def _apply_dir(self, primary: str):
        """振り分け先/仕分け元フォルダ適用の共通処理。
        primary="image"|"source" で主対象を指定。
        もう一方が未設定の場合は同じパスを自動セット。"""
        is_image  = (primary == "image")
        pri_var   = self.image_dir_var   if is_image else self.source_dir_var
        fb_var    = self.source_dir_var  if is_image else self.image_dir_var
        pri_hist  = "image_history"      if is_image else "source_history"
        fb_hist   = "source_history"     if is_image else "image_history"
        pri_combo = self.image_combo     if is_image else self.source_combo
        fb_combo  = self.source_combo    if is_image else self.image_combo
        pri_cfg   = "image_dir"          if is_image else "source_dir"
        fb_cfg    = "source_dir"         if is_image else "image_dir"
        fb_attr   = "source_dir"         if is_image else "image_dir"

        path = Path(pri_var.get().strip())
        if not valid_dir(path):
            return

        # 主対象を更新
        if is_image:
            self.image_dir = path
        else:
            self.source_dir = path
        pri_combo["values"] = self._push_history(pri_hist, str(path))
        self.cfg[pri_cfg] = str(path)

        # もう一方が未設定なら同じパスを自動セット
        if not valid_dir(getattr(self, fb_attr)):
            setattr(self, fb_attr, path)
            fb_var.set(str(path))
            fb_combo["values"] = self._push_history(fb_hist, str(path))
            self.cfg[fb_cfg] = str(path)

        save_config(self.cfg)
        if valid_dir(self.image_dir) and valid_dir(self.source_dir):
            self._load_images()

    def _apply_image_dir(self):
        self._apply_dir("image")

    def _apply_source_dir(self):
        self._apply_dir("source")

    def select_image_dir(self):
        init = str(self.image_dir) if valid_dir(self.image_dir) else "/"
        path = filedialog.askdirectory(title=t("select_dest"), initialdir=init)
        if path:
            self.image_dir_var.set(path)
            self._apply_image_dir()

    def select_source_dir(self):
        init = str(self.source_dir) if valid_dir(self.source_dir) else "/"
        path = filedialog.askdirectory(title=t("select_source"), initialdir=init)
        if path:
            self.source_dir_var.set(path)
            self._apply_source_dir()

    # ── ファイル読み込み・再開 ──
    def _load_images(self):
        self.folders = get_folders(self.image_dir, self.source_dir, self._exclude_folders())
        self.images  = sorted([p for p in self.source_dir.iterdir()
                                if p.is_file() and p.suffix.lower() in ALL_EXTS],
                               key=lambda p: (p.stat().st_mtime, p.name))
        self.index   = self._resume_index()
        self.show_image()

    def _resume_index(self) -> int:
        last_file  = self.cfg.get("last_file", "")
        last_src   = self.cfg.get("last_source_dir", "")
        # 保存時と同じ source_dir の場合のみ復元
        if last_file and last_src == str(self.source_dir):
            last_path = Path(last_file)
            # 完全一致
            for i, p in enumerate(self.images):
                if p == last_path:
                    return i
            # ファイル名一致（移動されてない場合の保険）
            for i, p in enumerate(self.images):
                if p.name == last_path.name:
                    return i
        return 0

    # ── アニメーション停止 ──
    def _stop_anim(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None
        if self._video_cap:
            self._video_cap.release()
            self._video_cap = None
        self._gif_frames = []
        self._gif_delays = []

    def _tick_gif(self, idx):
        """GIFアニメーション1フレームを表示し次フレームをスケジュール。
        処理が遅れた場合は経過時間分のフレームをスキップして同期を維持する。"""
        if not self._gif_frames:
            return
        now = time.perf_counter()
        elapsed_ms = (now - self._last_frame_t) * 1000  # GIF は常に1倍速
        self._last_frame_t = now
        # 経過時間に合わせてフレームをスキップ（重い処理後の大幅遅延を補正）
        acc = 0.0
        while acc < elapsed_ms:
            acc += self._gif_delays[idx % len(self._gif_frames)]
            if acc < elapsed_ms:
                idx = (idx + 1) % len(self._gif_frames)
        self.tk_img = self._gif_frames[idx]
        self.img_label.config(image=self.tk_img)
        self._anim_job = self.root.after(16, self._tick_gif, (idx+1) % len(self._gif_frames))

    def _play_video_stream(self, cap):
        now = time.perf_counter()
        elapsed = now - self._last_frame_t
        self._last_frame_t = now
        skip = max(0, int(elapsed * self._video_fps * self._playback_speed) - 1)
        for _ in range(skip):
            if not cap.grab():
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        ret, frame = cap.read()
        if not ret:
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = cap.read()
        if ret:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img.thumbnail((900, 440), Image.LANCZOS)
            self.tk_img = ImageTk.PhotoImage(img)
            self.img_label.config(image=self.tk_img)
        self._anim_job = self.root.after(16, self._play_video_stream, cap)

    # ── 表示 ──
    def show_image(self):
        """self.images（_load_imagesで構築済み）を使って表示する。ディスク再スキャンはしない。"""
        self._stop_anim()
        # 範囲外補正
        if self.index >= len(self.images):
            self.index = max(0, len(self.images) - 1)

        if not self.images:
            self.img_label.config(image="", text=t("all_done"), fg="white", font=("Arial", 24))
            self.counter_var.set(t("all_done_counter"))
            self.media_type_var.set("")
            return

        path = self.images[self.index]
        ext  = path.suffix.lower()
        self.counter_var.set(t("counter", cur=self.index+1,
                               total=len(self.images), rem=len(self.images)-self.index-1))
        self.name_var.set(path.name)

        try:
            if ext in GIF_EXTS:
                self.media_type_var.set(t("media_gif"))
                frames, delays = load_gif_frames(path)
                if frames:
                    self._gif_frames   = frames
                    self._gif_delays   = delays
                    self._last_frame_t = time.perf_counter()
                    self._tick_gif(0)
                else:
                    self.img_label.config(image="", text=t("gif_error"))
            elif ext in VIDEO_EXTS:
                self.media_type_var.set(t("media_video"))
                if HAS_CV2:
                    cap = cv2.VideoCapture(str(path))
                    self._video_fps    = cap.get(cv2.CAP_PROP_FPS) or 30
                    self._video_cap    = cap
                    self._last_frame_t = time.perf_counter()
                    self._play_video_stream(cap)
                else:
                    self.img_label.config(image="", text=t("video_no_cv2"))
            else:
                self.media_type_var.set("")
                img = Image.open(path)
                img.thumbnail((900, 440), Image.LANCZOS)
                self.tk_img = ImageTk.PhotoImage(img)
                self.img_label.config(image=self.tk_img, text="")
        except Exception as ex:
            self.img_label.config(image="", text=t("load_error", ex=ex))

        if not self._keep_names:
            self._clear_inputs()
        self.char_entries[0].focus()
        self._save_position()
        if self._auto_ai_var.get():
            self.root.after(50, self.analyze_ai)
        if self._danbooru_on and self.images:
            path = self.images[self.index]
            if path.suffix.lower() in IMG_EXTS:
                threading.Thread(target=self._run_danbooru,
                                 args=(path,), daemon=True).start()

    # ── アクション ──
    def move(self):
        if not self.images:
            return
        src   = self.images[self.index]
        names = [e.get() for e in self.char_entries if e.get()]
        if not names:
            return
        base = "_".join(names)
        if self.use_folder and len(names) == 1:
            dest_dir = self.image_dir / base
            dest_dir.mkdir(exist_ok=True)
        elif len(names) >= 2:
            multi_sub = self._multi_dir_var.get().strip()
            dest_dir = (self.image_dir / multi_sub) if multi_sub else self.image_dir
            dest_dir.mkdir(exist_ok=True)
        else:
            dest_dir = self.image_dir

        is_video = src.suffix.lower() in VIDEO_EXTS | GIF_EXTS
        prefix = self._prefix_var.get() if (is_video and self._prefix_on_var.get()) else ""

        # 画像・動画グループをまたいで連番を共有
        group_exts = VIDEO_EXTS | GIF_EXTS if is_video else IMG_EXTS
        import re as _re
        pat = _re.compile(rf"^{_re.escape(prefix)}{_re.escape(base)}_(\d+)\.")

        # dest_dir のファイル一覧を1回だけ取得してキャッシュ（MD5/類似/max_n で使い回す）
        # src が dest_dir 内にある場合（同フォルダ再仕分け）は自分自身を除外する
        dest_files = [f for f in dest_dir.iterdir() if f.is_file() and f != src]

        # ── 完全一致チェック（MD5）──
        if self._dupe_check:
            src_md5 = _file_md5(src)
            if src_md5:
                for f in dest_files:
                    if f.suffix.lower() in group_exts:
                        if _file_md5(f) == src_md5:
                            # 完全一致 → ソースをゴミ箱へ
                            self._stop_anim()
                            if HAS_TRASH:
                                send2trash(str(src))
                            else:
                                src.unlink()
                            self.counter_var.set(t("dupe_deleted", matched=f.name))
                            self.images.pop(self.index)
                            if self.index >= len(self.images):
                                self.index = max(0, len(self.images) - 1)
                            if not self._keep_names:
                                self._clear_inputs()
                            self.show_image()
                            return

        # ── 類似画像チェック（dHash）── 画像のみ
        insert_after_n = None
        if self._similar_insert and not is_video and src.suffix.lower() in IMG_EXTS:
            src_hash = _dhash(src)
            if src_hash is not None:
                best_dist = self._similar_thresh + 1
                best_n    = None
                for f in dest_files:
                    if f.suffix.lower() in IMG_EXTS:
                        m = pat.match(f.name)
                        if m:
                            fh = _dhash(f)
                            if fh is not None:
                                d = _hamming(src_hash, fh)
                                if d <= self._similar_thresh and d < best_dist:
                                    best_dist = d
                                    best_n = int(m.group(1))
                if best_n is not None:
                    insert_after_n = best_n

        # ── 移動 ──
        self._stop_anim()
        if insert_after_n is not None:
            # 類似あり → 直後に挿入（後続ファイルを繰り上げ）
            dest = self._insert_after(src, dest_dir, prefix + base, insert_after_n, group_exts)
            self.counter_var.set(t("similar_inserted", n=f"{insert_after_n:03d}"))
        else:
            max_n = 0
            for f in dest_files:
                if f.suffix.lower() in group_exts:
                    m = pat.match(f.name)
                    if m:
                        max_n = max(max_n, int(m.group(1)))
            n = max_n + 1
            dest = dest_dir / f"{prefix}{base}_{n:03d}{src.suffix.lower()}"
            while dest.exists():
                n += 1
                dest = dest_dir / f"{prefix}{base}_{n:03d}{src.suffix.lower()}"
            shutil.move(str(src), str(dest))

        self._last_move_dest = dest   # 類似整列で使う
        self.history.append(("move", dest, src))
        self._update_char_order(names)
        self.images.pop(self.index)
        if self.index >= len(self.images):
            self.index = max(0, len(self.images) - 1)
        self.folders = get_folders(self.image_dir, self.source_dir, self._exclude_folders())
        self.show_image()

    # ── 類似画像挿入 ──
    def _insert_after(self, src: Path, dest_dir: Path, full_base: str,
                      insert_after_n: int, group_exts: set) -> Path:
        """insert_after_n の直後に src を挿入し後続ファイルを1つ繰り上げ"""
        import re as _re
        pat = _re.compile(rf"^{_re.escape(full_base)}_(\d+)\.")
        # insert_after_n より大きい番号を降順で取得してシフト
        to_shift = []
        for f in dest_dir.iterdir():
            if f.is_file() and f.suffix.lower() in group_exts:
                m = pat.match(f.name)
                if m and int(m.group(1)) > insert_after_n:
                    to_shift.append((int(m.group(1)), f))
        to_shift.sort(key=lambda x: -x[0])  # 降順（高い番号から処理して衝突回避）
        for n, f in to_shift:
            f.rename(f.parent / f"{full_base}_{n + 1:03d}{f.suffix.lower()}")
        # ソース移動
        new_n = insert_after_n + 1
        dest = dest_dir / f"{full_base}_{new_n:03d}{src.suffix.lower()}"
        while dest.exists():  # 稀な拡張子衝突への保険
            new_n += 1
            dest = dest_dir / f"{full_base}_{new_n:03d}{src.suffix.lower()}"
        shutil.move(str(src), str(dest))
        return dest

    # ── キャラ順序学習 ──
    def _update_char_order(self, chars: list[str]):
        """moveのたびにキャラの相対順序をconfigへ保存"""
        if not self._learn_order or not chars:
            return
        order: list[str] = self.cfg.get("char_order", [])
        # 今回のキャラが既存リストで最初に登場するインデックスを基準に挿入
        existing_indices = [order.index(c) for c in chars if c in order]
        insert_pos = min(existing_indices) if existing_indices else len(order)
        # 今回のキャラをいったん除去
        base = [c for c in order if c not in chars]
        # insert_posより前にある要素数を数えて実際の挿入位置を決める
        actual_pos = sum(1 for c in order[:insert_pos] if c not in chars)
        new_order = base[:actual_pos] + chars + base[actual_pos:]
        self.cfg["char_order"] = new_order
        save_config(self.cfg)

    def _sort_by_learned_order(self, names: list[str]) -> list[str]:
        """学習済み順序でソート（未登録は末尾）。辞書引きでO(1)"""
        order: list[str] = self.cfg.get("char_order", [])
        if not order:
            return names
        rank = {c: i for i, c in enumerate(order)}  # O(n)で事前構築
        return sorted(names, key=lambda c: rank.get(c, len(order)))

    def prev_image(self):
        if not self.images:
            return
        self.index = (self.index - 1) % len(self.images)
        self.show_image()

    def skip(self):
        if not self.images:
            return
        if self._skip_remove:
            self._stop_anim()
            self.images.pop(self.index)
            if self.index >= len(self.images):
                self.index = 0
        else:
            self.index = (self.index + 1) % len(self.images)
        self.show_image()

    def delete_current(self):
        if not self.images:
            return
        path = self.images[self.index]
        self._stop_anim()
        if HAS_TRASH:
            send2trash(str(path))
        else:
            path.unlink()
        self.history.append(("delete", path, None))
        self.images.pop(self.index)
        if self.index >= len(self.images):
            self.index = max(0, len(self.images) - 1)
        self.show_image()

    def undo(self):
        if not self.history:
            return
        action = self.history.pop()
        if action[0] == "move":
            _, dest, orig = action
            if dest.exists():
                self._stop_anim()
                shutil.move(str(dest), str(orig))
                # 移動先フォルダが空になったら削除（image_dir 直下のサブフォルダのみ）
                parent = dest.parent
                if (parent != self.image_dir and
                        parent.is_dir() and not any(parent.iterdir())):
                    parent.rmdir()
                    self.folders = get_folders(self.image_dir, self.source_dir, self._exclude_folders())
                # 元のパスを self.images に挿入して表示位置を戻す
                if orig not in self.images:
                    self.images.insert(self.index, orig)
        elif action[0] == "delete":
            # ゴミ箱からの復元は自動では難しいのでスキップ
            pass
        self.show_image()

    def _toggle_keep_names(self):
        self._keep_names = not self._keep_names
        if self._keep_names:
            self.keep_btn.config(text=t("btn_keep_on"), bg="#1a4a2a", fg="#88ffaa")
        else:
            self.keep_btn.config(text=t("btn_keep_off"), bg="#2a2a2a", fg="#888")

    def cycle_speed(self):
        try:
            idx = self._speed_steps.index(self._playback_speed)
        except ValueError:
            idx = 1
        self._playback_speed = self._speed_steps[(idx+1) % len(self._speed_steps)]
        s = self._playback_speed
        label = f"🐢 {s}x" if s < 1 else f"🐇 {s}x" if s == 1.0 else f"⚡ {s}x"
        self.speed_btn.config(text=label)

    def play_current(self):
        if not self.images:
            return
        os.startfile(str(self.images[self.index]))




# ══════════════════════════════════════════════
#  SortApp
# ══════════════════════════════════════════════
class SortApp(_AIMixin, _SortMixin, _SettingsMixin, _OpsMixin):
    def __init__(self, root):
        self.root = root
        self.root.title("CharaSorter")
        self.root.configure(bg="#1e1e1e")
        self.root.geometry("1100x920")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        self.cfg        = load_config()
        self.image_dir  = Path(self.cfg.get("image_dir",  "."))
        self.source_dir = Path(self.cfg.get("source_dir", "."))
        self.history    = []
        self.use_folder = True
        self.images     = []
        self.index      = 0
        self.folders    = []

        self._vid_prefix_on  = self.cfg.get("vid_prefix_on",  False)
        self._vid_prefix_val = self.cfg.get("vid_prefix_val", "")
        self._work_name_val  = self.cfg.get("work_name", "")
        self._multi_dir_val  = self.cfg.get("multi_dir", "")
        self._auto_ai_val    = self.cfg.get("auto_ai", False)

        # 設定項目（再起動で反映）
        self._char_rows    = int(self.cfg.get("char_rows",   6))
        self._ac_limit     = int(self.cfg.get("ac_limit",    8))
        self._ai_threshold = float(self.cfg.get("ai_threshold", 0.25))
        self._vid_frames   = int(self.cfg.get("vid_frames",  3))
        self._skip_remove  = bool(self.cfg.get("skip_remove", False))
        self._learn_order  = bool(self.cfg.get("learn_order", True))
        self._keep_names      = False  # キャラ名保持モード（セッション限り）
        self._last_move_dest  = None   # 最後に移動したファイルのPath（類似整列用）
        self._dupe_check      = bool(self.cfg.get("dupe_check",     True))
        self._similar_insert  = bool(self.cfg.get("similar_insert", True))
        self._similar_thresh  = int(self.cfg.get("similar_thresh",  8))
        self._danbooru_on     = bool(self.cfg.get("danbooru_on",    True))
        self._danbooru_login  = self.cfg.get("danbooru_login",  "")
        self._danbooru_apikey = self.cfg.get("danbooru_apikey", "")

        self._anim_job       = None
        self._gif_frames     = []
        self._gif_delays     = []
        self._video_cap      = None
        self._video_fps      = 30.0
        self._playback_speed = 1.0
        self._speed_steps    = [0.5, 1.0, 1.5, 2.0, 3.0]
        self._last_frame_t   = 0.0

        self._build_ui()

        if valid_dir(self.image_dir) and valid_dir(self.source_dir):
            self._load_images()
        else:
            self.counter_var.set(t("please_select"))

    # ──────────────────────────────────────────
    def _rebuild_ui(self):
        """言語・char_rows変更時にUIを再構築する"""
        global LANG
        LANG = self.cfg.get("lang", LANG)
        self._char_rows = int(self.cfg.get("char_rows", 6))
        self._ac_limit  = int(self.cfg.get("ac_limit",  8))
        self._stop_anim()
        idx = self.index
        for w in self.root.winfo_children():
            w.destroy()
        self.root.title("CharaSorter")
        self._build_ui()
        if valid_dir(self.image_dir) and valid_dir(self.source_dir):
            self._load_images()
            self.index = min(idx, max(0, len(self.images) - 1))
            self.show_image()
        else:
            self.counter_var.set(t("please_select"))

    # ──────────────────────────────────────────
    def _build_ui(self):
        # ── フォルダバー ──
        folder_bar = tk.Frame(self.root, bg="#2a2a2a", pady=4)
        folder_bar.pack(fill="x")

        tk.Label(folder_bar, text=t("dest"), bg="#2a2a2a", fg="#aaa",
                 font=("Arial", 10)).pack(side="left", padx=(10, 2))
        self.image_dir_var = tk.StringVar(
            value=str(self.image_dir) if valid_dir(self.image_dir) else "")
        self.image_combo = ttk.Combobox(folder_bar, textvariable=self.image_dir_var,
                                        values=self.cfg.get("image_history", []),
                                        width=28, font=("Arial", 9))
        self.image_combo.pack(side="left", padx=(0, 2))
        self.image_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_image_dir())
        self.image_combo.bind("<Return>", lambda e: (self._apply_image_dir(), "break"))
        tk.Button(folder_bar, text="📂", command=self.select_image_dir,
                  bg="#444", fg="white", font=("Arial", 9), padx=4).pack(side="left")

        tk.Label(folder_bar, text=t("source"), bg="#2a2a2a", fg="#aaa",
                 font=("Arial", 10)).pack(side="left", padx=(12, 2))
        self.source_dir_var = tk.StringVar(
            value=str(self.source_dir) if valid_dir(self.source_dir) else "")
        self.source_combo = ttk.Combobox(folder_bar, textvariable=self.source_dir_var,
                                         values=self.cfg.get("source_history", []),
                                         width=28, font=("Arial", 9))
        self.source_combo.pack(side="left", padx=(0, 2))
        self.source_combo.bind("<<ComboboxSelected>>", lambda e: self._apply_source_dir())
        self.source_combo.bind("<Return>", lambda e: (self._apply_source_dir(), "break"))
        tk.Button(folder_bar, text="📂", command=self.select_source_dir,
                  bg="#444", fg="white", font=("Arial", 9), padx=4).pack(side="left")

        tk.Button(folder_bar, text="⚙", command=self.show_settings,
                  bg="#2a2a2a", fg="#aaa", font=("Arial", 12),
                  relief="flat", padx=6, pady=0,
                  activebackground="#3a3a3a", activeforeground="#fff",
                  cursor="hand2").pack(side="right", padx=(0, 4))

        self.folder_btn = tk.Button(folder_bar, text=t("folder_on"),
                                    command=self.toggle_folder,
                                    bg="#2a6a2a", fg="white",
                                    font=("Arial", 10, "bold"), padx=8)
        self.folder_btn.pack(side="right", padx=10)

        # ── オプション行 ──
        opt_bar = tk.Frame(self.root, bg="#242424", pady=2)
        opt_bar.pack(fill="x")

        # 作品名（AI分析フィルタ）
        tk.Label(opt_bar, text=t("work_name"), bg="#242424", fg="#bb88ff",
                 font=("Arial", 10, "bold")).pack(side="left", padx=(10, 2))
        self._work_name_var = tk.StringVar(value=self._work_name_val)
        self._work_all_list: list[str] = []   # 全作品リスト（フィルタ元）
        self._work_combo = ttk.Combobox(opt_bar, textvariable=self._work_name_var,
                                        values=[], font=("Arial", 10), width=16)
        self._work_combo.pack(side="left", padx=(0, 2))
        self._work_combo.bind("<KeyRelease>",        self._on_work_key)
        self._work_combo.bind("<FocusOut>",          lambda e: self._save_work_name())
        self._work_combo.bind("<Return>",            lambda e: (self._save_work_name(),
                                                                self._work_combo.after(10, self._work_combo.tk_focusNext().focus), "break"))
        self._work_combo.bind("<<ComboboxSelected>>",lambda e: self._save_work_name())
        tk.Button(opt_bar, text="📋", command=self.show_tag_list,
                  bg="#3a2a5a", fg="#bb88ff", font=("Arial", 10), padx=4,
                  relief="flat").pack(side="left", padx=(2, 2))
        tk.Label(opt_bar, text=t("work_hint"), bg="#242424", fg="#666",
                 font=("Arial", 9)).pack(side="left", padx=(0, 14))
        # AI自動分析
        self._auto_ai_var = tk.BooleanVar(value=self._auto_ai_val)
        tk.Checkbutton(opt_bar, text=t("auto_ai"), variable=self._auto_ai_var,
                       bg="#242424", fg="#bb88ff", selectcolor="#333",
                       activebackground="#242424", activeforeground="#fff",
                       font=("Arial", 10, "bold"),
                       command=self._save_auto_ai).pack(side="left", padx=(0, 14))

        # バックグラウンドで作品リストを読み込む
        threading.Thread(target=self._load_work_list, daemon=True).start()

        # 複数人フォルダ
        tk.Label(opt_bar, text=t("multi_folder"), bg="#242424", fg="#aaa",
                 font=("Arial", 10)).pack(side="left", padx=(0, 2))
        self._multi_dir_var = tk.StringVar(value=self._multi_dir_val)
        multi_e = ttk.Entry(opt_bar, textvariable=self._multi_dir_var,
                            font=("Arial", 10), width=10)
        multi_e.pack(side="left", padx=(0, 2))
        multi_e.bind("<FocusOut>", lambda e: self._save_multi_dir())
        multi_e.bind("<Return>",   lambda e: (self._save_multi_dir(), "break"))
        tk.Label(opt_bar, text=t("multi_hint"),
                 bg="#242424", fg="#666", font=("Arial", 9)).pack(side="left", padx=(0, 14))

        # 動画prefix
        self._prefix_on_var = tk.BooleanVar(value=self._vid_prefix_on)
        tk.Checkbutton(opt_bar, text=t("vid_prefix"), variable=self._prefix_on_var,
                       bg="#242424", fg="#aaa", selectcolor="#333",
                       activebackground="#242424", activeforeground="#fff",
                       font=("Arial", 10), command=self._save_prefix).pack(side="left", padx=(0, 2))
        self._prefix_var = tk.StringVar(value=self._vid_prefix_val)
        prefix_e = ttk.Entry(opt_bar, textvariable=self._prefix_var,
                             font=("Arial", 10), width=10)
        prefix_e.pack(side="left", padx=(0, 4))
        prefix_e.bind("<FocusOut>", lambda e: self._save_prefix())
        prefix_e.bind("<Return>",   lambda e: (self._save_prefix(), "break"))
        tk.Label(opt_bar, text=t("prefix_hint"),
                 bg="#242424", fg="#666", font=("Arial", 9)).pack(side="left")

        # ── カウンター・画像・ファイル名 ──
        self.counter_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.counter_var,
                 bg="#1e1e1e", fg="#aaaaaa", font=("Arial", 11)).pack(pady=(6, 0))

        self.img_label = tk.Label(self.root, bg="#1e1e1e")
        self.img_label.pack(expand=True, fill="both", padx=10)

        self.media_type_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.media_type_var,
                 bg="#1e1e1e", fg="#5599ff", font=("Arial", 11, "bold")).pack()

        self.name_var = tk.StringVar()
        tk.Label(self.root, textvariable=self.name_var,
                 bg="#1e1e1e", fg="#cccccc", font=("Arial", 10)).pack()

        # ── キャラ入力欄 ──
        input_area = tk.Frame(self.root, bg="#1e1e1e")
        input_area.pack(fill="x", pady=(6, 0))
        self.char_entries = []
        for i in range(self._char_rows):
            row = tk.Frame(input_area, bg="#1e1e1e")
            row.pack(fill="x", padx=20, pady=1)
            e = CharEntry(row, lambda: self.folders, label=t("char_label", n=i+1), ac_limit=self._ac_limit)
            e.frame.pack(side="left")
            # ↑↓ ボタン（横並び・Tab対象外）
            btn_frame = tk.Frame(row, bg="#1e1e1e")
            btn_frame.pack(side="left", padx=(4, 0))
            n_entries = 6
            up_active   = i > 0
            down_active = i < n_entries - 1
            tk.Button(btn_frame, text="↑", width=3,
                      bg="#2a3a5a" if up_active else "#2a2a2a",
                      fg="#88aaff" if up_active else "#555",
                      font=("Arial", 9, "bold"), relief="flat", takefocus=False,
                      state="normal" if up_active else "disabled",
                      command=lambda idx=i: self._swap_entries(idx, idx-1)
                      ).pack(side="left", padx=1)
            tk.Button(btn_frame, text="↓", width=3,
                      bg="#2a3a5a" if down_active else "#2a2a2a",
                      fg="#88aaff" if down_active else "#555",
                      font=("Arial", 9, "bold"), relief="flat", takefocus=False,
                      state="normal" if down_active else "disabled",
                      command=lambda idx=i: self._swap_entries(idx, idx+1)
                      ).pack(side="left", padx=1)
            self.char_entries.append(e)
        # siblings を設定（自分以外の全エントリ）
        for e in self.char_entries:
            e.siblings = [o for o in self.char_entries if o is not e]

        # ── ボタン行1 ──
        btn1 = tk.Frame(self.root, bg="#1e1e1e")
        btn1.pack(pady=(6, 2))
        tk.Button(btn1, text=t("btn_move"), command=self.move,
                  bg="#2ea44f", fg="white", font=("Arial", 12), width=16).pack(side="left", padx=4)
        tk.Button(btn1, text=t("btn_prev"), command=self.prev_image,
                  bg="#444", fg="white", font=("Arial", 12), width=14).pack(side="left", padx=4)
        tk.Button(btn1, text=t("btn_skip"), command=self.skip,
                  bg="#444", fg="white", font=("Arial", 12), width=14).pack(side="left", padx=4)
        tk.Button(btn1, text=t("btn_delete"), command=self.delete_current,
                  bg="#7a1a1a", fg="white", font=("Arial", 12), width=14).pack(side="left", padx=4)
        tk.Button(btn1, text=t("btn_undo"), command=self.undo,
                  bg="#6e6e6e", fg="white", font=("Arial", 12), width=12).pack(side="left", padx=4)

        # ── ボタン行2 ──
        btn2 = tk.Frame(self.root, bg="#1e1e1e")
        btn2.pack(pady=(0, 4))
        self.ai_btn = tk.Button(btn2, text=t("btn_ai"), command=self.analyze_ai,
                                bg="#4a2a6a", fg="white", font=("Arial", 12), width=16)
        self.ai_btn.pack(side="left", padx=4)
        tk.Button(btn2, text=t("btn_play"), command=self.play_current,
                  bg="#1a4a7a", fg="white", font=("Arial", 12), width=16).pack(side="left", padx=4)
        self.speed_btn = tk.Button(btn2, text="🐇 1.0x", command=self.cycle_speed,
                                   bg="#5a3a00", fg="white", font=("Arial", 12), width=8)
        self.speed_btn.pack(side="left", padx=4)
        tk.Button(btn2, text=t("btn_fix"), command=self.fix_numbering,
                  bg="#3a3a00", fg="#ffff88", font=("Arial", 12), width=10).pack(side="left", padx=4)
        tk.Button(btn2, text=t("btn_sim_sort"), command=self.sort_by_similarity,
                  bg="#003a3a", fg="#88ffff", font=("Arial", 12)).pack(side="left", padx=4)
        self.keep_btn = tk.Button(btn2, text=t("btn_keep_off"),
                                  command=self._toggle_keep_names,
                                  bg="#2a2a2a", fg="#888", font=("Arial", 12))
        self.keep_btn.pack(side="left", padx=4)

        tk.Label(self.root, text=t("hotkeys"),
                 bg="#1e1e1e", fg="#666", font=("Arial", 9)).pack()
        tk.Frame(self.root, bg="#1e1e1e", height=10).pack(fill="x")

        # ── キーバインド ──
        # Ctrl+小文字と大文字の両方に同じコマンドをバインドするヘルパー
        def _bind(key: str, cmd):
            self.root.bind(f"<Control-{key.lower()}>", lambda e: cmd())
            self.root.bind(f"<Control-{key.upper()}>", lambda e: cmd())

        self.root.bind("<Control-Return>", lambda e: self.move())
        self.root.bind("<Control-Right>",  lambda e: self.skip())
        self.root.bind("<Control-Left>",   lambda e: self.prev_image())
        _bind("z", self.undo)
        _bind("d", self.delete_current)
        _bind("q", self.analyze_ai)
        _bind("p", self.play_current)
        self.root.bind("<Return>", lambda e: self.move()
                       if not isinstance(e.widget, (ttk.Entry, ttk.Combobox)) else None)
        self.root.bind("<space>",  lambda e: self.skip()
                       if not isinstance(e.widget, (ttk.Entry, ttk.Combobox)) else None)

        self.char_entries[0].focus()
    def _on_close(self):
        self._save_position()
        self.root.destroy()

    # ── モード切替 ──

if __name__ == "__main__":
    root = tk.Tk()
    app = SortApp(root)
    root.mainloop()
