import 'package:app/screens/home_screen.dart';
import 'package:app/screens/sign_in_screen.dart';
import 'package:app/services/auth_service.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

/// 認証状態に応じて、表示する画面を振り分けるウィジェット
class AuthGate extends ConsumerWidget {
  const AuthGate({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    // 認証状態のストリームを監視
    final authState = ref.watch(authStateChangesProvider);

    return authState.when(
      data: (User? user) {
        if (user != null) {
          // ユーザーがログイン済みの場合、ホーム画面を表示
          return const HomeScreen();
        } else {
          // ユーザーが未ログインの場合、サインイン画面を表示
          return const SignInScreen();
        }
      },
      // 最初の認証状態を取得中はローディングインジケーターを表示
      loading: () =>
          const Scaffold(body: Center(child: CircularProgressIndicator())),
      // エラーが発生した場合はエラーメッセージを表示
      error: (error, stack) =>
          Scaffold(body: Center(child: Text('エラーが発生しました: $error'))),
    );
  }
}
