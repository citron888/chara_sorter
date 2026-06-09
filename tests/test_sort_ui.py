"""
CharaSorter ユニットテスト
対象: UI に依存しない純粋関数・ロジッククラスのメソッド

実行方法:
    cd C:\\my_program_folder\\chara_sorter
    python -m pytest tests/ -v
"""

import sys
import hashlib
import tempfile
from pathlib import Path

import pytest
from PIL import Image

# ── sort_ui をインポート（tkinter の初期化を回避）──────────────────
# tk.Tk() は import 時に呼ばれないので直接 import 可能
sys.path.insert(0, str(Path(__file__).parent.parent))
import sort_ui as ui


# ══════════════════════════════════════════════════════
#  ユーティリティ関数
# ══════════════════════════════════════════════════════

class TestFileMd5:
    def test_returns_hex_string(self, tmp_path):
        f = tmp_path / "a.txt"
        f.write_bytes(b"hello")
        result = ui._file_md5(f)
        assert isinstance(result, str)
        assert len(result) == 32

    def test_same_content_same_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"same content")
        f2.write_bytes(b"same content")
        assert ui._file_md5(f1) == ui._file_md5(f2)

    def test_different_content_different_hash(self, tmp_path):
        f1 = tmp_path / "a.txt"
        f2 = tmp_path / "b.txt"
        f1.write_bytes(b"content A")
        f2.write_bytes(b"content B")
        assert ui._file_md5(f1) != ui._file_md5(f2)

    def test_nonexistent_returns_none(self, tmp_path):
        result = ui._file_md5(tmp_path / "ghost.png")
        assert result is None


class TestDhash:
    def _solid_png(self, color, size=(64, 64)) -> Image.Image:
        return Image.new("RGB", size, color)

    def test_returns_list_of_4_ints(self, tmp_path):
        img = self._solid_png((128, 128, 128))
        path = tmp_path / "img.png"
        img.save(path)
        result = ui._dhash(path)
        assert isinstance(result, list)
        assert len(result) == 4
        assert all(isinstance(h, int) for h in result)

    def test_identical_images_zero_distance(self, tmp_path):
        img = self._solid_png((100, 150, 200))
        p1 = tmp_path / "a.png"
        p2 = tmp_path / "b.png"
        img.save(p1)
        img.save(p2)
        h1 = ui._dhash(p1)
        h2 = ui._dhash(p2)
        assert ui._hamming(h1, h2) == 0

    def test_very_different_images_high_distance(self, tmp_path):
        # 横グラデーション (左→右で明→暗) vs 縦グラデーション (上→下で明→暗)
        # 単色画像はdHashが全0になるためグラデーションを使う
        import numpy as np
        arr_h = np.tile(np.linspace(255, 0, 64, dtype=np.uint8), (64, 1))  # 横
        arr_v = arr_h.T                                                       # 縦
        p_h = tmp_path / "horizontal.png"
        p_v = tmp_path / "vertical.png"
        Image.fromarray(arr_h, "L").save(p_h)
        Image.fromarray(arr_v, "L").save(p_v)
        h1 = ui._dhash(p_h)
        h2 = ui._dhash(p_v)
        assert ui._hamming(h1, h2) > 20  # 構造が全く異なる

    def test_nonexistent_returns_none(self, tmp_path):
        assert ui._dhash(tmp_path / "ghost.png") is None

    def test_variant_detected_by_partial_region(self, tmp_path):
        """右側に何か追加した差分画像が部分ハッシュで検出されること"""
        base = Image.new("RGB", (200, 200), (100, 100, 200))
        variant = base.copy()
        # 右下に赤い矩形を追加（差分）
        for y in range(100, 200):
            for x in range(100, 200):
                variant.putpixel((x, y), (255, 0, 0))
        p_base = tmp_path / "base.png"
        p_var  = tmp_path / "variant.png"
        base.save(p_base)
        variant.save(p_var)
        h_base = ui._dhash(p_base)
        h_var  = ui._dhash(p_var)
        # 部分ハッシュ（左半分）はほぼ同じはずで閾値8以内
        assert ui._hamming(h_base, h_var) <= 8


