import 'package:app/services/auth_service.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

class SignInScreen extends ConsumerStatefulWidget {
  const SignInScreen({super.key});

  @override
  ConsumerState<SignInScreen> createState() => _SignInScreenState();
}

class _SignInScreenState extends ConsumerState<SignInScreen> {
  bool _isLoading = false;

  Future<void> _signIn() async {
    // 処理中はボタンを無効化
    if (_isLoading) return;

    setState(() {
      _isLoading = true;
    });

    try {
      // AuthService経由でサインイン処理を実行
      await ref.read(authServiceProvider).signIn();
      // 成功した場合、AuthGateが自動的にHomeScreenに遷移させるので、
      // ここで明示的な画面遷移は不要です。
    } catch (e) {
      // エラーが発生した場合はSnackBarで通知
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text('サインインに失敗しました: $e')));
      }
    } finally {
      // 処理が完了したらボタンを有効化
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // 現在の認証方法を取得
    final authMethod = ref.watch(authMethodProvider);
    final buttonText = authMethod == AuthMethod.google
        ? 'Googleでサインイン'
        : '匿名ではじめる';

    return Scaffold(
      body: Center(
        child: _isLoading
            ? const CircularProgressIndicator()
            : ElevatedButton(onPressed: _signIn, child: Text(buttonText)),
      ),
    );
  }
}
