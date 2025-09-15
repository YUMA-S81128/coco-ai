import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:google_sign_in/google_sign_in.dart';

/// 使用する認証方法を定義するEnum
enum AuthMethod { anonymous, google }

/// --dart-defineで渡された環境変数から認証方法を決定するProvider
///
/// デフォルトは `anonymous` (匿名認証)
final authMethodProvider = Provider<AuthMethod>((ref) {
  const method = String.fromEnvironment(
    'AUTH_METHOD',
    defaultValue: 'anonymous',
  );
  if (method == 'google') {
    return AuthMethod.google;
  }
  return AuthMethod.anonymous;
});

/// [AuthService] を提供するプロバイダー
final authServiceProvider = Provider(
  (ref) => AuthService(
    FirebaseAuth.instance,
    GoogleSignIn.instance,
    ref.watch(authMethodProvider),
  ),
);

/// 認証を処理するためのサービスクラス
class AuthService {
  final FirebaseAuth _auth;
  final GoogleSignIn _googleSignIn;
  final AuthMethod _authMethod;

  AuthService(this._auth, this._googleSignIn, this._authMethod);

  /// 現在のユーザーのIDを返す
  /// サインインしていない場合はnullを返す
  String? get currentUserId => _auth.currentUser?.uid;

  /// 認証状態の変更を監視するストリーム
  Stream<User?> get authStateChanges => _auth.authStateChanges();

  /// 設定された認証方法でサインインを実行する
  Future<UserCredential?> signIn() async {
    switch (_authMethod) {
      case AuthMethod.google:
        return _signInWithGoogle();
      case AuthMethod.anonymous:
        return _signInAnonymously();
    }
  }

  /// 匿名認証でサインインする
  Future<UserCredential> _signInAnonymously() async {
    return await _auth.signInAnonymously();
  }

  /// Google認証でサインインする
  Future<UserCredential?> _signInWithGoogle() async {
    // GoogleサインインのUIをトリガー
    final googleUser = await _googleSignIn.signIn();
    if (googleUser == null) {
      // ユーザーがダイアログを閉じた場合
      return null;
    }

    // 認証情報を取得
    final googleAuth = await googleUser.authentication;

    // Firebase用のクレデンシャルを作成
    final credential = GoogleAuthProvider.credential(
      accessToken: googleAuth.accessToken,
      idToken: googleAuth.idToken,
    );

    // Firebaseにサインイン
    return await _auth.signInWithCredential(credential);
  }
}

/// AuthServiceのauthStateChangesストリームを公開するStreamProvider
final authStateChangesProvider = StreamProvider<User?>((ref) {
  return ref.watch(authServiceProvider).authStateChanges;
});