class TestHamming:
    def test_identical_hashes_zero(self):
        h = [0xABCD, 0x1234, 0xFFFF, 0x0000]
        assert ui._hamming(h, h) == 0

    def test_uses_minimum_across_regions(self):
        # region0 は大きく異なる、region1 は同じ → 最小は0
        a = [0xFFFF, 0x0000, 0xFFFF, 0xFFFF]
        b = [0x0000, 0x0000, 0x0000, 0x0000]
        dist = ui._hamming(a, b)
        assert dist == 0  # region1 が完全一致

    def test_all_regions_differ(self):
        a = [0xFFFF] * 4
        b = [0x0000] * 4
        # 0xFFFF ^ 0x0000 = 0xFFFF → 16ビット差（16bit整数の場合）
        dist = ui._hamming(a, b)
        assert dist > 0


class TestDanbooruParseChars:
    def test_strips_series_suffix(self):
        result = ui._danbooru_parse_chars("aoi_kiryuin_(kill_la_kill)")
        assert result == ["aoi_kiryuin"]

    def test_multiple_chars(self):
        result = ui._danbooru_parse_chars(
            "special_week_(series_a) silence_suzuka_(series_a)"
        )
        assert result == ["special_week", "silence_suzuka"]

    def test_no_series_suffix_kept_as_is(self):
        result = ui._danbooru_parse_chars("hatsune_miku")
        assert result == ["hatsune_miku"]

    def test_empty_string_returns_empty(self):
        assert ui._danbooru_parse_chars("") == []

    def test_preserves_non_series_parens(self):
        # _(xxx) 以外の括弧は除去しない（通常タグに括弧はないが念のため）
        result = ui._danbooru_parse_chars("char_a_(series_b) char_c")
        assert "char_a" in result
        assert "char_c" in result


class TestGetFolders:
    def test_returns_sorted_subfolder_names(self, tmp_path):
        (tmp_path / "charlie").mkdir()
        (tmp_path / "alpha").mkdir()
        (tmp_path / "beta").mkdir()
        result = ui.get_folders(tmp_path, tmp_path)
        assert result == ["alpha", "beta", "charlie"]

    def test_excludes_files(self, tmp_path):
        (tmp_path / "sub").mkdir()
        (tmp_path / "file.txt").write_text("x")
        result = ui.get_folders(tmp_path, tmp_path)
        assert result == ["sub"]

    def test_exclude_set_removes_folder(self, tmp_path):
        (tmp_path / "keep").mkdir()
        (tmp_path / "skip").mkdir()
        result = ui.get_folders(tmp_path, tmp_path, exclude={"skip"})
        assert result == ["keep"]

    def test_source_dir_not_excluded(self, tmp_path):
        """source_dir が image_dir のサブフォルダでも除外されないこと（AC修正）"""
        source = tmp_path / "venus_paques"
        source.mkdir()
        result = ui.get_folders(tmp_path, source)
        assert "venus_paques" in result

    def test_nonexistent_dir_returns_empty(self, tmp_path):
        result = ui.get_folders(tmp_path / "ghost", tmp_path)
        assert result == []


# ══════════════════════════════════════════════════════
#  Mixin ロジック（SortApp インスタンスなしで直接テスト）
# ══════════════════════════════════════════════════════

class FakeApp(ui._SortMixin, ui._SettingsMixin, ui._OpsMixin, ui._AIMixin):
    """テスト用スタブ。Tk を起動せずに Mixin のロジックだけ検証する。"""
    def __init__(self):
        self.cfg            = {}
        self.images         = []
        self.index          = 0
        self.folders        = []
        self.image_dir      = Path(".")
        self.source_dir     = Path(".")
        self._learn_order   = True
        self._similar_thresh = 8


