/// アプリケーション内で使用するアセットのパスを管理するクラスです。
///
/// ファイルパスを直接文字列で記述するのではなく、このクラスの定数を参照することで、
/// 型安全性を高め、将来のパス変更に強くします。
class AppAssets {
  static const String coco = 'assets/images/coco.png';
  static const String ai = 'assets/images/ai.png';
}