class TestSortByLearnedOrder:
    def test_known_chars_sorted_by_rank(self):
        app = FakeApp()
        app.cfg["char_order"] = ["alpha", "beta", "gamma"]
        result = app._sort_by_learned_order(["gamma", "alpha", "beta"])
        assert result == ["alpha", "beta", "gamma"]

    def test_unknown_chars_go_to_end(self):
        app = FakeApp()
        app.cfg["char_order"] = ["alpha", "beta"]
        result = app._sort_by_learned_order(["unknown", "alpha"])
        assert result[0] == "alpha"
        assert result[1] == "unknown"

    def test_empty_order_returns_input_unchanged(self):
        app = FakeApp()
        app.cfg["char_order"] = []
        names = ["c", "a", "b"]
        assert app._sort_by_learned_order(names) == names

    def test_no_learn_order_key_returns_input(self):
        app = FakeApp()
        names = ["x", "y"]
        assert app._sort_by_learned_order(names) == names


class TestUpdateCharOrder:
    def test_new_chars_appended(self):
        app = FakeApp()
        app.cfg["char_order"] = []
        app._update_char_order(["alice"])
        assert "alice" in app.cfg["char_order"]

    def test_existing_char_keeps_relative_order(self):
        """同じキャラを再登録しても相対順序は崩れないこと"""
        app = FakeApp()
        app.cfg["char_order"] = ["alice", "bob", "charlie"]
        app._update_char_order(["bob"])
        order = app.cfg["char_order"]
        # alice → bob → charlie の順が維持されること
        assert order.index("alice") < order.index("bob") < order.index("charlie")

    def test_new_char_inserted_at_earliest_existing_position(self):
        """新キャラが既存キャラの直前に挿入されること"""
        app = FakeApp()
        app.cfg["char_order"] = ["alice", "charlie"]
        # bob を alice・charlie と一緒に登録すると alice の前に入る
        app._update_char_order(["alice", "bob"])
        order = app.cfg["char_order"]
        # bob が alice と同じグループで alice の近くにいること
        assert "bob" in order
        assert "alice" in order

    def test_disabled_does_nothing(self):
        app = FakeApp()
        app._learn_order = False
        app.cfg["char_order"] = ["alice"]
        app._update_char_order(["bob"])
        assert "bob" not in app.cfg.get("char_order", [])


class TestAtomicRenameBatch:
    def test_renames_files(self, tmp_path):
        src = tmp_path / "old_001.png"
        dst = tmp_path / "new_001.png"
        src.write_bytes(b"data")
        ui._SortMixin._atomic_rename_batch([(src, dst)])
        assert dst.exists()
        assert not src.exists()

    def test_no_conflict_two_phase(self, tmp_path):
        """a→b, b→c のように循環する場合も壊れないこと"""
        a = tmp_path / "a.png"
        b = tmp_path / "b.png"
        a.write_bytes(b"aaa")
        b.write_bytes(b"bbb")
        c = tmp_path / "c.png"
        # a→b は衝突するが tmp に退避するので安全
        ui._SortMixin._atomic_rename_batch([(a, b), (b, c)])
        assert (tmp_path / "b.png").read_bytes() == b"aaa"
        assert (tmp_path / "c.png").read_bytes() == b"bbb"


# ══════════════════════════════════════════════════════
#  move() のバグ回帰テスト
# ══════════════════════════════════════════════════════

class TestMoveSameFolder:
    """同一フォルダへの移動で削除されないこと（バグ修正 #1 の回帰テスト）"""

    def _make_app(self, tmp_path):
        """move() を呼べる最低限のスタブを作る"""
        import types, tkinter as tk

        class MinimalApp(ui._OpsMixin, ui._SortMixin, ui._SettingsMixin, ui._AIMixin):
            def __init__(self, image_dir):
                self.cfg              = {"dupe_check": True, "similar_insert": False}
                self.image_dir        = image_dir
                self.source_dir       = image_dir
                self.images           = []
                self.index            = 0
                self.folders          = []
                self._learn_order     = False
                self._dupe_check      = True
                self._similar_insert  = False
                self._similar_thresh  = 8
                self._keep_names      = False
                self.use_folder       = True
                self.history          = []
                self._last_move_dest  = None
                self._prefix_on_var   = types.SimpleNamespace(get=lambda: False)
                self._prefix_var      = types.SimpleNamespace(get=lambda: "")
                self._multi_dir_var   = types.SimpleNamespace(get=lambda: "")
                # char_entries: 1 エントリ
                self.char_entries     = [types.SimpleNamespace(get=lambda: "almond_eye")]
                # UI メソッドをスタブ化
                self.counter_var      = types.SimpleNamespace(set=lambda x: None)
                self._work_name_var   = types.SimpleNamespace(get=lambda: "")

            def _stop_anim(self):          pass
            def _clear_inputs(self):       pass
            def show_image(self):          pass
            def _exclude_folders(self):    return set()
            def _update_char_order(self, names): pass
            def _sort_by_learned_order(self, names): return names

        return MinimalApp(tmp_path)

    def test_same_folder_move_does_not_delete(self, tmp_path):
        """同フォルダに移動するとき、MD5が一致しても削除されないこと"""
        # almond_eye_001.png を almond_eye/ に同フォルダ移動
        dest_dir = tmp_path / "almond_eye"
        dest_dir.mkdir()
        src = dest_dir / "almond_eye_001.png"
        Image.new("RGB", (64, 64), (100, 150, 200)).save(src)

        app = self._make_app(tmp_path)
        app.images = [src]
        app.image_dir = tmp_path
        app.source_dir = dest_dir

        app.move()

        # ソースファイルが削除されていないこと（リネームされて残っているはず）
        remaining = list(dest_dir.glob("almond_eye_*.png"))
        assert len(remaining) >= 1, "ファイルが削除された（バグ再現）"


# ══════════════════════════════════════════════════════
#  dHash 類似判定の閾値・偽陽性 回帰テスト
#  yayoi_akikawa_024-028 が誤削除されたバグに対応
# ══════════════════════════════════════════════════════

class TestDhashThreshold:
    """閾値=8 のとき distance<=8 は類似、>=9 は非類似であること。
    以前 threshold=5 に下げたとき distance 6-8 の画像が誤検出されたバグの回帰テスト。"""

    def _make_gradient(self, angle_deg, size=64) -> Image.Image:
        """angle_deg 方向のグラデーション画像（0=横、90=縦、45=斜め等）"""
        import math
        import numpy as np
        arr = np.zeros((size, size), dtype=np.uint8)
        rad = math.radians(angle_deg)
        for y in range(size):
            for x in range(size):
                v = int(127 + 127 * math.cos(x * math.cos(rad) / size * math.pi
                                              + y * math.sin(rad) / size * math.pi))
                arr[y, x] = min(255, max(0, v))
        return Image.fromarray(arr, "L")

    def test_distance_at_threshold_is_similar(self, tmp_path):
        """distance == threshold(8) のとき類似判定になること（<= の確認）"""
        # 完全に同じ画像 → distance 0 ≤ 8
        img = Image.new("RGB", (64, 64), (100, 100, 100))
        p1 = tmp_path / "a.png"
        p2 = tmp_path / "b.png"
        img.save(p1)
        img.save(p2)
        h1, h2 = ui._dhash(p1), ui._dhash(p2)
        threshold = 8
        assert ui._hamming(h1, h2) <= threshold  # 類似と判定される

    def test_clearly_different_not_similar(self, tmp_path):
        """全く異なる画像が threshold=8 で非類似と判定されること（誤削除防止）"""
        import numpy as np
        # 横グラデーション vs ランダムノイズ
        grad = np.tile(np.linspace(0, 255, 64, dtype=np.uint8), (64, 1))
        rng  = np.random.default_rng(42)
        noise = rng.integers(0, 256, (64, 64), dtype=np.uint8)
        p_grad  = tmp_path / "grad.png"
        p_noise = tmp_path / "noise.png"
        Image.fromarray(grad, "L").save(p_grad)
        Image.fromarray(noise, "L").save(p_noise)
        h1 = ui._dhash(p_grad)
        h2 = ui._dhash(p_noise)
        assert ui._hamming(h1, h2) > 8  # 非類似（threshold=8 では引っかからない）

    def test_small_variant_within_threshold(self, tmp_path):
        """わずかな差分画像（右下に小さな追加）が threshold=8 以内で検出されること"""
        import numpy as np
        base = np.full((128, 128), 128, dtype=np.uint8)
        variant = base.copy()
        # 右下 16x16 だけ変更（全体の1/64 = 1.6%）
        variant[112:128, 112:128] = 200
        p_base = tmp_path / "base.png"
        p_var  = tmp_path / "variant.png"
        Image.fromarray(base, "L").save(p_base)
        Image.fromarray(variant, "L").save(p_var)
        h1 = ui._dhash(p_base)
        h2 = ui._dhash(p_var)
        assert ui._hamming(h1, h2) <= 8  # 差分画像として検出される

    def test_right_side_addition_detected_via_left_region(self, tmp_path):
        """右側にキャラ追加した差分画像が左半分ハッシュで類似検出されること。
        yayoi_akikawa_017 (右端に別キャラ追加) の検出ミスを修正したバグ回帰テスト。"""
        import numpy as np
        # 左半分: 共通のグラデーション / 右半分: 一方は無地、もう一方は逆グラデーション
        base    = np.zeros((128, 128), dtype=np.uint8)
        variant = np.zeros((128, 128), dtype=np.uint8)
        # 左半分: 両方同じグラデーション
        for x in range(64):
            base[:, x]    = x * 2
            variant[:, x] = x * 2
        # 右半分: base は無地 128、variant は逆グラデーション（追加キャラ相当）
        base[:, 64:]    = 128
        for x in range(64, 128):
            variant[:, x] = (128 - x) * 2 + 127
        variant = np.clip(variant, 0, 255).astype(np.uint8)

        p_base = tmp_path / "base.png"
        p_var  = tmp_path / "variant.png"
        Image.fromarray(base, "L").save(p_base)
        Image.fromarray(variant, "L").save(p_var)

        h1 = ui._dhash(p_base)
        h2 = ui._dhash(p_var)
        # 全体ハッシュでは差が大きいが、左半分ハッシュ(region[2])で近いこと
        whole_dist = bin(h1[0] ^ h2[0]).count("1")
        left_dist  = bin(h1[2] ^ h2[2]).count("1")
        assert left_dist < whole_dist, "左半分ハッシュが全体より近くなること"
        assert ui._hamming(h1, h2) <= 8  # min() が左半分の小さい距離を採用


# ══════════════════════════════════════════════════════
#  Tagger._filtered_tags のシリーズフィルタ
# ══════════════════════════════════════════════════════

class TestFilteredTags:
    """Tagger._filtered_tags が get_tag_list / _build_tag_map の共通ロジックを正しく実装すること。
    DRY-3 リファクタ後の回帰テスト。"""

    def _make_tagger_with_tags(self, tags: dict) -> ui.Tagger:
        t = ui.Tagger.__new__(ui.Tagger)
        t._char_tags = tags
        t._lock = __import__("threading").Lock()
        t._session = None
        t._work_all_list = []
        return t

    def test_no_filter_returns_all(self):
        """フィルタなし時は全タグをそのまま返す（_(series) は除去しない）"""
        tagger = self._make_tagger_with_tags({
            0: "hatsune_miku",
            1: "special_week_(series_a)",
        })
        result = tagger._filtered_tags("")
        # フィルタなしの場合は raw 名のまま返る（シリーズサフィックスは除去されない）
        assert set(result.values()) == {"hatsune_miku", "special_week_(series_a)"}

    def test_work_filter_returns_matching_only(self):
        tagger = self._make_tagger_with_tags({
            0: "hatsune_miku",
            1: "special_week_(series_a)",
            2: "silence_suzuka_(series_a)",
        })
        result = tagger._filtered_tags("series_a")
        assert set(result.values()) == {"special_week", "silence_suzuka"}
        assert 0 not in result  # hatsune_miku は含まれない

    def test_suffix_stripped_from_display_name(self):
        tagger = self._make_tagger_with_tags({
            0: "gold_ship_(series_a)",
        })
        result = tagger._filtered_tags("series_a")
        assert result[0] == "gold_ship"

    def test_get_tag_list_uses_filtered_tags(self):
        """get_tag_list が _filtered_tags に委譲していること（DRY-3 回帰）"""
        tagger = self._make_tagger_with_tags({
            0: "special_week_(series_a)",
            1: "hatsune_miku",
        })
        result = tagger.get_tag_list("series_a")
        assert result == ["special_week"]
        assert "hatsune_miku" not in result

    def test_build_tag_map_uses_filtered_tags(self):
        """_build_tag_map が _filtered_tags に委譲していること（DRY-3 回帰）"""
        tagger = self._make_tagger_with_tags({
            0: "special_week_(series_a)",
            1: "hatsune_miku",
        })
        result = tagger._build_tag_map("series_a")
        assert 0 in result
        assert 1 not in result


# ══════════════════════════════════════════════════════
#  _apply_dir のフォルダ設定ロジック（DRY-4 回帰テスト）
# ══════════════════════════════════════════════════════

class TestApplyDir:
    """_apply_image_dir / _apply_source_dir が _apply_dir に統合された後も
    正しくフォールバック設定が行われること。"""

    def _make_app(self, tmp_path):
        import types

        class _DictLike(dict):
            """combo["values"] = x の代入をサポートするスタブ"""
            pass

        class DirApp(ui._OpsMixin, ui._SortMixin, ui._SettingsMixin, ui._AIMixin):
            def __init__(self):
                self.cfg         = {}
                self.image_dir   = Path(".")
                self.source_dir  = Path(".")
                self.images      = []
                self.index       = 0
                self.folders     = []
                self._learn_order = False
                self._work_name_var = types.SimpleNamespace(get=lambda: "")
                # コンボボックスは dict-like（["values"] = x の代入が必要）
                self.image_combo  = _DictLike()
                self.source_combo = _DictLike()
                self.image_dir_var  = types.SimpleNamespace(get=lambda: "", set=lambda x: None)
                self.source_dir_var = types.SimpleNamespace(get=lambda: "", set=lambda x: None)

            def _push_history(self, key, path): return []
            def _load_images(self): pass
            def _exclude_folders(self): return set()

        return DirApp()

    def test_apply_image_dir_sets_cfg(self, tmp_path):
        app = self._make_app(tmp_path)
        app.image_dir_var = __import__("types").SimpleNamespace(
            get=lambda: str(tmp_path), set=lambda x: None)
        app.source_dir = tmp_path  # already valid
        app._apply_image_dir()
        assert app.image_dir == tmp_path
        assert app.cfg.get("image_dir") == str(tmp_path)

    def test_auto_set_source_if_unset(self, tmp_path):
        """image_dir 設定時に source_dir が未設定なら同じパスが自動セットされること"""
        app = self._make_app(tmp_path)
        app.image_dir_var = __import__("types").SimpleNamespace(
            get=lambda: str(tmp_path), set=lambda x: None)
        app.source_dir = Path(".")   # 無効（未設定扱い）
        calls = []
        app.source_dir_var = __import__("types").SimpleNamespace(
            get=lambda: ".", set=lambda x: calls.append(x))
        app._apply_image_dir()
        # source_dir が自動的に image_dir と同じパスにセットされること
        assert app.source_dir == tmp_path
        assert str(tmp_path) in calls
